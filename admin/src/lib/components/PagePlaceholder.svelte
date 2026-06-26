<script lang="ts">
	import type { Snippet } from 'svelte';
	import * as Card from '$lib/components/ui/card/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';

	interface Props {
		title: string;
		description: string;
		phase?: string;
		children?: Snippet;
	}

	let { title, description, phase = 'Phase 2', children }: Props = $props();
</script>

<Card.Root>
	<Card.Header>
		<div class="flex items-center justify-between gap-2">
			<Card.Title>{title}</Card.Title>
			<Badge variant="outline" class="border-primary/40 text-primary">{phase}</Badge>
		</div>
		<Card.Description>{description}</Card.Description>
	</Card.Header>
	{#if children}
		<Card.Content>
			{@render children()}
		</Card.Content>
	{/if}
</Card.Root>
