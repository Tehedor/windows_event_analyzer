// app/frontend/static/js/visualizer.js

import { API } from "./api.js";
import {
    showVisualizationPlaceholder,
    showVisualizationContent
} from "./ui.js";

/* =========================================================
   Caché del diccionario de eventos
   ========================================================= */
let EVENT_DICT = null;

async function loadEventDictionary() {
    if (EVENT_DICT) return EVENT_DICT;

    const res = await fetch("/events");
    if (!res.ok) {
        throw new Error("Error cargando diccionario de eventos");
    }

    EVENT_DICT = await res.json();
    return EVENT_DICT;
}

/* =========================================================
   Render principal de la visualización
   ========================================================= */
export async function renderVisualization(query) {
    const container = document.getElementById("visualization-content");
    container.innerHTML = "";

    if (!query || !query.query_id) {
        showVisualizationPlaceholder();
        return;
    }

    showVisualizationContent();

    try {
        // 🔹 cargar datos de la query
        const rows = await API.fetchQueryData(query.query_id);

        if (!Array.isArray(rows) || rows.length === 0) {
            container.innerHTML = "<p>No hay datos para esta consulta</p>";
            return;
        }

        // 🔹 cargar diccionario de eventos
        const eventDict = await loadEventDictionary();

        rows.forEach((row, index) => {
            const windowEl = document.createElement("div");
            windowEl.className = "window";

            // -------------------------------
            // Etiqueta de ventana
            // -------------------------------
            const label = document.createElement("div");
            label.className = "window-label";
            label.textContent = `Ventana ${index + 1}`;

            // -------------------------------
            // Eventos observación
            // -------------------------------
            const obsEvents = createEventsBlock(
                row.observation_events ||
                row.obs_events ||
                [],
                eventDict
            );

            // -------------------------------
            // Eventos predicción
            // -------------------------------
            const predEvents = createEventsBlock(
                row.prediction_events ||
                row.pred_events ||
                [],
                eventDict
            );

            // -------------------------------
            // Montaje final
            // -------------------------------
            windowEl.appendChild(label);
            windowEl.appendChild(obsEvents);

            const sep = document.createElement("span");
            sep.textContent = " | ";
            sep.style.margin = "0 6px";

            windowEl.appendChild(sep);
            windowEl.appendChild(predEvents);

            container.appendChild(windowEl);
        });

    } catch (err) {
        console.error(err);
        container.innerHTML = "<p>Error cargando visualización</p>";
    }
}

/* =========================================================
   Render de bloques de eventos (CON COLOR REAL)
   ========================================================= */
function createEventsBlock(events = [], eventDict) {
    const container = document.createElement("div");
    container.className = "window-events";

    events.forEach(eventId => {
        const block = document.createElement("div");
        block.className = "event-block";

        const event = eventDict[eventId];

        if (event) {
            block.style.backgroundColor = event.final_color;

            // 🔹 Texto dentro del bloque = ID del evento
            block.textContent = eventId;

            // 🔹 Tooltip completo
            block.title =
                `${event.event_name}\n` +
                `Percentil: ${event.percentile_target}\n` +
                `Evento ID: ${eventId}`;

            // 🔹 Color de texto automático
            block.style.color = getContrastColor(event.final_color);
        } else {
            // Fallback seguro
            block.style.backgroundColor = "#9ca3af";
            block.textContent = eventId;
            block.style.color = "#000";
            block.title = `Evento ${eventId}`;
        }

        container.appendChild(block);
    });

    return container;
}

/* =========================================================
   Utilidad: color de texto automático (blanco/negro)
   ========================================================= */
function getContrastColor(hexColor) {
    if (!hexColor || !hexColor.startsWith("#")) return "#000";

    const r = parseInt(hexColor.substr(1, 2), 16);
    const g = parseInt(hexColor.substr(3, 2), 16);
    const b = parseInt(hexColor.substr(5, 2), 16);

    // luminancia perceptual
    const luminance = (0.299 * r + 0.587 * g + 0.114 * b);

    return luminance > 150 ? "#000000" : "#ffffff";
}
