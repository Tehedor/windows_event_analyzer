// app/frontend/static/js/main.js
import { API } from "./api.js";
import { state } from "./state.js";
import {
    renderQueriesList,
    selectQuery,
    showVisualizationPlaceholder
} from "./ui.js";
import { enableDragScroll, loadPage } from "./visualizer.js"; // 🔥 loadPage importado aquí
import { initDictionary } from "./dictionary.js";

document.addEventListener("DOMContentLoaded", initApp);

async function initApp() {
    await initDictionary();
    // enableDragScroll();
    
    await loadQueries();

    if (state.queries.length > 0) {
        selectQuery(state.queries[state.queries.length - 1].query_id);
    } else {
        showVisualizationPlaceholder();
    }

    document
        .getElementById("query-form")
        .addEventListener("submit", onSubmitQuery);

    const toggle = document.getElementById("toggle-view-mode");

    toggle.addEventListener("change", () => {
        state.viewMode = toggle.checked ? "compact" : "normal";

        const container = document.getElementById("visualization-container");
        container.classList.toggle("compact-mode", state.viewMode === "compact");

        if (state.selectedQueryId) {
            const q = state.queries.find(q => q.query_id === state.selectedQueryId);
            // 🔥 AQUÍ: Usamos loadPage(q, 0) para no resetear la paginación
            if (q) loadPage(q, 0);
        }
    });
    
    setInterval(async () => {
        await loadQueries();
    }, 3000); // cada 3 segundos
}

async function loadQueries() {
    state.queries = await API.fetchQueries();
    renderQueriesList(state.queries);
}

async function onSubmitQuery(e) {
    e.preventDefault();

    const src = document.getElementById("src-input").value || null;
    const dst = document.getElementById("dst-input").value || null;

    // 1️⃣ Crear placeholder local inmediato
    const tempQuery = {
        query_id: "temp_" + Date.now(),
        src_raw: src,
        dst_raw: dst,
        status: "running",
        rows: null
    };

    state.queries.push(tempQuery);
    renderQueriesList(state.queries);

    try {
        // 2️⃣ Ejecutar query real
        const result = await API.runQuery(src, dst);

        // 3️⃣ Recargar lista real desde backend
        await loadQueries();

    } catch (err) {
        console.error(err);
    }
}