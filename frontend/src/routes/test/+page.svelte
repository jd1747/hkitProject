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
	let stoppedEarly = $state(false); // [추가] 중도 포기 여부를 기억하는 변수

	let isListening = $state(false); // 음성 인식 중 여부
	let transcript = $state(''); // 인식된 텍스트
	let response_time = $state(0); // 반응 시간 (초)
	let question_end_time = 0; // 질문 종료 시각 기록용
	let silence_timeout = null; // [추가] 무응답 타이머 변수
	let match_error = $state(''); // [추가] 매칭 실패 이유를 화면에 띄우기 위한 변수
	let matched_value = $state(null); // [추가] 매칭된 응답 번호를 화면에 표기하기 위한 변수
	let recognition;

	const TIMEOUT_SEC = 10; // 10초 기다려주기
	// 답변 옵션 및 유사도 분석용 키워드
	const ANSWER_OPTIONS = [
		{
			value: 0,
			label: '전혀 안 그래요',
			icon: '😊',
			keywords: ['전혀', '아니', '없어', '드물다', '영번', '0번', '0', '영']
		},
		{
			value: 1,
			label: '가끔 그래요',
			icon: '🤨',
			keywords: ['가끔', '조금', '한두번', '일번', '1번', '1', '일']
		},
		{
			value: 2,
			label: '종종 그래요',
			icon: '😟',
			keywords: ['종종', '자주', '많이', '이번', '2번', '2', '이']
		},
		{
			value: 3,
			label: '거의 매일 그래요',
			icon: '😫',
			keywords: ['매일', '항상', '맨날', '삼번', '3번', '3', '삼']
		}
	];

	/**
	 * 🔊 TTS 기능: 질문 읽기 (브라우저 환경 체크)
	 */
	function speak(text) {
		if (!browser) return;
		window.speechSynthesis.cancel();

		const utterance = new SpeechSynthesisUtterance(text);
		utterance.lang = 'ko-KR';
		utterance.rate = 1.0; // 아이들을 위해 천천히
		utterance.pitch = 1.2; // 밝은 톤

		// 🌟 [추가된 로직] 기기에 설치된 목소리 목록을 가져옵니다.
		const voices = window.speechSynthesis.getVoices();

		// 'Google', 'Online', 'Natural' 등 고품질 클라우드 음성이 있는지 찾아 우선 적용합니다.
		const bestVoice = voices.find(
			(voice) =>
				voice.lang.includes('ko') &&
				(voice.name.includes('Google') ||
					voice.name.includes('Online') ||
					voice.name.includes('Natural'))
		);

		// 고품질 목소리가 발견되면 적용하고, 없으면 기본 목소리를 사용합니다.
		if (bestVoice) {
			utterance.voice = bestVoice;
		}

		utterance.onend = () => {
			question_end_time = Date.now(); // 질문 종료 시점부터 반응 시간 측정 시작
			startSilenceTimer(); // [추가] 질문을 다 읽으면 무응답 타이머 시작
		};

		window.speechSynthesis.speak(utterance);
	}
	// 🌟 [추가] 화면 버튼을 클릭했을 때 저장을 막고 음성 대답을 유도하는 함수
	function guideVoiceOnly() {
		match_error = '버튼을 누르지 말고, 마이크를 켠 뒤 목소리로 대답해 주세요!';
		speak('마이크를 누르고 큰 목소리로 대답해줄래?');
		// answer(2, 'qwer');
	}

	/**
	 * ⏳ 무응답 대기 타이머: 10초간 대답이 없으면 다시 다정하게 물어봅니다.
	 */
	function startSilenceTimer() {
		clearTimeout(silence_timeout); // 기존 타이머 초기화

		silence_timeout = setTimeout(() => {
			console.log(`[무응답 타임아웃] ${TIMEOUT_SEC}초 경과`);

			if (recognition && isListening) {
				recognition.stop(); // 켜져있는 마이크 잠시 정지
			}

			// 다정한 목소리로 다시 가이드 (이 음성이 끝나면 다시 타이머가 돕니다)
			speak('대답하기 어려운 질문이니? 천천히 다시 한 번 말해줄래?');
		}, TIMEOUT_SEC * 1000);
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
				transcript = e.results[0][0].transcript; // [수정] Web Speech API 표준 경로 -> e.results[0][0].transcript

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
	 * 🧠 유사도 분석 및 자동 흐름 제어 (업그레이드 버전)
	 */
	function findBestMatch(rawInput) {
		clearTimeout(silence_timeout); // [추가] 목소리를 인식하면 즉시 무응답 타이머 취소
		// 1. 입력된 텍스트 전처리 (공백 및 마침표, 물음표 등 특수문자 제거)
		const input = rawInput.replace(/[\s.,!?]/g, '');
		let bestMatch = { value: -1, score: 0 };

		ANSWER_OPTIONS.forEach((option) => {
			option.keywords.forEach((keyword) => {
				// 2. 키워드가 문장 안에 그대로 포함되어 있다면 즉시 100% 매칭 처리
				if (input.includes(keyword)) {
					bestMatch = { value: option.value, score: 1.0 };
				}

				// 3. 포함되어 있지 않다면 발음이 뭉개진 경우를 대비해 레벤슈타인 계산 (기존 로직 유지)
				const score = getSimilarity(input, keyword);
				if (score > bestMatch.score && score > 0.4) {
					bestMatch = { value: option.value, score };
				}
			});
		});

		// 4. 개발자 확인용 콘솔 로그 (F12 콘솔창에서 매칭 결과를 볼 수 있습니다)
		console.log(`[음성 인식] 원본: "${rawInput}" -> 전처리: "${input}"`);

		if (bestMatch.value !== -1) {
			console.log(`[매칭 성공] ${bestMatch.value}점 (유사도: ${bestMatch.score.toFixed(2)})`);
			match_error = ''; // 성공하면 에러 메시지를 지웁니다.
			matched_value = bestMatch.value; // [추가] 매칭된 응답 번호를 화면에 표기합니다.
			answer(bestMatch.value, rawInput); // 답변 서버 저장 후 다음 문항으로 이동
		} else {
			console.log(`[매칭 실패] 일치하는 답변을 찾을 수 없습니다.`);
			matched_value = null; // [추가] 매칭 실패 시 응답 번호 표기 초기화
			match_error =
				'어떤 대답인지 잘 못 들었어요. (전혀, 가끔, 종종, 매일) 중 하나를 선택해주세요!';
			speak('잘 못 들었어, 다시 한번 크게 말해줄래?'); // 재가이드 음성 출력
		}
	}

	// 레벤슈타인 거리 알고리즘 -> 유사도 계산 (0~1 사이)
	function getSimilarity(s1, s2) {
		if (!s1 || !s2) return 0;

		// 방어 로직: 무조건 문자열로 변환하여 에러 원천 차단
		s1 = String(s1);
		s2 = String(s2);

		const len1 = s1.length,
			len2 = s2.length;
		const matrix = Array.from({ length: len1 + 1 }, () => Array(len2 + 1).fill(0));

		// 🌟 수정된 부분: 배열 전체를 덮어씌우지 않고 첫 번째 열과 행의 첫 칸만 정확히 채웁니다.
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
		// 🌟 [핵심 1] 주소 끝에 ?t=${Date.now()} 를 붙여 브라우저가 예전 질문을 똑같이 보여주는 현상(캐시)을 막습니다.
		const res = await fetch(`http://127.0.0.1:8000/question/${session_id}?t=${Date.now()}`);
		const data = await res.json();

		if (data.message === '설문 완료') {
			finished = true;
			speak('모든 질문이 끝났어요! 정말 잘했어!');
			await getResult();
		} else {
			question = data;
			transcript = '';
			match_error = '';
			matched_value = null;
			speak(question.text);
		}
	}

	async function answer(value, transcriptText) {
		// 1. 혹시라도 번호가 비어있으면 즉시 차단
		if (value === null || value === undefined) {
			match_error = '에러: 응답 번호가 비어 있습니다!';
			return;
		}

		clearTimeout(silence_timeout);

		try {
			// 2. 안전하게 마이크 끄기 (여기서 튕겨도 서버 통신은 정상 진행되도록 보호)
			if (recognition) {
				try {
					recognition.stop();
				} catch (e) {}
			}

			// 3. 백엔드로 보낼 데이터 예쁘게 포장하기
			const sendData = {
				session_id: session_id,
				answer: value,
				response_time: response_time,
				transcript: transcriptText
			};

			// 🌟 F12 콘솔창에서 어떤 번호가 날아가는지 실시간으로 확인할 수 있습니다!
			console.log('🚀 [서버로 전송하는 데이터]:', sendData);

			// 4. 전송 시작
			const res = await fetch('http://127.0.0.1:8000/answer', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(sendData)
			});

			console.log('📥 [서버 응답 상태 코드]:', res.status);

			const resData = await res.json();
			console.log('📥 [서버 응답 내용]:', resData);

			// 5. 서버가 거부한 이유를 화면에 띄우기
			if (res.status === 422) {
				throw new Error('데이터 전송 형식 오류(422). 파이썬 터미널 창을 꼭 확인하세요!');
			}
			if (resData.error) throw new Error(resData.error);
			if (!res.ok) throw new Error('서버 내부 에러 (500)');

			// 6. 정상 통과 시 1초 대기 후 다음 문항으로!
			await new Promise((resolve) => setTimeout(resolve, 1000));
			await getQuestion();
		} catch (error) {
			console.error('❌ 백엔드 통신 실패:', error);
			match_error = `[통신 실패] ${error.message}`;
		}
	}

	async function getResult() {
		try {
			// 🌟 결과 호출 시에도 캐시 방지 적용
			const res = await fetch(`http://127.0.0.1:8000/result/${session_id}?t=${Date.now()}`);
			result = await res.json();
			await fetch(`http://127.0.0.1:8000/answer/${session_id}`, { method: 'POST' });
		} catch (error) {
			console.error('결과 처리 및 저장 실패:', error);
		}
	}

	// 🌟 [수정] 중간에 '그만하기' 버튼을 눌렀을 때 실행되는 함수
	async function stopSurveyEarly() {
		if (!session_id || finished) return;

		if (recognition) recognition.stop();
		window.speechSynthesis.cancel();

		finished = true;
		stoppedEarly = true; // 💡 중도 포기 상태를 true로 체크합니다.

		// 아이를 위한 따뜻한 종료 음성
		speak('오늘은 여기까지 할게요. 다음에 또 만나서 이야기하자!');

		// 백엔드에 지금까지의 데이터 저장을 요청합니다.
		await getResult();
	}

	// 🌟 [추가 2] 사용자가 그냥 인터넷 창을 꺼버리거나 새로고침할 때 강제 저장
	function handleBeforeUnload(event) {
		if (session_id && !finished) {
			// 브라우저가 닫히는 급박한 순간에도 서버에 POST 요청을 던지는 특수 API
			navigator.sendBeacon(`http://127.0.0.1:8000/answer/${session_id}`);
		}
	}

	function toggleListening() {
		if (!recognition) return;
		if (isListening) recognition.stop();
		else {
			transcript = '';
			match_error = ''; // [추가] 다시 듣기를 시작하면 에러 메시지 초기화
			recognition.start();
			isListening = true;
		}
	}
