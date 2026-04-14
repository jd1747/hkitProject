<script>
    import { onMount } from "svelte";
    import { goto } from "$app/navigation";
    import { resolve } from "$app/paths";

    let session_id;
    let result = $state("");
    let count = $state(0);

    async function load() {
        const res = await fetch(`http://127.0.0.1:8000/result/${session_id}`);
        const data = await res.json();

        result = data.result;
        count = data.yes_count;
    }

    async function save() {
        await fetch(`http://127.0.0.1:8000/save/${session_id}`, {
            method: "POST"
        });

        alert("CSV 저장 완료!");
    }

    function restart() {
        localStorage.clear();
        goto(resolve("/"));
    }

    onMount(() => {
        session_id = localStorage.getItem("session_id");
        load();
    });
</script>

<h1>결과</h1>

<p>YES 개수: {count}</p>
<p>결과: {result}</p>

<button onclick={save}>저장</button>
<button onclick={restart}>다시하기</button>