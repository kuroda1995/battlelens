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

export const MAX_EV_PER_STAT = 252;
export const MAX_EV_TOTAL = 510;
export const MAX_IV = 31;

export function natureModifier(nature, statKey) {
	if (statKey === 'hp') return 1;
	const pair = NATURES[nature];
	if (!pair) return 1;
	const [boosted, lowered] = pair;
	if (statKey === boosted) return 1.1;
	if (statKey === lowered) return 0.9;
	return 1;
}

export function calculateStat(base, iv, ev, level, statKey, nature) {
	const inner = Math.floor(((2 * base + iv + Math.floor(ev / 4)) * level) / 100);
	if (statKey === 'hp') {
		return inner + level + 10;
	}
	const value = inner + 5;
	return Math.floor(value * natureModifier(nature, statKey));
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
