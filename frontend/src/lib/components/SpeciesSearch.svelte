<script>
	import { createEventDispatcher } from 'svelte';
	import { searchSpecies } from '../api.js';

	export let placeholder = 'ポケモン名で検索';

	const dispatch = createEventDispatcher();

	let query = '';
	let results = [];
	let loading = false;
	let error = '';
	let debounceHandle;

	function onInput() {
		clearTimeout(debounceHandle);
		debounceHandle = setTimeout(runSearch, 250);
	}

	async function runSearch() {
		if (!query.trim()) {
			results = [];
			return;
		}
		loading = true;
		error = '';
		try {
			results = await searchSpecies(query.trim());
		} catch (e) {
			error = e.message;
		} finally {
			loading = false;
		}
	}

	function select(item) {
		dispatch('select', item);
		query = '';
		results = [];
	}
</script>

<div class="search">
	<input type="text" bind:value={query} on:input={onInput} {placeholder} />
	{#if loading}<span class="hint">検索中…</span>{/if}
	{#if error}<span class="hint error">{error}</span>{/if}
	{#if results.length > 0}
		<ul class="results">
			{#each results as item (item.id)}
				<li>
					<button type="button" on:click={() => select(item)}>{item.name_ja ?? item.name}</button>
				</li>
			{/each}
		</ul>
	{/if}
</div>

<style>
	.search {
		position: relative;
	}
	.results {
		position: absolute;
		z-index: 10;
		list-style: none;
		margin: var(--size-1) 0 0;
		padding: var(--size-1);
		max-height: 220px;
		overflow-y: auto;
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius);
		box-shadow: var(--shadow);
		min-width: 12rem;
	}
	.results li button {
		width: 100%;
		text-align: left;
		border: none;
		background: transparent;
	}
	.results li button:hover {
		background: var(--color-bg);
	}
	.hint {
		display: block;
		font-size: var(--font-size-0);
		color: var(--color-text-muted);
	}
	.hint.error {
		color: var(--color-danger);
	}
</style>
