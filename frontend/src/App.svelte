<script>
	import PartyBuilder from './lib/components/PartyBuilder.svelte';
	import DamageCalculator from './lib/components/DamageCalculator.svelte';

	let activeTab = 'party';
</script>

<div class="page">
	<header>
		<h1>BattleLens <span class="tag">(仮称)</span></h1>
		<p class="subtitle">対戦パーティ構築・分析ツール</p>
		<nav>
			<button
				type="button"
				class:active={activeTab === 'party'}
				on:click={() => (activeTab = 'party')}
			>
				パーティ構築
			</button>
			<button
				type="button"
				class:active={activeTab === 'damage'}
				on:click={() => (activeTab = 'damage')}
			>
				ダメージ計算
			</button>
		</nav>
	</header>

	<main>
		{#if activeTab === 'party'}
			<PartyBuilder />
		{:else}
			<DamageCalculator />
		{/if}
	</main>

	<footer>
		<p>
			本アプリは個人が趣味・学習目的で作成した非公式のファンツールであり、Nintendo / Game
			Freak / The Pokémon Company とは一切関係ありません。種族・技データは
			<a href="https://pokeapi.co/" target="_blank" rel="noreferrer">PokéAPI</a>
			を通じて取得しています。
		</p>
	</footer>
</div>

<style>
	.page {
		max-width: 72rem;
		margin: 0 auto;
		padding: var(--size-4);
		display: flex;
		flex-direction: column;
		gap: var(--size-4);
		min-height: 100vh;
	}
	header h1 {
		margin: 0;
	}
	.tag {
		color: var(--color-text-muted);
		font-size: var(--font-size-3);
		font-weight: normal;
	}
	.subtitle {
		margin: 0;
		color: var(--color-text-muted);
	}
	nav {
		margin-top: var(--size-3);
		display: flex;
		gap: var(--size-2);
	}
	nav button.active {
		background: var(--color-primary);
		color: var(--color-primary-contrast);
		border-color: var(--color-primary);
	}
	main {
		flex: 1;
	}
	footer {
		border-top: 1px solid var(--color-border);
		padding-top: var(--size-3);
		font-size: var(--font-size-0);
		color: var(--color-text-muted);
	}
</style>
