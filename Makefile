.PHONY: help install dev-install test clean docker-build docker-up docker-down docker-logs backend-run frontend-run

help:
	@echo "Sarkari Path - Available Commands"
	@echo "=================================="
	@echo "make install        - Install all dependencies"
	@echo "make dev-install    - Install development dependencies"
	@echo "make test           - Run all tests"
	@echo "make clean          - Clean temporary files"
	@echo "make docker-build   - Build Docker images"
	@echo "make docker-up      - Start all containers"
	@echo "make docker-down    - Stop all containers"
	@echo "make docker-logs    - View container logs"
	@echo "make backend-run    - Run backend locally"
	@echo "make frontend-run   - Run frontend locally"

install:
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && pip install -r requirements.txt

dev-install:
	@echo "Installing development dependencies..."
	pip install pytest pytest-cov black flake8 pylint

test:
	@echo "Running backend tests..."
	cd backend && pytest tests/
	@echo "Running frontend tests..."
	cd frontend && pytest tests/

clean:
	@echo "Cleaning temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +

docker-build:
	@echo "Building Docker images..."
	docker-compose build

docker-up:
	@echo "Starting containers..."
	docker-compose up -d

docker-down:
	@echo "Stopping containers..."
	docker-compose down

docker-logs:
	docker-compose logs -f

backend-run:
	@echo "Starting backend server..."
	cd backend && python run.py

frontend-run:
	@echo "Starting frontend server..."
	cd frontend && python run.py
