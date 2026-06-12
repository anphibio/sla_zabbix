COMPOSE ?= docker compose
BACKEND_COMPOSE ?= -f docker-compose.backend.yml
FRONTEND_COMPOSE ?= -f docker-compose.frontend.yml
WORKER_COMPOSE ?= -f docker-compose.worker.yml
DB_COMPOSE ?= -f docker-compose.db.yml
COMPOSE_FILES ?= $(DB_COMPOSE) $(BACKEND_COMPOSE) $(FRONTEND_COMPOSE) $(WORKER_COMPOSE)

.PHONY: help up down restart build rebuild logs ps up-backend up-frontend up-worker up-db down-backend down-frontend down-worker down-db backend-logs frontend-logs worker-logs db-logs backend-shell frontend-shell worker-shell db-shell clean

help:
	@echo "Comandos DEV disponíveis:"
	@echo "  make up             - sobe o ambiente local"
	@echo "  make down           - derruba o ambiente local"
	@echo "  make restart        - reinicia os serviços"
	@echo "  make build          - builda as imagens locais"
	@echo "  make rebuild        - recria o ambiente do zero"
	@echo "  make logs           - acompanha logs de todos os serviços"
	@echo "  make ps             - lista status dos containers"
	@echo "  make up-backend     - sobe apenas o backend"
	@echo "  make up-frontend    - sobe apenas o frontend"
	@echo "  make up-worker      - sobe apenas o worker"
	@echo "  make up-db          - sobe apenas o banco"
	@echo "  make down-backend   - derruba apenas o backend"
	@echo "  make down-frontend  - derruba apenas o frontend"
	@echo "  make down-worker    - derruba apenas o worker"
	@echo "  make down-db        - derruba apenas o banco"
	@echo "  make backend-logs   - acompanha logs do backend"
	@echo "  make frontend-logs  - acompanha logs do frontend"
	@echo "  make worker-logs    - acompanha logs do worker"
	@echo "  make db-logs        - acompanha logs do banco"
	@echo "  make backend-shell  - abre shell no backend"
	@echo "  make frontend-shell - abre shell no frontend"
	@echo "  make worker-shell   - abre shell no worker"
	@echo "  make db-shell       - abre shell no banco"
	@echo "  make clean          - remove containers, volumes órfãos e imagens locais não usadas"

up:
	$(COMPOSE) $(COMPOSE_FILES) up -d

down:
	$(COMPOSE) $(COMPOSE_FILES) down

restart:
	$(COMPOSE) $(COMPOSE_FILES) restart

build:
	$(COMPOSE) $(COMPOSE_FILES) build

rebuild:
	$(COMPOSE) $(COMPOSE_FILES) down --remove-orphans
	$(COMPOSE) $(COMPOSE_FILES) up -d --build

logs:
	$(COMPOSE) $(COMPOSE_FILES) logs -f --tail=200

ps:
	$(COMPOSE) $(COMPOSE_FILES) ps

up-backend:
	$(COMPOSE) $(BACKEND_COMPOSE) up -d

up-frontend:
	$(COMPOSE) $(FRONTEND_COMPOSE) up -d

up-worker:
	$(COMPOSE) $(WORKER_COMPOSE) up -d

up-db:
	$(COMPOSE) $(DB_COMPOSE) up -d

down-backend:
	$(COMPOSE) $(BACKEND_COMPOSE) down

down-frontend:
	$(COMPOSE) $(FRONTEND_COMPOSE) down

down-worker:
	$(COMPOSE) $(WORKER_COMPOSE) down

down-db:
	$(COMPOSE) $(DB_COMPOSE) down

backend-logs:
	$(COMPOSE) $(BACKEND_COMPOSE) logs -f --tail=200 backend

frontend-logs:
	$(COMPOSE) $(FRONTEND_COMPOSE) logs -f --tail=200 frontend

worker-logs:
	$(COMPOSE) $(WORKER_COMPOSE) logs -f --tail=200 worker

db-logs:
	$(COMPOSE) $(DB_COMPOSE) logs -f --tail=200 db

backend-shell:
	$(COMPOSE) $(BACKEND_COMPOSE) exec backend sh

frontend-shell:
	$(COMPOSE) $(FRONTEND_COMPOSE) exec frontend sh

worker-shell:
	$(COMPOSE) $(WORKER_COMPOSE) exec worker sh

db-shell:
	$(COMPOSE) $(DB_COMPOSE) exec db sh

clean:
	$(COMPOSE) $(COMPOSE_FILES) down -v --remove-orphans --rmi local
