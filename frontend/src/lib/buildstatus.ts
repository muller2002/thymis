import { browser } from '$app/environment';
import { writable } from 'svelte/store';

type BuildStatus = {
	status: string;
	stdout: string;
	stderr: string;
};

let socket: WebSocket | undefined;

export let buildStatus = writable<BuildStatus | undefined>();

const startSocket = () => {
	console.log('starting socket');
	socket = new WebSocket('ws://localhost:8000/build_status');
	socket.onmessage = (event) => {
		buildStatus.set(JSON.parse(event.data));
	};
	socket.onclose = () => {
		setTimeout(startSocket, 1000);
	};
}

if (browser) {
	startSocket();
}
