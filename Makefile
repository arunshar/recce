.PHONY: install backend frontend dev build test docker-build docker-run up deploy clean

install:
	cd backend && python3 -m venv .venv && . .venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt
	cd frontend && npm install

backend:
	cd backend && . .venv/bin/activate && uvicorn app.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

dev:
	@echo "Run the backend and frontend in two terminals:"
	@echo "  make backend   # FastAPI on http://localhost:8000"
	@echo "  make frontend  # Vite on http://localhost:5173"

build:
	cd frontend && npm run build
	rm -rf backend/app/static && mkdir -p backend/app/static
	cp -r frontend/dist/. backend/app/static/

test:
	cd backend && . .venv/bin/activate && pip install -q -r requirements-dev.txt && python -m pytest -q

docker-build:
	docker build -t recce:latest .

docker-run: docker-build
	docker run --rm -p 8000:8080 -e GEMINI_API_KEY -e GOOGLE_MAPS_API_KEY recce:latest

up:
	docker compose up --build

deploy:
	bash scripts/deploy_cloud_run.sh

clean:
	rm -rf backend/.venv frontend/node_modules frontend/dist
	rm -rf backend/app/static && mkdir -p backend/app/static && touch backend/app/static/.gitkeep
