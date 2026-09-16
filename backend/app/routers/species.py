"""PokéAPI(https://pokeapi.co/)へのプロキシ・簡易キャッシュ。

このアプリ自身のDBにはゲームの大量データ(種族・技等)を複製せず、
必要な都度PokéAPIから取得する。プロセス内メモリに軽くキャッシュする
ことでPokéAPIへの負荷とレスポンス時間を抑える。

日本語での検索・表示に対応するため、種族名・特性名・技名は
pokemon-species / ability / move の names(language=ja-Hrkt)から取得する。
特性・技はタイプと違って総数が多い(技だけで900以上)ため、事前に
全件を取得するのではなく、実際に登場した分だけをその都度キャッシュに
追加していく方式にしている。EC2上の常駐プロセスだからこそ、
一度取得した名前はプロセスが生きている間ずっと使い回せる
(サーバーレスでコールドスタートのたびに再取得するのと対照的な設計)。
"""

import asyncio
import re

import httpx
from fastapi import APIRouter, HTTPException, status

from app.config import get_settings

router = APIRouter(prefix="/species", tags=["species"])

_species_name_cache: list[dict] | None = None
_ability_name_cache: dict[str, str] = {}
_move_name_cache: dict[str, str] = {}
_detail_cache: dict[str, dict] = {}
_cache_lock = asyncio.Lock()
_fetch_semaphore = asyncio.Semaphore(20)

_STAT_NAME_MAP = {
    "hp": "hp",
    "attack": "attack",
    "defense": "defense",
    "special-attack": "special_attack",
    "special-defense": "special_defense",
    "speed": "speed",
}

# タイプ名は18種類のみの固定語彙のため、都度PokéAPIを呼ばずハードコードする。
TYPE_NAME_JA = {
    "normal": "ノーマル",
    "fire": "ほのお",
    "water": "みず",
    "electric": "でんき",
    "grass": "くさ",
    "ice": "こおり",
    "fighting": "かくとう",
    "poison": "どく",
    "ground": "じめん",
    "flying": "ひこう",
    "psychic": "エスパー",
    "bug": "むし",
    "rock": "いわ",
    "ghost": "ゴースト",
    "dragon": "ドラゴン",
    "dark": "あく",
    "steel": "はがね",
    "fairy": "フェアリー",
}

_URL_ID_RE = re.compile(r"/(\d+)/?$")


def _extract_id(url: str) -> int:
    match = _URL_ID_RE.search(url)
    if not match:
        raise ValueError(f"IDを抽出できませんでした: {url}")
    return int(match.group(1))


def _japanese_name(names: list[dict]) -> str | None:
    for entry in names:
        if entry["language"]["name"] == "ja-Hrkt":
            return entry["name"]
    for entry in names:
        if entry["language"]["name"] == "ja":
            return entry["name"]
    return None


async def _get_species_name_cache(client: httpx.AsyncClient) -> list[dict]:
    """id / 英語名(スラッグ) / 日本語名 の一覧を構築してキャッシュする。

    対応範囲は基本種族(フォルム違いを除く)。メガシンカ等のフォルムは
    現状英語名のみの検索対象外とし、既知の制約としてREADMEに明記する。
    """
    global _species_name_cache
    async with _cache_lock:
        if _species_name_cache is not None:
            return _species_name_cache

        base_url = get_settings().pokeapi_base_url
        first_page = await client.get(f"{base_url}/pokemon-species", params={"limit": 1})
        first_page.raise_for_status()
        total = first_page.json()["count"]

        list_resp = await client.get(f"{base_url}/pokemon-species", params={"limit": total})
        list_resp.raise_for_status()
        entries = list_resp.json()["results"]

        async def fetch_one(entry: dict) -> dict:
            species_id = _extract_id(entry["url"])
            async with _fetch_semaphore:
                resp = await client.get(f"{base_url}/pokemon-species/{species_id}")
                resp.raise_for_status()
                data = resp.json()
            return {
                "id": species_id,
                "name": entry["name"],
                "name_ja": _japanese_name(data["names"]) or entry["name"],
            }

        _species_name_cache = await asyncio.gather(*(fetch_one(e) for e in entries))
        return _species_name_cache


async def _get_ja_names(
    client: httpx.AsyncClient, category: str, slugs: list[str], cache: dict[str, str]
) -> dict[str, str]:
    """指定カテゴリ(ability/move)のスラッグ群について、日本語名をまとめて解決する。

    既にキャッシュ済みのものはリクエストをスキップし、未取得のものだけ
    並列取得する。
    """
    base_url = get_settings().pokeapi_base_url
    missing = [s for s in dict.fromkeys(slugs) if s not in cache]

    async def fetch_one(slug: str) -> None:
        async with _fetch_semaphore:
            resp = await client.get(f"{base_url}/{category}/{slug}")
        if resp.status_code == status.HTTP_200_OK:
            cache[slug] = _japanese_name(resp.json()["names"]) or slug
        else:
            cache[slug] = slug

    if missing:
        await asyncio.gather(*(fetch_one(s) for s in missing))
    return {s: cache[s] for s in slugs}


@router.get("/search")
async def search_species(q: str = "", limit: int = 20) -> list[dict]:
    async with httpx.AsyncClient(timeout=15.0) as client:
        names = await _get_species_name_cache(client)
    query = q.strip()
    query_lower = query.lower()
    if not query:
        matches = names[:limit]
    else:
        matches = [
            item
            for item in names
            if query_lower in item["name"].lower() or query in item["name_ja"]
        ][:limit]
    return matches


@router.get("/{identifier}")
async def get_species_detail(identifier: str) -> dict:
    key = identifier.lower()
    if key in _detail_cache:
        return _detail_cache[key]

    base_url = get_settings().pokeapi_base_url
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get(f"{base_url}/pokemon/{key}")
        if resp.status_code == status.HTTP_404_NOT_FOUND:
            raise HTTPException(status_code=404, detail="指定された種族が見つかりません")
        resp.raise_for_status()
        data = resp.json()

        name_ja = None
        species_url = data.get("species", {}).get("url")
        if species_url:
            species_resp = await client.get(species_url)
            if species_resp.status_code == status.HTTP_200_OK:
                name_ja = _japanese_name(species_resp.json()["names"])

        ability_slugs = [a["ability"]["name"] for a in data["abilities"]]
        move_slugs = [m["move"]["name"] for m in data["moves"]]
        ability_ja, move_ja = await asyncio.gather(
            _get_ja_names(client, "ability", ability_slugs, _ability_name_cache),
            _get_ja_names(client, "move", move_slugs, _move_name_cache),
        )

    base_stats = {
        _STAT_NAME_MAP[s["stat"]["name"]]: s["base_stat"]
        for s in data["stats"]
        if s["stat"]["name"] in _STAT_NAME_MAP
    }
    result = {
        "id": data["id"],
        "name": data["name"],
        "name_ja": name_ja or data["name"],
        "types": [
            {"name": t["type"]["name"], "name_ja": TYPE_NAME_JA.get(t["type"]["name"], t["type"]["name"])}
            for t in data["types"]
        ],
        "base_stats": base_stats,
        "abilities": [
            {
                "name": a["ability"]["name"],
                "name_ja": ability_ja[a["ability"]["name"]],
                "is_hidden": a["is_hidden"],
            }
            for a in data["abilities"]
        ],
        "moves": [
            {
                "id": _extract_id(m["move"]["url"]),
                "name": m["move"]["name"],
                "name_ja": move_ja[m["move"]["name"]],
            }
            for m in data["moves"]
        ],
    }
    _detail_cache[key] = result
    return result
