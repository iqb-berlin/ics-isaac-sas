run:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up

up:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

down:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml down

build:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml build $(SERVICE)

logs:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml logs -f $(SERVICE)

run-prod:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.ics-is up

up-prod:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.ics-is up -d

down-prod:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.ics-is down

logs-prod:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.ics-is logs

build-prod:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml build $(SERVICE)

push-iqb-registry:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.ics-is build
	docker login scm.cms.hu-berlin.de:4567
	source .env.ics-is && docker push $(REGISTRY_PATH)ics-is-backend:$(TAG)
	source .env.ics-is && docker push $(REGISTRY_PATH)ics-is-worker:$(TAG)
	docker logout
