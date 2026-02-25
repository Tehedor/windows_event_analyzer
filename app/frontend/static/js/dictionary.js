// app/frontend/static/js/dictionary.js
import { API } from "./api.js";

let componentDict = null;

export async function initDictionary() {
    setupTabs();
    try {
        componentDict = await API.fetchComponentDict();
        populateCustomDropdown();
        renderEventList("all"); // Carga todos por defecto
    } catch (error) {
        console.error("Error al inicializar el diccionario:", error);
    }
}

// -----------------------------------------------------
// Pestañas (Tabs)
// -----------------------------------------------------
function setupTabs() {
    const tabBtns = document.querySelectorAll(".tab-btn");
    const tabViews = document.querySelectorAll(".tab-view");

    tabBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            tabBtns.forEach(b => b.classList.remove("active"));
            tabViews.forEach(v => v.classList.remove("active"));
            
            btn.classList.add("active");
            document.getElementById(btn.getAttribute("data-target")).classList.add("active");
        });
    });
}

// -----------------------------------------------------
// Lógica del Desplegable Personalizado
// -----------------------------------------------------
function populateCustomDropdown() { // <--- ESTA LÍNEA ES IMPORTANTE
    const dropdown = document.getElementById("custom-dropdown");
    const header = document.getElementById("dropdown-header");
    const list = document.getElementById("dropdown-list");
    const selectedText = document.getElementById("dropdown-selected-text");
    const colorBoxHeader = document.getElementById("component-color-box");

    list.innerHTML = "";

    // 1️⃣ Opción "Todos"
    const allOpt = document.createElement("li");
    allOpt.className = "dropdown-option selected";
    allOpt.dataset.value = "all";
    allOpt.innerHTML = `
        <div class="color-box" style="background-color: #d1d5db;"></div>
        <span>Todos los componentes</span>
    `;
    list.appendChild(allOpt);

    // 2️⃣ Crear opciones de componentes (CON FILTRO NaN)
    const components = Object.keys(componentDict).sort();
    
    components.forEach(comp => {
        // 🚀 NUEVO: Si el componente termina en _NaN, no lo renderizamos
        if (comp.endsWith("_NaN")) return; 

        const color = componentDict[comp].base_color || "#d1d5db";
        
        const opt = document.createElement("li");
        opt.className = "dropdown-option";
        opt.dataset.value = comp;
        opt.innerHTML = `
            <div class="color-box" style="background-color: ${color};"></div>
            <span class="component-name">${comp}</span>
            <span class="copy-component-btn" data-component="${comp}">copy</span>
        `;
        list.appendChild(opt);
    });
    // -----------------------------------------------------
    // Evento copy de componente
    // -----------------------------------------------------
    list.querySelectorAll(".copy-component-btn").forEach(btn => {
        btn.addEventListener("click", (e) => {
            e.stopPropagation(); // 🔥 evita que se seleccione el dropdown

            const compName = btn.dataset.component;
            const textToCopy = `@${compName}`;

            navigator.clipboard.writeText(textToCopy)
                .then(() => {
                    btn.textContent = "copied!";
                    setTimeout(() => {
                        btn.textContent = "copy";
                    }, 1000);
                })
                .catch(err => {
                    console.error("Error copiando:", err);
                });
        });
    });

    // 3️⃣ Evento abrir/cerrar desplegable
    header.addEventListener("click", () => {
        dropdown.classList.toggle("open");
    });

    // 5️⃣ Evento seleccionar una opción
    const options = list.querySelectorAll(".dropdown-option");
    options.forEach(opt => {
        opt.addEventListener("click", function (e) {
            const current = e.currentTarget;

            const val = current.dataset.value;
            const text = current.querySelector(".component-name")?.textContent
                || current.querySelector("span").textContent;

            const color = current.querySelector(".color-box")?.style.backgroundColor;

            selectedText.textContent = text;
            colorBoxHeader.style.backgroundColor = color;

            options.forEach(o => o.classList.remove("selected"));
            current.classList.add("selected");

            dropdown.classList.remove("open"); // 🔥 cierre garantizado

            renderEventList(val);
        });
    });


}

// -----------------------------------------------------
// Renderizado de la lista inferior
// -----------------------------------------------------
function renderEventList(filter) {
    const listContainer = document.getElementById("dictionary-events-list");
    listContainer.innerHTML = ""; // Limpiar lista

    let eventsToShow = [];

    if (filter === "all") {
        Object.values(componentDict).forEach(comp => {
            eventsToShow = eventsToShow.concat(comp.events);
        });
    } else {
        if (componentDict[filter]) {
            eventsToShow = componentDict[filter].events;
        }
    }

    // Ordenar por ID
    eventsToShow.sort((a, b) => a.event_id - b.event_id);

    // Crear elementos en el HTML
    eventsToShow.forEach(ev => {
        const li = document.createElement("li");
        li.className = "dict-event-item";

        // Cuadradito
        const colorBox = document.createElement("div");
        colorBox.className = "color-box";
        colorBox.style.backgroundColor = ev.final_color || "#999";

        // ID
        const idSpan = document.createElement("span");
        idSpan.className = "dict-event-id";
        idSpan.textContent = ev.event_id;

        // Nombre
        const nameSpan = document.createElement("span");
        nameSpan.className = "dict-event-name";
        nameSpan.textContent = ev.event_name;

        li.appendChild(colorBox);
        li.appendChild(idSpan);
        li.appendChild(nameSpan);

        listContainer.appendChild(li);
    });
}


// Lógica para colapsar el formulario
const toggleBtn = document.getElementById('toggle-form-btn');
const formContainer = document.getElementById('query-form-container');

if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
        formContainer.classList.toggle('collapsed');
        
        // Opcional: Cambiar el título del botón según el estado
        if (formContainer.classList.contains('collapsed')) {
            toggleBtn.title = "Expandir formulario";
        } else {
            toggleBtn.title = "Comprimir formulario";
        }
    });
}