// app/frontend/static/js/api.js
export const API = {
    async fetchQueries() {
        const res = await fetch("/queries");
        if (!res.ok) throw new Error("Error cargando queries");
        return await res.json();
    },

    async runQuery(src, dst) {
        const res = await fetch("/query", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ src, dst })
        });
        if (!res.ok) throw new Error(await res.text());
        return await res.json();
    },

    async fetchQueryData(queryId, offset = 0, limit = 500) {
        const res = await fetch(
            `/query/${queryId}/data?offset=${offset}&limit=${limit}`
        );
        if (!res.ok) throw new Error("Error cargando datos");
        return await res.json();
    }
};
