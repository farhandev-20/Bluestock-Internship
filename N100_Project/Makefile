.PHONY: help install load ratios test report dashboard api clean checklist

help:
	@echo "N100 Financial Intelligence Platform - Makefile Commands"
	@echo "---------------------------------------------------------"
	@echo "make load       : Load all Excel files into nifty100.db (Day 05)"
	@echo "make ratios     : Generate and populate the financial_ratios table"
	@echo "make test       : Run all pytest tests and generate reports/pytest_report.html"
	@echo "make report     : Generate all company tearsheets, sector reports, and portfolio report"
	@echo "make dashboard  : Launch Streamlit Dashboard on localhost:8501"
	@echo "make api        : Launch FastAPI server on localhost:8000"
	@echo "make checklist  : Verify all 20 Acceptance Gates and generate acceptance_checklist.pdf"
	@echo "make clean      : Remove cache (.pyc) and test artifacts (DB remains untouched)"

install:
	pip install -r requirements.txt

load:
	python -m src.etl.pipeline

ratios:
	python -m src.kpi.calculator

test:
	pytest tests/ -v --html=reports/pytest_report.html --self-contained-html

report:
	python -m src.reports.tearsheet
	python -m src.reports.sector_report
	python -m src.reports.portfolio_summary

dashboard:
	streamlit run src/dashboard/app.py --server.port 8501

api:
	uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

checklist:
	python -m src.reports.acceptance_checklist

clean:
	python -c "import shutil, glob, os; [shutil.rmtree(p, ignore_errors=True) for p in glob.glob('**/__pycache__', recursive=True) + ['.pytest_cache', '.ruff_cache']]"
