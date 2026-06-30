.PHONY: check validate-pb100 firmware-test clean

check: validate-pb100 firmware-test

validate-pb100:
	python3 tools/validate_pb100.py

firmware-test:
	$(MAKE) -C firmware test

clean:
	$(MAKE) -C firmware clean
