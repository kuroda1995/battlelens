"""PokéAPIへの問い合わせで複数のルーター(species/moves/damage)が共通して使う
ユーティリティ。並列リクエスト数の上限(セマフォ)もここで一元管理する。
"""

from __future__ import annotations

import asyncio
import re

fetch_semaphore = asyncio.Semaphore(20)

_URL_ID_RE = re.compile(r"/(\d+)/?$")


def extract_id(url: str) -> int:
    match = _URL_ID_RE.search(url)
    if not match:
        raise ValueError(f"IDを抽出できませんでした: {url}")
    return int(match.group(1))


def japanese_name(names: list[dict]) -> str | None:
    for entry in names:
        if entry["language"]["name"] == "ja-Hrkt":
            return entry["name"]
    for entry in names:
        if entry["language"]["name"] == "ja":
            return entry["name"]
    return None
