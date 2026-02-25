// app/frontend/static/js/api.js

export const API = {
    async fetchQueries() {
        // 🚀 AÑADIDO: ?t=... y cache: 'no-store' para evitar que el navegador se quede atascado en 'running'
        const res = await fetch(`/queries?t=${Date.now()}`, { cache: "no-store" });
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

    async fetchQueryData(queryId, offset = 0, limit = 250) {
        // 🚀 AÑADIDO: También evitamos la caché al cambiar de página
        const res = await fetch(
            `/query/${queryId}/data?offset=${offset}&limit=${limit}&t=${Date.now()}`,
            { cache: "no-store" }
        );
        if (!res.ok) throw new Error("Error cargando datos");
        return await res.json();
    },

    async fetchComponentDict() {
        const res = await fetch("/componentDict", { cache: "no-store" });
        if (!res.ok) throw new Error("Error cargando diccionario de componentes");
        return await res.json();
    }
};