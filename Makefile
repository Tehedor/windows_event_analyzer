# python -m gunicorn -b 0.0.0.0:8050 app:server --timeout 120
# nice -n 19 python -m gunicorn -b 0.0.0.0:8050 app:server --timeout 120


# Variables
PORT = 8050

.PHONY: run_dev run_dev_build run_server build up down restart logs clean make_tar_datasets help

## Desarrollo local
run_dev:
	@echo "🚀 Iniciando en modo desarrollo..."
	@docker compose -f ./docker-compose.dev.yml up 
# 	@cd app && \
	nice -n 19 python3 app.py

run_dev_build:
	@echo "🔨 Construyendo imagen Docker para desarrollo..."
	@docker compose -f ./docker-compose.dev.yml build

run_server:
	@echo "🚀 Iniciando con Gunicorn (producción local)..."
	@nice -n 19 python -m gunicorn -b 0.0.0.0:$(PORT) app:server --workers=1 --threads=4 --timeout=120

make_tar_datasets:
	@echo "📦 Creando archivo comprimido de Datasets..."
	@tar -czvf Datasets.tar.gz Datasets/

extract_tar_datasets:
	@echo "📂 Extrayendo Datasets.tar.gz..."
	@tar -xzvf Datasets.tar.gz
	@echo "✅ Datasets extraídos correctamente"



run:
	@echo "🚀 Iniciando contenedor Docker..."
	@docker compose up --build 



cat_all_py:
	@echo "📄 Concatenando todos los archivos .py..."
	@find app -name "*.py" -type f | sort | while read file; do \
        echo "\n\n================================"; \
        echo "FILE: $$file"; \
        echo "================================\n"; \
        cat "$$file"; \
	done > app_content.txt
	@echo "✅ Contenido guardado en app_content.txt"
