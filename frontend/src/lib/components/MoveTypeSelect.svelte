<script>
	import { createEventDispatcher } from 'svelte';
	import { TYPE_ORDER, TYPE_LABELS_JA } from '../stats.js';

	export let moves = []; // [{id, name, name_ja, type, power, damage_class}]
	export let value = null; // 選択中の技ID
	export let placeholder = '(選択してください)';

	const dispatch = createEventDispatcher();

	let open = false;

	$: selected = moves.find((m) => String(m.id) === String(value)) ?? null;

	$: groups = (() => {
		const byType = new Map();
		for (const move of moves) {
			const key = move.type ?? 'normal';
			if (!byType.has(key)) byType.set(key, []);
			byType.get(key).push(move);
		}
		const orderedKeys = [
			...TYPE_ORDER.filter((t) => byType.has(t)),
			...[...byType.keys()].filter((t) => !TYPE_ORDER.includes(t))
		];
		return orderedKeys.map((type) => ({ type, moves: byType.get(type) }));
	})();

	function selectMove(move) {
		value = move ? move.id : null;
		open = false;
		dispatch('select', move);
	}

	function toggle() {
		open = !open;
	}

	function clickOutside(node) {
		function handleClick(event) {
			if (!node.contains(event.target)) {
				open = false;
			}
		}
		document.addEventListener('click', handleClick, true);
		return {
			destroy() {
				document.removeEventListener('click', handleClick, true);
			}
		};
	}
</script>

<div class="move-select" use:clickOutside>
	<button type="button" class="trigger" on:click={toggle}>
		{#if selected}
			<span class="type-badge type-{selected.type}">
				{TYPE_LABELS_JA[selected.type] ?? selected.type}
			</span>
			<span class="name">{selected.name_ja ?? selected.name}</span>
		{:else}
			<span class="placeholder">{placeholder}</span>
		{/if}
		<span class="chevron">▾</span>
	</button>

	{#if open}
		<div class="panel">
			<button type="button" class="option none" on:click={() => selectMove(null)}>(なし)</button>
			{#each groups as group (group.type)}
				<div class="group">
					<div class="group-header type-badge type-{group.type}">
						{TYPE_LABELS_JA[group.type] ?? group.type}
					</div>
					{#each group.moves as move (move.id)}
						<button
							type="button"
							class="option"
							class:selected={String(move.id) === String(value)}
							on:click={() => selectMove(move)}
						>
							<span class="name">{move.name_ja ?? move.name}</span>
							{#if move.power}<span class="power">{move.power}</span>{/if}
						</button>
					{/each}
				</div>
			{/each}
		</div>
	{/if}
</div>

<style>
	.move-select {
		position: relative;
	}
	.trigger {
		width: 100%;
		display: flex;
		align-items: center;
		gap: var(--size-2);
		text-align: left;
	}
	.trigger .name {
		flex: 1;
	}
	.placeholder {
		flex: 1;
		color: var(--color-text-muted);
	}
	.chevron {
		color: var(--color-text-muted);
	}
	.panel {
		position: absolute;
		z-index: 20;
		top: calc(100% + var(--size-1));
		left: 0;
		right: 0;
		max-height: 20rem;
		overflow-y: auto;
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius);
		box-shadow: var(--shadow);
		padding: var(--size-1);
	}
	.group-header {
		position: sticky;
		top: 0;
		display: block;
		border-radius: 0;
		padding: var(--size-1) var(--size-2);
		font-size: var(--font-size-0);
		font-weight: bold;
	}
	.option {
		display: flex;
		justify-content: space-between;
		align-items: center;
		width: 100%;
		border: none;
		background: transparent;
		padding: var(--size-1) var(--size-2);
		text-align: left;
	}
	.option:hover {
		background: var(--color-bg);
	}
	.option.selected {
		background: var(--color-primary);
		color: var(--color-primary-contrast);
	}
	.option.none {
		color: var(--color-text-muted);
		border-bottom: 1px solid var(--color-border);
		margin-bottom: var(--size-1);
	}
	.power {
		font-size: var(--font-size-0);
		color: var(--color-text-muted);
	}
	.option.selected .power {
		color: inherit;
	}
</style>
