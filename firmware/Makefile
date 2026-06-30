CC ?= gcc
CPPFLAGS ?= -Icore -Iservices
CFLAGS ?= -std=c11 -Wall -Wextra -Werror

BUILD_DIR := build
FIRMWARE_HEADERS := $(wildcard core/*.h services/*.h)
POWER_BUDGET_TEST := $(BUILD_DIR)/test_power_budget
OUTPUT_MANAGER_TEST := $(BUILD_DIR)/test_output_manager
BATTERY_SERVICE_TEST := $(BUILD_DIR)/test_battery_service
EVENT_BUS_TEST := $(BUILD_DIR)/test_event_bus
EVENT_DISPATCHER_TEST := $(BUILD_DIR)/test_event_dispatcher
CAN_SAFETY_TEST := $(BUILD_DIR)/test_can_safety
SYSTEM_SAFETY_TEST := $(BUILD_DIR)/test_system_safety
HOST_TESTS := \
	$(POWER_BUDGET_TEST) \
	$(OUTPUT_MANAGER_TEST) \
	$(BATTERY_SERVICE_TEST) \
	$(EVENT_BUS_TEST) \
	$(EVENT_DISPATCHER_TEST) \
	$(CAN_SAFETY_TEST) \
	$(SYSTEM_SAFETY_TEST)

.PHONY: test clean

test: $(HOST_TESTS)
	$(POWER_BUDGET_TEST)
	$(OUTPUT_MANAGER_TEST)
	$(BATTERY_SERVICE_TEST)
	$(EVENT_BUS_TEST)
	$(EVENT_DISPATCHER_TEST)
	$(CAN_SAFETY_TEST)
	$(SYSTEM_SAFETY_TEST)

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

$(POWER_BUDGET_TEST): core/svc_config_defaults.c services/power_budget.c tests/test_power_budget.c $(FIRMWARE_HEADERS) | $(BUILD_DIR)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(filter %.c,$^) -o $@

$(OUTPUT_MANAGER_TEST): core/svc_config_defaults.c services/power_budget.c services/output_manager.c tests/test_output_manager.c $(FIRMWARE_HEADERS) | $(BUILD_DIR)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(filter %.c,$^) -o $@

$(BATTERY_SERVICE_TEST): core/svc_config_defaults.c services/battery_service.c tests/test_battery_service.c $(FIRMWARE_HEADERS) | $(BUILD_DIR)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(filter %.c,$^) -o $@

$(EVENT_BUS_TEST): services/event_bus.c tests/test_event_bus.c $(FIRMWARE_HEADERS) | $(BUILD_DIR)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(filter %.c,$^) -o $@

$(EVENT_DISPATCHER_TEST): core/svc_config_defaults.c services/event_bus.c services/event_dispatcher.c services/power_budget.c services/output_manager.c tests/test_event_dispatcher.c $(FIRMWARE_HEADERS) | $(BUILD_DIR)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(filter %.c,$^) -o $@

$(CAN_SAFETY_TEST): services/can_safety.c tests/test_can_safety.c $(FIRMWARE_HEADERS) | $(BUILD_DIR)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(filter %.c,$^) -o $@

$(SYSTEM_SAFETY_TEST): core/svc_config_defaults.c services/battery_service.c services/event_bus.c services/power_budget.c services/output_manager.c services/system_safety.c tests/test_system_safety.c $(FIRMWARE_HEADERS) | $(BUILD_DIR)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(filter %.c,$^) -o $@

clean:
	rm -rf $(BUILD_DIR)
