<script>
	import { STAT_KEYS, STAT_LABELS, MAX_EV_PER_STAT, MAX_EV_TOTAL, totalEv } from '../stats.js';

	export let evs;

	$: total = totalEv(evs);
	$: over = total > MAX_EV_TOTAL;

	function onChange(key, raw) {
		let value = Number(raw);
		if (Number.isNaN(value)) value = 0;
		value = Math.max(0, Math.min(MAX_EV_PER_STAT, value));
		evs = { ...evs, [key]: value };
	}
</script>

<div class="ev-allocator">
	<div class="total" class:over>努力値合計: {total} / {MAX_EV_TOTAL}</div>
	<div class="grid">
		{#each STAT_KEYS as key (key)}
			<label>
				<span>{STAT_LABELS[key]}</span>
				<input
					type="number"
					min="0"
					max={MAX_EV_PER_STAT}
					step="4"
					value={evs[key]}
					on:input={(e) => onChange(key, e.target.value)}
				/>
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
