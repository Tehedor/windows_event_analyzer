// app/frontend/static/js/ui.js
import { state } from "./state.js";
import { renderVisualization } from "./visualizer.js";

export function renderQueriesList(queries) {
    const list = document.getElementById("queries-list");
    // console.log("Renderizando lista de queries:", queries);
    list.innerHTML = "";

    queries.forEach(q => {
        const li = document.createElement("li");
        li.className = "query-item";
        li.dataset.queryId = q.query_id;

        li.innerHTML = `
            <div class="query-main">
                src=${q.src_raw ?? q.src} | dst=${q.dst_raw ?? q.dst}
            </div>
            <div class="query-meta">
                ${q.status === "done" ? `<span class="query-rows">${q.rows} filas</span>` : ""}
                <span class="query-status ${q.status}">${q.status}</span>
            </div>
        `;
        if (q.status !== "running") {
            li.onclick = () => selectQuery(q.query_id);
        }
        list.appendChild(li);
    });

    updateActiveQuery();
}

export function selectQuery(queryId) {
    state.selectedQueryId = queryId;
    updateActiveQuery();

    const query = state.queries.find(q => q.query_id === queryId);
    renderVisualization(query);
}

export function updateActiveQuery() {
    document.querySelectorAll(".query-item").forEach(el => {
        el.classList.toggle(
            "active",
            el.dataset.queryId === state.selectedQueryId
        );
    });
}

export function showVisualizationPlaceholder() {
    document.getElementById("visualization-placeholder").style.display = "flex";
    document.getElementById("visualization-content").style.display = "none";
}

export function showVisualizationContent() {
    document.getElementById("visualization-placeholder").style.display = "none";
    // Usar flex para permitir centrar el mensaje vacío verticalmente
    document.getElementById("visualization-content").style.display = "flex";
}
