PORT = 8050

######################################################################################
##### Deploy
######################################################################################
.PHONY: run run-build down
run-build:
	@echo "🚀 Iniciando contenedor Docker..."
	@docker compose up --build 

run:
	@echo "🚀 Iniciando contenedor Docker..."
	@docker compose up -d 

down:
	@echo "🛑 Deteniendo contenedor Docker..."
	@docker compose down

######################################################################################
##### Development
######################################################################################
.PHONY: run_dev-build run_dev down_dev run_dev-test
run_dev-build:
	@echo "🔨 Construyendo imagen Docker para desarrollo..."
	@docker compose -f ./docker-compose.dev.yml build

run_dev:
	@echo "🚀 Iniciando en modo desarrollo..."
	@docker compose -f ./docker-compose.dev.yml up 

run_dev-test:
	@echo "🚀 Iniciando en modo desarrollo..."
	@OUTPUT_DIR=output/queries OUTPUT_DIR_CSV=output/queries_csv \
        docker compose -f ./docker-compose.dev.yml up -d dash-dev
# docker exec mi_app_desarrollo env | grep -E 'OUTPUT_DIR|OUTPUT_DIR_CSV|INPUT_MULTI_REQUESTS_FILE'

down_dev:
	@echo "🛑 Deteniendo contenedor de desarrollo de pruebas..."
	@docker compose -f ./docker-compose.dev.yml down

######################################################################################
##### Test 
######################################################################################
VENV_BIN = .venv/bin
PYTHON = $(VENV_BIN)/python
PYTEST = $(VENV_BIN)/pytest
CONTAINER_NAME = mi_app_desarrollo

.PHONY: test_dsl test_dsl2 test_4 
test_dsl:
	@echo "🧪 Testeando DSL..."
	@cd app && \
	$(PYTHON) -m core.test.test_dsl

test_dsl2:
	@echo "🧪 Testeando DSL..."
	@cd app && \
	$(PYTHON) -m core.test.test_dsl2	

test_4:
	@echo "🧪 Testeando módulo 4..."
	@cd app && \
	$(PYTHON) -m core.test.test_module4

# Test de consutlas multiples a api rest
.PHONY: api_queries
# Realiza múltiples consultas a la API REST a paritr del file app/scripts/multi_requests.py
api_queries:
# 	@docker exec -it ${CONTAINER_NAME} ls
# 	@docker exec -it ${CONTAINER_NAME} pwd

	@docker exec -it ${CONTAINER_NAME} python -m scripts.multi_requests
# 	@$(PYTHON) -m files_output.multi_requests_file
# 	@cd app && \
# 	$(PYTHON) -m files_output.multi_requests_file

w_waste:
	@mkdir -p waste
	@mkdir -p waste/metadata
	@mkdir -p waste/queries	
	@mkdir -p waste/output


# GET /queries - Listar todas las queries
api_list: w_waste
	@curl -X GET "http://localhost:8050/queries" \
      -H "accept: application/json" | jq . > waste/queries_list.json

# POST /query - Ejecutar una query CON PARÁMETROS
api_query: w_waste
	@curl -X POST "http://localhost:8050/query" \
      -H "Content-Type: application/json" \
      -d '{"src": "$(SRC)", "dst": "$(DST)"}' | jq . > waste/queries/query_$(SRC)_$(DST)_response.jsons

api_query-d: 
	@echo "🔍 Ejecutando query con parámetros por defecto..."
	@make api_query SRC="999999" DST="999999"

# GET /query/{query_id} - Obtener metadata de una query
api_get: w_waste
	@curl -X GET "http://localhost:8050/query/$(QUERY_ID)" \
      -H "accept: application/json" | jq . > waste/metadata/query_$(QUERY_ID)_metadata.json 

# GET /query/{query_id}/data - Obtener datos paginados
api_data: w_waste
	@curl -X GET "http://localhost:8050/query/$(QUERY_ID)/data?offset=$(OFFSET)&limit=$(LIMIT)" \
      -H "accept: application/json" | jq . > waste/queries/query_$(QUERY_ID)_data_offset$(OFFSET)_limit$(LIMIT).json·


QUERY_ID-d:= "762592333e1d"
api_get-d:
	@echo "🔍 Obteniendo metadata de query con ID por defecto..."
	@make api_get QUERY_ID="$(QUERY_ID-d)"


# GET /events - Obtener diccionario de eventos
api_events: w_waste
	@curl -X GET "http://localhost:8050/events" \
      -H "accept: application/json" | jq . > waste/events_response.json


api_dict: 
	@curl -X GET "http://localhost:8050/componentDict" \
	  -H "accept: application/json" | jq . > waste/component_dictionary.json
api_dict-compact: 
	@curl -X GET "http://localhost:8050/componentDictCompact" \
	  -H "accept: application/json" | jq . > waste/component_dictionary_compact.json


######################################################################################
#####   PYTHON   ######
######################################################################################
.PHONY: ctrl_python
ctrl_python:
	@echo "🐍 Iniciando intérprete de Python en el entorno virtual..."
	@cd app && \
	$(PYTHON) -m pip freeze > requirements.txt
# 	$(PYTHON) -m pip install requests

######################################################################################
#####   OTROS   
######################################################################################
.PHONY: make_tar_datasets extract_tar_datasets cat_all_py tree clean clean_processed clean_queries
make_tar_datasets:
	@echo "📦 Creando archivo comprimido de Datasets..."
	@tar -czvf Datasets.tar.gz Datasets/

extract_tar_datasets:
	@echo "📂 Extrayendo Datasets.tar.gz..."
	@tar -xzvf Datasets.tar.gz
	@echo "✅ Datasets extraídos correctamente"

cat_all_py:
	@echo "📄 Concatenando todos los archivos .py..."
	@find app -name "*.py" -type f | sort | while read file; do \
        echo "\n\n================================"; \
        echo "FILE: $$file"; \
        echo "================================\n"; \
        cat "$$file"; \
	done > app_content.txt
	@echo "✅ Contenido guardado en app_content.txt"

tree: 
	@cd app && \
	tree . > a && \
	code a


clean_queries:
	@echo "🧹 Limpiando archivos de queries..."
	@rm -rf files_output/queries

clean_processed:
	@echo "🧹 Limpiando archivos procesados..."
	@rm -rf epoch_processed

clean: clean_queries clean_processed
	@echo "🧹 Limpieza completa de archivos de queries y procesados."
