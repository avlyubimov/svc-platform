CC ?= gcc
CPPFLAGS ?= -Icore -Iservices
CFLAGS ?= -std=c11 -Wall -Wextra -Werror

BUILD_DIR := build
FIRMWARE_HEADERS := $(wildcard core/*.h services/*.h)
CONFIG_VALIDATOR_TEST := $(BUILD_DIR)/test_config_validator
CONFIG_ACCEPTANCE_TEST := $(BUILD_DIR)/test_config_acceptance
HARDWARE_CAPABILITY_TEST := $(BUILD_DIR)/test_hardware_capability
POWER_BUDGET_TEST := $(BUILD_DIR)/test_power_budget
OUTPUT_MANAGER_TEST := $(BUILD_DIR)/test_output_manager
BATTERY_SERVICE_TEST := $(BUILD_DIR)/test_battery_service
EVENT_BUS_TEST := $(BUILD_DIR)/test_event_bus
EVENT_DISPATCHER_TEST := $(BUILD_DIR)/test_event_dispatcher
EVENT_LOG_TEST := $(BUILD_DIR)/test_event_log
CAN_SAFETY_TEST := $(BUILD_DIR)/test_can_safety
SYSTEM_SAFETY_TEST := $(BUILD_DIR)/test_system_safety
ROLE_RESOLVER_TEST := $(BUILD_DIR)/test_role_resolver
RULE_CONDITION_TEST := $(BUILD_DIR)/test_rule_condition
RULE_ENGINE_TEST := $(BUILD_DIR)/test_rule_engine
RULE_TEXT_TEST := $(BUILD_DIR)/test_rule_text
RUNTIME_BOOT_TEST := $(BUILD_DIR)/test_runtime_boot
TELEMETRY_TEST := $(BUILD_DIR)/test_telemetry
THERMAL_SERVICE_TEST := $(BUILD_DIR)/test_thermal_service
CONFIG_VALIDATOR_SRCS := \
	core/svc_config_defaults.c \
	services/battery_service.c \
	services/config_validator.c \
	services/event_bus.c \
	services/power_budget.c \
	services/output_manager.c \
	services/system_safety.c \
	services/telemetry.c \
	services/thermal_service.c \
	tests/test_config_validator.c
CONFIG_ACCEPTANCE_SRCS := \
	core/svc_config_defaults.c \
	services/battery_service.c \
	services/config_acceptance.c \
	services/config_validator.c \
	services/hardware_capability.c \
	services/pb100_capability.c \
	services/power_budget.c \
	services/telemetry.c \
	services/thermal_service.c \
	tests/test_config_acceptance.c
HARDWARE_CAPABILITY_SRCS := \
	core/svc_config_defaults.c \
	services/hardware_capability.c \
	services/pb100_capability.c \
	tests/test_hardware_capability.c
POWER_BUDGET_SRCS := \
	core/svc_config_defaults.c \
	services/power_budget.c \
	tests/test_power_budget.c
OUTPUT_MANAGER_SRCS := \
	core/svc_config_defaults.c \
	services/battery_service.c \
	services/config_validator.c \
	services/power_budget.c \
	services/output_manager.c \
	services/telemetry.c \
	services/thermal_service.c \
	tests/test_output_manager.c
BATTERY_SERVICE_SRCS := \
	core/svc_config_defaults.c \
	services/battery_service.c \
	tests/test_battery_service.c
EVENT_BUS_SRCS := \
	services/event_bus.c \
	tests/test_event_bus.c
EVENT_DISPATCHER_SRCS := \
	core/svc_config_defaults.c \
	services/battery_service.c \
	services/config_validator.c \
	services/event_bus.c \
	services/event_dispatcher.c \
	services/power_budget.c \
	services/output_manager.c \
	services/telemetry.c \
	services/thermal_service.c \
	tests/test_event_dispatcher.c
EVENT_LOG_SRCS := \
	services/event_log.c \
	tests/test_event_log.c
CAN_SAFETY_SRCS := \
	services/can_safety.c \
	tests/test_can_safety.c
SYSTEM_SAFETY_SRCS := \
	core/svc_config_defaults.c \
	services/battery_service.c \
	services/config_validator.c \
	services/event_bus.c \
	services/power_budget.c \
	services/output_manager.c \
	services/system_safety.c \
	services/telemetry.c \
	services/thermal_service.c \
	tests/test_system_safety.c
ROLE_RESOLVER_SRCS := \
	core/svc_config_defaults.c \
	services/battery_service.c \
	services/config_validator.c \
	services/power_budget.c \
	services/role_resolver.c \
	services/telemetry.c \
	services/thermal_service.c \
	tests/test_role_resolver.c
RULE_CONDITION_SRCS := \
	services/rule_condition.c \
	tests/test_rule_condition.c
RULE_ENGINE_SRCS := \
	core/svc_config_defaults.c \
	services/battery_service.c \
	services/config_validator.c \
	services/output_manager.c \
	services/power_budget.c \
	services/rule_condition.c \
	services/role_resolver.c \
	services/rule_engine.c \
	services/telemetry.c \
	services/thermal_service.c \
	tests/test_rule_engine.c
RULE_TEXT_SRCS := \
	core/svc_config_defaults.c \
	services/battery_service.c \
	services/config_validator.c \
	services/output_manager.c \
	services/power_budget.c \
	services/rule_condition.c \
	services/role_resolver.c \
	services/rule_engine.c \
	services/rule_text.c \
	services/telemetry.c \
	services/thermal_service.c \
	tests/test_rule_text.c
RUNTIME_BOOT_SRCS := \
	core/svc_config_defaults.c \
	services/battery_service.c \
	services/config_acceptance.c \
	services/config_validator.c \
	services/event_bus.c \
	services/hardware_capability.c \
	services/output_manager.c \
	services/pb100_capability.c \
	services/power_budget.c \
	services/runtime_boot.c \
	services/system_safety.c \
	services/telemetry.c \
	services/thermal_service.c \
	tests/test_runtime_boot.c
TELEMETRY_SRCS := \
	services/telemetry.c \
	tests/test_telemetry.c
THERMAL_SERVICE_SRCS := \
	core/svc_config_defaults.c \
	services/telemetry.c \
	services/thermal_service.c \
	tests/test_thermal_service.c
HOST_TESTS := \
	$(CONFIG_VALIDATOR_TEST) \
	$(CONFIG_ACCEPTANCE_TEST) \
	$(HARDWARE_CAPABILITY_TEST) \
	$(POWER_BUDGET_TEST) \
	$(OUTPUT_MANAGER_TEST) \
	$(BATTERY_SERVICE_TEST) \
	$(EVENT_BUS_TEST) \
	$(EVENT_DISPATCHER_TEST) \
	$(EVENT_LOG_TEST) \
	$(CAN_SAFETY_TEST) \
	$(SYSTEM_SAFETY_TEST) \
	$(ROLE_RESOLVER_TEST) \
	$(RULE_CONDITION_TEST) \
	$(RULE_ENGINE_TEST) \
	$(RULE_TEXT_TEST) \
	$(RUNTIME_BOOT_TEST) \
	$(TELEMETRY_TEST) \
	$(THERMAL_SERVICE_TEST)

.PHONY: test clean

test: $(HOST_TESTS)
	$(CONFIG_VALIDATOR_TEST)
	$(CONFIG_ACCEPTANCE_TEST)
	$(HARDWARE_CAPABILITY_TEST)
	$(POWER_BUDGET_TEST)
	$(OUTPUT_MANAGER_TEST)
	$(BATTERY_SERVICE_TEST)
	$(EVENT_BUS_TEST)
	$(EVENT_DISPATCHER_TEST)
	$(EVENT_LOG_TEST)
	$(CAN_SAFETY_TEST)
	$(SYSTEM_SAFETY_TEST)
	$(ROLE_RESOLVER_TEST)
	$(RULE_CONDITION_TEST)
	$(RULE_ENGINE_TEST)
	$(RULE_TEXT_TEST)
	$(RUNTIME_BOOT_TEST)
	$(TELEMETRY_TEST)
	$(THERMAL_SERVICE_TEST)

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

$(CONFIG_VALIDATOR_TEST): $(CONFIG_VALIDATOR_SRCS) $(FIRMWARE_HEADERS) | $(BUILD_DIR)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(filter %.c,$^) -o $@

$(CONFIG_ACCEPTANCE_TEST): $(CONFIG_ACCEPTANCE_SRCS) $(FIRMWARE_HEADERS) | $(BUILD_DIR)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(filter %.c,$^) -o $@

$(HARDWARE_CAPABILITY_TEST): $(HARDWARE_CAPABILITY_SRCS) $(FIRMWARE_HEADERS) | $(BUILD_DIR)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(filter %.c,$^) -o $@

$(POWER_BUDGET_TEST): $(POWER_BUDGET_SRCS) $(FIRMWARE_HEADERS) | $(BUILD_DIR)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(filter %.c,$^) -o $@

$(OUTPUT_MANAGER_TEST): $(OUTPUT_MANAGER_SRCS) $(FIRMWARE_HEADERS) | $(BUILD_DIR)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(filter %.c,$^) -o $@

$(BATTERY_SERVICE_TEST): $(BATTERY_SERVICE_SRCS) $(FIRMWARE_HEADERS) | $(BUILD_DIR)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(filter %.c,$^) -o $@

$(EVENT_BUS_TEST): $(EVENT_BUS_SRCS) $(FIRMWARE_HEADERS) | $(BUILD_DIR)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(filter %.c,$^) -o $@

$(EVENT_DISPATCHER_TEST): $(EVENT_DISPATCHER_SRCS) $(FIRMWARE_HEADERS) | $(BUILD_DIR)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(filter %.c,$^) -o $@

$(EVENT_LOG_TEST): $(EVENT_LOG_SRCS) $(FIRMWARE_HEADERS) | $(BUILD_DIR)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(filter %.c,$^) -o $@

$(CAN_SAFETY_TEST): $(CAN_SAFETY_SRCS) $(FIRMWARE_HEADERS) | $(BUILD_DIR)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(filter %.c,$^) -o $@

$(SYSTEM_SAFETY_TEST): $(SYSTEM_SAFETY_SRCS) $(FIRMWARE_HEADERS) | $(BUILD_DIR)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(filter %.c,$^) -o $@

$(ROLE_RESOLVER_TEST): $(ROLE_RESOLVER_SRCS) $(FIRMWARE_HEADERS) | $(BUILD_DIR)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(filter %.c,$^) -o $@

$(RULE_CONDITION_TEST): $(RULE_CONDITION_SRCS) $(FIRMWARE_HEADERS) | $(BUILD_DIR)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(filter %.c,$^) -o $@

$(RULE_ENGINE_TEST): $(RULE_ENGINE_SRCS) $(FIRMWARE_HEADERS) | $(BUILD_DIR)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(filter %.c,$^) -o $@

$(RULE_TEXT_TEST): $(RULE_TEXT_SRCS) $(FIRMWARE_HEADERS) | $(BUILD_DIR)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(filter %.c,$^) -o $@

$(RUNTIME_BOOT_TEST): $(RUNTIME_BOOT_SRCS) $(FIRMWARE_HEADERS) | $(BUILD_DIR)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(filter %.c,$^) -o $@

$(TELEMETRY_TEST): $(TELEMETRY_SRCS) $(FIRMWARE_HEADERS) | $(BUILD_DIR)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(filter %.c,$^) -o $@

$(THERMAL_SERVICE_TEST): $(THERMAL_SERVICE_SRCS) $(FIRMWARE_HEADERS) | $(BUILD_DIR)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(filter %.c,$^) -o $@

clean:
	rm -rf $(BUILD_DIR)
