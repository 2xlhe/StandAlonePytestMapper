tests=docs/versioning*
config_value=params/br-se1.yaml
init_time=$(date +"%Y%m%dT%H%M%S")

pytest_log_file=local-pytest-output.$(init_time).log

# Execute uv 
uv run pytest $(tests) --config $(config_value) -l -n auto -vv --tb=line --durations=0 | tee $(pytest_log_file)

# Extracting data from the pytest log and adding to parquets
uv run logExtractor.py

# Generating PDF
uv run relatory.py
