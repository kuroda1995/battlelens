<script>
	import { createEventDispatcher } from 'svelte';
	import SpeciesSearch from './SpeciesSearch.svelte';
	import EVAllocator from './EVAllocator.svelte';
	import MoveSelector from './MoveSelector.svelte';
	import StatDisplay from './StatDisplay.svelte';
	import { NATURES, STAT_LABELS, NATURE_LABELS_JA } from '../stats.js';
	import { getSpeciesDetail } from '../api.js';

	export let member;

	const dispatch = createEventDispatcher();

	let loadingSpecies = false;
	let error = '';

	function natureLabel(name) {
		const [boost, drop] = NATURES[name];
		const label = NATURE_LABELS_JA[name] ?? name;
		if (!boost) return `${label}(無補正)`;
		return `${label}(+${STAT_LABELS[boost]}/-${STAT_LABELS[drop]})`;
	}

	async function onSelectSpecies(event) {
		const { id } = event.detail;
		loadingSpecies = true;
		error = '';
		try {
			const detail = await getSpeciesDetail(id);
			member = {
				...member,
				speciesDetail: detail,
				ability: detail.abilities[0]?.name_ja ?? '',
				moves: []
			};
		} catch (e) {
			error = e.message;
		} finally {
			loadingSpecies = false;
		}
	}

	function changeSpecies() {
		member = { ...member, speciesDetail: null, moves: [] };
	}
</script>

<div class="card slot">
	<div class="slot-header">
		<strong>#{member.position}</strong>
		<button type="button" class="danger" on:click={() => dispatch('remove')}>削除</button>
	</div>

	{#if !member.speciesDetail}
		<SpeciesSearch on:select={onSelectSpecies} />
		{#if loadingSpecies}<p>読み込み中…</p>{/if}
		{#if error}<p class="error">{error}</p>{/if}
	{:else}
		<div class="species-row">
			<div>
				<strong>{member.speciesDetail.name_ja ?? member.speciesDetail.name}</strong>
				{#each member.speciesDetail.types as t (t.name)}
					<span class="type-badge type-{t.name}">{t.name_ja}</span>
				{/each}
			</div>
			<button type="button" on:click={changeSpecies}>変更</button>
		</div>

		<div class="fields">
			<label>
				<span>ニックネーム</span>
				<input type="text" bind:value={member.nickname} />
			</label>
			<label>
				<span>もちもの</span>
				<input type="text" bind:value={member.item} />
			</label>
			<label>
				<span>とくせい</span>
				<select bind:value={member.ability}>
					{#each member.speciesDetail.abilities as a (a.name)}
						<option value={a.name_ja}>{a.name_ja}{a.is_hidden ? '(夢)' : ''}</option>
					{/each}
				</select>
			</label>
			<label>
				<span>せいかく</span>
				<select bind:value={member.nature}>
					{#each Object.keys(NATURES) as n (n)}
						<option value={n}>{natureLabel(n)}</option>
					{/each}
				</select>
			</label>
		</div>

		<h4>努力値</h4>
		<EVAllocator bind:evs={member.evs} />

		<h4>わざ</h4>
		<MoveSelector availableMoves={member.speciesDetail.moves} bind:moves={member.moves} />

		<h4>実数値(Lv.50)</h4>
		<StatDisplay
			baseStats={member.speciesDetail.base_stats}
			ivs={member.ivs}
			evs={member.evs}
			nature={member.nature}
		/>
	{/if}
</div>

<style>
	.slot {
		display: flex;
		flex-direction: column;
		gap: var(--size-2);
	}
	.slot-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}
	.species-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: var(--size-2);
	}
	.fields {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(10rem, 1fr));
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
