COMPOSE := docker compose --env-file .env -f infra/docker-compose.yml

.PHONY: compose up up-core down down-volumes ps logs migrate-datalake smoke smoke-live

compose:
	@echo "Usage: make up | make up-core | make down | make logs"

up:
	$(COMPOSE) up -d --build postgres datalake market-live api-gateway mcp-stocklake mcp-market-live

up-core:
	$(COMPOSE) up -d --build postgres datalake market-live api-gateway

down:
	$(COMPOSE) down

down-volumes:
	$(COMPOSE) down -v

ps:
	$(COMPOSE) ps

logs:
	$(COMPOSE) logs -f --tail=200

migrate-datalake:
	$(COMPOSE) exec -T datalake alembic upgrade head

smoke:
	python scripts/smoke_gateway.py

smoke-live:
	python scripts/smoke_gateway.py --strict-live
