.PHONY: help install keys demo live test clean

TARGET ?= example.com
XLSX   ?= output/$(TARGET)_comparison.xlsx

help:            ## show this help
	@grep -E '^[a-z-]+:.*?##' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?##"}{printf "  %-10s %s\n", $$1, $$2}'

install:         ## install dependencies
	python3 -m pip install -r requirements.txt

keys:            ## show which API keys the program can see
	python3 run_osint_compare.py --keys

demo:            ## validate the pipeline with captured fixtures (no keys)
	python3 run_osint_compare.py wikipedia.org --demo \
		--xlsx output/demo_wikipedia.xlsx --json output/demo_wikipedia.json

live:            ## real five-tool run (needs .env keys), TARGET=example.com
	python3 run_osint_compare.py $(TARGET) --xlsx $(XLSX) \
		--json output/$(TARGET)_comparison.json --quiet

test:            ## offline test suite
	python3 -m unittest discover tests -v

clean:           ## remove generated artefacts
	rm -rf output/*.xlsx output/*.json __pycache__ osint_compare/__pycache__ \
		osint_compare/tools/__pycache__ tests/__pycache__
