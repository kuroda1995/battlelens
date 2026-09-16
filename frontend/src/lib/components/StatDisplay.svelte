<script>
	import { STAT_KEYS, STAT_LABELS, calculateStats } from '../stats.js';

	export let baseStats;
	export let ivs;
	export let evs;
	export let nature;
	export let level = 50;

	$: stats = baseStats ? calculateStats(baseStats, ivs, evs, nature, level) : null;
</script>

{#if stats}
	<table class="stats">
		<thead>
			<tr>
				{#each STAT_KEYS as key (key)}
					<th>{STAT_LABELS[key]}</th>
				{/each}
			</tr>
		</thead>
		<tbody>
			<tr>
				{#each STAT_KEYS as key (key)}
					<td>{stats[key]}</td>
				{/each}
			</tr>
		</tbody>
	</table>
{/if}

<style>
	.stats {
		border-collapse: collapse;
		width: 100%;
	}
	.stats th,
	.stats td {
		border: 1px solid var(--color-border);
		padding: var(--size-1) var(--size-2);
		text-align: center;
		font-size: var(--font-size-0);
	}
	.stats th {
		background: var(--color-bg);
	}
</style>
