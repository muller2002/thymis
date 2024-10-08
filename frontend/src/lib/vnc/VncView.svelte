<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { Device } from '$lib/state';
	import { state } from '$lib/state';
	import { controllerHost } from '$lib/api';
	import { Card, Spinner, Toggle, P } from 'flowbite-svelte';
	import { onDestroy, onMount } from 'svelte';
	import { deviceHasVNCModule } from '$lib/vnc/vnc';

	export let device: Device;
	let rfb: any;
	let connected = false;
	let connectionFailed = false;

	let controlDevice = false;

	$: hasVNC = device && deviceHasVNCModule(device, $state);

	const initVNC = async (device: Device) => {
		// @ts-ignore
		let RFB = await import('@novnc/novnc/lib/rfb.js');

		const url = `ws://${controllerHost}/vnc/${device.identifier}`;

		const password = '';
		const canvas = document.getElementById(`vnc-canvas-${device.targetHost}`);

		if (rfb) {
			rfb.disconnect();
		}

		connected = false;
		connectionFailed = false;

		rfb = new RFB.default(canvas, url, { credentials: { password: password } });
		rfb.addEventListener('connect', () => (connected = true));
		rfb.addEventListener('disconnect', () => (connectionFailed = true));
		rfb.addEventListener('securityfailure', () => (connectionFailed = true));

		rfb.viewOnly = !controlDevice;
		rfb.scaleViewport = true;
		rfb.showDotCursor = true;
	};

	const toggleControlDevice = () => {
		controlDevice = !controlDevice;

		if (rfb) {
			rfb.viewOnly = !controlDevice;
		}
	};

	onMount(() => {
		if (hasVNC) {
			initVNC(device);
		}
	});

	onDestroy(() => {
		if (rfb) {
			rfb.disconnect();
			rfb = null;
		}
	});
</script>

{#if hasVNC}
	<Card class="w-full max-w-none">
		<div class="flex justify-between">
			<pre>vncviewer {device.targetHost}:5900</pre>
			<div class="flex items-center gap-2">
				<P>{$t('vnc.control-device')}</P>
				<Toggle bind:checked={controlDevice} on:click={toggleControlDevice} />
			</div>
		</div>
		<div id={`vnc-canvas-${device.targetHost}`} class="relative w-full aspect-video mt-4">
			{#if connectionFailed}
				<p
					class="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-red-500"
				>
					{$t('vnc.connection-failed')}
				</p>
			{:else if !connected}
				<Spinner size="16" class="absolute top-1/2 left-1/2 -mt-8 -ml-8" />
			{/if}
		</div>
	</Card>
{/if}
