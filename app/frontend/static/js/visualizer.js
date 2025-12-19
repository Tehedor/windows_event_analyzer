// app/frontend/static/js/visualizer.js
import { API } from "./api.js";
import { state } from "./state.js";
import {
    showVisualizationPlaceholder,
    showVisualizationContent
} from "./ui.js";

/* =========================================================
   Diccionario de eventos
   ========================================================= */
let EVENT_DICT = null;

async function loadEventDictionary() {
    if (EVENT_DICT) return EVENT_DICT;

    const res = await fetch("/events");
    if (!res.ok) throw new Error("Error cargando diccionario");

    EVENT_DICT = await res.json();
    return EVENT_DICT;
}

/* =========================================================
   Render principal (RESET)
   ========================================================= */
export async function renderVisualization(query) {
    const container = document.getElementById("visualization-content");
    container.innerHTML = "";

    if (!query) {
        showVisualizationPlaceholder();
        return;
    }

    showVisualizationContent();

    // Reset paginación
    state.pagination.offset = 0;
    state.pagination.total = 0;
    state.pagination.loading = false;


    await loadMoreWindows(query, true);
}

/* =========================================================
   Cargar más ventanas
   ========================================================= */
export async function loadMoreWindows(query, reset = false) {
    if (state.pagination.loading) return;

    state.pagination.loading = true;

    const { offset, limit } = state.pagination;

    const data = await API.fetchQueryData(
        query.query_id,
        offset,
        limit
    );

    state.pagination.total = data.total;

    renderWindows(data.rows, offset === 0);

    state.pagination.offset += data.rows.length;
    state.pagination.loading = false;

    updateLoadMoreButton();
}

/* =========================================================
   Render ventanas
   ========================================================= */
async function renderWindows(rows, firstBatch) {
    const container = document.getElementById("visualization-content");
    const eventDict = await loadEventDictionary();

    rows.forEach((row, i) => {
        const idx = state.pagination.offset + i;

        const w = document.createElement("div");
        w.className = "window";

        w.innerHTML = `<div class="window-label">Ventana ${idx + 1}</div>`;

        w.appendChild(createEventsBlock(
            row.observation_events || row.obs_events || [],
            eventDict
        ));

        // w.appendChild(document.createTextNode(" | "));
        const sep = document.createElement("div");
        sep.className = "window-separator";
        w.appendChild(sep);


        w.appendChild(createEventsBlock(
            row.prediction_events || row.pred_events || [],
            eventDict
        ));

        container.appendChild(w);
    });
}

/* =========================================================
   Eventos
   ========================================================= */
function createEventsBlock(events, dict) {
    const c = document.createElement("div");
    c.className = "window-events";

    events.forEach(id => {
        const ev = dict[id];

        const b = document.createElement("div");
        b.className = "event-block compact";

        if (ev) {
            b.style.backgroundColor = ev.base_color;
            b.style.color = "#fff";

            const idSpan = document.createElement("span");
            idSpan.textContent = ev.event_id;

            const pctSpan = document.createElement("span");
            pctSpan.className = "event-percentile";
            pctSpan.textContent =
                ev.percentile_origin.replace("Q", "") +
                "-" +
                ev.percentile_target.replace("Q", "");

            b.appendChild(idSpan);
            b.appendChild(document.createTextNode(" | "));
            b.appendChild(pctSpan);
        } else {
            b.textContent = id;
        }

        c.appendChild(b);
    });

    return c;
}

/* =========================================================
   Botón cargar más
   ========================================================= */
function updateLoadMoreButton() {
    let btn = document.getElementById("load-more-btn");

    if (!btn) {
        btn = document.createElement("button");
        btn.id = "load-more-btn";
        btn.textContent = "Cargar más";
        btn.onclick = () => {
            const q = state.queries.find(
                q => q.query_id === state.selectedQueryId
            );
            loadMoreWindows(q);
        };

        document
            .getElementById("visualization-container")
            .appendChild(btn);
    }

    if (state.pagination.offset >= state.pagination.total) {
        btn.style.display = "none";
    } else {
        btn.style.display = "block";
        btn.textContent =
            `Cargar más (${state.pagination.offset}/${state.pagination.total})`;
    }
}
