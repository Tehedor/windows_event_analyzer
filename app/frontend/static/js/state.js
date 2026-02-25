// app/frontend/static/js/state.js

export const state = {
    queries: [],              // histórico de consultas
    selectedQueryId: null,    // query seleccionada

    viewMode: "normal",   

    pagination: {
        offset: 0,
        limit: 250,
        total: 0,
        loading: false
    }
};
