.PHONY: check validate-pb100 validate-board-order validate-readiness-consistency validate-config firmware-test pb100-release-status pb100-release-gate board-order-status board-order-gate clean

check: validate-pb100 validate-board-order validate-readiness-consistency validate-config firmware-test

validate-pb100:
	python3 tools/validate_pb100.py

validate-board-order:
	python3 tools/validate_board_order.py

validate-readiness-consistency:
	python3 tools/validate_readiness_consistency.py

validate-config:
	python3 tools/validate_config.py

firmware-test:
	$(MAKE) -C firmware test

pb100-release-status:
	python3 tools/pb100_release_status.py

pb100-release-gate:
	python3 tools/pb100_release_status.py --fail-on-blocked

board-order-status:
	python3 tools/board_order_status.py

board-order-gate:
	python3 tools/board_order_status.py --fail-on-blocked

clean:
	$(MAKE) -C firmware clean
