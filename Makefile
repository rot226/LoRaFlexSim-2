.PHONY: validate validate-language validate-docs-consistency static-legacy-identifiers

# Temporary migration mode: keep report-only to avoid permanently blocking CI.
# Switch to blocking mode after cleanup by overriding with:
#   make validate-language VALIDATE_LANGUAGE_ARGS=
VALIDATE_LANGUAGE_ARGS ?= --report-only

static-legacy-identifiers:
	pytest tests/test_legacy_identifiers_absent.py

validate-docs-consistency:
	python scripts/check_docs_consistency.py

validate-language:
	python scripts/check_english_surface.py $(VALIDATE_LANGUAGE_ARGS)

validate: validate-language validate-docs-consistency static-legacy-identifiers
	pytest -k "channel"
	pytest -k "omnet_phy or rx_chain or overlap_snir or flora_capture or startup_currents or pa_ramp"
	pytest -k "gateway or collision_capture or compare_flora"
	pytest -k "network_server or no_random_drop or run_simulate or class_bc"
	pytest -k "run_simulate or rest_api_gap or dashboard"
	pytest -k "lorawan or class_a or rx_windows or adr or flora_energy"
	pytest -k "mobility"
	pytest -k "rest_api or web_api"
	pytest -k "plot_modules_source_contract or run_all_contract_guards or run_all_relaunch_missing_replications"
	python scripts/run_validation.py
