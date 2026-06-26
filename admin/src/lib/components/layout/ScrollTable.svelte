<script lang="ts">
	import type { Snippet } from 'svelte';
	import { cn } from '$lib/utils';

	interface Props {
		class?: string;
		children: Snippet;
	}

	let { class: className, children }: Props = $props();
</script>

<div class={cn('-mx-3 overflow-x-auto px-3 sm:mx-0 sm:px-0', className)}>
	{@render children()}
</div>
