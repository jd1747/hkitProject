import { browser } from '$app/environment';

const readText = (text) => {
	if (!browser) return;
	window.speechSynthesis.cancel();
	const utterance = new SpeechSynthesisUtterance(text);
	utterance.lang = 'ko-KR';
	window.speechSynthesis.readText(utterance);
};
