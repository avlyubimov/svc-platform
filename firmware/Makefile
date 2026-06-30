CC ?= gcc
CFLAGS ?= -std=c11 -Wall -Wextra -Werror

BUILD_DIR := build
POWER_BUDGET_TEST := $(BUILD_DIR)/test_power_budget
OUTPUT_MANAGER_TEST := $(BUILD_DIR)/test_output_manager
BATTERY_SERVICE_TEST := $(BUILD_DIR)/test_battery_service

.PHONY: test clean

test: $(POWER_BUDGET_TEST) $(OUTPUT_MANAGER_TEST) $(BATTERY_SERVICE_TEST)
	$(POWER_BUDGET_TEST)
	$(OUTPUT_MANAGER_TEST)
	$(BATTERY_SERVICE_TEST)

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

$(POWER_BUDGET_TEST): core/svc_config_defaults.c services/power_budget.c tests/test_power_budget.c | $(BUILD_DIR)
	$(CC) $(CFLAGS) -Icore -Iservices $^ -o $@

$(OUTPUT_MANAGER_TEST): core/svc_config_defaults.c services/power_budget.c services/output_manager.c tests/test_output_manager.c | $(BUILD_DIR)
	$(CC) $(CFLAGS) -Icore -Iservices $^ -o $@

$(BATTERY_SERVICE_TEST): core/svc_config_defaults.c services/battery_service.c tests/test_battery_service.c | $(BUILD_DIR)
	$(CC) $(CFLAGS) -Icore -Iservices $^ -o $@

clean:
	rm -rf $(BUILD_DIR)
