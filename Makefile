.PHONY: install backend frontend dev build test test-unit test-integration test-e2e test-smoke test-contract test-regression test-performance test-security test-k8s test-frontend test-api-smoke docker-build docker-run up deploy k8s-smoke clean

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

test-unit:
	cd backend && . .venv/bin/activate && python -m pytest -q -m unit

test-integration:
	cd backend && . .venv/bin/activate && python -m pytest -q -m integration

test-e2e:
	cd backend && . .venv/bin/activate && python -m pytest -q -m e2e

test-smoke:
	cd backend && . .venv/bin/activate && python -m pytest -q -m smoke

test-contract:
	cd backend && . .venv/bin/activate && python -m pytest -q -m contract

test-regression:
	cd backend && . .venv/bin/activate && python -m pytest -q -m regression

test-performance:
	cd backend && . .venv/bin/activate && python -m pytest -q -m performance

test-security:
	cd backend && . .venv/bin/activate && python -m pytest -q -m security

test-k8s:
	cd backend && . .venv/bin/activate && python -m pytest -q -m k8s

test-frontend:
	cd frontend && npm run build && npm run smoke && npm run lint

test-api-smoke:
	python3 scripts/smoke_api.py --base-url $${RECCE_SMOKE_URL:-http://127.0.0.1:8000}

docker-build:
	docker build -t recce:latest .

docker-run: docker-build
	docker run --rm -p 8000:8080 -e GEMINI_API_KEY -e GOOGLE_MAPS_API_KEY recce:latest

up:
	docker compose up --build

deploy:
	bash scripts/deploy_cloud_run.sh

k8s-smoke:
	scripts/k8s_smoke.sh

clean:
	rm -rf backend/.venv frontend/node_modules frontend/dist
	rm -rf backend/app/static && mkdir -p backend/app/static && touch backend/app/static/.gitkeep
