run:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up

up:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

down:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up

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

# Push all docker images to 'scm.cms.hu-berlin.de:4567/iqb-lab/ics'
include .env.ics-is
push-iqb-registry:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.ics-is build
	docker login scm.cms.hu-berlin.de:4567
	docker push $(REGISTRY_PATH)ics-is-backend:$(TAG)
	docker push $(REGISTRY_PATH)ics-is-worker:$(TAG)
	docker logout
