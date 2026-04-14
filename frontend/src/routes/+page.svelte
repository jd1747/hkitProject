<script>
    let name = $state("");
    let session_id = $state(null);
    let question = $state(null);
    let finished = $state(false);
    let result = $state(null);

    async function start() {
        const res = await fetch("http://127.0.0.1:8000/session", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user_name: name })
        });

        const data = await res.json();
        session_id = data.session_id;
        await getQuestion();
    }

    async function getQuestion() {
        const res = await fetch(`http://127.0.0.1:8000/question/${session_id}`);
        const data = await res.json();

        if (data.message === "설문 완료") {
            finished = true;
            await getResult();
        } else {
            question = data;
        }
    }

    async function answer(value) {
        await fetch("http://127.0.0.1:8000/answer", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ session_id, answer: value })
        });

        await getQuestion();
    }

    async function getResult() {
        const res = await fetch(`http://127.0.0.1:8000/result/${session_id}`);
        result = await res.json();

        await fetch(`http://127.0.0.1:8000/save/${session_id}`, {
            method: "POST"
        });
    }
</script>

<style>
    body {
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
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        animation: fadeIn 0.4s ease;
    }

    input {
        width: 100%;
        padding: 12px;
        border-radius: 10px;
        border: 1px solid #ddd;
        margin-top: 15px;
        font-size: 16px;
    }

    button {
    width: 100%;
    margin-top: 10px;
    }

    button:nth-child(1) { background: #e2e8f0; }
    button:nth-child(2) { background: #90cdf4; }
    button:nth-child(3) { background: #63b3ed; }
    button:nth-child(4) { background: #3182ce; color: white; }

    .btn-primary {
        background: #667eea;
        color: white;
        width: 100%;
    }

    .btn-primary:hover {
        background: #5a67d8;
    }

    .btn-yes {
        background: #48bb78;
        color: white;
        width: 100%;
    }

    .btn-no {
        background: #f56565;
        color: white;
        width: 100%;
    }

    .btn-yes:hover { background: #38a169; }
    .btn-no:hover { background: #e53e3e; }

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
        transition: width 0.3s;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
</style>

<div class="container">
    <div class="card">

        <!-- 시작 -->
        {#if !session_id}
            <h2>🧠 ADHD 설문</h2>
            <input bind:value={name} placeholder="이름 입력" />
            <button class="btn-primary" onclick={start} disabled={!name?.trim()}>
                시작하기
            </button>

        <!-- 질문 -->
        {:else if !finished && question}
            <div class="progress">
                <div
                    class="progress-bar"
                    style="width: {(question.question_id / 20) * 100}%"
                ></div>
            </div>

            <p>{question.progress}</p>
            <h3>{question.text}</h3>

            <button onclick={() => answer(0)}>0️⃣ 극히 드물다</button>
            <button onclick={() => answer(1)}>1️⃣ 가끔 있었다</button>
            <button onclick={() => answer(2)}>2️⃣ 종종 있었다</button>
            <button onclick={() => answer(3)}>3️⃣ 대부분 그랬다</button>
        <!-- 결과 -->
        {:else if finished && result}
            <h2>📊 결과</h2>
            <p>총 점수: {result.total_score}</p>
            <h3 class={result.total_score >= 19 ? "danger" : "safe"}>
                {result.result}
            </h3>

            {#if result.total_score >= 19}
                <p style="color:red;">주의가 필요합니다. 전문가 상담을 권장합니다.</p>
            {:else}
                <p style="color:green;">정상 범위입니다 👍</p>
            {/if}

            <button class="btn-primary" onclick={() => location.reload()}>
                다시하기
            </button>
        {/if}

    </div>
</div>