<script>
	let name = $state('');
	let session_id = $state(null);
	let question = $state(null);
	let finished = $state(false);
	let result = $state(null);

	let isListening = $state(false);
	let isWaitingAnswer = $state(false);

	// TTS +  끝나면 자동 듣기
	function speakAndListen(text) {
		speechSynthesis.cancel();
		const msg = new SpeechSynthesisUtterance(text);
		msg.lang = 'ko-KR';

		msg.onend = () => {
			if (!finished) {
				setTimeout(() => {
					startListening();
				}, 500);
			}
		};
		speechSynthesis.speak(msg);
	}

	// STT
	function startListening() {
		if (isListening || !isWaitingAnswer) return;

		const recognition = new webkitSpeechRecognition();
		recognition.lang = 'ko-KR';
		recognition.interimResults = false;
		recognition.maxAlternatives = 1;

		isListening = true;
		recognition.onresult = (e) => {
			const text = e.results[0][0].transcript;
			console.log('음성 입력: ', text);
			const value = parseAnswer(text);

			if (value !== null) {
				isListening = false;
				isWaitingAnswer = false;
				answer(value);
			} else {
				speakAndListen('이해하지 못했습니다. 0부터 3 중 하나로 말씀해주세요.');
			}
		};

		recognition.onerror = () => {
			isListening = false;
			setTimeout(startListening, 1000);
		};
		recognition.onend = () => {
			isListening = false;
		};
		recognition.start();
	}

	// 음성 - 점수 변환 (temp)
	function parseAnswer(text) {
		text = text.replace(/\s+/g, '');

		if (text.includes('0') || text.includes('없') || text.includes('전혀')) return 0;
		if (text.includes('1') || text.includes('가끔') || text.includes('조금')) return 1;
		if (text.includes('2') || text.includes('종종') || text.includes('자주')) return 2;
		if (text.includes('3') || text.includes('대부분') || text.includes('항상')) return 3;

		return null;
	}

	// Start
	async function start() {
		const res = await fetch('http://127.0.0.1:8000/session', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ user_name: name })
		});

		const data = await res.json();
		session_id = data.session_id;

		speakAndListen('설문을 시작합니다. 질문에 음성으로 답하거나 버튼을 눌러주세요.');

		setTimeout(() => {
			getQuestion();
		}, 2000);
	}

	// GET questions
	async function getQuestion() {
		const res = await fetch(`http://127.0.0.1:8000/question/${session_id}`);
		const data = await res.json();

		if (data.message === '설문 완료') {
			finished = true;
			await getResult();
		} else {
			question = data;
			isWaitingAnswer = true;
			speakAndListen(question.text);
		}
	}

	// 자동 답변 (음성)
	async function answer(value) {
		await fetch('http://127.0.0.1:8000/answer', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ session_id, answer: value })
		});

		await getQuestion();
	}

	// 수동 답변 (버튼)
	function manualAnswer(value) {
		if (!isWaitingAnswer) return;

		speechSynthesis.cancel();
		isListening = false;
		isWaitingAnswer = false;

		answer(value);
	}

	// GET result
	async function getResult() {
		const res = await fetch(`http://127.0.0.1:8000/result/${session_id}`);
		result = await res.json();

		await fetch(`http://127.0.0.1:8000/save/${session_id}`, {
			method: 'POST'
		});
	}
</script>

<div class="container">
	<div class="card">
		<!-- 시작 -->
		{#if !session_id}
			<h2>🧠 ADHD 설문 (음성)</h2>
			<input bind:value={name} placeholder="이름 입력" />
			<button class="btn-primary" onclick={start} disabled={!name?.trim()}> 시작하기 </button>

			<!-- 질문 -->
		{:else if !finished && question}
			<div class="progress">
				<div class="progress-bar" style="width: {(question.question_id / 20) * 100}%"></div>
			</div>

			<p>{question.progress}</p>
			<h3>{question.text}</h3>

			<p style="font-size:12px; color:#888;">🎤 말하거나 아래 버튼 선택</p>

			<!-- button fallback -->
			<button class="answer-btn btn0" onclick={() => manualAnswer(0)}>0️⃣ 극히 드물다</button>
			<button class="answer-btn btn1" onclick={() => manualAnswer(1)}>1️⃣ 가끔 있었다</button>
			<button class="answer-btn btn2" onclick={() => manualAnswer(2)}>2️⃣ 종종 있었다</button>
			<button class="answer-btn btn3" onclick={() => manualAnswer(3)}>3️⃣ 대부분 그랬다</button>

			<button onclick={() => speakAndListen(question.text)}>다시 듣기</button>
			<!-- 결과 -->
		{:else if finished && result}
			<h2>📊 결과</h2>
			<p>총 점수: {result.total_score}</p>
			<h3>
				{result.result}
			</h3>

			<button class="btn-primary" onclick={() => location.reload()}> 다시하기 </button>
		{/if}
	</div>
</div>

<style>
	:global(body) {
		font-family: 'Pretendard', sans-serif;
		background: linear-gradient(135deg, #667eea, #764ba2);
		margin: 0;
	}

	.container {
		display: flex;
		justify-content: center;
		align-items: center;
		height: 100vh;
	}

	.card {
		background: white;
		padding: 40px;
		border-radius: 20px;
		width: 350px;
		text-align: center;
		box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
		/* animation: fadeIn 0.4s ease; */
	}

	input {
		width: 100%;
		padding: 12px;
		border-radius: 10px;
		border: 1px solid #ddd;
		margin-top: 15px;
		font-size: 16px;
	}
	/*
    button {
    width: 100%;
    margin-top: 10px;
    }

    button:nth-child(1) { background: #e2e8f0; }
    button:nth-child(2) { background: #90cdf4; }
    button:nth-child(3) { background: #63b3ed; }
    button:nth-child(4) { background: #3182ce; color: white; }
    */
	.btn-primary {
		background: #667eea;
		color: white;
		width: 100%;
		margin-top: 15px;
	}

	.btn-primary:hover {
		background: #5a67d8;
	}

	.progress {
		height: 8px;
		background: #eee;
		border-radius: 10px;
		margin-bottom: 20px;
		overflow: hidden;
	}

	.progress-bar {
		height: 100%;
		background: #667eea;
		/* transition: width 0.3s; */
	}

	.answer-btn {
		width: 100%;
		margin-top: 8px;
		padding: 10px;
		border-radius: 10px;
		border: none;
		cursor: pointer;
	}

	.btn0 {
		background: #e2e8f0;
	}
	.btn1 {
		background: #90cdf4;
	}
	.btn2 {
		background: #63b3ed;
	}
	.btn3 {
		background: #3182ce;
		color: white;
	}

	@keyframes fadeIn {
		from {
			opacity: 0;
			transform: translateY(10px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}
</style>