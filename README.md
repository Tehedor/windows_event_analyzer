# Windows Event Analyzer
Aplicación de visualización de eventos



# Structure
```xml
windows_app/
├── app/
│   ├── main.py                  # Entry point de la app web
│   │
│   ├── core/                    # Lógica pura (no sabe nada de web)
│   │   ├── config.py
│   │   ├── preprocessor.py
│   │   ├── input_parser.py
│   │   ├── query_engine.py
│   │   ├── event_dictionary.py
│   │   └── cache.py             # (nuevo) control de consultas repetidas
│   │
│   ├── services/                # Casos de uso
│   │   ├── query_service.py     # Orquesta una consulta completa
│   │   └── dictionary_service.py
│   │
│   ├── api/                     # Backend web (REST)
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   ├── schemas.py
│   │   └── dependencies.py
│   │
│   ├── renderers/               # Representaciones
│   │   ├── text_renderer.py
│   │   └── web_renderer.py      # HTML-friendly
│   │
│   └── state/                   # Estado compartido en memoria
│       ├── registry.py          # consultas en curso / cache
│       └── locks.py
│
├── frontend/
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   └── icons/
│   │
│   └── templates/
│       ├── index.html
│       └── components/
│
├── config/
│   └── config.yml
│
├── datasets/
│   ├── raw/
│   ├── processed/
│   └── components.yml
│
├── output/
│   ├── queries/                 # resultados cacheados
│   └── logs/
│
├── debug/
│
├── scripts/                     # utilidades CLI
│   └── run_query.py
│
├── tests/
│
├── README.md
└── requirements.txt


```