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

export async function loadPage(query, direction = 0) {
    if (state.pagination.loading) return;
    state.pagination.loading = true;

    // direction: 1 (siguiente), -1 (anterior), 0 (actual/reset sin mover página)
    state.pagination.offset += (direction * state.pagination.limit);
    if (state.pagination.offset < 0) state.pagination.offset = 0;

    const { offset, limit } = state.pagination;
    const data = await API.fetchQueryData(query.query_id, offset, limit);
 
    state.pagination.total = data.total;

    await renderWindows(data.rows, offset);

    state.pagination.loading = false;
    updatePaginationControls(); // Actualizamos los botones
}

// 🔥 MÁXIMA OPTIMIZACIÓN: Renderizado por Strings HTML
async function renderWindows(rows, currentOffset) {
    const container = document.getElementById("visualization-content");
    const eventDict = await loadEventDictionary();

    // Comprobamos el estado global para ver si estamos en modo compacto
    const isCompact = state.viewMode === "compact";

    if (rows.length === 0) {
        container.innerHTML = '<div class="no-data-message">No hay datos para mostrar en esta página.</div>';
        return;
    }

    // Usaremos un Array para ir apilando todo el HTML como texto
    let htmlChunks = [];

    rows.forEach((row, i) => {
        const idx = currentOffset + i;
        
        let windowHtml = `<div class="window">`;
        windowHtml += `<div class="window-label">${idx + 1}</div>`;
        
        // Soportar ambas nomenclaturas (obs_events o observation_events)
        const obs = row.obs_events || row.observation_events || [];
        const pred = row.pred_events || row.prediction_events || [];

        windowHtml += createEventsBlockHTML(obs, eventDict, isCompact);
        windowHtml += `<div class="window-separator"></div>`;
        windowHtml += createEventsBlockHTML(pred, eventDict, isCompact);
        
        windowHtml += `</div>`;
        
        htmlChunks.push(windowHtml);
    });

    // Inyectamos todo el texto HTML de un solo golpe en el DOM
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
            // Manejar variables si existen, sino en blanco
            const p1 = ev.percentile_origin ? ev.percentile_origin.replace("Q", "") : "";
            const p2 = ev.percentile_target ? ev.percentile_target.replace("Q", "") : "";
            
            const tooltip = `${ev.event_name}&#10;ID: ${ev.event_id}`;
            const bgColor = ev.base_color || ev.final_color || "#d1d5db";

            if (isCompact) {
                html += `<div class="event-block compact" style="background-color: ${bgColor}; color: #fff;" title="${tooltip}">${ev.event_id}</div>`;
            } else {
                html += `
                    <div class="event-block compact" style="background-color: ${bgColor}; color: #fff;" title="${tooltip}">
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

// 🔥 Controles de paginación CON INPUT INCLUIDO
function updatePaginationControls() {
    let paginationBox = document.getElementById("pagination-controls");
    
    if (!paginationBox) {
        paginationBox = document.createElement("div");
        paginationBox.id = "pagination-controls";
        document.getElementById("visualization-container").appendChild(paginationBox);
    }

    const { offset, limit, total } = state.pagination;
    const currentPage = Math.floor(offset / limit) + 1;
    const totalPages = Math.ceil(total / limit) || 1;

    // Generar HTML de los botones con el input type="number"
    paginationBox.innerHTML = `
        <button id="btn-prev-page" class="pag-btn" ${currentPage === 1 ? 'disabled' : ''}>◀ Anterior</button>
        <span class="page-info">
            Página <input type="number" id="page-input" class="page-input-style" value="${currentPage}" min="1" max="${totalPages}"> de ${totalPages} 
            <span style="color:#6b7280; font-size:11px;">(${total} ventanas)</span>
        </span>
        <button id="btn-next-page" class="pag-btn" ${currentPage >= totalPages ? 'disabled' : ''}>Siguiente ▶</button>
    `;

    // Asignar eventos
    setTimeout(() => {
        const btnPrev = document.getElementById("btn-prev-page");
        const btnNext = document.getElementById("btn-next-page");
        const pageInput = document.getElementById("page-input");

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
        
        // Evento para cambiar de página tipeando el número
        if(pageInput) {
            pageInput.addEventListener("change", (e) => {
                let newPage = parseInt(e.target.value);
                
                // Validaciones por si el usuario pone letras o números locos
                if (isNaN(newPage) || newPage < 1) newPage = 1;
                if (newPage > totalPages) newPage = totalPages;
                
                state.pagination.offset = (newPage - 1) * state.pagination.limit;
                
                const q = state.queries.find(q => q.query_id === state.selectedQueryId);
                loadPage(q, 0); 
            });
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