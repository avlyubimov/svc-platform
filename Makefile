.PHONY: check validate-pb100 validate-config firmware-test clean

check: validate-pb100 validate-config firmware-test

validate-pb100:
	python3 tools/validate_pb100.py

validate-config:
	python3 tools/validate_config.py

firmware-test:
	$(MAKE) -C firmware test

clean:
	$(MAKE) -C firmware clean
