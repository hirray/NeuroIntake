.PHONY: setup dev test pdf-demo clean

setup:
	python -m pip install -r requirements.txt
	python backend/app/report/fonts/download_fonts.py
	cd frontend && npm install

dev:
	python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8005

test:
	pytest tests/ -v

pdf-demo:
	python -m tests.generate_demo_pdfs
