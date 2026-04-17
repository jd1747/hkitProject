<script>
	import { onMount } from 'svelte';
	import { browser } from '$app/environment'; // SSR 에러 방지용

	// 1. 상태 관리 (Svelte 5 Runes)
	let agreed = $state(false); // 안내 및 동의 여부
	let name = $state(''); // 아이 이름
	let session_id = $state(null); // 서버 세션 아이디
	let question = $state(null); // 현재 질문 데이터
	let finished = $state(false); // 설문 종료 상태
	let result = $state(null); // 결과 데이터

	let isListening = $state(false); // 음성 인식 중 여부
	let transcript = $state(''); // 인식된 텍스트
	let response_time = $state(0); // 반응 시간 (초)
	let question_end_time = 0; // 질문 종료 시각 기록용

	let recognition;

	// 답변 옵션 및 유사도 분석용 키워드
	const ANSWER_OPTIONS = [
		{
			value: 0,
			label: '전혀 안 그래요',
			icon: '😊',
			keywords: ['전혀', '아니', '없어', '드물다', '영번']
		},
		{ value: 1, label: '가끔 그래요', icon: '🤨', keywords: ['가끔', '조금', '한두번', '일번'] },
		{ value: 2, label: '종종 그래요', icon: '😟', keywords: ['종종', '자주', '많이', '이번'] },
		{ value: 3, label: '거의 매일 그래요', icon: '😫', keywords: ['매일', '항상', '맨날', '삼번'] }
	];

	/**
	 * 🔊 TTS 기능: 질문 읽기 (브라우저 환경 체크)
	 */
	function speak(text) {
		if (!browser) return; // 서버 환경 차단
		window.speechSynthesis.cancel();
		const utterance = new SpeechSynthesisUtterance(text);
		utterance.lang = 'ko-KR';
		utterance.rate = 1.0;
		utterance.pitch = 1.2; // 밝은 톤

		utterance.onend = () => {
			question_end_time = Date.now(); // 질문 종료 시점부터 반응 시간 측정 시작 -> TTS가 끝나는 시점이 질문이 완전히 전달된 시점이므로, 이때부터 아이의 반응 시간을 측정하기 시작함
		};
		window.speechSynthesis.speak(utterance);
	}

	/**
	 * 🎤 STT 및 마운트 로직 (브라우저 전용 API 설정)
	 */
	onMount(() => {
		const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
		if (Recognition) {
			recognition = new Recognition();
			recognition.lang = 'ko-KR';
			recognition.interimResults = false;

			recognition.onresult = (e) => {
				const answer_received_time = Date.now();
				transcript = e.results.transcript; // [수정] Web Speech API 표준 경로

				// 반응 시간 계산-> 질문 종료 시점부터 답변 인식 시점까지의 시간 측정
				response_time = (answer_received_time - question_end_time) / 1000;

				// 자동으로 답변 판별 및 전송
				findBestMatch(transcript);
			};
			recognition.onend = () => {
				isListening = false;
			};
		}
	});

	/**
	 * 🧠 유사도 분석 및 자동 흐름 제어
	 */
	function findBestMatch(input) {
		let bestMatch = { value: -1, score: 0 };
		ANSWER_OPTIONS.forEach((option) => {
			option.keywords.forEach((keyword) => {
				const score = getSimilarity(input, keyword);
				if (score > bestMatch.score && score > 0.4) {
					bestMatch = { value: option.value, score };
				}
			});
		});

		if (bestMatch.value !== -1) {
			answer(bestMatch.value); // 답변 매칭 시 자동 저장 및 다음 문항으로 이동 -> 반응 시간 기록은 answer 함수 내에서 처리
		} else {
			speak('미안해, 다시 한번 말해줄래?'); // 인식 실패 시 재가이드 -> 반응 시간 측정은 질문 종료 시점부터 시작되므로, 재가이드 후에도 정확한 반응 시간 기록 가능
		}
	}

	// 레벤슈타인 거리 알고리즘 -> 유사도 계산 (0~1 사이)
	function getSimilarity(s1, s2) {
		if (!s1 || !s2) return 0;
		const len1 = s1.length,
			len2 = s2.length;
		const matrix = Array.from({ length: len1 + 1 }, () => Array(len2 + 1).fill(0));
		for (let i = 0; i <= len1; i++) matrix[i] = i;
		for (let j = 0; j <= len2; j++) matrix[j] = j;
		for (let i = 1; i <= len1; i++) {
			for (let j = 1; j <= len2; j++) {
				const cost = s1[i - 1] === s2[j - 1] ? 0 : 1;
				matrix[i][j] = Math.min(
					matrix[i - 1][j] + 1,
					matrix[i][j - 1] + 1,
					matrix[i - 1][j - 1] + cost
				);
			}
		}
		return 1 - matrix[len1][len2] / Math.max(len1, len2);
	}

	/**
	 * 🌐 API 통신 로직
	 */
	async function start() {
		const res = await fetch('http://127.0.0.1:8000/session', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ user_name: name })
		});
		const data = await res.json();
		session_id = data.session_id;
		await getQuestion();
	}

	async function getQuestion() {
		const res = await fetch(`http://127.0.0.1:8000/question/${session_id}`);
		const data = await res.json();
		if (data.message === '설문 완료') {
			finished = true;
			speak('모든 질문이 끝났어요! 정말 잘했어!');
			await getResult();
		} else {
			question = data;
			transcript = '';
			speak(question.text); // 새 질문 자동 읽기-> 반응 시간 측정 시작은 speak 함수 내에서 처리
		}
	}

	async function answer(value) {
		if (recognition) recognition.stop();
		await fetch('http://127.0.0.1:8000/answer', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ session_id, answer: value, response_time })
		});
		await getQuestion(); // 저장 후 다음 문항으로 연쇄 반응-
	}

	async function getResult() {
		const res = await fetch(`http://127.0.0.1:8000/result/${session_id}`);
		result = await res.json();
		await fetch(`http://127.0.0.1:8000/save/${session_id}`, { method: 'POST' });
	}

	function toggleListening() {
		if (!recognition) return;
		if (isListening) recognition.stop();
		else {
			transcript = '';
			recognition.start();
			isListening = true;
		}
	}
