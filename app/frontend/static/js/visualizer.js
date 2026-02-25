// app/frontend/static/js/visualizer.js
import { API } from "./api.js";
import { state } from "./state.js";
import {
    showVisualizationPlaceholder,
    showVisualizationContent
} from "./ui.js";

let EVENT_DICT = null;

async function loadEventDictionary() {
    if (EVENT_DICT) return EVENT_DICT;
    const res = await fetch("/events");
    if (!res.ok) throw new Error("Error cargando diccionario");
    EVENT_DICT = await res.json();
    return EVENT_DICT;
}

// app/frontend/static/js/visualizer.js
export async function renderVisualization(query) {
    const container = document.getElementById("visualization-content");
    container.innerHTML = "";
    if (!query) {
        showVisualizationPlaceholder();
        return;
    }
    showVisualizationContent();

    // Resetear paginación al cambiar de consulta
    state.pagination.offset = 0;
    state.pagination.total = 0;
    state.pagination.loading = false;

    await loadPage(query, 0); // Cargamos la página 0 (inicial)
}

// 🔥 NUEVO: Función para moverse entre páginas
export async function loadPage(query, direction = 0) {
    if (state.pagination.loading) return;
    state.pagination.loading = true;

    // direction: 1 (siguiente), -1 (anterior), 0 (actual/reset)
    state.pagination.offset += (direction * state.pagination.limit);
    if (state.pagination.offset < 0) state.pagination.offset = 0;

    const { offset, limit } = state.pagination;
    const data = await API.fetchQueryData(query.query_id, offset, limit);
 
    state.pagination.total = data.total;

    renderWindows(data.rows, offset);

    state.pagination.loading = false;
    updatePaginationControls(); // Actualizamos los botones
}

// 🔥 OPTIMIZADO// 🔥 MÁXIMA OPTIMIZACIÓN: Renderizado por Strings HTML
async function renderWindows(rows, currentOffset) {
    const container = document.getElementById("visualization-content");
    const eventDict = await loadEventDictionary();

    // Comprobamos el estado global para ver si estamos en modo compacto
    const isCompact = state.viewMode === "compact";

    if (rows.length === 0) {
        container.innerHTML = '<div class="no-data-message">No hay datos para mostrar en esta página.</div>';
        return;
    }

    // Usaremos un Array para ir apilando todo el HTML como texto (muchísimo más rápido que createElement)
    let htmlChunks = [];

    rows.forEach((row, i) => {
        const idx = currentOffset + i;
        
        // Abrimos la ventana
        let windowHtml = `<div class="window">`;
        
        // Etiqueta
        windowHtml += `<div class="window-label">${idx + 1}</div>`;
        
        // Bloque Observación
        windowHtml += createEventsBlockHTML(row.obs_events || [], eventDict, isCompact);
        
        // Separador
        windowHtml += `<div class="window-separator"></div>`;
        
        // Bloque Predicción
        windowHtml += createEventsBlockHTML(row.pred_events || [], eventDict, isCompact);
        
        // Cerramos la ventana
        windowHtml += `</div>`;
        
        htmlChunks.push(windowHtml);
    });

    // Inyectamos todo el texto HTML de un solo golpe en el DOM (Renderizado instantáneo)
    container.innerHTML = htmlChunks.join('');
    
    // Subir el scroll arriba del todo automáticamente al cambiar de página
    container.scrollTop = 0;
    container.scrollLeft = 0;
}

// Generador del HTML interno de cada bloque
function createEventsBlockHTML(events, dict, isCompact) {
    let html = `<div class="window-events">`;

    for (let i = 0; i < events.length; i++) {
        const id = events[i];
        const ev = dict[id];

        if (ev) {
            const p1 = ev.percentile_origin.replace("Q", "");
            const p2 = ev.percentile_target.replace("Q", "");
            
            // Usamos comillas simples en los atributos HTML para evitar conflictos
            const tooltip = `${ev.event_name}&#10;ID: ${ev.event_id}`;

            if (isCompact) {
                html += `<div class="event-block compact" style="background-color: ${ev.base_color}; color: #fff;" title="${tooltip}">${ev.event_id}</div>`;
            } else {
                html += `
                    <div class="event-block compact" style="background-color: ${ev.base_color}; color: #fff;" title="${tooltip}">
                        <div class="mini-grid">
                            <div class="col-id">${ev.event_id}</div>
                            <div class="col-sep">|</div>
                            <div class="col-stack">
                                <div class="row-range">${p1}</div>
                                <div class="row-range">${p2}</div>
                            </div>
                        </div>
                    </div>`;
            }
        } else {
            html += `<div class="event-block compact" style="background-color: #9ca3af;" title="Evento ${id}">${id}</div>`;
        }
    }

    html += `</div>`;
    return html;
}


// 🔥 NUEVO: Controles de paginación estilo Google (< Anterior | Siguiente >)
function updatePaginationControls() {
    let paginationBox = document.getElementById("pagination-controls");
    
    // Si no existe, lo creamos y lo pegamos debajo del contenedor de visualización
    if (!paginationBox) {
        paginationBox = document.createElement("div");
        paginationBox.id = "pagination-controls";
        document.getElementById("visualization-container").appendChild(paginationBox);
    }

    const { offset, limit, total } = state.pagination;
    const currentPage = Math.floor(offset / limit) + 1;
    const totalPages = Math.ceil(total / limit) || 1;

    // Generar HTML de los botones
    paginationBox.innerHTML = `
        <button id="btn-prev-page" class="pag-btn" ${currentPage === 1 ? 'disabled' : ''}>◀ Anterior</button>
        <span class="page-info">Página <b>${currentPage}</b> de ${totalPages} <span style="color:#6b7280; font-size:11px;">(${total} ventanas)</span></span>
        <button id="btn-next-page" class="pag-btn" ${currentPage >= totalPages ? 'disabled' : ''}>Siguiente ▶</button>
    `;

    // Asignar eventos (usamos setTimeout para asegurar que el HTML se haya insertado)
    setTimeout(() => {
        const btnPrev = document.getElementById("btn-prev-page");
        const btnNext = document.getElementById("btn-next-page");

        if(btnPrev) {
            btnPrev.onclick = () => {
                const q = state.queries.find(q => q.query_id === state.selectedQueryId);
                loadPage(q, -1);
            };
        }
        if(btnNext) {
            btnNext.onclick = () => {
                const q = state.queries.find(q => q.query_id === state.selectedQueryId);
                loadPage(q, 1);
            };
        }
    }, 0);
}



export function enableDragScroll() {
    const container = document.getElementById("visualization-container");

    let isDown = false;
    let startX;
    let startY;
    let scrollLeft;
    let scrollTop;

    container.addEventListener("mousedown", (e) => {
        isDown = true;
        container.classList.add("dragging");
        startX = e.pageX - container.offsetLeft;
        startY = e.pageY - container.offsetTop;
        scrollLeft = container.scrollLeft;
        scrollTop = container.scrollTop;
    });

    container.addEventListener("mouseleave", () => {
        isDown = false;
        container.classList.remove("dragging");
    });

    container.addEventListener("mouseup", () => {
        isDown = false;
        container.classList.remove("dragging");
    });

    container.addEventListener("mousemove", (e) => {
        if (!isDown) return;
        e.preventDefault();

        const x = e.pageX - container.offsetLeft;
        const y = e.pageY - container.offsetTop;

        const walkX = (x - startX);
        const walkY = (y - startY);

        container.scrollLeft = scrollLeft - walkX;
        container.scrollTop = scrollTop - walkY;
    });
}