/**
 * 実数値の即時プレビュー用ロジック。
 * バックエンド (backend/app/calculations/stats.py) と同じ計算式のJS版。
 * 保存時の正としてのバリデーション・計算はバックエンドが担うため、
 * ここではUXのための軽量な再実装として重複を許容している。
 */

export const STAT_KEYS = ['hp', 'attack', 'defense', 'special_attack', 'special_defense', 'speed'];

export const STAT_LABELS = {
	hp: 'HP',
	attack: 'こうげき',
	defense: 'ぼうぎょ',
	special_attack: 'とくこう',
	special_defense: 'とくぼう',
	speed: 'すばやさ'
};

export const NATURES = {
	hardy: [null, null],
	docile: [null, null],
	serious: [null, null],
	bashful: [null, null],
	quirky: [null, null],
	lonely: ['attack', 'defense'],
	brave: ['attack', 'speed'],
	adamant: ['attack', 'special_attack'],
	naughty: ['attack', 'special_defense'],
	bold: ['defense', 'attack'],
	relaxed: ['defense', 'speed'],
	impish: ['defense', 'special_attack'],
	lax: ['defense', 'special_defense'],
	timid: ['speed', 'attack'],
	hasty: ['speed', 'defense'],
	jolly: ['speed', 'special_attack'],
	naive: ['speed', 'special_defense'],
	modest: ['special_attack', 'attack'],
	mild: ['special_attack', 'defense'],
	quiet: ['special_attack', 'speed'],
	rash: ['special_attack', 'special_defense'],
	calm: ['special_defense', 'attack'],
	gentle: ['special_defense', 'defense'],
	sassy: ['special_defense', 'speed'],
	careful: ['special_defense', 'special_attack']
};

export const NATURE_LABELS_JA = {
	hardy: 'がんばりや',
	lonely: 'さみしがり',
	brave: 'ゆうかん',
	adamant: 'いじっぱり',
	naughty: 'やんちゃ',
	bold: 'ずぶとい',
	docile: 'すなお',
	relaxed: 'のんき',
	impish: 'わんぱく',
	lax: 'のうてんき',
	timid: 'おくびょう',
	hasty: 'せっかち',
	serious: 'まじめ',
	jolly: 'ようき',
	naive: 'むじゃき',
	modest: 'ひかえめ',
	mild: 'おっとり',
	quiet: 'れいせい',
	bashful: 'てれや',
	rash: 'うっかりや',
	calm: 'おだやか',
	gentle: 'おとなしい',
	sassy: 'なまいき',
	careful: 'しんちょう',
	quirky: 'きまぐれ'
};

export const TYPE_ORDER = [
	'normal',
	'fire',
	'water',
	'electric',
	'grass',
	'ice',
	'fighting',
	'poison',
	'ground',
	'flying',
	'psychic',
	'bug',
	'rock',
	'ghost',
	'dragon',
	'dark',
	'steel',
	'fairy'
];

export const TYPE_LABELS_JA = {
	normal: 'ノーマル',
	fire: 'ほのお',
	water: 'みず',
	electric: 'でんき',
	grass: 'くさ',
	ice: 'こおり',
	fighting: 'かくとう',
	poison: 'どく',
	ground: 'じめん',
	flying: 'ひこう',
	psychic: 'エスパー',
	bug: 'むし',
	rock: 'いわ',
	ghost: 'ゴースト',
	dragon: 'ドラゴン',
	dark: 'あく',
	steel: 'はがね',
	fairy: 'フェアリー'
};

export const ITEM_LABELS_JA = {
	none: 'なし',
	'choice-band': 'こだわりハチマキ(こうげき×1.5)',
	'choice-specs': 'こだわりメガネ(とくこう×1.5)',
	'choice-scarf': 'こだわりスカーフ(すばやさ×1.5)',
	'life-orb': 'いのちのたま(与ダメージ×1.3)',
	'expert-belt': 'たつじんのおび(効果ばつぐん時×1.2)',
	'assault-vest': 'とつげきチョッキ(とくぼう×1.5)',
	eviolite: 'しんかのきせき(ぼうぎょ・とくぼう×1.5)'
};

export const WEATHER_LABELS_JA = {
	none: 'なし',
	sun: 'はれ',
	rain: 'あめ',
	sand: 'すなあらし',
	snow: 'ゆき'
};

// 努力値は「ポケモンチャンピオンズ」仕様の0〜32段階(backend/app/calculations/stats.py
// と同じ式。実機の実測値で検証済み)。
// - 無補正 / 上がりやすい方: 1段階につき内部加算値+2
// - 上がりやすい方は、さらに最終値に従来シリーズと同じ×1.1の補正がかかる
// - 上がりにくい方は、乗算補正はかからない代わりに10・20・30段階目で増加が止まる(+0)
export const MAX_EV_PER_STAT = 32;
export const MAX_EV_TOTAL = 66;
export const MAX_IV = 31;

const HINDER_FLAT_STAGES = new Set([10, 20, 30]);

export function natureRole(nature, statKey) {
	if (statKey === 'hp') return 'neutral';
	const pair = NATURES[nature];
	if (!pair) return 'neutral';
	const [boosted, lowered] = pair;
	if (statKey === boosted) return 'boost';
	if (statKey === lowered) return 'hinder';
	return 'neutral';
}

export function evStageContribution(stage, role) {
	let contribution = stage * 2;
	if (role === 'hinder') {
		let penalty = 0;
		for (const s of HINDER_FLAT_STAGES) if (s <= stage) penalty += 1;
		contribution -= penalty * 2;
	}
	return contribution;
}

export function calculateStat(base, iv, ev, level, statKey, nature) {
	const role = natureRole(nature, statKey);
	const contribution = evStageContribution(ev, role);
	const inner = Math.floor(((2 * base + iv + contribution) * level) / 100);
	if (statKey === 'hp') {
		return inner + level + 10;
	}
	const raw = inner + 5;
	if (role === 'boost') {
		// 浮動小数点の誤差(140*1.1=153.999...等)を避けるため整数演算で×1.1する
		return Math.floor((raw * 11) / 10);
	}
	return raw;
}

export function calculateStats(baseStats, ivs, evs, nature, level = 50) {
	const result = {};
	for (const key of STAT_KEYS) {
		result[key] = calculateStat(baseStats[key] ?? 0, ivs[key] ?? MAX_IV, evs[key] ?? 0, level, key, nature);
	}
	return result;
}

export function totalEv(evs) {
	return STAT_KEYS.reduce((sum, key) => sum + (evs[key] ?? 0), 0);
}