</script>

<div class="container">
	<div class="card">
		{#if !agreed}
			<div class="intro-screen">
				<div class="character">👋😊</div>
				<h2>우리 같이 약속해요!</h2>
				<div class="consent-box">
					<p>1. 너의 <strong>목소리</strong>를 들려줘.</p>
					<p>2. 너의 <strong>이름</strong>을 기억할게.</p>
				</div>
				<button
					class="btn-start"
					onclick={() => {
						agreed = true;
						speak('안녕! 너의 이름을 알려줄래?');
					}}
				>
					응, 좋아! 👍
				</button>
			</div>
		{:else if !session_id}
			<div class="start-screen">
				<div class="character">🧒✨</div>
				<h2>안녕! 이름이 뭐야?</h2>
				<input bind:value={name} class="main-input" placeholder="이름을 입력해요" />
				<button class="btn-start" onclick={start} disabled={!name.trim()}> 준비됐어! 🚀 </button>
			</div>
		{:else if !finished && question}
			<div class="progress-bar-bg">
				<div class="progress-bar-fill" style="width: {(question.question_id / 20) * 100}%"></div>
			</div>

			<h3 class="question-text">
				{question.text}
				<button class="btn-speaker" onclick={() => speak(question.text)}>🔊</button>
			</h3>

			<div class="voice-ui">
				<button class="mic-btn {isListening ? 'active' : ''}" onclick={toggleListening}>
					<span class="mic-icon">🎤</span>
					<span class="mic-text">{isListening ? '듣고 있어요...' : '눌러서 말하기'}</span>
				</button>
				{#if transcript}
					<div class="transcript-box">
						<p class="transcript-text">"{transcript}"</p>
						<p class="time-tag">반응 시간: {response_time.toFixed(2)}초</p>
					</div>
				{/if}
			</div>

			<div class="image-grid">
				{#each ANSWER_OPTIONS as opt}
					<button class="image-card" onclick={() => answer(opt.value)}>
						<span class="emoji">{opt.icon}</span>
						<span class="label">{opt.label}</span>
					</button>
				{/each}
			</div>
		{:else if finished && result}
			<div class="result-box">
				<h2>🎉 참 잘했어요!</h2>
				<div class="score-display">총 점수: {result.total_score}점</div>
				<p>{result.result}</p>
				<button class="btn-start" onclick={() => location.reload()}>다시 해볼까?</button>
			</div>
		{/if}
	</div>
</div>

<style>
	/* 아이들을 위한 부드럽고 접근성 높은 디자인 */
	:global(body) {
		font-family: 'Pretendard', sans-serif;
		background: linear-gradient(135deg, #a1c4fd 0%, #c2e9fb 100%);
		margin: 0;
		display: flex;
		justify-content: center;
		align-items: center;
		height: 100vh;
	}

	.card {
		background: white;
		padding: 40px;
		border-radius: 40px; /* 둥근 디자인 */
		width: 420px;
		text-align: center;
		box-shadow: 0 20px 50px rgba(0, 0, 0, 0.1);
	}

	.consent-box {
		background: #f8fafc;
		padding: 20px;
		border-radius: 20px;
		text-align: left;
		margin-bottom: 25px;
		border: 2px dashed #667eea;
	}

	.main-input {
		width: 100%;
		padding: 20px;
		border-radius: 20px;
		border: 3px solid #e2e8f0;
		font-size: 22px;
		margin-bottom: 20px;
		text-align: center;
		box-sizing: border-box;
	}

	.btn-start {
		width: 100%;
		padding: 20px;
		background: #667eea;
		color: white;
		border: none;
		border-radius: 25px;
		font-size: 24px;
		font-weight: bold;
		cursor: pointer;
		box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
	}

	.mic-btn {
		background: #667eea;
		color: white;
		padding: 20px 40px;
		border-radius: 50px;
		border: none;
		font-size: 20px;
		margin: 20px 0;
		box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
	}

	.mic-btn.active {
		background: #ff5e5e;
		animation: pulse 1.5s infinite; /* 시각적 피드백 */
	}

	@keyframes pulse {
		0% {
			transform: scale(1);
			box-shadow: 0 0 0 0 rgba(255, 94, 94, 0.7);
		}
		70% {
			transform: scale(1.1);
			box-shadow: 0 0 0 15px rgba(255, 94, 94, 0);
		}
		100% {
			transform: scale(1);
		}
	}

	.image-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 15px;
		margin-top: 25px;
	}

	.image-card {
		background: #f8fafc;
		border: 3px solid #e2e8f0;
		border-radius: 20px;
		padding: 15px;
		cursor: pointer;
		transition: transform 0.2s;
	}

	.image-card:hover {
		transform: scale(1.05);
	}

	.emoji {
		font-size: 35px;
	}
	.label {
		display: block;
		font-size: 14px;
		margin-top: 5px;
		font-weight: bold;
	}

	.progress-bar-bg {
		background: #eee;
		height: 10px;
		border-radius: 10px;
		margin-bottom: 20px;
	}
	.progress-bar-fill {
		background: #667eea;
		height: 100%;
		border-radius: 10px;
		transition: width 0.3s;
	}

	.btn-speaker {
		background: none;
		border: none;
		font-size: 20px;
		cursor: pointer;
	}
	.transcript-box {
		margin-top: 20px;
		background: #f8fafc;
		padding: 15px;
		border-radius: 20px;
	}
	.time-tag {
		color: #667eea;
		font-weight: bold;
		font-size: 14px;
	}
	.score-display {
		font-size: 24px;
		font-weight: bold;
		margin: 20px 0;
		color: #667eea;
	}
</style>
