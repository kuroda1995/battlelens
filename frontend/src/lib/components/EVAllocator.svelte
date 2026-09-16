<script>
	import { STAT_KEYS, STAT_LABELS, MAX_EV_PER_STAT, MAX_EV_TOTAL, totalEv } from '../stats.js';

	export let evs;

	// 努力値は0〜32段階(ポケモンチャンピオンズ仕様)。選択式にして
	// 数値入力の上下クリック操作(時間がかかる)を避ける。
	const EV_OPTIONS = Array.from({ length: MAX_EV_PER_STAT + 1 }, (_, i) => i);

	$: total = totalEv(evs);
	$: over = total > MAX_EV_TOTAL;

	function onChange(key, raw) {
		evs = { ...evs, [key]: Number(raw) };
	}
</script>

<div class="ev-allocator">
	<div class="total" class:over>努力値合計: {total} / {MAX_EV_TOTAL}段階</div>
	<div class="grid">
		{#each STAT_KEYS as key (key)}
			<label>
				<span>{STAT_LABELS[key]}</span>
				<select value={evs[key]} on:change={(e) => onChange(key, e.target.value)}>
					{#each EV_OPTIONS as v (v)}
						<option value={v}>{v}</option>
					{/each}
				</select>
			</label>
		{/each}
	</div>
</div>

<style>
	.grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(6rem, 1fr));
		gap: var(--size-2);
	}
	label {
		display: flex;
		flex-direction: column;
		font-size: var(--font-size-0);
		gap: var(--size-1);
	}
	.total {
		margin-bottom: var(--size-2);
		font-weight: bold;
	}
	.total.over {
		color: var(--color-danger);
	}
</style>
