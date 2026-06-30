CC ?= gcc
CFLAGS ?= -std=c11 -Wall -Wextra -Werror

BUILD_DIR := build
POWER_BUDGET_TEST := $(BUILD_DIR)/test_power_budget
OUTPUT_MANAGER_TEST := $(BUILD_DIR)/test_output_manager
BATTERY_SERVICE_TEST := $(BUILD_DIR)/test_battery_service
EVENT_BUS_TEST := $(BUILD_DIR)/test_event_bus
CAN_SAFETY_TEST := $(BUILD_DIR)/test_can_safety
SYSTEM_SAFETY_TEST := $(BUILD_DIR)/test_system_safety

.PHONY: test clean

test: $(POWER_BUDGET_TEST) $(OUTPUT_MANAGER_TEST) $(BATTERY_SERVICE_TEST) $(EVENT_BUS_TEST) $(CAN_SAFETY_TEST) $(SYSTEM_SAFETY_TEST)
	$(POWER_BUDGET_TEST)
	$(OUTPUT_MANAGER_TEST)
	$(BATTERY_SERVICE_TEST)
	$(EVENT_BUS_TEST)
	$(CAN_SAFETY_TEST)
	$(SYSTEM_SAFETY_TEST)

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

$(POWER_BUDGET_TEST): core/svc_config_defaults.c services/power_budget.c tests/test_power_budget.c | $(BUILD_DIR)
	$(CC) $(CFLAGS) -Icore -Iservices $^ -o $@

$(OUTPUT_MANAGER_TEST): core/svc_config_defaults.c services/power_budget.c services/output_manager.c tests/test_output_manager.c | $(BUILD_DIR)
	$(CC) $(CFLAGS) -Icore -Iservices $^ -o $@

$(BATTERY_SERVICE_TEST): core/svc_config_defaults.c services/battery_service.c tests/test_battery_service.c | $(BUILD_DIR)
	$(CC) $(CFLAGS) -Icore -Iservices $^ -o $@

$(EVENT_BUS_TEST): services/event_bus.c tests/test_event_bus.c | $(BUILD_DIR)
	$(CC) $(CFLAGS) -Icore -Iservices $^ -o $@

$(CAN_SAFETY_TEST): services/can_safety.c tests/test_can_safety.c | $(BUILD_DIR)
	$(CC) $(CFLAGS) -Icore -Iservices $^ -o $@

$(SYSTEM_SAFETY_TEST): core/svc_config_defaults.c services/battery_service.c services/event_bus.c services/power_budget.c services/output_manager.c services/system_safety.c tests/test_system_safety.c | $(BUILD_DIR)
	$(CC) $(CFLAGS) -Icore -Iservices $^ -o $@

clean:
	rm -rf $(BUILD_DIR)
