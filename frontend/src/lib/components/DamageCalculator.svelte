<script>
	import DamageSideEditor from './DamageSideEditor.svelte';
	import MoveTypeSelect from './MoveTypeSelect.svelte';
	import { WEATHER_LABELS_JA, TYPE_LABELS_JA } from '../stats.js';
	import { calcDamage } from '../api.js';

	function newSide() {
		return {
			speciesDetail: null,
			level: 50,
			nature: 'hardy',
			evs: { hp: 0, attack: 0, defense: 0, special_attack: 0, special_defense: 0, speed: 0 },
			ivs: { hp: 31, attack: 31, defense: 31, special_attack: 31, special_defense: 31, speed: 31 },
			item: 'none'
		};
	}

	const DAMAGE_CLASS_LABEL = { physical: '物理', special: '特殊', status: '変化' };
	const TURN_ORDER_LABEL = {
		attacker: 'こうげき側が先制',
		defender: 'ぼうぎょ側が先制',
		tie: '同速(五分五分)'
	};

	let attacker = newSide();
	let defender = newSide();
	let moveId = null;
	let weather = 'none';
	let trickRoom = false;
	let critical = false;
	let result = null;
	let error = '';
	let calculating = false;

	$: availableMoves = attacker.speciesDetail?.moves ?? [];
	$: selectedMove = availableMoves.find((m) => String(m.id) === String(moveId)) ?? null;

	async function calculate() {
		error = '';
		result = null;
		if (!attacker.speciesDetail || !defender.speciesDetail) {
			error = 'こうげき側・ぼうぎょ側の両方でポケモンを選択してください';
			return;
		}
		if (!selectedMove) {
			error = '技を選択してください';
			return;
		}
		calculating = true;
		try {
			result = await calcDamage({
				attacker: {
					base_stats: attacker.speciesDetail.base_stats,
					types: attacker.speciesDetail.types.map((t) => t.name),
					nature: attacker.nature,
					evs: attacker.evs,
					ivs: attacker.ivs,
					level: attacker.level,
					item: attacker.item
				},
				defender: {
					base_stats: defender.speciesDetail.base_stats,
					types: defender.speciesDetail.types.map((t) => t.name),
					nature: defender.nature,
					evs: defender.evs,
					ivs: defender.ivs,
					level: defender.level,
					item: defender.item
				},
				move_power: selectedMove.power,
				move_type: selectedMove.type,
				move_damage_class: selectedMove.damage_class === 'special' ? 'special' : 'physical',
				weather,
				trick_room: trickRoom,
				critical
			});
		} catch (e) {
			error = e.message;
		} finally {
			calculating = false;
		}
	}
</script>

<div class="layout">
	<DamageSideEditor bind:side={attacker} label="こうげき側">
		{#if attacker.speciesDetail}
			<h4>わざ</h4>
			<div class="field">
				<span class="field-label">技を選択</span>
				<MoveTypeSelect moves={availableMoves} bind:value={moveId} />
			</div>
			{#if selectedMove}
				<p class="muted">
					威力: {selectedMove.power || '-'} / タイプ: {TYPE_LABELS_JA[selectedMove.type] ??
						selectedMove.type} / 区分: {DAMAGE_CLASS_LABEL[selectedMove.damage_class] ??
						selectedMove.damage_class}
				</p>
			{/if}
		{/if}
	</DamageSideEditor>

	<DamageSideEditor bind:side={defender} label="ぼうぎょ側" />
</div>

<div class="card conditions">
	<label>
		<span>天候</span>
		<select bind:value={weather}>
			{#each Object.entries(WEATHER_LABELS_JA) as [key, jaLabel] (key)}
				<option value={key}>{jaLabel}</option>
			{/each}
		</select>
	</label>
	<label class="checkbox">
		<input type="checkbox" bind:checked={trickRoom} />
		<span>トリックルーム</span>
	</label>
	<label class="checkbox">
		<input type="checkbox" bind:checked={critical} />
		<span>急所に当たる</span>
	</label>
	<button type="button" class="primary" on:click={calculate} disabled={calculating}>
		{calculating ? '計算中…' : 'ダメージを計算する'}
	</button>
</div>

{#if error}<p class="error">{error}</p>{/if}

{#if result}
	<div class="card result">
		<h3>計算結果</h3>
		{#if result.max_damage === 0}
			<p>このわざは効果がありません(ダメージ0)。</p>
		{:else}
			<p>
				ダメージ: {result.min_damage} 〜 {result.max_damage}
				({result.min_percent}% 〜 {result.max_percent}%)
			</p>
			<p>相手の最大HP: {result.defender_hp}</p>
			<p>確定数: {result.hits_to_ko_best}発 〜 {result.hits_to_ko_worst}発</p>
		{/if}
		<p>
			素早さ: こうげき側 {result.attacker_speed} / ぼうぎょ側 {result.defender_speed}
			→ {TURN_ORDER_LABEL[result.turn_order]}
		</p>
	</div>
{/if}

<style>
	.layout {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: var(--size-4);
	}
	@media (max-width: 800px) {
		.layout {
			grid-template-columns: 1fr;
		}
	}
	h4 {
		margin: var(--size-2) 0 0;
	}
	label,
	.field {
		display: flex;
		flex-direction: column;
		font-size: var(--font-size-0);
		gap: var(--size-1);
	}
	.conditions {
		margin-top: var(--size-3);
		display: flex;
		flex-wrap: wrap;
		gap: var(--size-3);
		align-items: end;
	}
	.checkbox {
		flex-direction: row;
		align-items: center;
	}
	.result {
		margin-top: var(--size-3);
	}
	.muted {
		color: var(--color-text-muted);
		font-size: var(--font-size-0);
	}
	.error {
		color: var(--color-danger);
	}
</style>
