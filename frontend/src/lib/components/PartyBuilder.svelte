<script>
	import { onMount } from 'svelte';
	import PokemonSlot from './PokemonSlot.svelte';
	import { listParties, getParty, createParty, updateParty, deleteParty } from '../api.js';
	import { getSpeciesDetail } from '../api.js';

	const MAX_MEMBERS = 6;

	function newMember(position) {
		return {
			position,
			speciesDetail: null,
			nickname: '',
			item: '',
			ability: '',
			nature: 'hardy',
			evs: { hp: 0, attack: 0, defense: 0, special_attack: 0, special_defense: 0, speed: 0 },
			ivs: { hp: 31, attack: 31, defense: 31, special_attack: 31, special_defense: 31, speed: 31 },
			moves: []
		};
	}

	let partyId = null;
	let name = '';
	let members = [newMember(1)];
	let savedParties = [];
	let saving = false;
	let saveError = '';
	let loadError = '';
	let listError = '';

	onMount(refreshList);

	async function refreshList() {
		listError = '';
		try {
			savedParties = await listParties();
		} catch (e) {
			listError = e.message;
		}
	}

	function addMember() {
		if (members.length >= MAX_MEMBERS) return;
		members = [...members, newMember(members.length + 1)];
	}

	function removeMember(index) {
		members = members.filter((_, i) => i !== index).map((m, i) => ({ ...m, position: i + 1 }));
	}

	function resetForm() {
		partyId = null;
		name = '';
		members = [newMember(1)];
		saveError = '';
	}

	function toPayload() {
		return {
			name,
			members: members
				.filter((m) => m.speciesDetail)
				.map((m) => ({
					position: m.position,
					species_id: m.speciesDetail.id,
					species_name: m.speciesDetail.name,
					nickname: m.nickname || null,
					item: m.item || null,
					ability: m.ability || null,
					nature: m.nature,
					evs: m.evs,
					ivs: m.ivs,
					moves: m.moves
				}))
		};
	}

	async function save() {
		saving = true;
		saveError = '';
		try {
			const payload = toPayload();
			if (payload.members.length === 0) {
				throw new Error('少なくとも1体はポケモンを選択してください');
			}
			if (partyId) {
				await updateParty(partyId, payload);
			} else {
				const created = await createParty(payload);
				partyId = created.id;
			}
			await refreshList();
		} catch (e) {
			saveError = e.message;
		} finally {
			saving = false;
		}
	}

	async function loadForEdit(id) {
		loadError = '';
		try {
			const party = await getParty(id);
			partyId = party.id;
			name = party.name;
			members = await Promise.all(
				party.members.map(async (m) => {
					const detail = await getSpeciesDetail(m.species_id);
					return {
						position: m.position,
						speciesDetail: detail,
						nickname: m.nickname ?? '',
						item: m.item ?? '',
						ability: m.ability ?? '',
						nature: m.nature,
						evs: m.evs,
						ivs: m.ivs,
						moves: m.moves
					};
				})
			);
		} catch (e) {
			loadError = e.message;
		}
	}

	async function remove(id) {
		if (!confirm('このパーティを削除しますか?')) return;
		try {
			await deleteParty(id);
			if (partyId === id) resetForm();
			await refreshList();
		} catch (e) {
			listError = e.message;
		}
	}
</script>

<div class="layout">
	<section class="editor">
		<div class="card">
			<label class="party-name">
				<span>パーティ名</span>
				<input type="text" bind:value={name} placeholder="例: シーズン1レンタルパーティ" />
			</label>

			<div class="slots">
				{#each members as member, index (member.position)}
					<PokemonSlot bind:member={members[index]} on:remove={() => removeMember(index)} />
				{/each}
			</div>

			<div class="actions">
				<button type="button" on:click={addMember} disabled={members.length >= MAX_MEMBERS}>
					+ ポケモンを追加 ({members.length}/{MAX_MEMBERS})
				</button>
				<button type="button" class="primary" on:click={save} disabled={saving}>
					{saving ? '保存中…' : partyId ? '更新する' : '新規保存'}
				</button>
				<button type="button" on:click={resetForm}>新規作成に戻る</button>
			</div>
			{#if saveError}<p class="error">{saveError}</p>{/if}
		</div>
	</section>

	<aside class="saved">
		<h3>保存済みパーティ</h3>
		{#if listError}<p class="error">{listError}</p>{/if}
		{#if loadError}<p class="error">{loadError}</p>{/if}
		{#if savedParties.length === 0}
			<p>まだ保存されたパーティはありません。</p>
		{:else}
			<ul>
				{#each savedParties as p (p.id)}
					<li class="card">
						<div>
							<strong>{p.name}</strong>
							<div class="muted">{p.members.length}体 / 更新: {new Date(p.updated_at).toLocaleString()}</div>
						</div>
						<div class="row-actions">
							<button type="button" on:click={() => loadForEdit(p.id)}>編集</button>
							<button type="button" class="danger" on:click={() => remove(p.id)}>削除</button>
						</div>
					</li>
				{/each}
			</ul>
		{/if}
	</aside>
</div>

<style>
	.layout {
		display: grid;
		grid-template-columns: minmax(0, 2fr) minmax(0, 1fr);
		gap: var(--size-4);
		align-items: start;
	}
	@media (max-width: 800px) {
		.layout {
			grid-template-columns: 1fr;
		}
	}
	.party-name {
		display: flex;
		flex-direction: column;
		gap: var(--size-1);
		margin-bottom: var(--size-3);
	}
	.slots {
		display: grid;
		gap: var(--size-3);
	}
	.actions {
		margin-top: var(--size-3);
		display: flex;
		flex-wrap: wrap;
		gap: var(--size-2);
	}
	.saved ul {
		list-style: none;
		margin: 0;
		padding: 0;
		display: grid;
		gap: var(--size-2);
	}
	.saved li {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: var(--size-2);
	}
	.row-actions {
		display: flex;
		gap: var(--size-1);
	}
	.muted {
		color: var(--color-text-muted);
		font-size: var(--font-size-0);
	}
	.error {
		color: var(--color-danger);
	}
</style>
