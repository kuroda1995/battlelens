<script>
	export let availableMoves = [];
	export let moves = [];

	function moveForSlot(slot) {
		return moves.find((m) => m.slot === slot)?.move_id ?? '';
	}

	function onChange(slot, rawId) {
		const next = moves.filter((m) => m.slot !== slot);
		if (rawId !== '') {
			const found = availableMoves.find((m) => String(m.id) === String(rawId));
			if (found) {
				next.push({ slot, move_id: found.id, move_name: found.name_ja ?? found.name });
			}
		}
		next.sort((a, b) => a.slot - b.slot);
		moves = next;
	}
</script>

<div class="moves">
	{#each [1, 2, 3, 4] as slot (slot)}
		<label>
			<span>技{slot}</span>
			<select value={moveForSlot(slot)} on:change={(e) => onChange(slot, e.target.value)}>
				<option value="">(なし)</option>
				{#each availableMoves as move (move.id)}
					<option value={move.id}>{move.name_ja ?? move.name}</option>
				{/each}
			</select>
		</label>
	{/each}
</div>

<style>
	.moves {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(10rem, 1fr));
		gap: var(--size-2);
	}
	label {
		display: flex;
		flex-direction: column;
		font-size: var(--font-size-0);
		gap: var(--size-1);
	}
</style>
