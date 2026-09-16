<script>
	import SpeciesSearch from './SpeciesSearch.svelte';
	import EVAllocator from './EVAllocator.svelte';
	import { NATURES, NATURE_LABELS_JA, ITEM_LABELS_JA } from '../stats.js';
	import { getSpeciesDetail } from '../api.js';

	export let side;
	export let label;

	let loading = false;
	let error = '';

	async function onSelectSpecies(event) {
		const { id } = event.detail;
		loading = true;
		error = '';
		try {
			const detail = await getSpeciesDetail(id);
			side = { ...side, speciesDetail: detail };
		} catch (e) {
			error = e.message;
		} finally {
			loading = false;
		}
	}

	function changeSpecies() {
		side = { ...side, speciesDetail: null };
	}
</script>

<div class="card side">
	<h3>{label}</h3>
	{#if !side.speciesDetail}
		<SpeciesSearch on:select={onSelectSpecies} />
		{#if loading}<p>読み込み中…</p>{/if}
		{#if error}<p class="error">{error}</p>{/if}
	{:else}
		<div class="species-row">
			<div>
				<strong>{side.speciesDetail.name_ja ?? side.speciesDetail.name}</strong>
				{#each side.speciesDetail.types as t (t.name)}
					<span class="type-badge type-{t.name}">{t.name_ja}</span>
				{/each}
			</div>
			<button type="button" on:click={changeSpecies}>変更</button>
		</div>

		<div class="fields">
			<label>
				<span>レベル</span>
				<input type="number" min="1" max="100" bind:value={side.level} />
			</label>
			<label>
				<span>せいかく</span>
				<select bind:value={side.nature}>
					{#each Object.keys(NATURES) as n (n)}
						<option value={n}>{NATURE_LABELS_JA[n]}</option>
					{/each}
				</select>
			</label>
			<label>
				<span>もちもの</span>
				<select bind:value={side.item}>
					{#each Object.entries(ITEM_LABELS_JA) as [key, jaLabel] (key)}
						<option value={key}>{jaLabel}</option>
					{/each}
				</select>
			</label>
		</div>

		<h4>努力値</h4>
		<EVAllocator bind:evs={side.evs} />

		<slot />
	{/if}
</div>

<style>
	.side {
		display: flex;
		flex-direction: column;
		gap: var(--size-2);
	}
	.species-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: var(--size-2);
	}
	.fields {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(9rem, 1fr));
		gap: var(--size-2);
	}
	.fields label {
		display: flex;
		flex-direction: column;
		font-size: var(--font-size-0);
		gap: var(--size-1);
	}
	h4 {
		margin: var(--size-2) 0 0;
	}
	.error {
		color: var(--color-danger);
	}
</style>
