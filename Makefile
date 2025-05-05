run:
	docker compose up

run-prod:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.ics-is up

down-prod:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml down

# Push all docker images to 'scm.cms.hu-berlin.de:4567/iqb/studio-lite'
push-iqb-registry:
	docker compose build
	docker login scm.cms.hu-berlin.de:4567
	docker push scm.cms.hu-berlin.de:4567/iqb/studio-lite/iqbberlin/studio-lite-db:$(TAG)
	docker push scm.cms.hu-berlin.de:4567/iqb/studio-lite/iqbberlin/studio-lite-liquibase:$(TAG)
	docker push scm.cms.hu-berlin.de:4567/iqb/studio-lite/iqbberlin/studio-lite-backend:$(TAG)
	docker push scm.cms.hu-berlin.de:4567/iqb/studio-lite/iqbberlin/studio-lite-frontend:$(TAG)
	docker logout
