<script>
	import MoveTypeSelect from './MoveTypeSelect.svelte';

	export let availableMoves = [];
	export let moves = [];

	function moveForSlot(slot) {
		return moves.find((m) => m.slot === slot)?.move_id ?? null;
	}

	function onSelect(slot, move) {
		const next = moves.filter((m) => m.slot !== slot);
		if (move) {
			next.push({ slot, move_id: move.id, move_name: move.name_ja ?? move.name });
		}
		next.sort((a, b) => a.slot - b.slot);
		moves = next;
	}
</script>

<div class="moves">
	{#each [1, 2, 3, 4] as slot (slot)}
		<div class="slot-move">
			<span class="slot-label">技{slot}</span>
			<MoveTypeSelect
				moves={availableMoves}
				value={moveForSlot(slot)}
				on:select={(e) => onSelect(slot, e.detail)}
			/>
		</div>
	{/each}
</div>

<style>
	.moves {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(10rem, 1fr));
		gap: var(--size-2);
	}
	.slot-move {
		display: flex;
		flex-direction: column;
		font-size: var(--font-size-0);
		gap: var(--size-1);
	}
</style>
