run-local:
	docker compose up
	source venv/bin/activate
	uvicorn main:app --port 9999 --reload --app-dir src
