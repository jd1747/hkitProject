<script>
    import { onMount } from "svelte";
    import { goto } from "$app/navigation";
    import { resolve } from "$app/paths";

    let session_id;
    let question = $state("");
    let progress = $state("");

    async function load() {
        const res = await fetch(`http://127.0.0.1:8000/question/${session_id}`);
        const data = await res.json();

        if (data.message === "설문 완료") {
            goto(resolve("/result"));
            return;
        }

        question = data.text;
        progress = data.progress;
    }

    async function answer(val) {
        await fetch("http://127.0.0.1:8000/answer", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                session_id: session_id,
                answer: val
            })
        });

        load();
    }

    onMount(() => {
        session_id = localStorage.getItem("session_id");
        load();
    });
</script>

<h2>{progress}</h2>
<p>{question}</p>

<button onclick={() => answer(0)}>0️⃣ 극히 드물다</button>
<button onclick={() => answer(1)}>1️⃣ 가끔 있었다</button>
<button onclick={() => answer(2)}>2️⃣ 종종 있었다</button>
<button onclick={() => answer(3)}>3️⃣ 대부분 그랬다</button>