run:
	docker compose up

run-prod:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.ics-is up

down-prod:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml down


# Push all docker images to 'scm.cms.hu-berlin.de:4567/iqb-lab/ics'
push-iqb-registry:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.ics-is build
	docker login scm.cms.hu-berlin.de:4567
	docker push scm.cms.hu-berlin.de:4567/iqb-lab/ics/ics-is-backend:$(TAG)
	docker push scm.cms.hu-berlin.de:4567/iqb-lab/ics/ics-is-worker:$(TAG)
	docker logout
