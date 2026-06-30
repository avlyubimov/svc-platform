CC ?= gcc
CFLAGS ?= -std=c11 -Wall -Wextra -Werror

BUILD_DIR := build
POWER_BUDGET_TEST := $(BUILD_DIR)/test_power_budget

.PHONY: test clean

test: $(POWER_BUDGET_TEST)
	$(POWER_BUDGET_TEST)

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

$(POWER_BUDGET_TEST): core/svc_config_defaults.c services/power_budget.c tests/test_power_budget.c | $(BUILD_DIR)
	$(CC) $(CFLAGS) -Icore -Iservices $^ -o $@

clean:
	rm -rf $(BUILD_DIR)
