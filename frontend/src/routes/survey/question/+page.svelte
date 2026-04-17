<script></script>

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