</script>

<svelte:window onbeforeunload={handleBeforeUnload} />

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

			<div style="text-align: right; margin-bottom: 10px;">
				<button class="btn-stop" onclick={stopSurveyEarly}>🛑 그만하기</button>
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
						<p class="transcript-text">🎤 내 대답: "{transcript}"</p>

						{#if matched_value !== null}
							<p style="color: #2b6cb0; font-size: 20px; font-weight: bold; margin: 10px 0;">
								✅ 해당 문항 응답 번호: {matched_value}번
							</p>
						{/if}

						<p class="time-tag">반응 시간: {response_time.toFixed(2)}초</p>

						{#if match_error}
							<p style="color: #ff5e5e; font-weight: bold; margin-top: 10px; font-size: 14px;">
								⚠️ {match_error}
							</p>
						{/if}
					</div>
				{/if}
			</div>

			<div class="image-grid">
				{#each ANSWER_OPTIONS as opt}
					<button class="image-card" onclick={guideVoiceOnly}>
						<span class="emoji">{opt.icon}</span>
						<span class="label">{opt.label}</span>
					</button>
				{/each}
			</div>
		{:else if finished && result}
			<div class="result-box">
				{#if stoppedEarly}
					<h2>👋 오늘은 여기까지!</h2>
					<p style="font-size: 18px; margin: 20px 0; line-height: 1.5;">
						정말 잘해줬어! 조금 피곤했구나?<br />
						<strong>나중에 컨디션이 좋을 때<br />처음부터 다시 한 번 꼭 진행해 주세요!</strong>
					</p>
				{:else}
					<h2>🎉 참 잘했어요!</h2>
					<div class="score-display">총 점수: {result.total_score}점</div>
					<p>{result.result}</p>
				{/if}

				<button class="btn-start" style="margin-top: 20px;" onclick={() => location.reload()}>
					처음 화면으로 돌아가기
				</button>
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

	/* 🌟 [추가 5] 그만하기 버튼 스타일 */
	.btn-stop {
		background: #ff5e5e;
		color: white;
		border: none;
		border-radius: 15px;
		padding: 8px 15px;
		font-size: 14px;
		font-weight: bold;
		cursor: pointer;
		box-shadow: 0 4px 6px rgba(255, 94, 94, 0.3);
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
