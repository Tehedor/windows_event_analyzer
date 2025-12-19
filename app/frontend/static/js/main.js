// app/frontend/static/js/main.js
import { API } from "./api.js";
import { state } from "./state.js";
import {
    renderQueriesList,
    selectQuery,
    showVisualizationPlaceholder
} from "./ui.js";

document.addEventListener("DOMContentLoaded", initApp);

async function initApp() {
    await loadQueries();

    if (state.queries.length > 0) {
        selectQuery(state.queries[state.queries.length - 1].query_id);
    } else {
        showVisualizationPlaceholder();
    }

    document
        .getElementById("query-form")
        .addEventListener("submit", onSubmitQuery);
}

async function loadQueries() {
    state.queries = await API.fetchQueries();
    renderQueriesList(state.queries);
}

async function onSubmitQuery(e) {
    e.preventDefault();

    const src = document.getElementById("src-input").value || null;
    const dst = document.getElementById("dst-input").value || null;

    const result = await API.runQuery(src, dst);
    await loadQueries();
    selectQuery(result.query_id);
}
