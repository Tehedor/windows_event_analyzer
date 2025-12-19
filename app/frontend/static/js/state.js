// app/frontend/static/js/state.js

export const state = {
    queries: [],              // histórico de consultas
    selectedQueryId: null,    // query seleccionada

    pagination: {
        offset: 0,
        limit: 500,
        total: 0,
        loading: false
    }
};
