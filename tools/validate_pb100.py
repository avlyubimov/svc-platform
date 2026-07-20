#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PB100_DIR = REPO_ROOT / "hardware" / "power-board" / "PB-100"
KICAD_DIR = PB100_DIR / "kicad"
PRODUCTION_DIR = REPO_ROOT / "production"
REQUIRED_KICAD_CLI_VERSION = "10.0.4"
MIN_KICAD_COMPONENTS = 20
MIN_KICAD_NETS = 20
DISALLOWED_LAYOUT_SUFFIXES = {
    ".kicad_pcb",
    ".drl",
    ".gbr",
    ".gbl",
    ".gbo",
    ".gbs",
    ".gko",
    ".gm1",
    ".gtl",
    ".gto",
    ".gts",
    ".kicad_pos",
    ".pos",
    ".xln",
    ".zip",
}
DISALLOWED_LAYOUT_NAME_FRAGMENTS = (
    "gerber",
    "drill",
    "pick-place",
    "pick_and_place",
    "pickplace",
    "placement",
)
MANUFACTURING_HINT_SUFFIXES = {".csv", ".rpt", ".txt", ".xlsx", ".zip"}
FORBIDDEN_ROLE_TOKENS = (
    "FOG",
    "SEAT",
    "USB",
    "CHIGEE",
    "DVR",
    "BRAKE",
    "CIGARETTE",
)
SYMBOL_MPN_COLUMNS = (
    "Symbol key",
    "Schematic block",
    "Function",
    "Critical",
    "Preferred MPN or class",
    "Preferred package",
    "Alternate 1",
    "Alternate 2",
    "KiCad symbol status",
    "Footprint status",
    "Assembly/sourcing status",
    "Freeze condition",
    "Primary source",
)
REQUIRED_SYMBOL_KEYS = {
    "HS_CTRL",
    "OUT_FET",
    "OUT2_ESCAPE_FET",
    "INPUT_IDEAL_DIODE",
    "INPUT_CONNECTOR",
    "INPUT_REVERSE_FET",
    "INPUT_TVS",
    "LOGIC_BUCK",
    "LOGIC_BUCK_INDUCTOR",
    "TOTAL_CURRENT_MONITOR",
    "TOTAL_CURRENT_SHUNT",
    "THERMAL_NTC",
    "B2B_CONNECTOR",
    "OUTPUT_CONNECTOR",
    "OUTPUT_FUSE_HOLDER",
    "MAIN_FUSE_HOLDER",
    "CAN1_TX_DISABLE",
}
INTERNAL_SYMBOL_TRACE_SOURCE_BY_KEY = {
    "LOGIC_BUCK_INDUCTOR": "hardware/power-board/PB-100/PB-100-logic-power-rail-trace.csv",
    "BOARD_ID_RESISTOR": "hardware/power-board/PB-100/PB-100-b2b-interface-trace.csv",
    "CAN1_TX_DISABLE": "hardware/power-board/PB-100/PB-100-can1-tx-disable-trace.csv",
}
SYMBOL_WORKLIST_COLUMNS = (
    "Symbol key",
    "Concrete symbol name",
    "Library",
    "Symbol source",
    "Pin evidence status",
    "Footprint dependency",
    "Instance refs",
    "Allowed action",
    "Blocked action",
    "Freeze close evidence",
)
SYMBOL_PIN_EVIDENCE_COLUMNS = (
    "Symbol name",
    "Pin number",
    "Pin name",
    "Source",
    "Source revision",
    "Package",
    "Notes",
)
PIN_MAP_EVIDENCE_SYMBOLS = {"PB100_JPB1_100PIN_PRELIM"}
INSTANCE_SYMBOL_MAP_COLUMNS = (
    "Ref",
    "Instance block",
    "Symbol key",
    "Concrete symbol name",
    "Symbol state",
    "Notes",
)
SHEET_REFERENCE_MAP_COLUMNS = (
    "Sheet file",
    "Ref",
    "Symbol key",
    "Capture status",
    "Notes",
)
KICAD_SHEET_MANIFEST_COLUMNS = (
    "Sheet file",
    "Sheet kind",
    "Purpose",
    "Primary artifacts",
    "Status",
    "Capture gate",
)
NET_DOMAIN_PLAN_COLUMNS = (
    "Net pattern",
    "Domain",
    "Primary sheet",
    "Direction",
    "Default state",
    "Safety rule",
)
BOM_SYMBOL_MAP_COLUMNS = (
    "Symbol key",
    "BOM file",
    "BOM item",
    "Qty basis",
    "Population",
    "Assembly owner",
    "Status",
    "Notes",
)
SCHEMATIC_READINESS_DASHBOARD_COLUMNS = (
    "Area",
    "Status",
    "Evidence",
    "Machine check",
    "Remaining close work",
)
SCHEMATIC_FREEZE_GAP_REGISTER_COLUMNS = (
    "Gate",
    "Status",
    "Close evidence required",
    "Primary gap artifact",
    "Validator coverage",
    "Next close action",
)
BOARD_RELEASE_BLOCKER_REGISTER_COLUMNS = (
    "Gate",
    "Blocker ID",
    "Status",
    "Blocking evidence",
    "Required close evidence",
    "External dependency",
    "Next engineering action",
    "Layout impact",
)
BOARD_PRINT_CLOSURE_MATRIX_COLUMNS = (
    "Gate",
    "Blocker ID",
    "Closeout artifact",
    "Current proof state",
    "Remaining evidence to close",
    "Required current-state evidence",
    "Board-print blocked action",
)
ENGINEERING_BLOCKER_CLOSEOUT = (
    "hardware/power-board/PB-100/PB-100-engineering-blocker-closeout.md"
)
SCHEMATIC_REVIEW_CLOSEOUT = (
    "hardware/power-board/PB-100/PB-100-schematic-review-closeout.md"
)
OUTPUT_CHANNEL_PIN_CONTRACT_COLUMNS = (
    "Output",
    "Controller ref",
    "Switch ref",
    "Fuse ref",
    "Connector ref",
    "Control net",
    "Fault net",
    "Current net",
    "Load net",
    "Fused net",
    "Default state",
    "Safety rule",
)
OUTPUT_CONTROLLER_PIN_TEMPLATE_COLUMNS = (
    "Pin number",
    "Pin name",
    "Signal role",
    "Net pattern",
    "Direction",
    "Default state",
    "Freeze dependency",
)
INPUT_PROTECTION_PIN_CONTRACT_COLUMNS = (
    "Ref",
    "Symbol key",
    "Concrete symbol name",
    "Interface point",
    "Planned net",
    "Direction",
    "Default state",
    "Freeze dependency",
)
LOGIC_POWER_DESIGN_COLUMNS = (
    "Item",
    "Ref or net",
    "Design state",
    "Value status",
    "Freeze dependency",
    "Notes",
)
OUTPUT_STAGE_DESIGN_VALUE_COLUMNS = (
    "Output class",
    "Applies to",
    "Design item",
    "Related net pattern",
    "Value status",
    "Candidate direction",
    "Freeze dependency",
    "Notes",
)
LOW_CURRENT_OUTPUT_BASELINE_TRACE_COLUMNS = (
    "Output",
    "Capability class",
    "Fuse target A",
    "Current limit A",
    "Switch architecture",
    "Role boundary",
    "Freeze dependency",
)
HIGH_MEDIUM_OUTPUT_BASELINE_TRACE_COLUMNS = (
    "Output group",
    "Outputs",
    "Capability class",
    "Fuse targets A",
    "Current limits A",
    "Switch architecture",
    "Telemetry path",
    "Freeze dependency",
)
OUTPUT_FREEZE_REVIEW_COLUMNS = (
    "Review item",
    "Required boundary",
    "Primary evidence",
    "Schematic freeze check",
    "Pass condition",
    "Blocked action",
)
OUTPUT_NET_EXPANSION_COLUMNS = (
    "Output",
    "Net pattern",
    "Expanded net",
    "Primary sheet",
    "Source artifact",
    "Default state",
    "Safety rule",
)
INPUT_POWER_DESIGN_VALUE_COLUMNS = (
    "Block",
    "Design item",
    "Related net",
    "Value status",
    "Candidate direction",
    "Freeze dependency",
    "Notes",
)
INPUT_REVERSE_PACKAGE_TRACE_COLUMNS = (
    "Trace item",
    "Primary evidence",
    "Preferred path",
    "Alternate path",
    "Safety boundary",
    "Freeze dependency",
)
INPUT_REVERSE_Q1_FREEZE_CHECKLIST_COLUMNS = (
    "Check ID",
    "Review item",
    "Required close evidence",
    "Primary artifacts",
    "Pass condition",
    "Blocked action",
)
INPUT_REVERSE_Q1_DERIVATION_PRECHECK_COLUMNS = (
    "Derivation ID",
    "Scope",
    "Formula or source basis",
    "Project input",
    "Required PB-100 close evidence",
    "Blocked action",
)
INPUT_REVERSE_Q1_CLOSEOUT_PRECHECK_COLUMNS = (
    "Precheck ID",
    "Scope",
    "Required evidence bridge",
    "Project input",
    "Required PB-100 close evidence",
    "Blocked action",
)
BOARD_CURRENT_BUDGET_TRACE_COLUMNS = (
    "Check",
    "Target",
    "Repository evidence",
    "Measured or enforced by",
    "Freeze state",
    "Remaining work",
)
BOARD_CURRENT_BUDGET_FREEZE_REVIEW_COLUMNS = (
    "Review item",
    "Required boundary",
    "Primary evidence",
    "Schematic freeze check",
    "Pass condition",
    "Blocked action",
)
BOARD_CURRENT_BUDGET_VALUE_FREEZE_CHECKLIST_COLUMNS = (
    "Check ID",
    "Review item",
    "Required close evidence",
    "Primary artifacts",
    "Pass condition",
    "Blocked action",
)
BOARD_CURRENT_BUDGET_VALUE_DERIVATION_PRECHECK_COLUMNS = (
    "Derivation ID",
    "Scope",
    "Formula or source basis",
    "Project input",
    "Required PB-100 close evidence",
    "Blocked action",
)
BOARD_CURRENT_BUDGET_CLOSEOUT_PRECHECK_COLUMNS = (
    "Precheck ID",
    "Scope",
    "Required evidence bridge",
    "Project input",
    "Required PB-100 close evidence",
    "Blocked action",
)
CURRENT_TELEMETRY_TRACE_COLUMNS = (
    "Measurement group",
    "Signals",
    "Range target A",
    "Primary hardware path",
    "Firmware safety use",
    "Freeze dependency",
)
CURRENT_TELEMETRY_FREEZE_REVIEW_COLUMNS = (
    "Review item",
    "Required boundary",
    "Primary evidence",
    "Schematic freeze check",
    "Pass condition",
    "Blocked action",
)
CURRENT_TELEMETRY_VALUE_FREEZE_CHECKLIST_COLUMNS = (
    "Check ID",
    "Review item",
    "Required close evidence",
    "Primary artifacts",
    "Pass condition",
    "Blocked action",
)
CURRENT_TELEMETRY_VALUE_DERIVATION_PRECHECK_COLUMNS = (
    "Derivation ID",
    "Scope",
    "Formula or source basis",
    "Project input",
    "Required PB-100 close evidence",
    "Blocked action",
)
CURRENT_TELEMETRY_CLOSEOUT_PRECHECK_COLUMNS = (
    "Precheck ID",
    "Scope",
    "Required evidence bridge",
    "Project input",
    "Required PB-100 close evidence",
    "Blocked action",
)
THERMAL_TELEMETRY_TRACE_COLUMNS = (
    "Thermal zone",
    "Signal",
    "Sensor candidate",
    "Telemetry path",
    "Default thresholds",
    "Configuration boundary",
    "Freeze dependency",
)
THERMAL_TELEMETRY_FREEZE_REVIEW_COLUMNS = (
    "Review item",
    "Required boundary",
    "Primary evidence",
    "Schematic freeze check",
    "Pass condition",
    "Blocked action",
)
THERMAL_TELEMETRY_VALUE_FREEZE_CHECKLIST_COLUMNS = (
    "Check ID",
    "Review item",
    "Required close evidence",
    "Primary artifacts",
    "Pass condition",
    "Blocked action",
)
THERMAL_TELEMETRY_VALUE_DERIVATION_PRECHECK_COLUMNS = (
    "Derivation ID",
    "Scope",
    "Formula or source basis",
    "Project input",
    "Required PB-100 close evidence",
    "Blocked action",
)
THERMAL_TELEMETRY_CLOSEOUT_PRECHECK_COLUMNS = (
    "Precheck ID",
    "Scope",
    "Required evidence bridge",
    "Project input",
    "Required PB-100 close evidence",
    "Blocked action",
)
FACTORY_ASSEMBLY_FREEZE_CHECKLIST_COLUMNS = (
    "Check ID",
    "Review item",
    "Required close evidence",
    "Primary artifacts",
    "Pass condition",
    "Blocked action",
)
FACTORY_ASSEMBLY_SOURCING_PRECHECK_COLUMNS = (
    "Precheck ID",
    "Scope",
    "Required evidence bridge",
    "Project input",
    "Required PB-100 close evidence",
    "Blocked action",
)
FACTORY_ASSEMBLY_CLOSEOUT_PRECHECK_COLUMNS = (
    "Precheck ID",
    "Scope",
    "Required evidence bridge",
    "Project input",
    "Required PB-100 close evidence",
    "Blocked action",
)
LOGIC_POWER_RAIL_TRACE_COLUMNS = (
    "Trace item",
    "Net or ref",
    "Planning baseline",
    "Safety boundary",
    "Freeze dependency",
)
B2B_INTERFACE_TRACE_COLUMNS = (
    "Trace item",
    "Signals",
    "Pin span",
    "LB-100 resource class",
    "Default state or safety boundary",
    "Freeze dependency",
)
B2B_RESOURCE_BINDING_COLUMNS = (
    "Binding item",
    "JPB1 pins",
    "Nets",
    "Requirement scope",
    "LB-100 resource class",
    "Direction",
    "STM32H5 planning note",
    "Freeze dependency",
)
B2B_LB100_PIN_AUDIT_COLUMNS = (
    "Audit ID",
    "Audit item",
    "JPB1 scope",
    "Required evidence",
    "Pass condition",
    "Blocked action",
)
B2B_INTERFACE_FREEZE_CHECKLIST_COLUMNS = (
    "Check ID",
    "Review item",
    "Required close evidence",
    "Primary artifacts",
    "Pass condition",
    "Blocked action",
)
B2B_INTERFACE_CLOSEOUT_PRECHECK_COLUMNS = (
    "Precheck ID",
    "Scope",
    "Required evidence bridge",
    "Project input",
    "Required PB-100 close evidence",
    "Blocked action",
)
TVS_LOAD_DUMP_MARGIN_TRACE_COLUMNS = (
    "Protected item",
    "Voltage class",
    "Active TVS branch",
    "Clamp or stress point",
    "Margin state",
    "Schematic freeze action",
)
TVS_OVERSHOOT_ESCAPE_CHECKLIST_COLUMNS = (
    "Check ID",
    "Review item",
    "Required close evidence",
    "Primary artifacts",
    "Pass condition",
    "Blocked action",
)
TVS_OVERSHOOT_VALIDATION_PRECHECK_COLUMNS = (
    "Validation ID",
    "Scope",
    "Required setup",
    "Primary artifacts",
    "Pass condition",
    "Blocked action",
)
TVS_OVERSHOOT_CLOSEOUT_PRECHECK_COLUMNS = (
    "Precheck ID",
    "Scope",
    "Required evidence bridge",
    "Project input",
    "Required PB-100 close evidence",
    "Blocked action",
)
LOGIC_POWER_DESIGN_VALUE_COLUMNS = (
    "Design item",
    "Related net",
    "Value status",
    "Candidate direction",
    "Freeze dependency",
    "Notes",
)
LOGIC_POWER_VALUE_FREEZE_CHECKLIST_COLUMNS = (
    "Check ID",
    "Review item",
    "Required close evidence",
    "Primary artifacts",
    "Pass condition",
    "Blocked action",
)
LOGIC_POWER_CLOSEOUT_PRECHECK_COLUMNS = (
    "Precheck ID",
    "Scope",
    "Required evidence bridge",
    "Project input",
    "Required PB-100 close evidence",
    "Blocked action",
)
LOGIC_POWER_VALUE_DERIVATION_PRECHECK_COLUMNS = (
    "Derivation ID",
    "Scope",
    "Formula or source basis",
    "Project input",
    "Required PB-100 close evidence",
    "Blocked action",
)
OUTPUT_STAGE_VALUE_FREEZE_CHECKLIST_COLUMNS = (
    "Check ID",
    "Output class",
    "Required close evidence",
    "Primary artifacts",
    "Pass condition",
    "Blocked action",
)
OUTPUT_STAGE_VALUE_DERIVATION_PRECHECK_COLUMNS = (
    "Derivation ID",
    "Scope",
    "Formula or source basis",
    "Project input",
    "Required PB-100 close evidence",
    "Blocked action",
)
OUTPUT_STAGE_CLOSEOUT_PRECHECK_COLUMNS = (
    "Precheck ID",
    "Scope",
    "Required evidence bridge",
    "Project input",
    "Required PB-100 close evidence",
    "Blocked action",
)
CAN1_DEFAULT_DISABLE_DERIVATION_PRECHECK_COLUMNS = (
    "Derivation ID",
    "Scope",
    "Formula or source basis",
    "Project input",
    "Required PB-100 close evidence",
    "Blocked action",
)
CAN1_DEFAULT_DISABLE_CLOSEOUT_PRECHECK_COLUMNS = (
    "Precheck ID",
    "Scope",
    "Required evidence bridge",
    "Project input",
    "Required PB-100 close evidence",
    "Blocked action",
)
CAN1_SAFETY_VERIFICATION_COLUMNS = (
    "Requirement",
    "Signal or artifact",
    "Rev.1 default",
    "Verification method",
    "Pass condition",
    "Blocked change",
)
CAN1_TX_DISABLE_TRACE_COLUMNS = (
    "Trace item",
    "Signal or artifact",
    "Rev.1 physical default",
    "Verification boundary",
    "Blocked change",
    "Freeze dependency",
)
CAN1_PRODUCTION_DNP_REVIEW_COLUMNS = (
    "Review item",
    "Signal or artifact",
    "Required default",
    "Primary evidence",
    "Verification method",
    "Pass condition",
    "Blocked action",
)
CAN1_RESET_BENCH_CHECKLIST_COLUMNS = (
    "Check ID",
    "Scenario",
    "Fixture state",
    "Required observation",
    "Primary evidence",
    "Pass condition",
    "Blocked release action",
)
CAN1_DEFAULT_DISABLE_FREEZE_CHECKLIST_COLUMNS = (
    "Check ID",
    "Review item",
    "Required close evidence",
    "Primary artifacts",
    "Pass condition",
    "Blocked action",
)
GARAGE_CONNECTOR_FUSE_PLAN_COLUMNS = (
    "Interface",
    "Target current or fuse",
    "Connector or fuse family",
    "Status",
    "Notes",
)
GARAGE_INSTALL_FREEZE_CHECKLIST_COLUMNS = (
    "Check ID",
    "Review item",
    "Required close evidence",
    "Primary artifacts",
    "Pass condition",
    "Blocked action",
)
GARAGE_INSTALL_SOURCING_PRECHECK_COLUMNS = (
    "Precheck ID",
    "Scope",
    "Required evidence bridge",
    "Project input",
    "Required PB-100 close evidence",
    "Blocked action",
)
GARAGE_INSTALL_CLOSEOUT_PRECHECK_COLUMNS = (
    "Precheck ID",
    "Scope",
    "Required evidence bridge",
    "Project input",
    "Required PB-100 close evidence",
    "Blocked action",
)
ASSEMBLY_SOURCING_RECHECK_COLUMNS = (
    "Symbol key",
    "Assembly owner",
    "Preferred MPN or class",
    "Recheck status",
    "Recheck source",
    "Alternate coverage",
    "Factory action",
    "Garage action",
    "Freeze dependency",
)
ASSEMBLY_READINESS_TRACE_COLUMNS = (
    "Assembly owner",
    "Scope",
    "Required symbol keys",
    "Current state",
    "Freeze action",
    "Blocked action",
)
SOURCING_EVIDENCE_COLUMNS = (
    "Symbol key",
    "Evidence date",
    "Evidence source type",
    "Primary evidence URL",
    "Secondary evidence URL",
    "Evidence result",
    "Open sourcing blocker",
)
VALIDATION_TRACEABILITY_COLUMNS = (
    "Test ID",
    "Freeze gate",
    "Validation phase",
    "Primary artifact",
    "Method",
    "Pass condition",
    "Safety constraint",
)
POST_PROTOTYPE_VALIDATION_GATE_COLUMNS = (
    "Bench ID",
    "Area",
    "Requires assembled board",
    "Pre-layout artifact",
    "Post-prototype evidence",
    "Blocks until complete",
    "Status",
)
TEST_POINT_PLAN_COLUMNS = (
    "Test point ref",
    "Net",
    "Sheet",
    "Signal class",
    "Requirement",
    "Population",
    "Access intent",
    "Validation target",
    "Placement status",
)
FAULT_RESPONSE_MATRIX_COLUMNS = (
    "Fault ID",
    "Area",
    "Fault condition",
    "Detection source",
    "Hardware default",
    "Firmware response",
    "User-visible state",
    "Validation artifact",
    "Safety constraint",
)
SCHEMATIC_CAPTURE_WORK_QUEUE_COLUMNS = (
    "Work item",
    "Sheet file",
    "Capture scope",
    "Required refs",
    "Primary source artifacts",
    "Capture status",
    "Blocker",
    "Freeze close evidence",
    "Layout boundary",
)
CAPTURE_TRACE_ARTIFACTS_BY_WORK_ITEM = {
    "CAP-INP": (
        "PB-100-input-reverse-package-trace.csv",
        "PB-100-input-reverse-freeze-review.csv",
        "PB-100-input-reverse-q1-freeze-checklist.csv",
        "PB-100-input-reverse-q1-derivation-precheck.csv",
        "PB-100-input-reverse-q1-closeout-precheck.csv",
        "PB-100-board-current-budget-trace.csv",
        "PB-100-board-current-budget-freeze-review.csv",
        "PB-100-board-current-budget-design-calculation.md",
        "PB-100-board-current-budget-value-freeze-checklist.csv",
        "PB-100-board-current-budget-value-derivation-precheck.csv",
        "PB-100-tvs-load-dump-margin-trace.csv",
        "PB-100-tvs-load-dump-freeze-review.csv",
        "PB-100-tvs-overshoot-escape-checklist.csv",
        "PB-100-tvs-overshoot-validation-precheck.csv",
        "PB-100-tvs-overshoot-closeout-precheck.csv",
    ),
    "CAP-LOGIC": (
        "PB-100-logic-power-rail-trace.csv",
        "PB-100-logic-power-freeze-review.csv",
        "PB-100-logic-power-value-freeze-checklist.csv",
        "PB-100-logic-power-value-derivation-precheck.csv",
        "PB-100-logic-power-closeout-precheck.csv",
    ),
    "CAP-OUT-TEMPLATE": (
        "PB-100-high-medium-output-baseline-trace.csv",
        "PB-100-high-medium-output-freeze-review.csv",
        "PB-100-low-current-output-baseline-trace.csv",
        "PB-100-low-current-output-freeze-review.csv",
        "PB-100-output-stage-value-freeze-checklist.csv",
        "PB-100-output-stage-value-derivation-precheck.csv",
        "PB-100-output-stage-closeout-precheck.csv",
    ),
    "CAP-OUT-INST": (
        "PB-100-high-medium-output-baseline-trace.csv",
        "PB-100-high-medium-output-freeze-review.csv",
        "PB-100-low-current-output-baseline-trace.csv",
        "PB-100-low-current-output-freeze-review.csv",
        "PB-100-output-stage-value-freeze-checklist.csv",
        "PB-100-output-stage-value-derivation-precheck.csv",
        "PB-100-output-stage-closeout-precheck.csv",
    ),
    "CAP-TEL": (
        "PB-100-current-telemetry-trace.csv",
        "PB-100-current-telemetry-freeze-review.csv",
        "PB-100-current-telemetry-value-freeze-checklist.csv",
        "PB-100-current-telemetry-value-derivation-precheck.csv",
        "PB-100-current-telemetry-closeout-precheck.csv",
        "PB-100-thermal-telemetry-trace.csv",
        "PB-100-thermal-telemetry-freeze-review.csv",
        "PB-100-thermal-telemetry-value-freeze-checklist.csv",
        "PB-100-thermal-telemetry-value-derivation-precheck.csv",
        "PB-100-thermal-telemetry-closeout-precheck.csv",
    ),
    "CAP-B2B": (
        "PB-100-b2b-interface-trace.csv",
        "PB-100-b2b-lb100-resource-binding.csv",
        "PB-100-b2b-lb100-pin-audit-checklist.csv",
        "PB-100-b2b-interface-freeze-checklist.csv",
        "PB-100-b2b-interface-closeout-precheck.csv",
    ),
    "CAP-CAN1": (
        "PB-100-can1-tx-disable-trace.csv",
        "PB-100-can1-production-dnp-review.csv",
        "PB-100-can1-default-disable-freeze-checklist.csv",
        "PB-100-can1-default-disable-derivation-precheck.csv",
        "PB-100-can1-default-disable-closeout-precheck.csv",
    ),
}
REVIEW_RELEASE_MANIFEST_COLUMNS = (
    "Artifact",
    "Category",
    "Freeze role",
    "Required for freeze",
    "Validation hook",
    "Status",
)
REQUIRED_NET_PATTERNS = {
    "VBAT_RAW",
    "VBAT_PROT",
    "PB_5V_OUT",
    "LB_3V3_IO",
    "OUTn_CTL",
    "OUTn_FLT",
    "OUTn_IMON",
    "OUTn_LOAD",
    "OUTn_FUSED",
    "CAN1_TX_DISABLE_CMD",
    "CAN1_TX_DISABLED_STATUS",
    "CAN1_RX_ROUTE",
    "CAN1_TX_ROUTE",
}
ALLOWED_BOM_FILES = {"factory_bom_draft.csv", "garage_bom_draft.csv"}
OUTPUT_CONTROLLER_SYMBOL = "PB100_TPS48110AQDGXRQ1_PRELIM"
REQUIRED_READINESS_AREAS = {
    "Architecture baseline",
    "PB-100 requirements",
    "Symbol readiness",
    "KiCad scaffold",
    "Capture work queue",
    "Review release manifest",
    "Freeze gap register",
    "Validation traceability",
    "Instance map",
    "Sheet map",
    "Net domains",
    "Output pin contract",
    "Output controller template",
    "Output net expansion",
    "Output stage design values",
    "Input controller template",
    "Current monitor template",
    "Logic buck template",
    "Input power design values",
    "Logic power design values",
    "Input protection contract",
    "Test point plan",
    "Fault response matrix",
    "Hardware capability manifest",
    "Logic power values",
    "BOM synchronization",
    "Assembly sourcing recheck",
    "CAN1 safety",
    "CAN1 safety verification",
    "Layout authorization",
}
ALLOWED_DASHBOARD_STATUSES = {"Closed", "Conditional", "Open", "Blocked", "Ready"}
REQUIRED_LOGIC_POWER_ITEMS = {
    "Buck regulator",
    "Buck input rail",
    "Buck output rail",
    "Inductor",
    "Input capacitors",
    "Output capacitors",
    "Feedback divider",
    "UVLO network",
    "Power-good",
    "EMI input filter",
}
REQUIRED_OUTPUT_STAGE_CLASSES = {"High current", "Medium current", "Low current"}
REQUIRED_OUTPUT_STAGE_ITEMS = {
    "OV threshold divider",
    "Current warning threshold",
    "Short-circuit threshold",
    "Fault timer",
    "Bootstrap capacitor",
    "Gate drive resistors",
    "Current sense topology",
    "Inductive clamp strategy",
}
REQUIRED_HIGH_MEDIUM_OUTPUT_FREEZE_REVIEW_ITEMS = {
    "Controller baseline",
    "OUT2 SOA envelope",
    "Medium fuse paths",
    "Gate drive default off",
    "Sense and telemetry",
    "Fault timing and thresholds",
    "Inductive clamp strategy",
    "Thermal and layout boundary",
}
REQUIRED_LOW_CURRENT_OUTPUT_FREEZE_REVIEW_ITEMS = {
    "ADR-0011 boundary",
    "Fuse and current class",
    "Gate drive default off",
    "Sense and telemetry",
    "Threshold and timer values",
    "Clamp and load handling",
    "Thermal and sourcing boundary",
    "Configuration separation",
}
REQUIRED_INPUT_POWER_ITEMS = {
    "Battery positive derating",
    "TVS clamp selection",
    "Charge-pump capacitor",
    "Enable network",
    "Gate clamp and discharge",
    "Q1 package and copper path",
    "Shunt value and power rating",
    "I2C address straps",
    "I2C pull-up domain",
    "Alert mapping",
    "Bus voltage sense",
    "Protected battery distribution",
}
REQUIRED_INPUT_REVERSE_FREEZE_REVIEW_ITEMS = {
    "Controller gate default",
    "Rejected 60V history",
    "Selected 80V LFPAK88 path",
    "80V non-drop-in alternatives",
    "Protected measurement sequence",
    "TVS overshoot dependency",
    "Assembly and sourcing gate",
    "Layout authorization boundary",
}
REQUIRED_INPUT_REVERSE_Q1_FREEZE_CHECKS = {
    "Q1-FRZ-001",
    "Q1-FRZ-002",
    "Q1-FRZ-003",
    "Q1-FRZ-004",
    "Q1-FRZ-005",
    "Q1-FRZ-006",
    "Q1-FRZ-007",
    "Q1-FRZ-008",
    "Q1-FRZ-009",
}
REQUIRED_INPUT_REVERSE_Q1_DERIVATION_CHECKS = {
    "Q1-DER-001",
    "Q1-DER-002",
    "Q1-DER-003",
    "Q1-DER-004",
    "Q1-DER-005",
    "Q1-DER-006",
    "Q1-DER-007",
    "Q1-DER-008",
    "Q1-DER-009",
    "Q1-DER-010",
}
REQUIRED_INPUT_REVERSE_Q1_CLOSEOUT_PRECHECKS = {
    "Q1-CLS-001",
    "Q1-CLS-002",
    "Q1-CLS-003",
    "Q1-CLS-004",
    "Q1-CLS-005",
    "Q1-CLS-006",
    "Q1-CLS-007",
    "Q1-CLS-008",
    "Q1-CLS-009",
    "Q1-CLS-010",
}
REQUIRED_TVS_LOAD_DUMP_FREEZE_REVIEW_ITEMS = {
    "Active HM3 branch",
    "100V device margin",
    "60V MOSFET historical rejection",
    "80V MOSFET selected baseline",
    "60V buck alternate boundary",
    "40V smart-switch ADR boundary",
    "OV and input-filter dependencies",
    "Assembly and sourcing gate",
    "Layout authorization boundary",
}
REQUIRED_TVS_OVERSHOOT_ESCAPE_CHECKS = {
    "TVS-FRZ-001",
    "TVS-FRZ-002",
    "TVS-FRZ-003",
    "TVS-FRZ-004",
    "TVS-FRZ-005",
    "TVS-FRZ-006",
    "TVS-FRZ-007",
    "TVS-FRZ-008",
    "TVS-FRZ-009",
}
REQUIRED_TVS_OVERSHOOT_VALIDATION_CHECKS = {
    "TVS-VAL-001",
    "TVS-VAL-002",
    "TVS-VAL-003",
    "TVS-VAL-004",
    "TVS-VAL-005",
    "TVS-VAL-006",
    "TVS-VAL-007",
    "TVS-VAL-008",
    "TVS-VAL-009",
    "TVS-VAL-010",
}
REQUIRED_TVS_OVERSHOOT_CLOSEOUT_PRECHECKS = {
    "TVS-CLS-001",
    "TVS-CLS-002",
    "TVS-CLS-003",
    "TVS-CLS-004",
    "TVS-CLS-005",
    "TVS-CLS-006",
    "TVS-CLS-007",
    "TVS-CLS-008",
    "TVS-CLS-009",
    "TVS-CLS-010",
}
REQUIRED_LOGIC_POWER_VALUE_ITEMS = {
    "Input filter",
    "UVLO divider",
    "RON programming",
    "Feedback divider",
    "Bootstrap capacitor",
    "Switch node damping",
    "Inductor",
    "Output capacitors",
    "Power-good pull-up",
    "Higher-current fallback",
}
REQUIRED_LOGIC_POWER_FREEZE_REVIEW_ITEMS = {
    "Regulator family boundary",
    "Protected input sequence",
    "PB_5V_OUT ownership",
    "Cold-crank UVLO safe-off",
    "Programming values remain TBD",
    "Switch node and EMI boundary",
    "Inductor and capacitor class",
    "Power-good interface",
    "Assembly and sourcing gate",
    "Layout authorization boundary",
}
REQUIRED_LOGIC_POWER_VALUE_FREEZE_CHECKS = {
    "LOGIC-FRZ-001",
    "LOGIC-FRZ-002",
    "LOGIC-FRZ-003",
    "LOGIC-FRZ-004",
    "LOGIC-FRZ-005",
    "LOGIC-FRZ-006",
    "LOGIC-FRZ-007",
    "LOGIC-FRZ-008",
    "LOGIC-FRZ-009",
    "LOGIC-FRZ-010",
}
REQUIRED_LOGIC_POWER_VALUE_DERIVATION_CHECKS = {
    "LOGIC-DER-001",
    "LOGIC-DER-002",
    "LOGIC-DER-003",
    "LOGIC-DER-004",
    "LOGIC-DER-005",
    "LOGIC-DER-006",
    "LOGIC-DER-007",
    "LOGIC-DER-008",
    "LOGIC-DER-009",
    "LOGIC-DER-010",
}
REQUIRED_LOGIC_POWER_CLOSEOUT_PRECHECKS = {
    "LOGIC-CLS-001",
    "LOGIC-CLS-002",
    "LOGIC-CLS-003",
    "LOGIC-CLS-004",
    "LOGIC-CLS-005",
    "LOGIC-CLS-006",
    "LOGIC-CLS-007",
    "LOGIC-CLS-008",
    "LOGIC-CLS-009",
    "LOGIC-CLS-010",
}
REQUIRED_CAN1_SAFETY_REQUIREMENTS = {
    "Vehicle CAN read-only default",
    "TX physical path",
    "Disable command",
    "Disabled status",
    "RX independence",
    "DNP BOM ownership",
    "Firmware safety",
    "Future TX change process",
}
REQUIRED_CAN1_PRODUCTION_DNP_REVIEW_ITEMS = {
    "Physical missing link",
    "Default disabled gate",
    "Physical status readback",
    "RX independence",
    "Firmware listen-only",
    "Future change process",
    "Factory DNP ownership",
}
REQUIRED_CAN1_RESET_BENCH_CHECKS = {
    "CAN1-RST-001",
    "CAN1-RST-002",
    "CAN1-RST-003",
    "CAN1-RST-004",
    "CAN1-RST-005",
    "CAN1-RST-006",
}
REQUIRED_CAN1_DEFAULT_DISABLE_FREEZE_CHECKS = {
    "CAN1-FRZ-001",
    "CAN1-FRZ-002",
    "CAN1-FRZ-003",
    "CAN1-FRZ-004",
    "CAN1-FRZ-005",
    "CAN1-FRZ-006",
    "CAN1-FRZ-007",
    "CAN1-FRZ-008",
    "CAN1-FRZ-009",
    "CAN1-FRZ-010",
}
REQUIRED_CAN1_DEFAULT_DISABLE_DERIVATION_CHECKS = {
    "CAN1-DER-001",
    "CAN1-DER-002",
    "CAN1-DER-003",
    "CAN1-DER-004",
    "CAN1-DER-005",
    "CAN1-DER-006",
    "CAN1-DER-007",
    "CAN1-DER-008",
    "CAN1-DER-009",
    "CAN1-DER-010",
}
REQUIRED_CAN1_DEFAULT_DISABLE_CLOSEOUT_PRECHECKS = {
    "CAN1-CLS-001",
    "CAN1-CLS-002",
    "CAN1-CLS-003",
    "CAN1-CLS-004",
    "CAN1-CLS-005",
    "CAN1-CLS-006",
    "CAN1-CLS-007",
    "CAN1-CLS-008",
    "CAN1-CLS-009",
    "CAN1-CLS-010",
}
REQUIRED_B2B_LB100_PIN_AUDIT_ITEMS = {
    "B2B-AUD-001",
    "B2B-AUD-002",
    "B2B-AUD-003",
    "B2B-AUD-004",
    "B2B-AUD-005",
    "B2B-AUD-006",
    "B2B-AUD-007",
    "B2B-AUD-008",
    "B2B-AUD-009",
}
REQUIRED_B2B_INTERFACE_FREEZE_CHECKS = {
    "B2B-FRZ-001",
    "B2B-FRZ-002",
    "B2B-FRZ-003",
    "B2B-FRZ-004",
    "B2B-FRZ-005",
    "B2B-FRZ-006",
    "B2B-FRZ-007",
    "B2B-FRZ-008",
    "B2B-FRZ-009",
    "B2B-FRZ-010",
}
REQUIRED_B2B_INTERFACE_CLOSEOUT_PRECHECKS = {
    "B2B-CLS-001",
    "B2B-CLS-002",
    "B2B-CLS-003",
    "B2B-CLS-004",
    "B2B-CLS-005",
    "B2B-CLS-006",
    "B2B-CLS-007",
    "B2B-CLS-008",
    "B2B-CLS-009",
    "B2B-CLS-010",
}
REQUIRED_OUTPUT_STAGE_VALUE_FREEZE_CHECKS = {
    "OUTVAL-001",
    "OUTVAL-002",
    "OUTVAL-003",
    "OUTVAL-004",
    "OUTVAL-005",
    "OUTVAL-006",
    "OUTVAL-007",
    "OUTVAL-008",
    "OUTVAL-009",
}
REQUIRED_OUTPUT_STAGE_VALUE_DERIVATION_CHECKS = {
    "OUTDRV-001",
    "OUTDRV-002",
    "OUTDRV-003",
    "OUTDRV-004",
    "OUTDRV-005",
    "OUTDRV-006",
    "OUTDRV-007",
    "OUTDRV-008",
    "OUTDRV-009",
    "OUTDRV-010",
}
REQUIRED_OUTPUT_STAGE_CLOSEOUT_PRECHECKS = {
    "OUTCLS-001",
    "OUTCLS-002",
    "OUTCLS-003",
    "OUTCLS-004",
    "OUTCLS-005",
    "OUTCLS-006",
    "OUTCLS-007",
    "OUTCLS-008",
    "OUTCLS-009",
    "OUTCLS-010",
}
REQUIRED_BOARD_CURRENT_BUDGET_FREEZE_REVIEW_ITEMS = {
    "Main fuse and input connector",
    "Q1 reverse path thermal",
    "Input shunt and Kelvin path",
    "Protected copper distribution",
    "Firmware configuration budget",
    "Telemetry enforcement",
    "Output oversubscription boundary",
    "Layout authorization boundary",
}
REQUIRED_BOARD_CURRENT_BUDGET_VALUE_FREEZE_CHECKS = {
    "BUDGET-FRZ-001",
    "BUDGET-FRZ-002",
    "BUDGET-FRZ-003",
    "BUDGET-FRZ-004",
    "BUDGET-FRZ-005",
    "BUDGET-FRZ-006",
    "BUDGET-FRZ-007",
    "BUDGET-FRZ-008",
    "BUDGET-FRZ-009",
    "BUDGET-FRZ-010",
}
REQUIRED_BOARD_CURRENT_BUDGET_VALUE_DERIVATION_CHECKS = {
    "BUDGET-DER-001",
    "BUDGET-DER-002",
    "BUDGET-DER-003",
    "BUDGET-DER-004",
    "BUDGET-DER-005",
    "BUDGET-DER-006",
    "BUDGET-DER-007",
    "BUDGET-DER-008",
    "BUDGET-DER-009",
    "BUDGET-DER-010",
}
REQUIRED_BOARD_CURRENT_BUDGET_CLOSEOUT_PRECHECKS = {
    "BUDGET-CLS-001",
    "BUDGET-CLS-002",
    "BUDGET-CLS-003",
    "BUDGET-CLS-004",
    "BUDGET-CLS-005",
    "BUDGET-CLS-006",
    "BUDGET-CLS-007",
    "BUDGET-CLS-008",
    "BUDGET-CLS-009",
    "BUDGET-CLS-010",
}
REQUIRED_CURRENT_TELEMETRY_FREEZE_REVIEW_ITEMS = {
    "Total shunt range",
    "Monitor range",
    "Kelvin and copper heating",
    "ADC or I2C ownership",
    "Per-output IMON scaling",
    "Calibration configuration",
    "Stale telemetry safe fault",
    "Bench validation path",
}
REQUIRED_CURRENT_TELEMETRY_VALUE_FREEZE_CHECKS = {
    "CUR-FRZ-001",
    "CUR-FRZ-002",
    "CUR-FRZ-003",
    "CUR-FRZ-004",
    "CUR-FRZ-005",
    "CUR-FRZ-006",
    "CUR-FRZ-007",
    "CUR-FRZ-008",
    "CUR-FRZ-009",
    "CUR-FRZ-010",
}
REQUIRED_CURRENT_TELEMETRY_VALUE_DERIVATION_CHECKS = {
    "CUR-DER-001",
    "CUR-DER-002",
    "CUR-DER-003",
    "CUR-DER-004",
    "CUR-DER-005",
    "CUR-DER-006",
    "CUR-DER-007",
    "CUR-DER-008",
    "CUR-DER-009",
    "CUR-DER-010",
}
REQUIRED_CURRENT_TELEMETRY_CLOSEOUT_PRECHECKS = {
    "CUR-CLS-001",
    "CUR-CLS-002",
    "CUR-CLS-003",
    "CUR-CLS-004",
    "CUR-CLS-005",
    "CUR-CLS-006",
    "CUR-CLS-007",
    "CUR-CLS-008",
    "CUR-CLS-009",
    "CUR-CLS-010",
}
REQUIRED_THERMAL_TELEMETRY_FREEZE_REVIEW_ITEMS = {
    "Sensor class",
    "Divider and ADC scaling",
    "Placement zones",
    "Configuration thresholds",
    "Firmware fail-safe",
    "Calibration boundary",
    "Assembly and alternates",
    "Bench validation path",
}
REQUIRED_THERMAL_TELEMETRY_VALUE_FREEZE_CHECKS = {
    "THERM-FRZ-001",
    "THERM-FRZ-002",
    "THERM-FRZ-003",
    "THERM-FRZ-004",
    "THERM-FRZ-005",
    "THERM-FRZ-006",
    "THERM-FRZ-007",
    "THERM-FRZ-008",
    "THERM-FRZ-009",
    "THERM-FRZ-010",
}
REQUIRED_THERMAL_TELEMETRY_VALUE_DERIVATION_CHECKS = {
    "THERM-DER-001",
    "THERM-DER-002",
    "THERM-DER-003",
    "THERM-DER-004",
    "THERM-DER-005",
    "THERM-DER-006",
    "THERM-DER-007",
    "THERM-DER-008",
    "THERM-DER-009",
    "THERM-DER-010",
}
REQUIRED_THERMAL_TELEMETRY_CLOSEOUT_PRECHECKS = {
    "THERM-CLS-001",
    "THERM-CLS-002",
    "THERM-CLS-003",
    "THERM-CLS-004",
    "THERM-CLS-005",
    "THERM-CLS-006",
    "THERM-CLS-007",
    "THERM-CLS-008",
    "THERM-CLS-009",
    "THERM-CLS-010",
}
REQUIRED_FACTORY_ASSEMBLY_FREEZE_CHECKS = {
    "FACT-FRZ-001",
    "FACT-FRZ-002",
    "FACT-FRZ-003",
    "FACT-FRZ-004",
    "FACT-FRZ-005",
    "FACT-FRZ-006",
    "FACT-FRZ-007",
    "FACT-FRZ-008",
    "FACT-FRZ-009",
    "FACT-FRZ-010",
}
REQUIRED_FACTORY_ASSEMBLY_SOURCING_PRECHECKS = {
    "FACT-SRC-001",
    "FACT-SRC-002",
    "FACT-SRC-003",
    "FACT-SRC-004",
    "FACT-SRC-005",
    "FACT-SRC-006",
    "FACT-SRC-007",
    "FACT-SRC-008",
    "FACT-SRC-009",
    "FACT-SRC-010",
}
REQUIRED_FACTORY_ASSEMBLY_CLOSEOUT_PRECHECKS = {
    "FACT-CLS-001",
    "FACT-CLS-002",
    "FACT-CLS-003",
    "FACT-CLS-004",
    "FACT-CLS-005",
    "FACT-CLS-006",
    "FACT-CLS-007",
    "FACT-CLS-008",
    "FACT-CLS-009",
    "FACT-CLS-010",
}
REQUIRED_GARAGE_INSTALL_FREEZE_CHECKS = {
    "GAR-FRZ-001",
    "GAR-FRZ-002",
    "GAR-FRZ-003",
    "GAR-FRZ-004",
    "GAR-FRZ-005",
    "GAR-FRZ-006",
    "GAR-FRZ-007",
    "GAR-FRZ-008",
    "GAR-FRZ-009",
    "GAR-FRZ-010",
}
REQUIRED_GARAGE_INSTALL_SOURCING_PRECHECKS = {
    "GAR-SRC-001",
    "GAR-SRC-002",
    "GAR-SRC-003",
    "GAR-SRC-004",
    "GAR-SRC-005",
    "GAR-SRC-006",
    "GAR-SRC-007",
    "GAR-SRC-008",
    "GAR-SRC-009",
    "GAR-SRC-010",
}
REQUIRED_GARAGE_INSTALL_CLOSEOUT_PRECHECKS = {
    "GAR-CLS-001",
    "GAR-CLS-002",
    "GAR-CLS-003",
    "GAR-CLS-004",
    "GAR-CLS-005",
    "GAR-CLS-006",
    "GAR-CLS-007",
    "GAR-CLS-008",
    "GAR-CLS-009",
    "GAR-CLS-010",
}
REQUIRED_FAULT_IDS = {
    "PBFLT-INPUT-REV",
    "PBFLT-LOAD-DUMP",
    "PBFLT-LOGIC-RAIL",
    "PBFLT-LB-ABSENT",
    "PBFLT-OUT-OC",
    "PBFLT-OUT-SHORT",
    "PBFLT-OUT2-INRUSH",
    "PBFLT-FUSE-OPEN",
    "PBFLT-THERM-HIGH",
    "PBFLT-THERM-STALE",
    "PBFLT-CUR-STALE",
    "PBFLT-BUDGET",
    "PBFLT-CAN1-TX",
    "PBFLT-B2B-MISMATCH",
}
REQUIRED_CAPTURE_WORK_ITEMS = {
    "CAP-TOP",
    "CAP-INP",
    "CAP-LOGIC",
    "CAP-OUT-TEMPLATE",
    "CAP-OUT-INST",
    "CAP-TEL",
    "CAP-B2B",
    "CAP-CAN1",
    "CAP-TP",
}
ALLOWED_CAPTURE_STATUSES = {
    "Scaffold ready",
    "Linked scaffold",
    "Planned capture",
    "Blocked pending symbol",
    "Review-defined",
}
REQUIRED_RELEASE_MANIFEST_ARTIFACTS = {
    "docs/adr/ADR-0013-pb-100-prelayout-vs-postprototype-validation.md",
    ENGINEERING_BLOCKER_CLOSEOUT,
    SCHEMATIC_REVIEW_CLOSEOUT,
    "hardware/power-board/PB-100/PB-100-schematic-package.md",
    "hardware/power-board/PB-100/PB-100-schematic-readiness-dashboard.csv",
    "hardware/power-board/PB-100/PB-100-schematic-freeze-checklist.md",
    "hardware/power-board/PB-100/PB-100-schematic-freeze-gap-register.csv",
    "hardware/power-board/PB-100/PB-100-board-release-blocker-register.csv",
    "hardware/power-board/PB-100/PB-100-board-print-closure-matrix.csv",
    "hardware/power-board/PB-100/PB-100-validation-traceability.csv",
    "hardware/power-board/PB-100/PB-100-schematic-capture-work-queue.csv",
    "hardware/power-board/PB-100/PB-100-review-release-manifest.csv",
    "hardware/power-board/PB-100/PB-100-board-current-budget-trace.csv",
    "hardware/power-board/PB-100/PB-100-board-current-budget-freeze-review.csv",
    "hardware/power-board/PB-100/PB-100-board-current-budget-design-calculation.md",
    "hardware/power-board/PB-100/PB-100-board-current-budget-value-freeze-checklist.csv",
    "hardware/power-board/PB-100/PB-100-board-current-budget-value-derivation-precheck.csv",
    "hardware/power-board/PB-100/PB-100-board-current-budget-closeout-precheck.csv",
    "hardware/power-board/PB-100/PB-100-post-prototype-validation-gate.csv",
    "hardware/power-board/PB-100/PB-100-low-current-output-baseline-trace.csv",
    "hardware/power-board/PB-100/PB-100-low-current-output-freeze-review.csv",
    "hardware/power-board/PB-100/PB-100-high-medium-output-baseline-trace.csv",
    "hardware/power-board/PB-100/PB-100-high-medium-output-freeze-review.csv",
    "hardware/power-board/PB-100/PB-100-output-stage-value-freeze-checklist.csv",
    "hardware/power-board/PB-100/PB-100-output-stage-value-derivation-precheck.csv",
    "hardware/power-board/PB-100/PB-100-output-stage-closeout-precheck.csv",
    "hardware/power-board/PB-100/PB-100-current-telemetry-trace.csv",
    "hardware/power-board/PB-100/PB-100-current-telemetry-freeze-review.csv",
    "hardware/power-board/PB-100/PB-100-current-telemetry-design-calculation.md",
    "hardware/power-board/PB-100/PB-100-current-telemetry-value-freeze-checklist.csv",
    "hardware/power-board/PB-100/PB-100-current-telemetry-value-derivation-precheck.csv",
    "hardware/power-board/PB-100/PB-100-current-telemetry-closeout-precheck.csv",
    "hardware/power-board/PB-100/PB-100-thermal-telemetry-trace.csv",
    "hardware/power-board/PB-100/PB-100-thermal-telemetry-freeze-review.csv",
    "hardware/power-board/PB-100/PB-100-thermal-telemetry-design-calculation.md",
    "hardware/power-board/PB-100/PB-100-thermal-telemetry-value-freeze-checklist.csv",
    "hardware/power-board/PB-100/PB-100-thermal-telemetry-value-derivation-precheck.csv",
    "hardware/power-board/PB-100/PB-100-thermal-telemetry-closeout-precheck.csv",
    "hardware/power-board/PB-100/PB-100-logic-power-rail-trace.csv",
    "hardware/power-board/PB-100/PB-100-logic-power-freeze-review.csv",
    "hardware/power-board/PB-100/PB-100-logic-power-design-calculation.md",
    "hardware/power-board/PB-100/PB-100-logic-power-value-freeze-checklist.csv",
    "hardware/power-board/PB-100/PB-100-logic-power-value-derivation-precheck.csv",
    "hardware/power-board/PB-100/PB-100-logic-power-closeout-precheck.csv",
    "hardware/power-board/PB-100/PB-100-input-reverse-package-trace.csv",
    "hardware/power-board/PB-100/PB-100-input-reverse-freeze-review.csv",
    "hardware/power-board/PB-100/PB-100-input-reverse-q1-freeze-checklist.csv",
    "hardware/power-board/PB-100/PB-100-input-reverse-q1-derivation-precheck.csv",
    "hardware/power-board/PB-100/PB-100-input-reverse-q1-closeout-precheck.csv",
    "hardware/power-board/PB-100/PB-100-b2b-interface-trace.csv",
    "hardware/power-board/PB-100/PB-100-b2b-lb100-resource-binding.csv",
    "hardware/power-board/PB-100/PB-100-b2b-lb100-pin-audit-checklist.csv",
    "hardware/power-board/PB-100/PB-100-b2b-interface-freeze-checklist.csv",
    "hardware/power-board/PB-100/PB-100-b2b-interface-closeout-precheck.csv",
    "hardware/power-board/PB-100/PB-100-b2b-lb100-pin-binding-precheck.md",
    "hardware/power-board/PB-100/PB-100-output-net-expansion.csv",
    "hardware/power-board/PB-100/PB-100-test-point-plan.csv",
    "hardware/power-board/PB-100/PB-100-fault-response-matrix.csv",
    "hardware/power-board/PB-100/PB-100-can1-tx-disable-trace.csv",
    "hardware/power-board/PB-100/PB-100-can1-safety-verification.csv",
    "hardware/power-board/PB-100/PB-100-can1-production-dnp-review.csv",
    "hardware/power-board/PB-100/PB-100-can1-reset-bench-checklist.csv",
    "hardware/power-board/PB-100/PB-100-can1-tx-disable-design-calculation.md",
    "hardware/power-board/PB-100/PB-100-can1-default-disable-freeze-checklist.csv",
    "hardware/power-board/PB-100/PB-100-can1-default-disable-derivation-precheck.csv",
    "hardware/power-board/PB-100/PB-100-can1-default-disable-closeout-precheck.csv",
    "hardware/power-board/PB-100/PB-100-tvs-load-dump-margin-trace.csv",
    "hardware/power-board/PB-100/PB-100-tvs-load-dump-freeze-review.csv",
    "hardware/power-board/PB-100/PB-100-tvs-overshoot-validation-precheck.csv",
    "hardware/power-board/PB-100/PB-100-tvs-overshoot-escape-checklist.csv",
    "hardware/power-board/PB-100/PB-100-tvs-overshoot-closeout-precheck.csv",
    "hardware/power-board/PB-100/PB-100-assembly-readiness-trace.csv",
    "hardware/power-board/PB-100/PB-100-factory-assembly-freeze-checklist.csv",
    "hardware/power-board/PB-100/PB-100-factory-assembly-sourcing-precheck.csv",
    "hardware/power-board/PB-100/PB-100-factory-assembly-closeout-precheck.csv",
    "hardware/power-board/PB-100/PB-100-garage-connector-fuse-plan.md",
    "hardware/power-board/PB-100/PB-100-garage-connector-fuse-plan.csv",
    "hardware/power-board/PB-100/PB-100-garage-install-freeze-checklist.csv",
    "hardware/power-board/PB-100/PB-100-garage-install-sourcing-precheck.csv",
    "hardware/power-board/PB-100/PB-100-garage-install-closeout-precheck.csv",
    "hardware/power-board/PB-100/kicad/PB-100.kicad_sch",
    "hardware/power-board/PB-100/kicad/lib/PB100.kicad_sym",
    "firmware/configs/hardware/pb-100-capabilities.json",
    "production/bom/pb100_symbol_bom_map.csv",
    "production/bom/pb100_assembly_sourcing_recheck.csv",
}


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        fail(f"missing required file: {path.relative_to(REPO_ROOT)}")


def validate_csv(path: Path) -> None:
    try:
        rows = list(csv.reader(path.open(newline="", encoding="utf-8")))
    except FileNotFoundError:
        fail(f"missing required CSV: {path.relative_to(REPO_ROOT)}")
    if not rows:
        fail(f"empty CSV: {path.relative_to(REPO_ROOT)}")
    expected_width = len(rows[0])
    for row_number, row_values in enumerate(rows, 1):
        if len(row_values) != expected_width:
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: "
                f"expected {expected_width} columns, got {len(row_values)}"
            )


def validate_s_expression_balance(path: Path) -> None:
    text = read_text(path)
    depth = 0
    in_string = False
    escaped = False
    for character in text:
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
        else:
            if character == '"':
                in_string = True
            elif character == "(":
                depth += 1
            elif character == ")":
                depth -= 1
                if depth < 0:
                    fail(f"negative parenthesis depth in {path.relative_to(REPO_ROOT)}")
    if depth != 0 or in_string:
        fail(
            f"unbalanced S-expression in {path.relative_to(REPO_ROOT)}: "
            f"depth={depth}, in_string={in_string}"
        )


def validate_kicad_scaffold() -> None:
    json.loads(read_text(KICAD_DIR / "PB-100.kicad_pro"))
    for schematic_path in sorted(KICAD_DIR.rglob("*.kicad_sch")):
        validate_s_expression_balance(schematic_path)
    for table_name in ("sym-lib-table", "fp-lib-table"):
        validate_s_expression_balance(KICAD_DIR / table_name)
    validate_s_expression_balance(KICAD_DIR / "lib" / "PB100.kicad_sym")
    validate_no_layout_artifacts()
    validate_kicad_top_sheet_links()
    validate_kicad_no_sheet_placeholders()


def validate_kicad_top_sheet_links() -> None:
    top_path = KICAD_DIR / "PB-100.kicad_sch"
    top_text = read_text(top_path)
    manifest_rows = list(
        csv.DictReader((PB100_DIR / "PB-100-kicad-sheet-manifest.csv").open(newline="", encoding="utf-8"))
    )
    child_sheets = [row["Sheet file"].strip() for row in manifest_rows if row["Sheet kind"].strip() == "child"]
    for sheet_file in child_sheets:
        sheet_path = KICAD_DIR / "sheets" / sheet_file
        if not sheet_path.exists():
            fail(f"missing child sheet linked by manifest: {sheet_path.relative_to(REPO_ROOT)}")
        sheet_name = sheet_file.removesuffix(".kicad_sch")
        sheetfile_token = f'(property "Sheetfile" "sheets/{sheet_file}"'
        sheetname_token = f'(property "Sheetname" "{sheet_name}"'
        if sheetfile_token not in top_text:
            fail(f"{top_path.relative_to(REPO_ROOT)} must link sheets/{sheet_file}")
        if sheetname_token not in top_text:
            fail(f"{top_path.relative_to(REPO_ROOT)} must name child sheet {sheet_name}")


def validate_kicad_no_sheet_placeholders() -> None:
    for schematic_path in sorted(KICAD_DIR.rglob("*.kicad_sch")):
        text = read_text(schematic_path).lower()
        for token in ("sheet-placeholder", "placeholder sheet"):
            if token in text:
                fail(
                    f"{schematic_path.relative_to(REPO_ROOT)} still contains `{token}`; "
                    "PB-100 child sheets must contain captured schematic content before ERC/netlist validation"
                )


def validate_kicad_cli_checks() -> None:
    kicad_cli = shutil.which("kicad-cli")
    if kicad_cli is None:
        fail("kicad-cli is required for PB-100 validation; install KiCad CLI before running make check")

    version_result = subprocess.run(
        [kicad_cli, "--version"],
        check=False,
        text=True,
        capture_output=True)
    if version_result.returncode != 0:
        details = "\n".join(part for part in (version_result.stdout.strip(), version_result.stderr.strip()) if part)
        fail(f"unable to read kicad-cli version: {details}")
    actual_version = version_result.stdout.strip()
    if actual_version != REQUIRED_KICAD_CLI_VERSION:
        fail(f"kicad-cli version {actual_version} is not the required {REQUIRED_KICAD_CLI_VERSION}")

    with tempfile.TemporaryDirectory(prefix="svc-pb100-kicad-") as temp_dir:
        report_path = Path(temp_dir) / "PB-100-erc.json"
        command = [
            kicad_cli,
            "sch",
            "erc",
            "--format",
            "json",
            "--output",
            str(report_path),
            "--exit-code-violations",
            str(KICAD_DIR / "PB-100.kicad_sch"),
        ]
        result = subprocess.run(command, check=False, text=True, capture_output=True)
        if result.returncode != 0:
            details = "\n".join(part for part in (result.stdout.strip(), result.stderr.strip()) if part)
            fail(f"KiCad ERC failed for PB-100 schematic: {details}")

        try:
            report = json.loads(read_text(report_path))
        except json.JSONDecodeError as error:
            fail(f"invalid KiCad ERC JSON report: {error}")

        violations = []
        for sheet in report.get("sheets", []):
            violations.extend(sheet.get("violations", []))
        if violations:
            fail(f"KiCad ERC reported {len(violations)} PB-100 schematic violations")

        version = report.get("kicad_version", "unknown")
        print(f"PB-100 KiCad ERC passed with kicad-cli {version}")
        validate_kicad_cli_netlist_export(kicad_cli, Path(temp_dir))


def validate_kicad_cli_netlist_export(kicad_cli: str, temp_dir: Path) -> None:
    netlist_path = temp_dir / "PB-100.net"
    command = [
        kicad_cli,
        "sch",
        "export",
        "netlist",
        "--format",
        "kicadsexpr",
        "--output",
        str(netlist_path),
        str(KICAD_DIR / "PB-100.kicad_sch"),
    ]
    result = subprocess.run(command, check=False, text=True, capture_output=True)
    if result.returncode != 0:
        details = "\n".join(part for part in (result.stdout.strip(), result.stderr.strip()) if part)
        fail(f"KiCad netlist export failed for PB-100 schematic: {details}")

    netlist_text = read_text(netlist_path)
    if "(export" not in netlist_text or "(design" not in netlist_text:
        fail("KiCad netlist export did not produce a valid PB-100 netlist")
    validate_s_expression_balance(netlist_path)
    component_count = len(re.findall(r"(?m)^\s*\(comp\b", netlist_text))
    net_count = len(re.findall(r"(?m)^\s*\(net\b", netlist_text))
    if component_count < MIN_KICAD_COMPONENTS:
        fail(
            f"KiCad netlist has {component_count} components; "
            f"expected at least {MIN_KICAD_COMPONENTS}"
        )
    if net_count < MIN_KICAD_NETS:
        fail(
            f"KiCad netlist has {net_count} electrical nets; "
            f"expected at least {MIN_KICAD_NETS}"
        )
    validate_can1_netlist_topology(kicad_cli, temp_dir)
    print("PB-100 KiCad netlist export passed")


def validate_can1_netlist_topology(kicad_cli: str, temp_dir: Path) -> None:
    """Validate the captured CAN1 safety circuit from connectivity, not labels in prose."""
    netlist_path = temp_dir / "PB-100.xml"
    command = [
        kicad_cli,
        "sch",
        "export",
        "netlist",
        "--format",
        "kicadxml",
        "--output",
        str(netlist_path),
        str(KICAD_DIR / "PB-100.kicad_sch"),
    ]
    result = subprocess.run(command, check=False, text=True, capture_output=True)
    if result.returncode != 0:
        details = "\n".join(part for part in (result.stdout.strip(), result.stderr.strip()) if part)
        fail(f"KiCad XML netlist export failed for CAN1 topology validation: {details}")

    try:
        root = ET.parse(netlist_path).getroot()
    except (ET.ParseError, OSError) as error:
        fail(f"invalid KiCad XML netlist for CAN1 topology validation: {error}")

    components = {
        component.get("ref", ""): component
        for component in root.findall("./components/comp")
    }
    expected_components = {
        "JP_CAN1": ("CAN1_TX_DNP_LINK_PRELIM", "PB100:R0603_DNP_LINK_1608Metric"),
        "U_CAN1": ("SN74LVC1G125_Q1_DBV_PRELIM", "PB100:SOT-23-5_DBV_TI"),
        "R_CAN1_OE": ("47k 1%", "PB100:R0402"),
        "R_CAN1_TX_BIAS": ("47k 1%", "PB100:R0402"),
        "R_CAN1_STATUS_SER": ("1k 1%", "PB100:R0402"),
        "R_CAN1_STATUS_PULL": ("100k 1%", "PB100:R0402"),
        "U_CAN1_PHY": ("TJA1051TK/3/1J", "PB100:HVSON-8_L3.0-W3.0-P0.65-BL-EP"),
        "R_CAN1_SILENT": ("47k 1%", "PB100:R0402"),
        "JP_CAN1_NORMAL": ("CAN1_NORMAL_MODE_DNP", "PB100:R0603_DNP_LINK_1608Metric"),
        "D_CAN1": ("ESD2CANFD24QDBZRQ1", "PB100:SOT-23-3_DBZ_TI"),
        "R_CAN1_TERM": ("120R 1% DNP", "PB100:R0603_DNP_LINK_1608Metric"),
        "C_CAN1_VCC": ("100nF 50V X7R", "PB100:C0402"),
        "C_CAN1_VIO": ("100nF 50V X7R", "PB100:C0402"),
    }
    for reference, (expected_value, expected_footprint) in expected_components.items():
        component = components.get(reference)
        if component is None:
            fail(f"CAN1 topology is missing physical component {reference}")
        value = component.findtext("value", default="").strip()
        footprint = component.findtext("footprint", default="").strip()
        if value != expected_value:
            fail(f"CAN1 component {reference} value is {value!r}; expected {expected_value!r}")
        if footprint != expected_footprint:
            fail(
                f"CAN1 component {reference} footprint is {footprint!r}; "
                f"expected {expected_footprint!r}"
            )

    if components["JP_CAN1"].find("./property[@name='dnp']") is None:
        fail("JP_CAN1 must be physically marked DNP in the exported KiCad netlist")
    for reference in ("JP_CAN1_NORMAL", "R_CAN1_TERM"):
        if components[reference].find("./property[@name='dnp']") is None:
            fail(f"{reference} must be physically marked DNP in the exported KiCad netlist")

    nets = {}
    for net in root.findall("./nets/net"):
        name = net.get("name", "")
        nets[name] = {(node.get("ref", ""), node.get("pin", "")) for node in net.findall("node")}

    exact_nets = {
        "CAN1_TX_ROUTE": {("JPB1", "70"), ("U_CAN1", "2")},
        "CAN1_TX_GATE_OUT": {("U_CAN1", "4"), ("JP_CAN1", "1")},
        "CAN1_TXD_SAFE": {
            ("JP_CAN1", "2"),
            ("R_CAN1_TX_BIAS", "2"),
            ("U_CAN1_PHY", "1"),
        },
        "CAN1_RX_ROUTE": {("JPB1", "69"), ("U_CAN1_PHY", "4")},
        "CAN1_PHY_SILENT": {
            ("JP_CAN1_NORMAL", "1"),
            ("R_CAN1_SILENT", "2"),
            ("U_CAN1_PHY", "8"),
        },
        "CAN1_HARNESS_H": {
            ("D_CAN1", "1"),
            ("R_CAN1_TERM", "1"),
            ("U_CAN1_PHY", "7"),
        },
        "CAN1_HARNESS_L": {
            ("D_CAN1", "2"),
            ("R_CAN1_TERM", "2"),
            ("U_CAN1_PHY", "6"),
        },
        "CAN1_TX_DISABLED_STATUS": {
            ("JPB1", "68"),
            ("R_CAN1_STATUS_SER", "2"),
            ("R_CAN1_STATUS_PULL", "2"),
        },
        "CAN1_TX_DISABLE_CMD": {
            ("JPB1", "67"),
            ("U_CAN1", "1"),
            ("R_CAN1_OE", "2"),
            ("R_CAN1_STATUS_SER", "1"),
        },
    }
    for net_name, expected_nodes in exact_nets.items():
        actual_nodes = nets.get(net_name)
        if actual_nodes != expected_nodes:
            fail(
                f"CAN1 net {net_name} has nodes {sorted(actual_nodes or set())}; "
                f"expected {sorted(expected_nodes)}"
            )

    rail_nodes = nets.get("LB_3V3_IO", set())
    required_rail_nodes = {
        ("U_CAN1", "5"),
        ("R_CAN1_OE", "1"),
        ("R_CAN1_TX_BIAS", "1"),
        ("R_CAN1_STATUS_PULL", "1"),
        ("U_CAN1_PHY", "5"),
        ("R_CAN1_SILENT", "1"),
        ("C_CAN1_VIO", "1"),
    }
    missing_rail_nodes = required_rail_nodes - rail_nodes
    if missing_rail_nodes:
        fail(f"CAN1 safety pull-ups are not tied to LB_3V3_IO: {sorted(missing_rail_nodes)}")

    required_pb5v_nodes = {("U_CAN1_PHY", "3"), ("C_CAN1_VCC", "1")}
    missing_pb5v_nodes = required_pb5v_nodes - nets.get("PB_5V_OUT", set())
    if missing_pb5v_nodes:
        fail(f"CAN1 transceiver VCC is not tied to PB_5V_OUT: {sorted(missing_pb5v_nodes)}")
    required_ground_nodes = {
        ("U_CAN1_PHY", "2"),
        ("U_CAN1_PHY", "9"),
        ("D_CAN1", "3"),
        ("JP_CAN1_NORMAL", "2"),
        ("C_CAN1_VCC", "2"),
        ("C_CAN1_VIO", "2"),
    }
    missing_ground_nodes = required_ground_nodes - nets.get("GND", set())
    if missing_ground_nodes:
        fail(f"CAN1 physical-layer ground is incomplete: {sorted(missing_ground_nodes)}")

    jpb1 = components.get("JPB1")
    if jpb1 is None:
        fail("PB-100 topology is missing JPB1")
    if jpb1.findtext("footprint", default="").strip() != "PB100:FX18-100P-0.8SV10_Hirose":
        fail("JPB1 must bind the reviewed Hirose FX18-100P footprint")
    mf_nodes = {
        ("JPB1", "MF_A_PIN1_51_END"),
        ("JPB1", "MF_B_PIN1_51_END"),
        ("JPB1", "MF_A_PIN50_100_END"),
        ("JPB1", "MF_B_PIN50_100_END"),
    }
    missing_mf_nodes = mf_nodes - nets.get("GND", set())
    if missing_mf_nodes:
        fail(f"JPB1 MF contacts are not tied only to GND: {sorted(missing_mf_nodes)}")
    forbidden_mf_nets = {
        net_name: sorted(mf_nodes & nodes)
        for net_name, nodes in nets.items()
        if net_name in {"AGND", "PB_5V_OUT", "LB_3V3_IO", "VBAT", "VBAT_RAW", "VBAT_PROT"}
        and mf_nodes & nodes
    }
    if forbidden_mf_nets:
        fail(f"JPB1 MF contacts are tied to forbidden nets: {forbidden_mf_nets}")

    print("PB-100 CAN1 and JPB1 MF physical net topology passed")


def validate_no_layout_artifacts() -> None:
    search_roots = (PB100_DIR, PRODUCTION_DIR)
    for search_root in search_roots:
        for path in search_root.rglob("*"):
            if not path.is_file():
                continue
            name = path.name.lower()
            suffix = path.suffix.lower()
            if name.endswith(".kicad_pcb-bak") or suffix in DISALLOWED_LAYOUT_SUFFIXES:
                fail(f"layout/manufacturing artifact is blocked before schematic freeze: {path.relative_to(REPO_ROOT)}")
            if suffix in MANUFACTURING_HINT_SUFFIXES and any(fragment in name for fragment in DISALLOWED_LAYOUT_NAME_FRAGMENTS):
                fail(f"layout/manufacturing artifact name is blocked before schematic freeze: {path.relative_to(REPO_ROOT)}")


def validate_symbol_library() -> None:
    symbol_text = read_text(KICAD_DIR / "lib" / "PB100.kicad_sym")
    required_symbols = [
        "PB100_INPUT_PROTECTION_PRELIM",
        "PB100_LOGIC_POWER_PRELIM",
        "PB100_OUTPUT_CHANNEL_PRELIM",
        "PB100_B2B_JPB1_ABSTRACT",
        "PB100_CAN1_TX_DISABLE_PRELIM",
    ]
    for symbol_name in required_symbols:
        if f'(symbol "{symbol_name}"' not in symbol_text:
            fail(f"missing preliminary KiCad symbol: {symbol_name}")
    if symbol_text.count("(in_bom no)") < len(required_symbols):
        fail("preliminary symbols must be excluded from BOM")
    if symbol_text.count("(on_board no)") < len(required_symbols):
        fail("preliminary symbols must be excluded from board")


def validate_kicad_no_role_tokens() -> None:
    checked_paths = sorted(KICAD_DIR.rglob("*.kicad_sch")) + sorted((KICAD_DIR / "lib").rglob("*.kicad_sym"))
    for path in checked_paths:
        text = read_text(path)
        for forbidden_token in FORBIDDEN_ROLE_TOKENS:
            if forbidden_token in text:
                fail(
                    f"accessory role token `{forbidden_token}` appears in KiCad artifact: "
                    f"{path.relative_to(REPO_ROOT)}"
                )


def validate_instance_plan() -> None:
    path = PB100_DIR / "PB-100-schematic-instance-plan.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    references = {row["Ref"] for row in rows}
    for output_number in range(1, 11):
        suffix = f"{100 + output_number}"
        for prefix in ("U", "Q", "F", "J"):
            expected_ref = f"{prefix}{suffix}"
            if expected_ref not in references:
                fail(f"missing output instance reference: {expected_ref}")


def validate_symbol_mpn_readiness() -> None:
    path = PB100_DIR / "PB-100-symbol-mpn-readiness.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty symbol/MPN readiness table: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in SYMBOL_MPN_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    seen_keys = set()
    worklist_path = PB100_DIR / "PB-100-symbol-capture-worklist.csv"
    worklist_rows = list(csv.DictReader(worklist_path.open(newline="", encoding="utf-8")))
    created_worklist_keys = {
        row["Symbol key"].strip()
        for row in worklist_rows
        if "preliminary symbol created" in row["Pin evidence status"].strip().lower()
    }
    for row_number, row in enumerate(rows, 2):
        symbol_key = row["Symbol key"].strip()
        if not symbol_key:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: missing symbol key")
        if symbol_key in seen_keys:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate symbol key {symbol_key}")
        seen_keys.add(symbol_key)

        critical = row["Critical"].strip().lower()
        if critical not in {"yes", "no"}:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: Critical must be yes or no")

        primary_source = row["Primary source"].strip()
        if not primary_source:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: missing primary source")
        if not (
            primary_source.startswith("https://")
            or primary_source.startswith("docs/")
            or primary_source.startswith("hardware/")
        ):
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: primary source must be "
                "an https URL or an internal docs/ or hardware/ path"
            )

        for column in (
            "Schematic block",
            "Function",
            "Preferred MPN or class",
            "Preferred package",
            "KiCad symbol status",
            "Footprint status",
            "Assembly/sourcing status",
            "Freeze condition",
        ):
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")

        if critical == "yes":
            for column in ("Alternate 1", "Alternate 2"):
                if not row[column].strip():
                    fail(
                        f"{path.relative_to(REPO_ROOT)}:{row_number}: "
                        f"critical symbol {symbol_key} is missing {column}"
                    )
            assembly_status = row["Assembly/sourcing status"].lower()
            if "recheck" not in assembly_status and "garage-installed" not in assembly_status:
                fail(
                    f"{path.relative_to(REPO_ROOT)}:{row_number}: critical symbol "
                    f"{symbol_key} must keep assembly/sourcing recheck explicit"
                )

        if row["KiCad symbol status"].strip().lower() in {"final", "locked"}:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: symbol status must not be final/locked")
        if symbol_key in created_worklist_keys and "created" not in row["KiCad symbol status"].lower():
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: symbol {symbol_key} "
                "is created in worklist but readiness status does not say created"
            )

    missing_keys = sorted(REQUIRED_SYMBOL_KEYS - seen_keys)
    if missing_keys:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required symbol keys: "
            f"{', '.join(missing_keys)}"
        )


def validate_symbol_trace_provenance() -> None:
    readiness_path = PB100_DIR / "PB-100-symbol-mpn-readiness.csv"
    readiness_rows = list(csv.DictReader(readiness_path.open(newline="", encoding="utf-8")))
    readiness_by_key = {row["Symbol key"].strip(): row for row in readiness_rows}
    worklist_path = PB100_DIR / "PB-100-symbol-capture-worklist.csv"
    worklist_rows = list(csv.DictReader(worklist_path.open(newline="", encoding="utf-8")))
    worklist_by_key = {row["Symbol key"].strip(): row for row in worklist_rows}
    for symbol_key, expected_source in INTERNAL_SYMBOL_TRACE_SOURCE_BY_KEY.items():
        source_path = REPO_ROOT / expected_source
        if not source_path.exists():
            fail(f"missing internal symbol trace source: {expected_source}")
        if symbol_key not in readiness_by_key:
            fail(f"{readiness_path.relative_to(REPO_ROOT)} is missing {symbol_key}")
        if symbol_key not in worklist_by_key:
            fail(f"{worklist_path.relative_to(REPO_ROOT)} is missing {symbol_key}")
        readiness_source = readiness_by_key[symbol_key]["Primary source"].strip()
        if readiness_source != expected_source:
            fail(f"{symbol_key} readiness primary source must be {expected_source}")
        worklist_source = worklist_by_key[symbol_key]["Symbol source"].strip()
        if worklist_source != expected_source:
            fail(f"{symbol_key} worklist symbol source must be {expected_source}")


def validate_symbol_capture_worklist() -> None:
    path = PB100_DIR / "PB-100-symbol-capture-worklist.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty symbol capture worklist: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in SYMBOL_WORKLIST_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    readiness_path = PB100_DIR / "PB-100-symbol-mpn-readiness.csv"
    readiness_rows = list(csv.DictReader(readiness_path.open(newline="", encoding="utf-8")))
    readiness_keys = {row["Symbol key"].strip() for row in readiness_rows}
    critical_keys = {
        row["Symbol key"].strip()
        for row in readiness_rows
        if row["Critical"].strip().lower() == "yes"
    }

    symbol_text = read_text(KICAD_DIR / "lib" / "PB100.kicad_sym")
    open_items_text = read_text(PB100_DIR / "PB-100-symbol-open-items.md")
    worklist_keys = set()
    for row_number, row in enumerate(rows, 2):
        symbol_key = row["Symbol key"].strip()
        if symbol_key not in readiness_keys:
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: "
                f"unknown readiness symbol key {symbol_key}"
            )
        if symbol_key in worklist_keys:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate symbol key {symbol_key}")
        worklist_keys.add(symbol_key)

        concrete_symbol_name = row["Concrete symbol name"].strip()
        if not concrete_symbol_name.startswith("PB100_") or not concrete_symbol_name.endswith("_PRELIM"):
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: concrete symbol name "
                "must use PB100_*_PRELIM"
            )
        if row["Library"].strip() != "PB100":
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: library must be PB100")

        symbol_source = row["Symbol source"].strip()
        if not (
            symbol_source.startswith("https://")
            or symbol_source.startswith("docs/")
            or symbol_source.startswith("hardware/")
        ):
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: symbol source must be "
                "an https URL or an internal docs/ or hardware/ path"
            )

        for column in (
            "Pin evidence status",
            "Footprint dependency",
            "Instance refs",
            "Allowed action",
            "Blocked action",
            "Freeze close evidence",
        ):
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        if "do not" not in row["Blocked action"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: blocked action must be explicit")

        created = "preliminary symbol created" in row["Pin evidence status"].strip().lower()
        symbol_present = f'(symbol "{concrete_symbol_name}"' in symbol_text
        if not created:
            if not row["Pin evidence status"].strip().lower().startswith("pending"):
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: pending symbol status must be explicit")
            if symbol_present:
                fail(
                    f"{path.relative_to(REPO_ROOT)}:{row_number}: pending symbol "
                    f"{concrete_symbol_name} is already present in PB100.kicad_sym"
                )
            if symbol_key not in open_items_text or concrete_symbol_name not in open_items_text:
                fail(
                    f"{path.relative_to(REPO_ROOT)}:{row_number}: pending symbol "
                    f"{symbol_key}/{concrete_symbol_name} must be tracked in PB-100-symbol-open-items.md"
                )

    missing_worklist_keys = sorted(critical_keys - worklist_keys)
    if missing_worklist_keys:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing critical symbol worklist keys: "
            f"{', '.join(missing_worklist_keys)}"
        )


def validate_symbol_capture_progress() -> None:
    path = PB100_DIR / "PB-100-symbol-capture-worklist.csv"
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    symbol_text = read_text(KICAD_DIR / "lib" / "PB100.kicad_sym")
    for row_number, row in enumerate(rows, 2):
        pin_status = row["Pin evidence status"].strip().lower()
        if "preliminary symbol created" not in pin_status:
            continue

        symbol_name = row["Concrete symbol name"].strip()
        marker = f'(symbol "{symbol_name}"'
        start = symbol_text.find(marker)
        if start < 0:
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: worklist marks "
                f"{symbol_name} created, but symbol is missing from PB100.kicad_sym"
            )

        next_symbol = symbol_text.find('\n  (symbol "', start + 1)
        if next_symbol < 0:
            next_symbol = symbol_text.rfind("\n)")
        symbol_block = symbol_text[start:next_symbol]
        selected_physical_symbols = {
            "PB100_TJA1051TK3_CAN_PHY_PRELIM": "PB100:HVSON-8_L3.0-W3.0-P0.65-BL-EP",
            "PB100_ESD2CANFD24_Q1_PRELIM": "PB100:SOT-23-3_DBZ_TI",
        }
        if symbol_name in selected_physical_symbols:
            if "(in_bom yes)" not in symbol_block or "(on_board yes)" not in symbol_block:
                fail(f"selected physical symbol {symbol_name} must be included in BOM and board")
            expected_footprint = selected_physical_symbols[symbol_name]
            if f'(property "Footprint" "{expected_footprint}"' not in symbol_block:
                fail(f"selected physical symbol {symbol_name} must bind {expected_footprint}")
            continue
        if "(in_bom no)" not in symbol_block:
            fail(f"preliminary symbol {symbol_name} must be excluded from BOM")
        if "(on_board no)" not in symbol_block:
            fail(f"preliminary symbol {symbol_name} must be excluded from board")
        if symbol_name == "PB100_JPB1_100PIN_PRELIM":
            if '(property "Footprint" "PB100:FX18-100P-0.8SV10_Hirose"' not in symbol_block:
                fail("JPB1 preliminary symbol must bind the Product Owner-approved FX18 footprint")
        elif symbol_name == "PB100_POWER_NMOS_ESCAPE_PRELIM":
            if '(property "Footprint" "PB100:LFPAK88_SOT1235_Nexperia"' not in symbol_block:
                fail("selected 80 V power MOSFET symbol must bind the reviewed LFPAK88 footprint")
        elif '(property "Footprint" ""' not in symbol_block:
            fail(f"preliminary symbol {symbol_name} must not lock a footprint")


def symbol_block(symbol_text: str, symbol_name: str) -> str:
    marker = f'(symbol "{symbol_name}"'
    start = symbol_text.find(marker)
    if start < 0:
        return ""
    next_symbol = symbol_text.find('\n  (symbol "', start + 1)
    if next_symbol < 0:
        next_symbol = symbol_text.rfind("\n)")
    return symbol_text[start:next_symbol]


def validate_symbol_pin_evidence() -> None:
    path = PB100_DIR / "PB-100-symbol-pin-evidence.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty symbol pin evidence table: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in SYMBOL_PIN_EVIDENCE_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    worklist_path = PB100_DIR / "PB-100-symbol-capture-worklist.csv"
    worklist_rows = list(csv.DictReader(worklist_path.open(newline="", encoding="utf-8")))
    created_symbols = {
        row["Concrete symbol name"].strip()
        for row in worklist_rows
        if "preliminary symbol created" in row["Pin evidence status"].strip().lower()
    }

    symbol_text = read_text(KICAD_DIR / "lib" / "PB100.kicad_sym")
    evidence_by_symbol: dict[str, set[tuple[str, str]]] = {}
    for row_number, row in enumerate(rows, 2):
        symbol_name = row["Symbol name"].strip()
        pin_number = row["Pin number"].strip()
        pin_name = row["Pin name"].strip()
        source = row["Source"].strip()
        if not symbol_name or not pin_number or not pin_name:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: missing symbol or pin identity")
        if not (source.startswith("https://") or source.startswith("hardware/") or source.startswith("docs/")):
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: source must be "
                "an https URL or an internal docs/ or hardware/ path"
            )
        for column in ("Source revision", "Package", "Notes"):
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")

        block = symbol_block(symbol_text, symbol_name)
        if not block:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: symbol {symbol_name} is missing")

        expected_name = f'(name "{pin_name}"'
        expected_number = f'(number "{pin_number}"'
        pin_matches = [
            line
            for line in block.splitlines()
            if expected_name in line and expected_number in line
        ]
        if not pin_matches:
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: pin {pin_number} "
                f"{pin_name} is not present in {symbol_name}"
            )

        evidence_by_symbol.setdefault(symbol_name, set()).add((pin_number, pin_name))

    missing_evidence = sorted(created_symbols - evidence_by_symbol.keys() - PIN_MAP_EVIDENCE_SYMBOLS)
    if missing_evidence:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing pin evidence for created symbols: "
            f"{', '.join(missing_evidence)}"
        )


def parse_symbol_pin_numbers(symbol_name: str) -> set[str]:
    block = symbol_block(read_text(KICAD_DIR / "lib" / "PB100.kicad_sym"), symbol_name)
    if not block:
        fail(f"symbol pad-map target is missing from PB100.kicad_sym: {symbol_name}")
    return set(re.findall(r'\(number "([^"]+)"', block))


def parse_footprint_pad_numbers(path: Path) -> set[str]:
    if not path.exists():
        fail(f"symbol-footprint pad-map references missing footprint: {path.relative_to(REPO_ROOT)}")
    return set(re.findall(r'\(pad "([^"]+)"', read_text(path)))


def footprint_pad_blocks(path: Path, pad_number: str) -> list[str]:
    text = read_text(path)
    pattern = re.compile(rf'\n\t\(pad "{re.escape(pad_number)}" .*?\n\t\)', re.DOTALL)
    return pattern.findall(text)


def validate_large_mosfet_paste_segmentation() -> None:
    checks = (
        (
            PB100_DIR / "kicad" / "lib" / "PB100.pretty" / "PG-HSOF-8-1_TOLL_Infineon.kicad_mod",
            "Tab",
            42,
        ),
        (
            PB100_DIR / "kicad" / "lib" / "PB100.pretty" / "LFPAK88_SOT1235_Nexperia.kicad_mod",
            "mb",
            12,
        ),
    )
    for path, pad_number, minimum_paste_apertures in checks:
        blocks = footprint_pad_blocks(path, pad_number)
        if not blocks:
            fail(f"{path.relative_to(REPO_ROOT)} is missing large MOSFET drain pad {pad_number}")
        copper_blocks = [block for block in blocks if '"F.Cu"' in block]
        paste_only_blocks = [
            block
            for block in blocks
            if '"F.Paste"' in block and '"F.Cu"' not in block and '"F.Mask"' not in block
        ]
        if len(copper_blocks) != 1:
            fail(
                f"{path.relative_to(REPO_ROOT)} must have exactly one copper/mask drain pad "
                f"{pad_number}, got {len(copper_blocks)}"
            )
        if '"F.Paste"' in copper_blocks[0]:
            fail(f"{path.relative_to(REPO_ROOT)} drain copper pad {pad_number} must not use solid F.Paste")
        if len(paste_only_blocks) < minimum_paste_apertures:
            fail(
                f"{path.relative_to(REPO_ROOT)} drain pad {pad_number} needs at least "
                f"{minimum_paste_apertures} segmented paste apertures, got {len(paste_only_blocks)}"
            )


def validate_symbol_footprint_pad_map() -> None:
    path = PB100_DIR / "PB-100-symbol-footprint-pad-map.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty symbol-footprint pad-map: {path.relative_to(REPO_ROOT)}")
    required_columns = {
        "Map ID",
        "Symbol name",
        "Symbol pin numbers",
        "Footprint path",
        "Footprint pad numbers",
        "Compatibility state",
        "Evidence",
        "Blocked action",
    }
    missing_columns = required_columns - set(rows[0])
    if missing_columns:
        fail(f"{path.relative_to(REPO_ROOT)} is missing columns: {', '.join(sorted(missing_columns))}")
    seen_ids = set()
    for row_number, row in enumerate(rows, 2):
        map_id = row["Map ID"].strip()
        if map_id in seen_ids:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate Map ID {map_id}")
        seen_ids.add(map_id)
        if row["Compatibility state"].strip() != "Compatible":
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: Compatibility state must be Compatible")
        if "Do not" not in row["Blocked action"]:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: Blocked action must be explicit")
        symbol_name = row["Symbol name"].strip()
        symbol_expected = set(row["Symbol pin numbers"].split())
        footprint_path = REPO_ROOT / row["Footprint path"].strip()
        footprint_expected = set(row["Footprint pad numbers"].split())
        symbol_actual = parse_symbol_pin_numbers(symbol_name)
        footprint_actual = parse_footprint_pad_numbers(footprint_path)
        missing_symbol_pins = sorted(symbol_expected - symbol_actual)
        missing_footprint_pads = sorted(footprint_expected - footprint_actual)
        if missing_symbol_pins:
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: {symbol_name} missing symbol pins "
                f"{', '.join(missing_symbol_pins)}"
            )
        if missing_footprint_pads:
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: "
                f"{row['Footprint path'].strip()} missing footprint pads {', '.join(missing_footprint_pads)}"
            )
        if symbol_expected != footprint_expected:
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: symbol pin set and footprint pad set must match"
            )


def validate_input_reverse_fet_symbol_evidence() -> None:
    symbol_name = "PB100_POWER_NMOS_ESCAPE_PRELIM"
    symbol_text = read_text(KICAD_DIR / "lib" / "PB100.kicad_sym")
    block = symbol_block(symbol_text, symbol_name)
    if not block:
        fail(f"{symbol_name} must exist after Q1 pin evidence is captured")

    for pin_number, pin_name in (
        ("1", "G"),
        ("2", "S"),
        ("3", "S"),
        ("4", "S"),
        ("mb", "D"),
    ):
        expected_name = f'(name "{pin_name}"'
        expected_number = f'(number "{pin_number}"'
        if not any(expected_name in line and expected_number in line for line in block.splitlines()):
            fail(f"{symbol_name} is missing Q1 pin {pin_number} {pin_name}")

    if "(in_bom no)" not in block:
        fail(f"{symbol_name} must remain excluded from BOM")
    if "(on_board no)" not in block:
        fail(f"{symbol_name} must remain excluded from board")
    if '(property "Value" "BUK7S1R2-80M"' not in block:
        fail(f"{symbol_name} must lock the Product Owner-approved BUK7S1R2-80M value")
    if '(property "Footprint" "PB100:LFPAK88_SOT1235_Nexperia"' not in block:
        fail(f"{symbol_name} must bind the reviewed LFPAK88 footprint")

    open_items_text = read_text(PB100_DIR / "PB-100-symbol-open-items.md")
    if "Evidence captured" not in open_items_text:
        fail("Q1 symbol-open-items row must mark evidence captured")
    if "40 A copper/thermal review remains open" not in open_items_text:
        fail("Q1 symbol-open-items row must keep 40 A copper/thermal review open")


def validate_jpb1_symbol_from_pin_map() -> None:
    worklist_path = PB100_DIR / "PB-100-symbol-capture-worklist.csv"
    worklist_rows = list(csv.DictReader(worklist_path.open(newline="", encoding="utf-8")))
    created = any(
        row["Concrete symbol name"].strip() == "PB100_JPB1_100PIN_PRELIM"
        and "preliminary symbol created" in row["Pin evidence status"].strip().lower()
        for row in worklist_rows
    )
    if not created:
        return

    pin_map_path = PB100_DIR / "PB-100-b2b-pin-map.csv"
    validate_csv(pin_map_path)
    pin_map_rows = list(csv.DictReader(pin_map_path.open(newline="", encoding="utf-8")))
    if len(pin_map_rows) != 100:
        fail(f"{pin_map_path.relative_to(REPO_ROOT)} must contain exactly 100 JPB1 pins")

    symbol_name = "PB100_JPB1_100PIN_PRELIM"
    symbol_text = read_text(KICAD_DIR / "lib" / "PB100.kicad_sym")
    block = symbol_block(symbol_text, symbol_name)
    if not block:
        fail(f"created B2B symbol is missing from PB100.kicad_sym: {symbol_name}")

    for row in pin_map_rows:
        pin_number = row["Pin"].strip()
        pin_name = row["Net"].strip()
        expected_name = f'(name "{pin_name}"'
        expected_number = f'(number "{pin_number}"'
        if not any(expected_name in line and expected_number in line for line in block.splitlines()):
            fail(f"{symbol_name} is missing JPB1 pin {pin_number} {pin_name}")

    for mf_identifier in (
        "MF_A_PIN1_51_END",
        "MF_B_PIN1_51_END",
        "MF_A_PIN50_100_END",
        "MF_B_PIN50_100_END",
    ):
        if f'(number "{mf_identifier}"' not in block:
            fail(f"{symbol_name} is missing approved GND MF pin {mf_identifier}")
    if '(property "Footprint" "PB100:FX18-100P-0.8SV10_Hirose"' not in block:
        fail(f"{symbol_name} must bind the reviewed Hirose FX18-100P footprint")


def validate_instance_symbol_map() -> None:
    path = PB100_DIR / "PB-100-schematic-instance-symbol-map.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty instance-symbol map: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in INSTANCE_SYMBOL_MAP_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    instance_path = PB100_DIR / "PB-100-schematic-instance-plan.csv"
    instance_rows = list(csv.DictReader(instance_path.open(newline="", encoding="utf-8")))
    instance_refs = {row["Ref"].strip() for row in instance_rows}
    map_refs = {row["Ref"].strip() for row in rows}
    missing_refs = sorted(instance_refs - map_refs)
    extra_refs = sorted(map_refs - instance_refs)
    if missing_refs:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing instance refs: "
            f"{', '.join(missing_refs)}"
        )
    if extra_refs:
        fail(
            f"{path.relative_to(REPO_ROOT)} has refs not in instance plan: "
            f"{', '.join(extra_refs)}"
        )

    readiness_rows = list(
        csv.DictReader((PB100_DIR / "PB-100-symbol-mpn-readiness.csv").open(newline="", encoding="utf-8"))
    )
    readiness_keys = {row["Symbol key"].strip() for row in readiness_rows}
    worklist_rows = list(
        csv.DictReader((PB100_DIR / "PB-100-symbol-capture-worklist.csv").open(newline="", encoding="utf-8"))
    )
    worklist_by_key = {row["Symbol key"].strip(): row for row in worklist_rows}
    symbol_text = read_text(KICAD_DIR / "lib" / "PB100.kicad_sym")

    for row_number, row in enumerate(rows, 2):
        ref = row["Ref"].strip()
        symbol_key = row["Symbol key"].strip()
        symbol_name = row["Concrete symbol name"].strip()
        symbol_state = row["Symbol state"].strip()
        if symbol_key not in readiness_keys:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown symbol key {symbol_key}")
        worklist_row = worklist_by_key.get(symbol_key)
        if worklist_row is None:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: symbol key {symbol_key} is missing worklist row")
        can1_concrete_symbols = {
            "PB100_CAN1_TX_DISABLE_PRELIM",
            "PB100_CAN1_SAFETY_RESISTOR_PRELIM",
            "PB100_CAN1_TX_DNP_LINK_PRELIM",
            "PB100_SN74LVC1G125_Q1_DBV_PRELIM",
        }
        if symbol_key == "CAN1_TX_DISABLE" and symbol_name in can1_concrete_symbols:
            pass
        elif symbol_name != worklist_row["Concrete symbol name"].strip():
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: {ref} maps to {symbol_name}, "
                f"but worklist uses {worklist_row['Concrete symbol name'].strip()}"
            )
        if symbol_state not in {"Created", "Pending"}:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: Symbol state must be Created or Pending")
        symbol_present = f'(symbol "{symbol_name}"' in symbol_text
        if symbol_state == "Created" and not symbol_present and symbol_name not in PIN_MAP_EVIDENCE_SYMBOLS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: created symbol is missing: {symbol_name}")
        if symbol_state == "Pending" and symbol_present:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: pending symbol is already present: {symbol_name}")
        if ref == "Q102" and not all(
            token in row["Notes"] for token in ("BUK7S1R2-80M", "SOA", "thermal")
        ):
            fail("Q102 instance-symbol map must preserve selected 80 V SOA/thermal evidence")


def validate_sheet_reference_map() -> None:
    path = PB100_DIR / "PB-100-schematic-sheet-reference-map.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty sheet-reference map: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in SHEET_REFERENCE_MAP_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    instance_map_path = PB100_DIR / "PB-100-schematic-instance-symbol-map.csv"
    instance_rows = list(csv.DictReader(instance_map_path.open(newline="", encoding="utf-8")))
    symbol_by_ref = {row["Ref"].strip(): row["Symbol key"].strip() for row in instance_rows}
    expected_refs = set(symbol_by_ref)
    seen_refs = set()
    allowed_virtual_sheets = {"cross-sheet-review"}
    allowed_statuses = {"Planned", "Pending symbol", "Review-defined"}

    for row_number, row in enumerate(rows, 2):
        sheet_file = row["Sheet file"].strip()
        ref = row["Ref"].strip()
        symbol_key = row["Symbol key"].strip()
        capture_status = row["Capture status"].strip()
        if ref in seen_refs:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate ref {ref}")
        seen_refs.add(ref)
        if ref not in symbol_by_ref:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown instance ref {ref}")
        if symbol_key != symbol_by_ref[ref]:
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: {ref} uses {symbol_key}, "
                f"but instance-symbol map uses {symbol_by_ref[ref]}"
            )
        if capture_status not in allowed_statuses:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: invalid capture status {capture_status}")
        if not row["Notes"].strip():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty Notes")
        if sheet_file not in allowed_virtual_sheets:
            sheet_path = KICAD_DIR / "sheets" / sheet_file
            if not sheet_path.exists():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: missing sheet file {sheet_file}")
        if ref == "TP1..TPn" and sheet_file != "cross-sheet-review":
            fail("TP1..TPn must remain cross-sheet-review until exact test point locations close")

    missing_refs = sorted(expected_refs - seen_refs)
    extra_refs = sorted(seen_refs - expected_refs)
    if missing_refs:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing refs from instance-symbol map: "
            f"{', '.join(missing_refs)}"
        )
    if extra_refs:
        fail(
            f"{path.relative_to(REPO_ROOT)} has refs not in instance-symbol map: "
            f"{', '.join(extra_refs)}"
        )


def validate_kicad_sheet_manifest() -> None:
    path = PB100_DIR / "PB-100-kicad-sheet-manifest.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty KiCad sheet manifest: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in KICAD_SHEET_MANIFEST_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    expected_sheet_files = {"PB-100.kicad_sch"} | {
        sheet_path.name for sheet_path in sorted((KICAD_DIR / "sheets").glob("*.kicad_sch"))
    }
    manifest_sheet_files = {row["Sheet file"].strip() for row in rows}
    missing_sheets = sorted(expected_sheet_files - manifest_sheet_files)
    extra_sheets = sorted(manifest_sheet_files - expected_sheet_files)
    if missing_sheets:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing KiCad sheets: "
            f"{', '.join(missing_sheets)}"
        )
    if extra_sheets:
        fail(
            f"{path.relative_to(REPO_ROOT)} lists unknown KiCad sheets: "
            f"{', '.join(extra_sheets)}"
        )

    allowed_kinds = {"top", "child"}
    allowed_statuses = {"Scaffold", "Template scaffold"}
    for row_number, row in enumerate(rows, 2):
        sheet_file = row["Sheet file"].strip()
        sheet_kind = row["Sheet kind"].strip()
        if sheet_kind not in allowed_kinds:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: invalid sheet kind {sheet_kind}")
        if row["Status"].strip() not in allowed_statuses:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: invalid sheet status {row['Status'].strip()}")
        for column in ("Purpose", "Primary artifacts", "Capture gate"):
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        if sheet_kind == "top" and sheet_file != "PB-100.kicad_sch":
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: only PB-100.kicad_sch may be top")
        if sheet_kind == "child" and not (KICAD_DIR / "sheets" / sheet_file).exists():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: child sheet file is missing: {sheet_file}")

    manifest_rows_by_sheet = {row["Sheet file"].strip(): row for row in rows}
    capture_queue_rows = list(
        csv.DictReader((PB100_DIR / "PB-100-schematic-capture-work-queue.csv").open(newline="", encoding="utf-8"))
    )
    capture_rows_by_work_item = {row["Work item"].strip(): row for row in capture_queue_rows}
    for work_item, tokens in CAPTURE_TRACE_ARTIFACTS_BY_WORK_ITEM.items():
        if work_item not in capture_rows_by_work_item:
            fail(f"KiCad sheet manifest trace check is missing capture work item {work_item}")
        sheet_file = capture_rows_by_work_item[work_item]["Sheet file"].strip()
        if sheet_file not in manifest_rows_by_sheet:
            fail(f"{path.relative_to(REPO_ROOT)} must include manifest row for {sheet_file}")
        primary_artifacts = manifest_rows_by_sheet[sheet_file]["Primary artifacts"]
        for token in tokens:
            if token not in primary_artifacts:
                fail(f"{path.relative_to(REPO_ROOT)} {sheet_file} row must include {token}")

    sheet_reference_rows = list(
        csv.DictReader((PB100_DIR / "PB-100-schematic-sheet-reference-map.csv").open(newline="", encoding="utf-8"))
    )
    referenced_sheets = {
        row["Sheet file"].strip()
        for row in sheet_reference_rows
        if row["Sheet file"].strip() != "cross-sheet-review"
    }
    missing_referenced = sorted(referenced_sheets - manifest_sheet_files)
    if missing_referenced:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing sheets used by sheet-reference map: "
            f"{', '.join(missing_referenced)}"
        )


def validate_net_domain_plan() -> None:
    path = PB100_DIR / "PB-100-schematic-net-domain-plan.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty schematic net-domain plan: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in NET_DOMAIN_PLAN_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    sheet_manifest_path = PB100_DIR / "PB-100-kicad-sheet-manifest.csv"
    sheet_manifest_rows = list(csv.DictReader(sheet_manifest_path.open(newline="", encoding="utf-8")))
    manifest_sheets = {row["Sheet file"].strip() for row in sheet_manifest_rows}
    seen_patterns = set()
    for row_number, row in enumerate(rows, 2):
        net_pattern = row["Net pattern"].strip()
        if not net_pattern:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty Net pattern")
        if net_pattern in seen_patterns:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate Net pattern {net_pattern}")
        seen_patterns.add(net_pattern)
        for forbidden_token in FORBIDDEN_ROLE_TOKENS:
            if forbidden_token in net_pattern:
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: role token in net pattern {net_pattern}")
        for column in ("Domain", "Direction", "Default state", "Safety rule"):
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        primary_sheet = row["Primary sheet"].strip()
        if primary_sheet not in manifest_sheets:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown Primary sheet {primary_sheet}")

    missing_patterns = sorted(REQUIRED_NET_PATTERNS - seen_patterns)
    if missing_patterns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required net patterns: "
            f"{', '.join(missing_patterns)}"
        )

    can_tx_rows = [row for row in rows if row["Net pattern"].strip() == "CAN1_TX_ROUTE"]
    if len(can_tx_rows) != 1:
        fail("CAN1_TX_ROUTE must appear exactly once in schematic net-domain plan")
    can_tx_row = can_tx_rows[0]
    default_state = can_tx_row["Default state"].lower()
    safety_rule = can_tx_row["Safety rule"].lower()
    if "dnp/open" not in default_state:
        fail("CAN1_TX_ROUTE default state must remain DNP/open")
    if "future adr" not in safety_rule:
        fail("CAN1_TX_ROUTE safety rule must require a future ADR")


def validate_bom_symbol_map() -> None:
    path = REPO_ROOT / "production" / "bom" / "pb100_symbol_bom_map.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty PB-100 symbol BOM map: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in BOM_SYMBOL_MAP_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    readiness_rows = list(
        csv.DictReader((PB100_DIR / "PB-100-symbol-mpn-readiness.csv").open(newline="", encoding="utf-8"))
    )
    readiness_keys = {row["Symbol key"].strip() for row in readiness_rows}
    critical_keys = {
        row["Symbol key"].strip()
        for row in readiness_rows
        if row["Critical"].strip().lower() == "yes"
    }

    bom_items_by_file: dict[str, set[str]] = {}
    for bom_file in ALLOWED_BOM_FILES:
        bom_path = REPO_ROOT / "production" / "bom" / bom_file
        validate_csv(bom_path)
        bom_rows = list(csv.DictReader(bom_path.open(newline="", encoding="utf-8")))
        bom_items_by_file[bom_file] = {row["Item"].strip() for row in bom_rows}

    seen_keys = set()
    for row_number, row in enumerate(rows, 2):
        symbol_key = row["Symbol key"].strip()
        bom_file = row["BOM file"].strip()
        bom_item = row["BOM item"].strip()
        if symbol_key not in readiness_keys:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown symbol key {symbol_key}")
        if symbol_key in seen_keys:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate symbol key {symbol_key}")
        seen_keys.add(symbol_key)
        if bom_file not in ALLOWED_BOM_FILES:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unsupported BOM file {bom_file}")
        if bom_item not in bom_items_by_file[bom_file]:
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: BOM item {bom_item} "
                f"is missing from production/bom/{bom_file}"
            )
        for column in ("Qty basis", "Population", "Assembly owner", "Status", "Notes"):
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        if bom_file == "factory_bom_draft.csv" and row["Assembly owner"].strip() != "Factory":
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: factory BOM row must use Factory owner")
        if bom_file == "garage_bom_draft.csv" and row["Assembly owner"].strip() != "Garage":
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: garage BOM row must use Garage owner")

    missing_keys = sorted(readiness_keys - seen_keys)
    if missing_keys:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing symbol keys: "
            f"{', '.join(missing_keys)}"
        )

    missing_critical = sorted(critical_keys - seen_keys)
    if missing_critical:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing critical symbol keys: "
            f"{', '.join(missing_critical)}"
        )

    can1_rows = [row for row in rows if row["Symbol key"].strip() == "CAN1_TX_DISABLE"]
    if len(can1_rows) != 1:
        fail("CAN1_TX_DISABLE must appear exactly once in PB-100 symbol BOM map")
    can1_row = can1_rows[0]
    if "dnp/open" not in can1_row["Population"].lower() and "dnp/open" not in can1_row["Notes"].lower():
        fail("CAN1_TX_DISABLE BOM mapping must keep DNP/open explicit")


def validate_schematic_readiness_dashboard() -> None:
    path = PB100_DIR / "PB-100-schematic-readiness-dashboard.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty schematic readiness dashboard: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in SCHEMATIC_READINESS_DASHBOARD_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    seen_areas = set()
    rows_by_area: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        area = row["Area"].strip()
        status = row["Status"].strip()
        if not area:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: missing Area")
        if area in seen_areas:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate Area {area}")
        seen_areas.add(area)
        rows_by_area[area] = row
        if status not in ALLOWED_DASHBOARD_STATUSES:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: invalid Status {status}")
        for column in ("Evidence", "Machine check", "Remaining close work"):
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")

    missing_areas = sorted(REQUIRED_READINESS_AREAS - seen_areas)
    if missing_areas:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing readiness areas: "
            f"{', '.join(missing_areas)}"
        )

    if rows_by_area["Architecture baseline"]["Status"].strip() != "Closed":
        fail("Architecture baseline must remain Closed in schematic readiness dashboard")
    if rows_by_area["PB-100 requirements"]["Status"].strip() != "Closed":
        fail("PB-100 requirements must remain Closed in schematic readiness dashboard")
    freeze_closed = freeze_checklist_status() == "Closed"
    expected_layout_status = "Ready" if freeze_closed else "Blocked"
    if rows_by_area["Layout authorization"]["Status"].strip() != expected_layout_status:
        fail(f"Layout authorization must be {expected_layout_status} for current schematic freeze state")
    if "schematic freeze" not in rows_by_area["Layout authorization"]["Remaining close work"].lower():
        fail("Layout authorization close work must reference schematic freeze")

    symbol_row = rows_by_area["Symbol readiness"]
    expected_symbol_status = "Closed" if freeze_closed else "Conditional"
    if symbol_row["Status"].strip() != expected_symbol_status:
        fail(f"Symbol readiness must be {expected_symbol_status} for current schematic freeze state")
    symbol_close_work = symbol_row["Remaining close work"].lower()
    if "q1" not in symbol_close_work or "40 a" not in symbol_close_work:
        fail("Symbol readiness must mention Q1 and 40 A close work")

    can_row = rows_by_area["CAN1 safety"]
    can_text = " ".join(can_row[column] for column in SCHEMATIC_READINESS_DASHBOARD_COLUMNS).lower()
    if "dnp/open" not in can_text or "future adr" not in can_text:
        fail("CAN1 safety dashboard row must keep DNP/open and future ADR explicit")

    required_dashboard_evidence = {
        "Symbol readiness": (
            "PB-100-input-reverse-package-trace.csv",
            "PB-100-input-reverse-q1-freeze-checklist.csv",
            "PB-100-input-reverse-q1-derivation-precheck.csv",
            "PB-100-input-reverse-q1-closeout-precheck.csv",
        ),
        "Output pin contract": ("PB-100-high-medium-output-baseline-trace.csv", "PB-100-low-current-output-baseline-trace.csv"),
        "Output stage design values": (
            "PB-100-high-medium-output-baseline-trace.csv",
            "PB-100-low-current-output-baseline-trace.csv",
            "PB-100-output-stage-value-freeze-checklist.csv",
            "PB-100-output-stage-value-derivation-precheck.csv",
            "PB-100-output-stage-closeout-precheck.csv",
        ),
        "Input power design values": (
            "PB-100-board-current-budget-trace.csv",
            "PB-100-board-current-budget-freeze-review.csv",
            "PB-100-board-current-budget-design-calculation.md",
            "PB-100-board-current-budget-value-freeze-checklist.csv",
            "PB-100-board-current-budget-value-derivation-precheck.csv",
            "PB-100-input-reverse-package-trace.csv",
            "PB-100-input-reverse-q1-derivation-precheck.csv",
            "PB-100-input-reverse-q1-closeout-precheck.csv",
            "PB-100-tvs-load-dump-margin-trace.csv",
            "PB-100-tvs-load-dump-freeze-review.csv",
            "PB-100-tvs-overshoot-escape-checklist.csv",
            "PB-100-tvs-overshoot-validation-precheck.csv",
        ),
        "Logic power design values": (
            "PB-100-logic-power-rail-trace.csv",
            "PB-100-logic-power-freeze-review.csv",
            "PB-100-logic-power-value-freeze-checklist.csv",
            "PB-100-logic-power-value-derivation-precheck.csv",
            "PB-100-logic-power-closeout-precheck.csv",
        ),
        "Input protection contract": (
            "PB-100-input-reverse-package-trace.csv",
            "PB-100-input-reverse-q1-freeze-checklist.csv",
            "PB-100-input-reverse-q1-derivation-precheck.csv",
            "PB-100-input-reverse-q1-closeout-precheck.csv",
        ),
        "Current monitor template": (
            "PB-100-current-monitor-pin-template.csv",
            "PB-100-current-telemetry-value-freeze-checklist.csv",
            "PB-100-current-telemetry-value-derivation-precheck.csv",
            "PB-100-current-telemetry-closeout-precheck.csv",
        ),
        "Hardware capability manifest": (
            "PB-100-current-telemetry-trace.csv",
            "PB-100-thermal-telemetry-trace.csv",
            "PB-100-can1-tx-disable-trace.csv",
        ),
        "Logic power values": (
            "PB-100-logic-power-rail-trace.csv",
            "PB-100-logic-power-freeze-review.csv",
            "PB-100-logic-power-value-freeze-checklist.csv",
            "PB-100-logic-power-value-derivation-precheck.csv",
            "PB-100-logic-power-closeout-precheck.csv",
        ),
        "B2B LB-100 pin precheck": (
            "PB-100-b2b-lb100-pin-binding-precheck.md",
            "PB-100-b2b-lb100-pin-audit-checklist.csv",
            "PB-100-b2b-interface-freeze-checklist.csv",
            "PB-100-b2b-interface-closeout-precheck.csv",
        ),
        "BOM synchronization": (
            "PB-100-assembly-readiness-trace.csv",
            "PB-100-factory-assembly-freeze-checklist.csv",
            "PB-100-factory-assembly-sourcing-precheck.csv",
            "PB-100-factory-assembly-closeout-precheck.csv",
            "PB-100-garage-install-freeze-checklist.csv",
            "PB-100-garage-install-closeout-precheck.csv",
        ),
        "Assembly sourcing recheck": (
            "PB-100-assembly-readiness-trace.csv",
            "PB-100-factory-assembly-freeze-checklist.csv",
            "PB-100-factory-assembly-sourcing-precheck.csv",
            "PB-100-factory-assembly-closeout-precheck.csv",
            "PB-100-garage-install-freeze-checklist.csv",
            "PB-100-garage-install-closeout-precheck.csv",
        ),
        "CAN1 safety": (
            "PB-100-can1-tx-disable-trace.csv",
            "PB-100-can1-production-dnp-review.csv",
            "PB-100-can1-default-disable-freeze-checklist.csv",
            "PB-100-can1-default-disable-derivation-precheck.csv",
            "PB-100-can1-default-disable-closeout-precheck.csv",
        ),
        "CAN1 safety verification": (
            "PB-100-can1-tx-disable-trace.csv",
            "PB-100-can1-reset-bench-checklist.csv",
            "PB-100-can1-default-disable-freeze-checklist.csv",
            "PB-100-can1-default-disable-derivation-precheck.csv",
            "PB-100-can1-default-disable-closeout-precheck.csv",
        ),
    }
    for area, tokens in required_dashboard_evidence.items():
        evidence = rows_by_area[area]["Evidence"]
        for token in tokens:
            if token not in evidence:
                fail(f"readiness dashboard evidence for {area} must include {token}")


def freeze_checklist_rows_by_gate() -> dict[str, dict[str, str]]:
    text = read_text(PB100_DIR / "PB-100-schematic-freeze-checklist.md")
    rows_by_gate: dict[str, dict[str, str]] = {}
    for line in text.splitlines():
        if not line.startswith("| "):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 4 or cells[0] in {"Gate", "---"}:
            continue
        gate, status, evidence, close_condition = cells[0], cells[1], cells[2], cells[3]
        if status in {"Closed", "Conditional", "Open", "Blocked"}:
            rows_by_gate[gate] = {
                "Status": status,
                "Evidence": evidence,
                "Close condition": close_condition,
            }
    return rows_by_gate


def freeze_checklist_status() -> str:
    text = read_text(PB100_DIR / "PB-100-schematic-freeze-checklist.md")
    match = re.search(r"^Status:\s*(.+?)\s*$", text, flags=re.MULTILINE)
    if match is None:
        fail("PB-100 schematic freeze checklist must include top-level Status")
    return match.group(1).strip()


def freeze_checklist_gates_by_status() -> dict[str, str]:
    rows_by_gate = freeze_checklist_rows_by_gate()
    gates_by_status = {gate: row["Status"] for gate, row in rows_by_gate.items()}
    return gates_by_status


def validate_schematic_freeze_gap_register() -> None:
    path = PB100_DIR / "PB-100-schematic-freeze-gap-register.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty schematic freeze gap register: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in SCHEMATIC_FREEZE_GAP_REGISTER_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    checklist_rows_by_gate = freeze_checklist_rows_by_gate()
    gates_by_status = {gate: row["Status"] for gate, row in checklist_rows_by_gate.items()}
    tracked_gates = set(pbrel_id_by_gate())
    seen_gates = set()
    rows_by_gate: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        gate = row["Gate"].strip()
        status = row["Status"].strip()
        if gate in seen_gates:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate Gate {gate}")
        seen_gates.add(gate)
        rows_by_gate[gate] = row
        if gate not in gates_by_status:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown freeze checklist gate {gate}")
        if gate not in tracked_gates:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: gate {gate} is not a tracked PB freeze gate")
        if status not in {"Closed", "Conditional", "Open", "Blocked"}:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: invalid gap status {status}")
        if status != gates_by_status[gate]:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: gap status must match checklist status {gates_by_status[gate]}")
        for column in (
            "Close evidence required",
            "Primary gap artifact",
            "Validator coverage",
            "Next close action",
        ):
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")

    missing_gates = sorted(tracked_gates - seen_gates)
    extra_gates = sorted(seen_gates - tracked_gates)
    if missing_gates:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing tracked PB freeze gates: "
            f"{', '.join(missing_gates)}"
        )
    if extra_gates:
        fail(
            f"{path.relative_to(REPO_ROOT)} has non-tracked PB freeze gates: "
            f"{', '.join(extra_gates)}"
        )

    required_checklist_evidence = {
        "CAN1 safety policy": (
            "PB-100-can1-tx-disable-trace.csv",
            "PB-100-can1-safety-verification.csv",
            "PB-100-can1-production-dnp-review.csv",
            "PB-100-can1-default-disable-freeze-checklist.csv",
            "PB-100-can1-default-disable-derivation-precheck.csv",
            "PB-100-can1-default-disable-closeout-precheck.csv",
        ),
        "Board current budget": (
            "PB-100-board-current-budget-trace.csv",
            "PB-100-board-current-budget-freeze-review.csv",
            "PB-100-board-current-budget-design-calculation.md",
            "PB-100-board-current-budget-value-freeze-checklist.csv",
            "PB-100-board-current-budget-value-derivation-precheck.csv",
            "PB-100-board-current-budget-closeout-precheck.csv",
            "PB-100-input-power-design-values.csv",
        ),
        "Board-to-board interface": (
            "PB-100-b2b-interface-trace.csv",
            "PB-100-b2b-lb100-resource-binding.csv",
            "PB-100-b2b-lb100-pin-audit-checklist.csv",
            "PB-100-b2b-interface-freeze-checklist.csv",
            "PB-100-b2b-interface-closeout-precheck.csv",
            "PB-100-b2b-pin-map.csv",
        ),
        "High/medium output stage": (
            "PB-100-high-medium-output-baseline-trace.csv",
            "PB-100-high-medium-output-freeze-review.csv",
            "PB-100-output-stage-value-freeze-checklist.csv",
            "PB-100-output-stage-value-derivation-precheck.csv",
            "PB-100-output-stage-closeout-precheck.csv",
            "PB-100-out2-soa.md",
        ),
        "Low-current output stage": (
            "PB-100-low-current-output-baseline-trace.csv",
            "PB-100-low-current-output-freeze-review.csv",
            "PB-100-output-stage-value-freeze-checklist.csv",
            "PB-100-output-stage-value-derivation-precheck.csv",
            "PB-100-output-stage-closeout-precheck.csv",
            "ADR-0011",
        ),
        "Input reverse protection": (
            "PB-100-input-reverse-package-trace.csv",
            "PB-100-input-reverse-freeze-review.csv",
            "PB-100-input-reverse-q1-freeze-checklist.csv",
            "PB-100-input-reverse-q1-derivation-precheck.csv",
            "PB-100-input-reverse-q1-closeout-precheck.csv",
            "PB-100-input-reverse-protection.md",
        ),
        "TVS/load-dump protection": (
            "PB-100-tvs-load-dump-margin-trace.csv",
            "PB-100-tvs-load-dump-freeze-review.csv",
            "PB-100-tvs-overshoot-escape-checklist.csv",
            "PB-100-tvs-overshoot-validation-precheck.csv",
            "PB-100-protection-validation.csv",
        ),
        "Logic power rails": (
            "PB-100-logic-power-rail-trace.csv",
            "PB-100-logic-power-freeze-review.csv",
            "PB-100-logic-power-value-freeze-checklist.csv",
            "PB-100-logic-power-value-derivation-precheck.csv",
            "PB-100-logic-power-closeout-precheck.csv",
            "PB-100-logic-power-budget.csv",
        ),
        "Current telemetry": (
            "PB-100-current-telemetry-trace.csv",
            "PB-100-current-telemetry-freeze-review.csv",
            "PB-100-current-telemetry-value-freeze-checklist.csv",
            "PB-100-current-telemetry-value-derivation-precheck.csv",
            "PB-100-current-telemetry-closeout-precheck.csv",
            "PB-100-current-telemetry-map.csv",
        ),
        "Thermal telemetry": (
            "PB-100-thermal-telemetry-trace.csv",
            "PB-100-thermal-telemetry-freeze-review.csv",
            "PB-100-thermal-telemetry-value-freeze-checklist.csv",
            "PB-100-thermal-telemetry-value-derivation-precheck.csv",
            "PB-100-thermal-telemetry-closeout-precheck.csv",
            "PB-100-thermal-telemetry-map.csv",
        ),
        "Factory assembly readiness": (
            "PB-100-assembly-readiness-trace.csv",
            "PB-100-factory-assembly-freeze-checklist.csv",
            "PB-100-factory-assembly-sourcing-precheck.csv",
            "PB-100-factory-assembly-closeout-precheck.csv",
            "pb100_sourcing_evidence_snapshot.csv",
        ),
        "Garage assembly readiness": (
            "PB-100-assembly-readiness-trace.csv",
            "PB-100-garage-connector-fuse-plan.md",
            "PB-100-garage-install-freeze-checklist.csv",
            "PB-100-garage-install-sourcing-precheck.csv",
            "PB-100-garage-install-closeout-precheck.csv",
        ),
    }
    for gate, tokens in required_checklist_evidence.items():
        evidence = checklist_rows_by_gate[gate]["Evidence"]
        for token in tokens:
            if token not in evidence:
                fail(f"freeze checklist evidence for {gate} must include {token}")

    can_gap_text = " ".join(rows_by_gate["CAN1 safety policy"].values())
    can_text = can_gap_text.lower()
    if "dnp/open" not in can_text or "default" not in can_text:
        fail("CAN1 safety policy gap must keep DNP/open default explicit")
    for token in (
        "PB-100-can1-tx-disable-trace.csv",
        "PB-100-can1-production-dnp-review.csv",
        "PB-100-can1-reset-bench-checklist.csv",
        "PB-100-can1-default-disable-freeze-checklist.csv",
        "PB-100-can1-default-disable-derivation-precheck.csv",
        "PB-100-can1-default-disable-closeout-precheck.csv",
        "JP_CAN1",
        "U_CAN1",
        "future ADR",
        "explicit hardware action",
    ):
        if token not in can_gap_text:
            fail(f"CAN1 safety policy gap must keep {token} explicit")
    input_text = " ".join(rows_by_gate["Input reverse protection"].values())
    for token in (
        "PB-100-input-reverse-package-trace.csv",
        "PB-100-input-reverse-freeze-review.csv",
        "PB-100-input-reverse-q1-freeze-checklist.csv",
        "PB-100-input-reverse-q1-derivation-precheck.csv",
        "PB-100-input-reverse-q1-closeout-precheck.csv",
        "Q1",
        "40 A",
        "BUK7S1R2-80M",
        "80 V",
        "LFPAK88",
        "SOA",
    ):
        if token not in input_text:
            fail(f"Input reverse protection gap must keep {token} explicit")
    high_medium_text = " ".join(rows_by_gate["High/medium output stage"].values())
    for token in (
        "PB-100-high-medium-output-baseline-trace.csv",
        "PB-100-high-medium-output-freeze-review.csv",
        "PB-100-output-stage-value-freeze-checklist.csv",
        "PB-100-output-stage-value-derivation-precheck.csv",
        "PB-100-output-stage-closeout-precheck.csv",
        "OUT2",
        "SOA",
        "gate drive",
        "sense",
    ):
        if token not in high_medium_text:
            fail(f"High/medium output stage gap must keep {token} explicit")
    low_current_text = " ".join(rows_by_gate["Low-current output stage"].values())
    for token in (
        "PB-100-low-current-output-baseline-trace.csv",
        "PB-100-low-current-output-freeze-review.csv",
        "PB-100-output-stage-value-freeze-checklist.csv",
        "PB-100-output-stage-value-derivation-precheck.csv",
        "PB-100-output-stage-closeout-precheck.csv",
        "OUT5",
        "OUT8",
        "OUT9",
        "no direct 40 V",
    ):
        if token not in low_current_text:
            fail(f"Low-current output stage gap must keep {token} explicit")
    current_budget_text = " ".join(rows_by_gate["Board current budget"].values())
    for token in (
        "PB-100-board-current-budget-trace.csv",
        "PB-100-board-current-budget-freeze-review.csv",
        "PB-100-board-current-budget-design-calculation.md",
        "PB-100-board-current-budget-value-freeze-checklist.csv",
        "PB-100-board-current-budget-value-derivation-precheck.csv",
        "PB-100-board-current-budget-closeout-precheck.csv",
        "40 A",
        "firmware config",
        "shunt",
    ):
        if token not in current_budget_text:
            fail(f"Board current budget gap must keep {token} explicit")
    tvs_text = " ".join(rows_by_gate["TVS/load-dump protection"].values())
    for token in (
        "PB-100-tvs-load-dump-margin-trace.csv",
        "PB-100-tvs-load-dump-freeze-review.csv",
        "PB-100-tvs-overshoot-escape-checklist.csv",
        "PB-100-tvs-overshoot-validation-precheck.csv",
        "PB-100-tvs-overshoot-closeout-precheck.csv",
        "80 V",
        "DO-218AC",
        "overshoot",
        "peak stress",
    ):
        if token not in tvs_text:
            fail(f"TVS/load-dump gap must keep {token} explicit")
    current_telemetry_text = " ".join(rows_by_gate["Current telemetry"].values())
    for token in (
        "PB-100-current-telemetry-trace.csv",
        "PB-100-current-telemetry-freeze-review.csv",
        "PB-100-current-telemetry-value-freeze-checklist.csv",
        "PB-100-current-telemetry-value-derivation-precheck.csv",
        "PB-100-current-telemetry-closeout-precheck.csv",
        "0.5mΩ",
        "ADC or I2C",
        "firmware safety",
    ):
        if token not in current_telemetry_text:
            fail(f"Current telemetry gap must keep {token} explicit")
    thermal_telemetry_text = " ".join(rows_by_gate["Thermal telemetry"].values())
    for token in (
        "PB-100-thermal-telemetry-trace.csv",
        "PB-100-thermal-telemetry-freeze-review.csv",
        "PB-100-thermal-telemetry-value-freeze-checklist.csv",
        "PB-100-thermal-telemetry-value-derivation-precheck.csv",
        "PB-100-thermal-telemetry-closeout-precheck.csv",
        "NTCGS103JF103FT8",
        "self-heating",
        "firmware thresholds",
    ):
        if token not in thermal_telemetry_text:
            fail(f"Thermal telemetry gap must keep {token} explicit")
    logic_power_text = " ".join(rows_by_gate["Logic power rails"].values())
    for token in (
        "PB-100-logic-power-rail-trace.csv",
        "PB-100-logic-power-freeze-review.csv",
        "PB-100-logic-power-value-freeze-checklist.csv",
        "PB-100-logic-power-value-derivation-precheck.csv",
        "PB-100-logic-power-closeout-precheck.csv",
        "1 A",
        "power-good",
        "UVLO",
    ):
        if token not in logic_power_text:
            fail(f"Logic power rails gap must keep {token} explicit")
    b2b_text = " ".join(rows_by_gate["Board-to-board interface"].values())
    for token in (
        "PB-100-b2b-interface-trace.csv",
        "PB-100-b2b-lb100-resource-binding.csv",
        "PB-100-b2b-lb100-pin-audit-checklist.csv",
        "PB-100-b2b-interface-freeze-checklist.csv",
        "PB-100-b2b-interface-closeout-precheck.csv",
        "FX18-100P-0.8SV10",
        "FX18-100S-0.8SV20",
        "exact LB-100 MCU pin binding",
    ):
        if token not in b2b_text:
            fail(f"Board-to-board interface gap must keep {token} explicit")
    factory_text = " ".join(rows_by_gate["Factory assembly readiness"].values()).lower()
    if (
        "pb-100-assembly-readiness-trace.csv" not in factory_text
        or "pb-100-factory-assembly-freeze-checklist.csv" not in factory_text
        or "pb-100-factory-assembly-sourcing-precheck.csv" not in factory_text
        or "pb-100-factory-assembly-closeout-precheck.csv" not in factory_text
        or "assembly" not in factory_text
        or "alternat" not in factory_text
    ):
        fail("Factory assembly readiness gap must keep assembly and alternatives explicit")
    garage_text = " ".join(rows_by_gate["Garage assembly readiness"].values()).lower()
    if (
        "pb-100-assembly-readiness-trace.csv" not in garage_text
        or "pb-100-garage-install-freeze-checklist.csv" not in garage_text
        or "pb-100-garage-install-sourcing-precheck.csv" not in garage_text
        or "pb-100-garage-install-closeout-precheck.csv" not in garage_text
        or "garage" not in garage_text
        or "user" not in garage_text
    ):
        fail("Garage assembly readiness gap must keep garage/user scope explicit")


def required_closeout_artifact_by_gate() -> dict[str, str]:
    return {
        "CAN1 safety policy": "pb-100-can1-default-disable-closeout-precheck.csv",
        "Board current budget": "pb-100-board-current-budget-closeout-precheck.csv",
        "Board-to-board interface": "pb-100-b2b-interface-closeout-precheck.csv",
        "High/medium output stage": "pb-100-output-stage-closeout-precheck.csv",
        "Low-current output stage": "pb-100-output-stage-closeout-precheck.csv",
        "Input reverse protection": "pb-100-input-reverse-q1-closeout-precheck.csv",
        "TVS/load-dump protection": "pb-100-tvs-overshoot-closeout-precheck.csv",
        "Logic power rails": "pb-100-logic-power-closeout-precheck.csv",
        "Current telemetry": "pb-100-current-telemetry-closeout-precheck.csv",
        "Thermal telemetry": "pb-100-thermal-telemetry-closeout-precheck.csv",
        "Factory assembly readiness": "pb-100-factory-assembly-closeout-precheck.csv",
        "Garage assembly readiness": "pb-100-garage-install-closeout-precheck.csv",
    }


def pbrel_id_by_gate() -> dict[str, str]:
    return {
        "CAN1 safety policy": "PBREL-001",
        "Board current budget": "PBREL-002",
        "Board-to-board interface": "PBREL-003",
        "High/medium output stage": "PBREL-004",
        "Low-current output stage": "PBREL-005",
        "Input reverse protection": "PBREL-006",
        "TVS/load-dump protection": "PBREL-007",
        "Logic power rails": "PBREL-008",
        "Current telemetry": "PBREL-009",
        "Thermal telemetry": "PBREL-010",
        "Factory assembly readiness": "PBREL-011",
        "Garage assembly readiness": "PBREL-012",
    }


def engineering_blocker_closeout_statuses() -> dict[str, str]:
    path = REPO_ROOT / ENGINEERING_BLOCKER_CLOSEOUT
    if not path.exists():
        return {}
    text = read_text(path)
    statuses: dict[str, str] = {}
    for blocker_id in pbrel_id_by_gate().values():
        marker = f"## {blocker_id} "
        marker_index = text.find(marker)
        if marker_index < 0:
            continue
        next_marker_index = text.find("\n## PBREL-", marker_index + len(marker))
        section = text[marker_index:] if next_marker_index < 0 else text[marker_index:next_marker_index]
        status_match = re.search(r"Closeout status:\s*([A-Za-z -]+)\.", section)
        if status_match:
            statuses[blocker_id] = status_match.group(1).strip()
    return statuses


def validate_engineering_blocker_closeout() -> None:
    path = REPO_ROOT / ENGINEERING_BLOCKER_CLOSEOUT
    text = read_text(path)
    normalized_text = re.sub(r"\s+", " ", text)
    lower_text = text.lower()
    if "does not authorize pcb layout" not in lower_text:
        fail(f"{path.relative_to(REPO_ROOT)} must explicitly avoid PCB layout authorization")
    for token in (
        "PB-100.kicad_pcb",
        "Gerbers",
        "drills",
        "pick-place",
        "BOM/CPL",
        "manufacturing ZIP",
        "PCBA order",
    ):
        if token not in text and token not in normalized_text:
            fail(f"{path.relative_to(REPO_ROOT)} must keep no-layout token {token}")

    common_section_tokens = (
        "Closeout status:",
        "Why blocker existed",
        "Candidate comparison",
        "Recommended solution",
        "Risks",
        "Alternatives",
        "Cost impact",
        "Thermal impact",
        "Production impact",
        "Field reliability impact",
        "Why this component/solution",
        "Why not alternative A",
        "Why not alternative B",
        "Expected lifetime",
        "Operating margin",
        "Maximum junction temperature",
        "Availability",
        "Automotive qualification",
        "LCSC availability",
        "PCBWay/JLCPCB compatibility",
        "Known risks",
        "Evidence and calculations",
        "Datasheet and sourcing evidence",
        "Post-prototype validation",
        "No-layout boundary",
    )
    specific_tokens_by_id = {
        "PBREL-001": (
            "CAN1_TX_ROUTE",
            "DNP/open",
            "future ADR",
            "SN74LVC1G125-Q1",
            "PB-BENCH-012",
        ),
        "PBREL-002": (
            "40 A",
            "50 A",
            "0.5mΩ",
            "CSS4J-4026R-L500F",
            "PB-BENCH-006",
            "PB-BENCH-010",
        ),
        "PBREL-003": (
            "FX18-100P-0.8SV10",
            "FX18-100S-0.8SV20",
            "STM32H563VITx",
            "JPB1",
        ),
        "PBREL-004": (
            "TPS48110AQDGXRQ1",
            "BUK7S1R2-80M",
            "OUT2",
            "SOA",
        ),
        "PBREL-005": (
            "OUT5",
            "OUT8",
            "OUT9",
            "ADR-0011",
            "no direct 40 V",
        ),
        "PBREL-006": (
            "LM74700QDBVRQ1",
            "BUK7S1R2-80M",
            "40 A",
            "Q1",
        ),
        "PBREL-007": (
            "SM8S33AHM3/I",
            "53.3 V",
            "80 V",
            "overshoot",
        ),
        "PBREL-008": (
            "LM5164QDDATQ1",
            "PB_5V_OUT",
            "100 V",
            "1 A",
            "LM5013-Q1",
        ),
        "PBREL-009": (
            "INA228-Q1",
            "0.5mΩ",
            "±40.96 mV",
            "PB-BENCH-005",
        ),
        "PBREL-010": (
            "NTCGS103JF103FT8",
            "TEMP_PCB",
            "TEMP_PWR_A",
            "TEMP_PWR_B",
            "PB-BENCH-009",
        ),
        "PBREL-011": (
            "JLCPCB",
            "PCBWay",
            "DNP/open",
            "PowerPAK",
            "TOLL",
            "LFPAK88",
            "DO-218AC",
            "FX18",
        ),
        "PBREL-012": (
            "TE DEUTSCH",
            "DTP",
            "DT",
            "Littelfuse",
            "MAXI",
            "garage-installed",
        ),
    }
    blocker_rows = list(
        csv.DictReader(
            (PB100_DIR / "PB-100-board-release-blocker-register.csv").open(
                newline="", encoding="utf-8"
            )
        )
    )
    expected_status_by_id = {
        row["Blocker ID"].strip(): row["Status"].strip() for row in blocker_rows
    }
    for gate, blocker_id in pbrel_id_by_gate().items():
        marker = f"## {blocker_id} — {gate}"
        marker_index = text.find(marker)
        if marker_index < 0:
            fail(f"{path.relative_to(REPO_ROOT)} is missing closeout section {marker}")
        next_marker_index = text.find("\n## PBREL-", marker_index + len(marker))
        section = text[marker_index:] if next_marker_index < 0 else text[marker_index:next_marker_index]
        normalized_section = re.sub(r"\s+", " ", section)
        status_match = re.search(r"Closeout status:\s*([A-Za-z -]+)\.", section)
        if status_match is None:
            fail(f"{path.relative_to(REPO_ROOT)} {blocker_id} section must include a closeout status")
        actual_status = status_match.group(1).strip()
        expected_status = expected_status_by_id.get(blocker_id)
        if actual_status != expected_status:
            fail(
                f"{path.relative_to(REPO_ROOT)} {blocker_id} status {actual_status} "
                f"does not match blocker register status {expected_status}"
            )
        for token in common_section_tokens + specific_tokens_by_id[blocker_id]:
            if token not in section and token not in normalized_section:
                fail(f"{path.relative_to(REPO_ROOT)} {blocker_id} section must include {token}")


def validate_schematic_review_closeout() -> None:
    path = REPO_ROOT / SCHEMATIC_REVIEW_CLOSEOUT
    text = read_text(path)
    normalized_text = " ".join(text.split())
    for token in (
        "Status: Retracted; schematic freeze is Open",
        "Review date: 2026-07-20",
        "does not create KiCad PCB layout",
        "PB-100.kicad_pcb",
        "Gerbers",
        "drills",
        "pick-place",
        "BOM/CPL",
        "manufacturing ZIP",
        "PCBA orders",
        "closure was retracted",
        "80 V MOSFET baseline",
        "actual overshoot",
        "FX18 MF/TH mechanics",
        "post-prototype",
        "board-print remains NO-GO",
        "CAN1_TX_ROUTE",
        "DNP/open",
        "40 A default total current budget",
        "JPB1",
        "TPS48110AQDGXRQ1",
        "ADR-0011",
        "SM8S33AHM3/I",
        "80 V MOSFET",
        "LM74700QDBVRQ1",
        "LM5164QDDATQ1",
        "INA228-Q1",
        "TEMP_PCB",
        "TEMP_PWR_A",
        "TEMP_PWR_B",
        "JLCPCB/PCBWay",
        "garage",
        "PB-100-engineering-blocker-closeout.md",
        "PB-100-post-prototype-validation-gate.csv",
    ):
        if token not in text and token not in normalized_text:
            fail(f"{path.relative_to(REPO_ROOT)} must include {token}")


def validate_board_release_blocker_register() -> None:
    path = PB100_DIR / "PB-100-board-release-blocker-register.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty board release blocker register: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in BOARD_RELEASE_BLOCKER_REGISTER_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    gates_by_status = freeze_checklist_gates_by_status()
    required_closeout_by_gate = required_closeout_artifact_by_gate()
    expected_blocker_id_by_gate = pbrel_id_by_gate()
    closeout_statuses = engineering_blocker_closeout_statuses()
    allowed_statuses = {"Closed", "Conditional", "Open", "Blocked"}
    seen_gates = set()
    seen_blockers = set()
    for row_number, row in enumerate(rows, 2):
        gate = row["Gate"].strip()
        blocker_id = row["Blocker ID"].strip()
        status = row["Status"].strip()
        if gate in seen_gates:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate Gate {gate}")
        seen_gates.add(gate)
        if blocker_id in seen_blockers:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate Blocker ID {blocker_id}")
        seen_blockers.add(blocker_id)
        if gate not in gates_by_status:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown freeze checklist gate {gate}")
        if gate not in expected_blocker_id_by_gate:
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: gate {gate} is not a tracked PBREL gate"
            )
        expected_blocker_id = expected_blocker_id_by_gate[gate]
        if blocker_id != expected_blocker_id:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: Blocker ID must be {expected_blocker_id}")
        if not blocker_id.startswith("PBREL-"):
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: Blocker ID must start with PBREL-")
        if status not in allowed_statuses:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: invalid release blocker status {status}")
        if status == "Closed" and closeout_statuses.get(blocker_id) != "Closed":
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: Closed blocker {blocker_id} "
                f"must have Closed closeout in {ENGINEERING_BLOCKER_CLOSEOUT}"
            )
        if gates_by_status[gate] == "Closed" and status != "Closed":
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: closed freeze gate {gate} cannot keep an active blocker")
        for column in BOARD_RELEASE_BLOCKER_REGISTER_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        row_text = " ".join(row.values()).lower()
        if "block" not in row["Layout impact"].lower() or "layout" not in row["Layout impact"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: Layout impact must explicitly block layout")
        if "final" not in row["Required close evidence"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: Required close evidence must require final evidence")
        if "review" not in row_text and "test" not in row_text:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: release blocker must require review or test")
        required_closeout = required_closeout_by_gate.get(gate)
        if required_closeout is None:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: no closeout artifact rule for gate {gate}")
        if required_closeout not in row_text:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: release blocker must reference {required_closeout}")
        validate_no_role_tokens_in_row(path, row_number, row)

    missing_gates = sorted(set(expected_blocker_id_by_gate) - seen_gates)
    extra_gates = sorted(seen_gates - set(expected_blocker_id_by_gate))
    if missing_gates:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing PBREL blocker rows for gates: "
            f"{', '.join(missing_gates)}"
        )
    if extra_gates:
        fail(
            f"{path.relative_to(REPO_ROOT)} has blockers for non-PBREL gates: "
            f"{', '.join(extra_gates)}"
        )


def validate_board_print_closure_matrix() -> None:
    path = PB100_DIR / "PB-100-board-print-closure-matrix.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty board-print closure matrix: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in BOARD_PRINT_CLOSURE_MATRIX_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    blocker_rows = list(
        csv.DictReader((PB100_DIR / "PB-100-board-release-blocker-register.csv").open(newline="", encoding="utf-8"))
    )
    blockers_by_gate = {
        row["Gate"].strip(): row
        for row in blocker_rows
    }
    required_closeout_by_gate = required_closeout_artifact_by_gate()
    allowed_states = {"Closed", "Conditional", "Open", "Blocked"}

    rows_by_gate: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        gate = row["Gate"].strip()
        if gate in rows_by_gate:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate Gate {gate}")
        rows_by_gate[gate] = row
        if gate not in blockers_by_gate:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: gate {gate} has no release blocker row")
        for column in BOARD_PRINT_CLOSURE_MATRIX_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        proof_state = row["Current proof state"].strip()
        if proof_state not in allowed_states:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: invalid Current proof state {proof_state}")
        blocker_row = blockers_by_gate[gate]
        blocker_status = blocker_row["Status"].strip()
        if proof_state != blocker_status:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: Current proof state must match blocker status {blocker_status}")
        blocker_id = blocker_row["Blocker ID"].strip()
        if row["Blocker ID"].strip() != blocker_id:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: Blocker ID must match {blocker_id}")
        required_closeout = required_closeout_by_gate[gate]
        if row["Closeout artifact"].strip().lower() != required_closeout:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: Closeout artifact must be {required_closeout}")
        row_text = " ".join(row.values()).lower()
        if "dated" not in row_text:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: close evidence must require dated evidence")
        if "do not" not in row["Board-print blocked action"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: Board-print blocked action must be explicit")
        for token in ("pb-100.kicad_pcb", "gerbers", "drills", "pick-place", "manufacturing zip"):
            if token not in row["Board-print blocked action"].lower():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: Board-print blocked action must block {token}")
        validate_no_role_tokens_in_row(path, row_number, row)

    missing_gates = sorted(blockers_by_gate.keys() - rows_by_gate.keys())
    extra_gates = sorted(rows_by_gate.keys() - blockers_by_gate.keys())
    if missing_gates:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing release blocker closure rows: "
            f"{', '.join(missing_gates)}"
        )
    if extra_gates:
        fail(
            f"{path.relative_to(REPO_ROOT)} has closure rows without blocker rows: "
            f"{', '.join(extra_gates)}"
        )

    matrix_text = read_text(path)
    for token in (
        "PBREL-001",
        "PBREL-002",
        "PBREL-003",
        "PBREL-004",
        "PBREL-005",
        "PBREL-006",
        "PBREL-007",
        "PBREL-008",
        "PBREL-009",
        "PBREL-010",
        "PBREL-011",
        "PBREL-012",
        "PB-100.kicad_pcb",
        "Gerbers",
        "drills",
        "pick-place",
        "manufacturing ZIP",
        "fabrication package",
        "PCBA order package",
    ):
        if token not in matrix_text:
            fail(f"board-print closure matrix must include {token}")


def validate_output_channel_pin_contract() -> None:
    path = PB100_DIR / "PB-100-output-channel-pin-contract.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty output channel pin contract: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in OUTPUT_CHANNEL_PIN_CONTRACT_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    output_matrix_rows = list(
        csv.DictReader((PB100_DIR / "PB-100-output-channel-matrix.csv").open(newline="", encoding="utf-8"))
    )
    expected_outputs = {row["Output"].strip() for row in output_matrix_rows}
    instance_map_rows = list(
        csv.DictReader((PB100_DIR / "PB-100-schematic-instance-symbol-map.csv").open(newline="", encoding="utf-8"))
    )
    symbol_key_by_ref = {row["Ref"].strip(): row["Symbol key"].strip() for row in instance_map_rows}
    b2b_rows = list(csv.DictReader((PB100_DIR / "PB-100-b2b-pin-map.csv").open(newline="", encoding="utf-8")))
    b2b_nets = {row["Net"].strip() for row in b2b_rows}

    seen_outputs = set()
    for row_number, row in enumerate(rows, 2):
        output = row["Output"].strip()
        if output in seen_outputs:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate output {output}")
        seen_outputs.add(output)
        if output not in expected_outputs:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown output {output}")
        try:
            output_number = int(output.removeprefix("OUT"))
        except ValueError:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: invalid output name {output}")

        expected_refs = {
            "Controller ref": (f"U{100 + output_number}", "HS_CTRL"),
            "Switch ref": (f"Q{100 + output_number}", "OUT_FET"),
            "Fuse ref": (f"F{100 + output_number}", "OUTPUT_FUSE_HOLDER"),
            "Connector ref": (f"J{100 + output_number}", "OUTPUT_CONNECTOR"),
        }
        for column, (expected_ref, expected_key) in expected_refs.items():
            actual_ref = row[column].strip()
            if actual_ref != expected_ref:
                fail(
                    f"{path.relative_to(REPO_ROOT)}:{row_number}: {column} must be "
                    f"{expected_ref}, got {actual_ref}"
                )
            actual_key = symbol_key_by_ref.get(actual_ref)
            if actual_key != expected_key:
                fail(
                    f"{path.relative_to(REPO_ROOT)}:{row_number}: {actual_ref} must map to "
                    f"{expected_key}, got {actual_key}"
                )

        expected_nets = {
            "Control net": f"{output}_CTL",
            "Fault net": f"{output}_FLT",
            "Current net": f"{output}_IMON",
            "Load net": f"{output}_LOAD",
            "Fused net": f"{output}_FUSED",
        }
        for column, expected_net in expected_nets.items():
            actual_net = row[column].strip()
            if actual_net != expected_net:
                fail(
                    f"{path.relative_to(REPO_ROOT)}:{row_number}: {column} must be "
                    f"{expected_net}, got {actual_net}"
                )
            for forbidden_token in FORBIDDEN_ROLE_TOKENS:
                if forbidden_token in actual_net:
                    fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: role token in net {actual_net}")

        for connector_net in (row["Control net"].strip(), row["Fault net"].strip(), row["Current net"].strip()):
            if connector_net not in b2b_nets:
                fail(
                    f"{path.relative_to(REPO_ROOT)}:{row_number}: {connector_net} "
                    "is missing from PB-100-b2b-pin-map.csv"
                )

        default_state = row["Default state"].strip().lower()
        safety_rule = row["Safety rule"].strip().lower()
        if "off" not in default_state:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: default state must be off")
        if "configuration" not in safety_rule:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: safety rule must preserve configuration mapping")
        if output == "OUT2" and "soa" not in safety_rule:
            fail("OUT2 output pin contract must keep SOA close work explicit")

    missing_outputs = sorted(expected_outputs - seen_outputs)
    extra_outputs = sorted(seen_outputs - expected_outputs)
    if missing_outputs:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing outputs: "
            f"{', '.join(missing_outputs)}"
        )
    if extra_outputs:
        fail(
            f"{path.relative_to(REPO_ROOT)} has outputs not in output matrix: "
            f"{', '.join(extra_outputs)}"
        )


def validate_output_controller_pin_template() -> None:
    path = PB100_DIR / "PB-100-output-controller-pin-template.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty output controller pin template: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in OUTPUT_CONTROLLER_PIN_TEMPLATE_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    evidence_rows = list(
        csv.DictReader((PB100_DIR / "PB-100-symbol-pin-evidence.csv").open(newline="", encoding="utf-8"))
    )
    evidence_pins = {
        row["Pin number"].strip(): row["Pin name"].strip()
        for row in evidence_rows
        if row["Symbol name"].strip() == OUTPUT_CONTROLLER_SYMBOL
    }
    if not evidence_pins:
        fail(f"missing pin evidence for {OUTPUT_CONTROLLER_SYMBOL}")

    seen_pins = set()
    net_patterns = set()
    for row_number, row in enumerate(rows, 2):
        pin_number = row["Pin number"].strip()
        pin_name = row["Pin name"].strip()
        net_pattern = row["Net pattern"].strip()
        for column in OUTPUT_CONTROLLER_PIN_TEMPLATE_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        if pin_number in seen_pins:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate pin {pin_number}")
        seen_pins.add(pin_number)
        expected_pin_name = evidence_pins.get(pin_number)
        if expected_pin_name is None:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: pin {pin_number} is not in pin evidence")
        if pin_name != expected_pin_name:
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: pin {pin_number} must be "
                f"{expected_pin_name}, got {pin_name}"
            )
        for forbidden_token in FORBIDDEN_ROLE_TOKENS:
            if forbidden_token in net_pattern:
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: role token in net pattern {net_pattern}")
        if not (
            net_pattern.startswith("OUTn_")
            or net_pattern in {"GND", "NC", "VBAT_PROT"}
        ):
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: unsupported output-controller "
                f"net pattern {net_pattern}"
            )
        if pin_name == "N.C." and net_pattern != "NC":
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: N.C. pin must use NC net pattern")
        if pin_name == "GND" and net_pattern != "GND":
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: GND pin must use GND net pattern")
        if pin_name == "VS" and net_pattern != "VBAT_PROT":
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: VS pin must use VBAT_PROT")
        if "final" in row["Default state"].lower() and "not final" not in row["Default state"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: default state must not lock final values")
        if "schematic review" not in row["Freeze dependency"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: freeze dependency must reference schematic review")
        net_patterns.add(net_pattern)

    missing_pins = sorted(evidence_pins.keys() - seen_pins, key=lambda value: int(value))
    extra_pins = sorted(seen_pins - evidence_pins.keys(), key=lambda value: int(value))
    if missing_pins:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing controller pins: "
            f"{', '.join(missing_pins)}"
        )
    if extra_pins:
        fail(
            f"{path.relative_to(REPO_ROOT)} has pins not in evidence: "
            f"{', '.join(extra_pins)}"
        )
    for required_pattern in ("OUTn_CTL", "OUTn_FLT", "OUTn_IMON", "OUTn_SRC", "OUTn_PU", "OUTn_PD", "VBAT_PROT"):
        if required_pattern not in net_patterns:
            fail(
                f"{path.relative_to(REPO_ROOT)} is missing required output-controller "
                f"net pattern {required_pattern}"
            )


def sort_pin_number(pin_number: str) -> tuple[int, str]:
    return (0, f"{int(pin_number):04d}") if pin_number.isdigit() else (1, pin_number)


def validate_component_pin_template(
    file_name: str,
    symbol_name: str,
    allowed_net_patterns: set[str],
    required_net_patterns: set[str],
) -> None:
    path = PB100_DIR / file_name
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty component pin template: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in OUTPUT_CONTROLLER_PIN_TEMPLATE_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    evidence_rows = list(
        csv.DictReader((PB100_DIR / "PB-100-symbol-pin-evidence.csv").open(newline="", encoding="utf-8"))
    )
    evidence_pins = {
        row["Pin number"].strip(): row["Pin name"].strip()
        for row in evidence_rows
        if row["Symbol name"].strip() == symbol_name
    }
    if not evidence_pins:
        fail(f"missing pin evidence for {symbol_name}")

    seen_pins = set()
    net_patterns = set()
    for row_number, row in enumerate(rows, 2):
        pin_number = row["Pin number"].strip()
        pin_name = row["Pin name"].strip()
        net_pattern = row["Net pattern"].strip()
        for column in OUTPUT_CONTROLLER_PIN_TEMPLATE_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        if pin_number in seen_pins:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate pin {pin_number}")
        seen_pins.add(pin_number)
        expected_pin_name = evidence_pins.get(pin_number)
        if expected_pin_name is None:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: pin {pin_number} is not in pin evidence")
        if pin_name != expected_pin_name:
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: pin {pin_number} must be "
                f"{expected_pin_name}, got {pin_name}"
            )
        if net_pattern not in allowed_net_patterns:
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: unsupported net pattern "
                f"{net_pattern}"
            )
        for forbidden_token in FORBIDDEN_ROLE_TOKENS:
            if forbidden_token in net_pattern:
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: role token in net pattern {net_pattern}")
        if "final" in row["Default state"].lower() and "not final" not in row["Default state"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: default state must not lock final values")
        if "schematic review" not in row["Freeze dependency"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: freeze dependency must reference schematic review")
        net_patterns.add(net_pattern)

    missing_pins = sorted(evidence_pins.keys() - seen_pins, key=sort_pin_number)
    extra_pins = sorted(seen_pins - evidence_pins.keys(), key=sort_pin_number)
    if missing_pins:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing pins for {symbol_name}: "
            f"{', '.join(missing_pins)}"
        )
    if extra_pins:
        fail(
            f"{path.relative_to(REPO_ROOT)} has pins not in evidence for {symbol_name}: "
            f"{', '.join(extra_pins)}"
        )

    missing_patterns = sorted(required_net_patterns - net_patterns)
    if missing_patterns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required net patterns: "
            f"{', '.join(missing_patterns)}"
        )


def validate_input_and_power_pin_templates() -> None:
    validate_component_pin_template(
        "PB-100-input-controller-pin-template.csv",
        "PB100_LM74700QDBVRQ1_PRELIM",
        {
            "LM74700_VCAP",
            "GND",
            "INPUT_PROT_EN",
            "VBAT_REV_PROT",
            "INPUT_FET_GATE",
            "VBAT_RAW",
        },
        {"VBAT_RAW", "VBAT_REV_PROT", "INPUT_FET_GATE", "INPUT_PROT_EN"},
    )
    validate_component_pin_template(
        "PB-100-current-monitor-pin-template.csv",
        "PB100_INA228_Q1_PRELIM",
        {
            "IIN_MON_A1",
            "IIN_MON_A0",
            "PB_I2C_INT",
            "PB_I2C_SDA",
            "PB_I2C_SCL",
            "LB_3V3_IO",
            "GND",
            "VBAT_PROT",
            "IIN_SHUNT_LO",
            "IIN_SHUNT_HI",
        },
        {"IIN_SHUNT_HI", "IIN_SHUNT_LO", "PB_I2C_SDA", "PB_I2C_SCL", "VBAT_PROT"},
    )
    validate_component_pin_template(
        "PB-100-logic-buck-pin-template.csv",
        "PB100_LM5164QDDATQ1_PRELIM",
        {
            "GND",
            "VBAT_PROT",
            "BUCK_EN_UVLO",
            "BUCK_RON_SET",
            "BUCK_FB",
            "PB_PWR_GOOD",
            "BUCK_BST",
            "BUCK_SW",
        },
        {"VBAT_PROT", "BUCK_EN_UVLO", "BUCK_FB", "PB_PWR_GOOD", "BUCK_SW"},
    )


def validate_input_protection_pin_contract() -> None:
    path = PB100_DIR / "PB-100-input-protection-pin-contract.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty input protection pin contract: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in INPUT_PROTECTION_PIN_CONTRACT_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    instance_map_rows = list(
        csv.DictReader((PB100_DIR / "PB-100-schematic-instance-symbol-map.csv").open(newline="", encoding="utf-8"))
    )
    instance_by_ref = {row["Ref"].strip(): row for row in instance_map_rows}
    required_refs = {"J1", "D1", "U1", "Q1", "RSH1", "U2"}
    required_nets = {
        "VBAT_RAW",
        "GND",
        "VBAT_PROT",
        "INPUT_FET_GATE",
        "VBAT_REV_PROT",
        "IIN_SHUNT_HI",
        "IIN_SHUNT_LO",
        "IIN_SENSE",
        "VBAT_SENSE",
    }
    seen_refs = set()
    seen_nets = set()
    q1_rows = []
    for row_number, row in enumerate(rows, 2):
        ref = row["Ref"].strip()
        symbol_key = row["Symbol key"].strip()
        concrete_symbol_name = row["Concrete symbol name"].strip()
        planned_net = row["Planned net"].strip()
        for column in ("Ref", "Symbol key", "Concrete symbol name", "Interface point", "Planned net", "Direction", "Default state", "Freeze dependency"):
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        instance_row = instance_by_ref.get(ref)
        if instance_row is None:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown instance ref {ref}")
        if symbol_key != instance_row["Symbol key"].strip():
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: {ref} uses {symbol_key}, "
                f"but instance-symbol map uses {instance_row['Symbol key'].strip()}"
            )
        if concrete_symbol_name != instance_row["Concrete symbol name"].strip():
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: {ref} uses {concrete_symbol_name}, "
                f"but instance-symbol map uses {instance_row['Concrete symbol name'].strip()}"
            )
        for forbidden_token in FORBIDDEN_ROLE_TOKENS:
            if forbidden_token in planned_net:
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: role token in planned net {planned_net}")
        seen_refs.add(ref)
        seen_nets.add(planned_net)
        if ref == "Q1":
            q1_rows.append(row)

    missing_refs = sorted(required_refs - seen_refs)
    if missing_refs:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing input refs: "
            f"{', '.join(missing_refs)}"
        )
    missing_nets = sorted(required_nets - seen_nets)
    if missing_nets:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing input planned nets: "
            f"{', '.join(missing_nets)}"
        )
    if not q1_rows:
        fail("input protection pin contract must include Q1 reverse FET rows")
    q1_state = instance_by_ref["Q1"]["Symbol state"].strip()
    if q1_state != "Created":
        fail("Q1 must be Created after INPUT_REVERSE_FET symbol evidence closes")
    q1_close_text = " ".join(
        row[column]
        for row in q1_rows
        for column in ("Interface point", "Default state", "Freeze dependency")
    )
    if not all(token in q1_close_text for token in ("BUK7S1R2-80M", "LFPAK88", "40 A")):
        fail("Q1 input protection rows must keep selected 80 V LFPAK88 and 40 A review explicit")


def validate_logic_power_design_placeholders() -> None:
    path = PB100_DIR / "PB-100-logic-power-design-placeholders.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty logic power design placeholders: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in LOGIC_POWER_DESIGN_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    seen_items = set()
    refs_or_nets = set()
    for row_number, row in enumerate(rows, 2):
        item = row["Item"].strip()
        if not item:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: missing Item")
        if item in seen_items:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate Item {item}")
        seen_items.add(item)
        refs_or_nets.add(row["Ref or net"].strip())
        for column in ("Ref or net", "Design state", "Value status", "Freeze dependency", "Notes"):
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")

        value_status = row["Value status"].strip().lower()
        if "final" in value_status and "not final" not in value_status:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: logic power value must not be final before review")
        for blocked_word in ("locked", "released"):
            if blocked_word in value_status:
                fail(
                    f"{path.relative_to(REPO_ROOT)}:{row_number}: logic power value "
                    f"must not be {blocked_word} before review"
                )
        if "tbd" not in value_status and "not final" not in value_status:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: Value status must remain TBD/not final")

    missing_items = sorted(REQUIRED_LOGIC_POWER_ITEMS - seen_items)
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing logic power items: "
            f"{', '.join(missing_items)}"
        )
    for required_ref_or_net in ("U3", "L1", "VBAT_PROT", "PB_5V_OUT", "PB_PWR_GOOD"):
        if required_ref_or_net not in refs_or_nets:
            fail(
                f"{path.relative_to(REPO_ROOT)} is missing required logic power "
                f"ref/net {required_ref_or_net}"
            )


def validate_not_final_value_status(path: Path, row_number: int, value_status: str) -> None:
    normalized = value_status.strip().lower()
    if "tbd" not in normalized and "not final" not in normalized:
        fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: Value status must remain TBD/not final")
    if "final" in normalized and "not final" not in normalized:
        fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: value must not be final before schematic review")
    for blocked_word in ("locked", "released", "approved"):
        if blocked_word in normalized:
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: value must not be "
                f"{blocked_word} before schematic review"
            )


def validate_no_role_tokens_in_row(path: Path, row_number: int, row: dict[str, str]) -> None:
    row_text = " ".join(row.values())
    for forbidden_token in FORBIDDEN_ROLE_TOKENS:
        if forbidden_token in row_text:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: role token {forbidden_token} is not allowed")


def output_controller_template_net_patterns() -> set[str]:
    path = PB100_DIR / "PB-100-output-controller-pin-template.csv"
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    return {row["Net pattern"].strip() for row in rows}


def validate_output_net_expansion() -> None:
    path = PB100_DIR / "PB-100-output-net-expansion.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty output net expansion: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in OUTPUT_NET_EXPANSION_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    output_matrix_rows = list(
        csv.DictReader((PB100_DIR / "PB-100-output-channel-matrix.csv").open(newline="", encoding="utf-8"))
    )
    expected_outputs = {row["Output"].strip() for row in output_matrix_rows}
    expected_patterns = {
        pattern for pattern in output_controller_template_net_patterns() if pattern.startswith("OUTn_")
    } | {"OUTn_LOAD", "OUTn_FUSED"}
    b2b_rows = list(csv.DictReader((PB100_DIR / "PB-100-b2b-pin-map.csv").open(newline="", encoding="utf-8")))
    b2b_nets = {row["Net"].strip() for row in b2b_rows}
    manifest_rows = list(csv.DictReader((PB100_DIR / "PB-100-kicad-sheet-manifest.csv").open(newline="", encoding="utf-8")))
    manifest_sheets = {row["Sheet file"].strip() for row in manifest_rows}

    seen_pairs = set()
    for row_number, row in enumerate(rows, 2):
        output = row["Output"].strip()
        pattern = row["Net pattern"].strip()
        expanded_net = row["Expanded net"].strip()
        if output not in expected_outputs:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown output {output}")
        if pattern not in expected_patterns:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unexpected net pattern {pattern}")
        expected_net = pattern.replace("OUTn", output)
        if expanded_net != expected_net:
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: expected expanded net "
                f"{expected_net}, got {expanded_net}"
            )
        pair = (output, pattern)
        if pair in seen_pairs:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate expansion {output}/{pattern}")
        seen_pairs.add(pair)
        validate_no_role_tokens_in_row(path, row_number, row)
        primary_sheet = row["Primary sheet"].strip()
        if primary_sheet not in manifest_sheets:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown Primary sheet {primary_sheet}")
        for column in ("Source artifact", "Default state", "Safety rule"):
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        if pattern in {"OUTn_CTL", "OUTn_FLT", "OUTn_IMON"} and expanded_net not in b2b_nets:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: {expanded_net} is missing from JPB1 pin map")
        if pattern == "OUTn_CTL" and "configuration" not in row["Safety rule"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: control nets must preserve configuration mapping")
        if pattern in {"OUTn_LOAD", "OUTn_FUSED"} and "off" not in row["Default state"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: output power nets must default off")
        if pattern.startswith("OUTn_") and "OUTn" in expanded_net:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: expanded net still contains OUTn")

    expected_pairs = {(output, pattern) for output in expected_outputs for pattern in expected_patterns}
    missing_pairs = sorted(expected_pairs - seen_pairs)
    extra_pairs = sorted(seen_pairs - expected_pairs)
    if missing_pairs:
        formatted = ", ".join(f"{output}/{pattern}" for output, pattern in missing_pairs)
        fail(f"{path.relative_to(REPO_ROOT)} is missing expansions: {formatted}")
    if extra_pairs:
        formatted = ", ".join(f"{output}/{pattern}" for output, pattern in extra_pairs)
        fail(f"{path.relative_to(REPO_ROOT)} has extra expansions: {formatted}")


def validate_output_stage_design_values() -> None:
    path = PB100_DIR / "PB-100-output-stage-design-values.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty output-stage design values: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in OUTPUT_STAGE_DESIGN_VALUE_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    allowed_patterns = output_controller_template_net_patterns() | {"OUTn_LOAD"}
    seen_items: dict[str, set[str]] = {output_class: set() for output_class in REQUIRED_OUTPUT_STAGE_CLASSES}
    class_text: dict[str, list[str]] = {output_class: [] for output_class in REQUIRED_OUTPUT_STAGE_CLASSES}
    for row_number, row in enumerate(rows, 2):
        output_class = row["Output class"].strip()
        design_item = row["Design item"].strip()
        if output_class not in REQUIRED_OUTPUT_STAGE_CLASSES:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: invalid output class {output_class}")
        if design_item not in REQUIRED_OUTPUT_STAGE_ITEMS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: invalid design item {design_item}")
        if design_item in seen_items[output_class]:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate {output_class}/{design_item}")
        seen_items[output_class].add(design_item)
        class_text[output_class].append(" ".join(row.values()))
        validate_no_role_tokens_in_row(path, row_number, row)
        for column in ("Applies to", "Related net pattern", "Candidate direction", "Freeze dependency", "Notes"):
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_not_final_value_status(path, row_number, row["Value status"])
        if "schematic freeze" not in row["Freeze dependency"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: freeze dependency must reference schematic freeze")
        related_patterns = [part.strip() for part in row["Related net pattern"].split(";")]
        if not related_patterns:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: missing related net pattern")
        for pattern in related_patterns:
            if pattern not in allowed_patterns:
                fail(
                    f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown output "
                    f"net pattern {pattern}"
                )
        if output_class == "High current" and "OUT2" not in row["Applies to"]:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: high-current rows must apply to OUT2")

    for output_class, items in seen_items.items():
        missing_items = sorted(REQUIRED_OUTPUT_STAGE_ITEMS - items)
        if missing_items:
            fail(
                f"{path.relative_to(REPO_ROOT)} is missing {output_class} design items: "
                f"{', '.join(missing_items)}"
            )
    if "SOA" not in " ".join(class_text["High current"]):
        fail("high-current output-stage design values must keep OUT2 SOA explicit")
    if "external controller" not in " ".join(class_text["Low current"]).lower():
        fail("low-current output-stage design values must preserve external-controller baseline")


def validate_output_stage_value_freeze_checklist() -> None:
    path = PB100_DIR / "PB-100-output-stage-value-freeze-checklist.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty output-stage value freeze checklist: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in OUTPUT_STAGE_VALUE_FREEZE_CHECKLIST_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_check: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        check_id = row["Check ID"].strip()
        if check_id not in REQUIRED_OUTPUT_STAGE_VALUE_FREEZE_CHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown output-stage value check {check_id}")
        if check_id in rows_by_check:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate output-stage value check {check_id}")
        rows_by_check[check_id] = row
        for column in OUTPUT_STAGE_VALUE_FREEZE_CHECKLIST_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        row_text = " ".join(row.values()).lower()
        if check_id == "OUTVAL-002" and ("out2" not in row_text or "soa" not in row_text or "escape path" not in row_text):
            fail("OUT2 output-stage checklist row must keep SOA and escape path explicit")
        if check_id == "OUTVAL-004" and ("no direct 40 v smart-switch rail" not in row_text or "adr" not in row_text):
            fail("low-current output-stage checklist row must keep no-direct-40V-smart-switch ADR boundary")
        if check_id == "OUTVAL-006" and ("default-off" not in row_text or "reset" not in row_text):
            fail("output gate-drive checklist row must keep default-off reset boundary")
        if check_id == "OUTVAL-007" and ("0-30a" not in row_text or "0-20a" not in row_text or "0-8a" not in row_text):
            fail("output telemetry checklist row must keep all class telemetry ranges")
        if check_id == "OUTVAL-009" and ("no pcb layout" not in row_text or "pb-100.kicad_pcb" not in row_text):
            fail("output no-layout checklist row must block PCB layout explicitly")

    missing_checks = sorted(REQUIRED_OUTPUT_STAGE_VALUE_FREEZE_CHECKS - rows_by_check.keys())
    if missing_checks:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing output-stage value checks: "
            f"{', '.join(missing_checks)}"
        )

    checklist_text = read_text(path)
    for token in (
        "TPS48110AQDGXRQ1",
        "OUT2",
        "20A fuse",
        "18A configured limit",
        "40A 1s",
        "80A 100ms",
        "OUTn_IWRN_SET",
        "OUTn_ISCP_SET",
        "OUTn_TMR",
        "OUTn_PU",
        "OUTn_PD",
        "OUTn_CS_P",
        "OUTn_CS_N",
        "0-30A",
        "0-20A",
        "0-8A",
        "BUK7S1R2-80M",
        "80V",
        "No PCB layout",
        "PB-100.kicad_pcb",
    ):
        if token not in checklist_text:
            fail(f"output-stage value freeze checklist must include {token}")


def validate_output_stage_value_derivation_precheck() -> None:
    path = PB100_DIR / "PB-100-output-stage-value-derivation-precheck.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty output-stage value derivation precheck: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in OUTPUT_STAGE_VALUE_DERIVATION_PRECHECK_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_id: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        derivation_id = row["Derivation ID"].strip()
        if derivation_id not in REQUIRED_OUTPUT_STAGE_VALUE_DERIVATION_CHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown output derivation item {derivation_id}")
        if derivation_id in rows_by_id:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate output derivation item {derivation_id}")
        rows_by_id[derivation_id] = row
        for column in OUTPUT_STAGE_VALUE_DERIVATION_PRECHECK_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        row_text = " ".join(row.values()).lower()
        if derivation_id == "OUTDRV-004" and ("equation 6" not in row_text or "riwrn" not in row_text):
            fail("output derivation precheck must include RIWRN Equation 6")
        if derivation_id == "OUTDRV-005" and ("equation 7" not in row_text or "10ms" not in row_text):
            fail("output derivation precheck must include TMR Equation 7 and OUT2 10ms boundary")
        if derivation_id == "OUTDRV-006" and ("equation 11" not in row_text or "riscp" not in row_text):
            fail("output derivation precheck must include RISCP Equation 11")
        if derivation_id == "OUTDRV-007" and ("equation 12" not in row_text or "equation 13" not in row_text):
            fail("output derivation precheck must include IMON Equations 12 and 13")
        if derivation_id == "OUTDRV-010" and ("no-layout" not in row_text and "pb-100.kicad_pcb" not in row_text):
            fail("output derivation precheck must keep no-layout boundary explicit")

    missing_items = sorted(REQUIRED_OUTPUT_STAGE_VALUE_DERIVATION_CHECKS - rows_by_id.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing output-stage derivation items: "
            f"{', '.join(missing_items)}"
        )

    precheck_text = read_text(path)
    for token in (
        "TI TPS4811-Q1",
        "TPS48110Q1EVM",
        "OUTn_IWRN_SET",
        "OUTn_ISCP_SET",
        "OUTn_TMR",
        "OUTn_BST",
        "Equation 1",
        "Equation 4",
        "Equation 6",
        "Equation 7",
        "Equation 11",
        "Equation 12",
        "Equation 13",
        "OUT2",
        "18A",
        "12A",
        "8A",
        "4A",
        "0-30A",
        "0-20A",
        "0-8A",
        "ADR-0011",
        "no direct 40V smart-switch rail",
        "PB-100.kicad_pcb",
    ):
        if token not in precheck_text:
            fail(f"output-stage value derivation precheck must include {token}")


def validate_output_stage_closeout_precheck() -> None:
    path = PB100_DIR / "PB-100-output-stage-closeout-precheck.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty output-stage closeout precheck: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in OUTPUT_STAGE_CLOSEOUT_PRECHECK_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_id: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        precheck_id = row["Precheck ID"].strip()
        if precheck_id not in REQUIRED_OUTPUT_STAGE_CLOSEOUT_PRECHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown output closeout precheck {precheck_id}")
        if precheck_id in rows_by_id:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate output closeout precheck {precheck_id}")
        rows_by_id[precheck_id] = row
        for column in OUTPUT_STAGE_CLOSEOUT_PRECHECK_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        row_text = " ".join(row.values()).lower()
        if "do not" not in row["Blocked action"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: blocked action must be explicit")
        if precheck_id == "OUTCLS-002" and ("out2" not in row_text or "out5" not in row_text or "out10" not in row_text):
            fail("output closeout class-map row must cover OUT2, low-current, and OUT10 classes")
        if precheck_id == "OUTCLS-008" and ("adr-0011" not in row_text or "no direct 40 v smart-switch rail" not in row_text):
            fail("output closeout low-current row must preserve ADR-0011 no-direct-40V-smart-switch boundary")
        if precheck_id == "OUTCLS-010" and ("no pcb layout" not in row_text or "pb-100.kicad_pcb" not in row_text):
            fail("output closeout no-layout row must block PCB layout explicitly")

    missing_items = sorted(REQUIRED_OUTPUT_STAGE_CLOSEOUT_PRECHECKS - rows_by_id.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing output closeout prechecks: "
            f"{', '.join(missing_items)}"
        )

    precheck_text = read_text(path)
    for token in (
        "TI TPS4811-Q1",
        "TPS48110AQDGXRQ1",
        "TPS48110Q1EVM",
        "Equation 1",
        "Equation 4",
        "Equation 6",
        "Equation 7",
        "Equation 11",
        "Equation 12",
        "Equation 13",
        "High current",
        "Medium current",
        "Low current",
        "OUT2",
        "OUT10",
        "OUT5",
        "OUT8",
        "OUT9",
        "20A fuse",
        "18A configured limit",
        "15A/12A",
        "10A/8A",
        "5A fuse",
        "4A configured limit",
        "OV threshold divider",
        "Current warning threshold",
        "Short-circuit threshold",
        "Fault timer",
        "Bootstrap capacitor",
        "Gate drive resistors",
        "Current sense topology",
        "Inductive clamp strategy",
        "Value status TBD not final",
        "OUTn_IWRN_SET",
        "OUTn_ISCP_SET",
        "OUTn_TMR",
        "RSET",
        "RSNS",
        "VOS_SET",
        "RIWRN",
        "RISCP",
        "CTMR",
        "10ms",
        "OUTn_BST",
        "OUTn_PU",
        "OUTn_PD",
        "OUTn_CTL",
        "OUTn_INP",
        "default-off",
        "reset",
        "gate pull-down",
        "Qg_total",
        "C1",
        "OUTn_CS_P",
        "OUTn_CS_N",
        "OUTn_IMON",
        "0-30A",
        "0-20A",
        "0-8A",
        "LB-100 ADC",
        "OUT2 SOA",
        "fuse energy",
        "40A 1s",
        "80A 100ms",
        "BUK7S1R2-80M",
        "80V",
        "PB-100-tvs-load-dump-margin-trace.csv",
        "PB-100-mosfet-voltage-margin-review.md",
        "ADR-0011",
        "external-controller",
        "BUK7S1R2-80M 80V N-MOSFET",
        "no direct 40 V smart-switch rail",
        "no direct 40V smart-switch rail",
        "output-channel-template.kicad_sch",
        "outputs-1-10.kicad_sch",
        "PB-100-output-net-expansion.csv",
        "PB-100-schematic-instance-symbol-map.csv",
        "OUT1 through OUT10",
        "generic OUTn names",
        "No PCB layout",
        "PB-100.kicad_pcb",
        "MOSFET placement",
        "fuse placement",
        "connector placement",
        "high-current copper",
        "Gerbers",
        "drills",
        "pick-place",
        "manufacturing ZIP",
    ):
        if token not in precheck_text:
            fail(f"output-stage closeout precheck must include {token}")

    design_rows = list(csv.DictReader((PB100_DIR / "PB-100-output-stage-design-values.csv").open(newline="", encoding="utf-8")))
    seen_items: dict[str, set[str]] = {output_class: set() for output_class in REQUIRED_OUTPUT_STAGE_CLASSES}
    for row in design_rows:
        output_class = row["Output class"].strip()
        if output_class in seen_items:
            seen_items[output_class].add(row["Design item"].strip())
            if "tbd not final" not in row["Value status"].lower():
                fail("output-stage closeout precheck requires design values to remain non-final before freeze")
    for output_class, items in seen_items.items():
        missing_items = sorted(REQUIRED_OUTPUT_STAGE_ITEMS - items)
        if missing_items:
            fail(
                f"output-stage closeout precheck requires {output_class} design values to include: "
                f"{', '.join(missing_items)}"
            )

    freeze_text = read_text(PB100_DIR / "PB-100-output-stage-value-freeze-checklist.csv")
    derivation_text = read_text(PB100_DIR / "PB-100-output-stage-value-derivation-precheck.csv")
    for token in ("OUTVAL-002", "OUTVAL-004", "OUTVAL-009"):
        if token not in freeze_text:
            fail(f"output-stage closeout precheck requires freeze checklist token {token}")
    for token in ("OUTDRV-004", "OUTDRV-005", "OUTDRV-006", "OUTDRV-007", "OUTDRV-010"):
        if token not in derivation_text:
            fail(f"output-stage closeout precheck requires derivation token {token}")


def validate_low_current_output_baseline_trace() -> None:
    path = PB100_DIR / "PB-100-low-current-output-baseline-trace.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty low-current output baseline trace: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in LOW_CURRENT_OUTPUT_BASELINE_TRACE_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    expected_outputs = {"OUT5", "OUT8", "OUT9"}
    rows_by_output: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        output = row["Output"].strip()
        if output in rows_by_output:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate output {output}")
        if output not in expected_outputs:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unexpected low-current output {output}")
        rows_by_output[output] = row
        for column in LOW_CURRENT_OUTPUT_BASELINE_TRACE_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        row_text = " ".join(row.values())
        for token in (
            "Low current",
            "5",
            "4",
            "TPS48110AQDGXRQ1 plus selected BUK7S1R2-80M 80V LFPAK88 N-MOSFET",
            "configuration only",
            "no direct 40 V smart-switch rail",
            "future ADR",
            "schematic freeze",
        ):
            if token not in row_text:
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: low-current row must include {token}")

    missing_outputs = sorted(expected_outputs - rows_by_output.keys())
    if missing_outputs:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing low-current outputs: "
            f"{', '.join(missing_outputs)}"
        )

    matrix_rows = list(csv.DictReader((PB100_DIR / "PB-100-output-channel-matrix.csv").open(newline="", encoding="utf-8")))
    matrix_by_output = {row["Output"].strip(): row for row in matrix_rows}
    capabilities = json.loads(read_text(REPO_ROOT / "firmware" / "configs" / "hardware" / "pb-100-capabilities.json"))
    capability_by_output = {row["id"]: row for row in capabilities["outputs"]}
    config_example = json.loads(read_text(REPO_ROOT / "firmware" / "configs" / "config-example.json"))
    config_by_output = {row["id"]: row for row in config_example["outputs"]}

    for output in sorted(expected_outputs):
        trace_row = rows_by_output[output]
        matrix_row = matrix_by_output.get(output)
        capability_row = capability_by_output.get(output)
        config_row = config_by_output.get(output)
        if matrix_row is None or capability_row is None or config_row is None:
            fail(f"{output} must exist in matrix, capability manifest, and config example")
        if matrix_row["Class"].strip() != "Low current":
            fail(f"{output} must remain Low current in output channel matrix")
        if matrix_row["Initial switch direction"].strip() != trace_row["Switch architecture"].strip():
            fail(f"{output} switch architecture must match output channel matrix")
        if int(matrix_row["Target fuse A"]) != int(trace_row["Fuse target A"]):
            fail(f"{output} fuse target must match output channel matrix")
        if int(matrix_row["Target current limit A"]) != int(trace_row["Current limit A"]):
            fail(f"{output} current limit must match output channel matrix")
        if capability_row["class"] != "Low current":
            fail(f"{output} must remain Low current in capability manifest")
        if capability_row["target_fuse_a"] != int(trace_row["Fuse target A"]):
            fail(f"{output} capability fuse target must match low-current trace")
        if capability_row["target_current_limit_a"] != int(trace_row["Current limit A"]):
            fail(f"{output} capability current limit must match low-current trace")
        if config_row["fuse_a"] != int(trace_row["Fuse target A"]):
            fail(f"{output} config example fuse must match low-current trace")
        if config_row["current_limit_a"] != int(trace_row["Current limit A"]):
            fail(f"{output} config example current limit must match low-current trace")

    output_contract_text = read_text(PB100_DIR / "PB-100-output-channel-pin-contract.csv")
    for output in sorted(expected_outputs):
        if f"{output}_CTL" not in output_contract_text or f"{output}_IMON" not in output_contract_text:
            fail(f"output pin contract must include {output} control and current telemetry nets")

    low_current_design_rows = [
        row
        for row in csv.DictReader((PB100_DIR / "PB-100-output-stage-design-values.csv").open(newline="", encoding="utf-8"))
        if row["Output class"].strip() == "Low current"
    ]
    if len(low_current_design_rows) != len(REQUIRED_OUTPUT_STAGE_ITEMS):
        fail("low-current output-stage design values must cover every required design item")
    low_current_text = " ".join(" ".join(row.values()) for row in low_current_design_rows).lower()
    if "external controller baseline" not in low_current_text or "no direct 40 v smart-switch rail" not in low_current_text:
        fail("low-current design values must keep external-controller baseline and no direct 40 V rail explicit")


def parse_space_separated_outputs(value: str) -> list[str]:
    return [part.strip() for part in value.split() if part.strip()]


def validate_high_medium_output_baseline_trace() -> None:
    path = PB100_DIR / "PB-100-high-medium-output-baseline-trace.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty high/medium output baseline trace: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in HIGH_MEDIUM_OUTPUT_BASELINE_TRACE_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    expected_groups = {
        "High current": {
            "outputs": ["OUT2"],
            "class": "High current",
            "fuses": "20",
            "limits": "18",
        },
        "Medium current 12A": {
            "outputs": ["OUT1"],
            "class": "Medium current",
            "fuses": "15",
            "limits": "12",
        },
        "Medium current 8A": {
            "outputs": ["OUT3", "OUT4", "OUT6", "OUT7", "OUT10"],
            "class": "Medium current",
            "fuses": "10",
            "limits": "8",
        },
    }
    rows_by_group: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        group = row["Output group"].strip()
        if group in rows_by_group:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate output group {group}")
        if group not in expected_groups:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unexpected output group {group}")
        rows_by_group[group] = row
        for column in HIGH_MEDIUM_OUTPUT_BASELINE_TRACE_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        row_text = " ".join(row.values())
        for token in ("TPS48110AQDGXRQ1 plus selected BUK7S1R2-80M 80V LFPAK88 MOSFET", "layout"):
            if token not in row_text:
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: high/medium row must include {token}")

    missing_groups = sorted(set(expected_groups) - set(rows_by_group))
    if missing_groups:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing output groups: "
            f"{', '.join(missing_groups)}"
        )

    matrix_rows = list(csv.DictReader((PB100_DIR / "PB-100-output-channel-matrix.csv").open(newline="", encoding="utf-8")))
    matrix_by_output = {row["Output"].strip(): row for row in matrix_rows}
    capabilities = json.loads(read_text(REPO_ROOT / "firmware" / "configs" / "hardware" / "pb-100-capabilities.json"))
    capability_by_output = {row["id"]: row for row in capabilities["outputs"]}
    config_example = json.loads(read_text(REPO_ROOT / "firmware" / "configs" / "config-example.json"))
    config_by_output = {row["id"]: row for row in config_example["outputs"]}

    covered_outputs: set[str] = set()
    for group, expected in expected_groups.items():
        row = rows_by_group[group]
        outputs = parse_space_separated_outputs(row["Outputs"])
        if outputs != expected["outputs"]:
            fail(f"{group} outputs must be {' '.join(expected['outputs'])}")
        if row["Capability class"].strip() != expected["class"]:
            fail(f"{group} class must be {expected['class']}")
        if row["Fuse targets A"].strip() != expected["fuses"]:
            fail(f"{group} fuse target must be {expected['fuses']}")
        if row["Current limits A"].strip() != expected["limits"]:
            fail(f"{group} current limit must be {expected['limits']}")
        covered_outputs.update(outputs)
        for output in outputs:
            matrix_row = matrix_by_output.get(output)
            capability_row = capability_by_output.get(output)
            config_row = config_by_output.get(output)
            if matrix_row is None or capability_row is None or config_row is None:
                fail(f"{output} must exist in matrix, capability manifest, and config example")
            if matrix_row["Class"].strip() != expected["class"]:
                fail(f"{output} must remain {expected['class']} in output channel matrix")
            if matrix_row["Initial switch direction"].strip() != "TPS48110AQDGXRQ1 plus selected BUK7S1R2-80M 80V LFPAK88 N-MOSFET":
                fail(f"{output} must keep TPS48110 external MOSFET switch direction")
            if int(matrix_row["Target fuse A"]) != int(expected["fuses"]):
                fail(f"{output} fuse target must match high/medium trace")
            if int(matrix_row["Target current limit A"]) != int(expected["limits"]):
                fail(f"{output} current limit must match high/medium trace")
            if capability_row["class"] != expected["class"]:
                fail(f"{output} must remain {expected['class']} in capability manifest")
            if capability_row["target_fuse_a"] != int(expected["fuses"]):
                fail(f"{output} capability fuse target must match high/medium trace")
            if capability_row["target_current_limit_a"] != int(expected["limits"]):
                fail(f"{output} capability current limit must match high/medium trace")
            if config_row["fuse_a"] != int(expected["fuses"]):
                fail(f"{output} config example fuse must match high/medium trace")
            if config_row["current_limit_a"] != int(expected["limits"]):
                fail(f"{output} config example current limit must match high/medium trace")
            if f"{output}_IMON" not in row["Telemetry path"]:
                fail(f"{output} telemetry path must include {output}_IMON")

    if covered_outputs != {"OUT1", "OUT2", "OUT3", "OUT4", "OUT6", "OUT7", "OUT10"}:
        fail("high/medium trace must cover OUT1 OUT2 OUT3 OUT4 OUT6 OUT7 OUT10")

    high_design_text = " ".join(
        " ".join(row.values())
        for row in csv.DictReader((PB100_DIR / "PB-100-output-stage-design-values.csv").open(newline="", encoding="utf-8"))
        if row["Output class"].strip() == "High current"
    )
    medium_design_text = " ".join(
        " ".join(row.values())
        for row in csv.DictReader((PB100_DIR / "PB-100-output-stage-design-values.csv").open(newline="", encoding="utf-8"))
        if row["Output class"].strip() == "Medium current"
    )
    if "OUT2" not in high_design_text or "SOA" not in high_design_text:
        fail("high-current design values must keep OUT2 SOA explicit")
    for token in ("Current sense topology", "Gate drive resistors", "Inductive clamp strategy"):
        if token not in high_design_text or token not in medium_design_text:
            fail(f"high/medium output-stage design values must include {token}")
    if "OUT1 OUT3 OUT4 OUT6 OUT7 OUT10" not in medium_design_text:
        fail("medium-current design values must keep the medium output set explicit")


def validate_high_medium_output_freeze_review() -> None:
    path = PB100_DIR / "PB-100-high-medium-output-freeze-review.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty high/medium output freeze review: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in OUTPUT_FREEZE_REVIEW_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_item: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        review_item = row["Review item"].strip()
        if review_item not in REQUIRED_HIGH_MEDIUM_OUTPUT_FREEZE_REVIEW_ITEMS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown high/medium output review item {review_item}")
        if review_item in rows_by_item:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate high/medium output review item {review_item}")
        rows_by_item[review_item] = row
        for column in OUTPUT_FREEZE_REVIEW_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)

    missing_items = sorted(REQUIRED_HIGH_MEDIUM_OUTPUT_FREEZE_REVIEW_ITEMS - rows_by_item.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing high/medium output review items: "
            f"{', '.join(missing_items)}"
        )

    review_text = read_text(path)
    for token in (
        "TPS48110AQDGXRQ1",
        "OUT2",
        "20A fuse",
        "18A configured limit",
        "40A 1s",
        "80A 100ms",
        "OUT2 escape path",
        "OUT1",
        "OUT3 OUT4 OUT6 OUT7 OUT10",
        "OUTn_PU",
        "OUTn_PD",
        "OUTn_CTL",
        "OUTn_CS_P",
        "OUTn_CS_N",
        "OUTn_IMON",
        "OUTn_IWRN_SET",
        "OUTn_ISCP_SET",
        "OUTn_TMR",
        "OUTn_LOAD",
        "No PCB layout",
    ):
        if token not in review_text:
            fail(f"high/medium output freeze review must include {token}")

    for token in (
        "PB-100-high-medium-output-baseline-trace.csv",
        "PB-100-output-controller-pin-template.csv",
        "PB-100-output-stage-design-values.csv",
        "PB-100-current-telemetry-freeze-review.csv",
        "PB-100-thermal-telemetry-freeze-review.csv",
    ):
        if token not in review_text:
            fail(f"high/medium output freeze review must cite {token}")

    high_medium_text = read_text(PB100_DIR / "PB-100-high-medium-output-baseline-trace.csv")
    for token in ("OUT2", "OUT1", "OUT3 OUT4 OUT6 OUT7 OUT10", "TPS48110AQDGXRQ1 plus selected BUK7S1R2-80M 80V LFPAK88 MOSFET"):
        if token not in high_medium_text:
            fail(f"high/medium baseline trace must support freeze review token {token}")

    soa_text = read_text(PB100_DIR / "PB-100-out2-soa-envelope.csv")
    for token in ("40", "1 s", "80", "100 ms", "10 ms max"):
        if token not in soa_text:
            fail(f"OUT2 SOA envelope must support freeze review token {token}")

    firmware_tests = read_text(REPO_ROOT / "firmware" / "tests" / "test_output_manager.c")
    for token in ("test_init_keeps_all_outputs_off", "test_invalid_telemetry_is_denied"):
        if token not in firmware_tests:
            fail(f"output manager tests must retain high/medium freeze review token {token}")


def validate_low_current_output_freeze_review() -> None:
    path = PB100_DIR / "PB-100-low-current-output-freeze-review.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty low-current output freeze review: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in OUTPUT_FREEZE_REVIEW_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_item: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        review_item = row["Review item"].strip()
        if review_item not in REQUIRED_LOW_CURRENT_OUTPUT_FREEZE_REVIEW_ITEMS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown low-current output review item {review_item}")
        if review_item in rows_by_item:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate low-current output review item {review_item}")
        rows_by_item[review_item] = row
        for column in OUTPUT_FREEZE_REVIEW_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)

    missing_items = sorted(REQUIRED_LOW_CURRENT_OUTPUT_FREEZE_REVIEW_ITEMS - rows_by_item.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing low-current output review items: "
            f"{', '.join(missing_items)}"
        )

    review_text = read_text(path)
    for token in (
        "ADR-0011",
        "OUT5",
        "OUT8",
        "OUT9",
        "5A fuse",
        "4A configured current limit",
        "TPS48110AQDGXRQ1",
        "BUK7S1R2-80M 80V external N-MOSFET",
        "no direct 40V smart-switch rail",
        "future ADR",
        "OUTn_CTL",
        "OUTn_PU",
        "OUTn_PD",
        "OUT5_IMON",
        "OUT8_IMON",
        "OUT9_IMON",
        "0-8A",
        "OUTn_IWRN_SET",
        "OUTn_ISCP_SET",
        "OUTn_TMR",
        "configuration and rules",
    ):
        if token not in review_text:
            fail(f"low-current output freeze review must include {token}")

    low_current_text = read_text(PB100_DIR / "PB-100-low-current-output-baseline-trace.csv")
    for token in ("OUT5", "OUT8", "OUT9", "no direct 40 V smart-switch rail", "future ADR"):
        if token not in low_current_text:
            fail(f"low-current baseline trace must support freeze review token {token}")

    design_values_text = read_text(PB100_DIR / "PB-100-output-stage-design-values.csv")
    for token in ("Low current", "OUT5 OUT8 OUT9", "No direct 40 V smart-switch rail"):
        if token not in design_values_text:
            fail(f"output-stage design values must support low-current freeze review token {token}")

    firmware_joined = "\n".join(
        (
            read_text(REPO_ROOT / "firmware" / "tests" / "test_role_resolver.c"),
            read_text(REPO_ROOT / "firmware" / "tests" / "test_rule_runtime.c"),
            read_text(REPO_ROOT / "firmware" / "tests" / "test_output_manager.c"),
        )
    )
    for token in ("test_missing_role_is_reported", "test_fault_dispatch_runs_before_rule_actions", "test_init_keeps_all_outputs_off"):
        if token not in firmware_joined:
            fail(f"firmware tests must retain low-current freeze review token {token}")


def validate_input_power_design_values() -> None:
    path = PB100_DIR / "PB-100-input-power-design-values.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty input-power design values: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in INPUT_POWER_DESIGN_VALUE_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    allowed_nets = {
        "VBAT_RAW",
        "VBAT_REV_PROT",
        "VBAT_PROT",
        "LM74700_VCAP",
        "INPUT_PROT_EN",
        "INPUT_FET_GATE",
        "IIN_SHUNT_HI",
        "IIN_SHUNT_LO",
        "IIN_MON_A0",
        "IIN_MON_A1",
        "PB_I2C_SCL",
        "PB_I2C_SDA",
        "PB_I2C_INT",
    }
    seen_items = set()
    for row_number, row in enumerate(rows, 2):
        design_item = row["Design item"].strip()
        if design_item not in REQUIRED_INPUT_POWER_ITEMS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: invalid design item {design_item}")
        if design_item in seen_items:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate design item {design_item}")
        seen_items.add(design_item)
        validate_no_role_tokens_in_row(path, row_number, row)
        for column in ("Block", "Related net", "Candidate direction", "Freeze dependency", "Notes"):
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_not_final_value_status(path, row_number, row["Value status"])
        if "schematic freeze" not in row["Freeze dependency"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: freeze dependency must reference schematic freeze")
        for net_name in [part.strip() for part in row["Related net"].split(";")]:
            if net_name not in allowed_nets:
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown input-power net {net_name}")
        if design_item == "Q1 package and copper path":
            row_text = " ".join(row.values())
            if not all(token in row_text for token in ("BUK7S1R2-80M", "LFPAK88", "80 V", "40 A")):
                fail("Q1 package and copper path must keep selected 80 V LFPAK88 and 40 A review explicit")
        if design_item == "Shunt value and power rating":
            row_text = " ".join(row.values()).lower()
            for token in ("four-terminal", "0.5m", "60a", "30mv", "1.8w", "40a", "0.8w"):
                if token not in row_text:
                    fail(f"input shunt design row must preserve {token} assumption")

    missing_items = sorted(REQUIRED_INPUT_POWER_ITEMS - seen_items)
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing input-power design items: "
            f"{', '.join(missing_items)}"
        )


def validate_input_reverse_package_trace() -> None:
    path = PB100_DIR / "PB-100-input-reverse-package-trace.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty input reverse package trace: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in INPUT_REVERSE_PACKAGE_TRACE_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    required_items = {
        "Controller gate path",
        "Rejected 60 V TOLL history",
        "Selected 80 V LFPAK88 path",
        "80 V alternatives",
        "Current measurement boundary",
        "Assembly sourcing gate",
    }
    rows_by_item: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        item = row["Trace item"].strip()
        if item in rows_by_item:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate trace item {item}")
        if item not in required_items:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown trace item {item}")
        rows_by_item[item] = row
        for column in INPUT_REVERSE_PACKAGE_TRACE_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        if "schematic freeze" not in " ".join(row.values()).lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: freeze dependency must reference schematic freeze")

    missing_items = sorted(required_items - rows_by_item.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing input reverse trace items: "
            f"{', '.join(missing_items)}"
        )

    trace_text = read_text(path)
    for token in (
        "IAUTN06S5N008ATMA1",
        "60 V",
        "TOLL",
        "0.76 mOhm",
        "2.43 W",
        "40 A",
        "BUK7S1R2-80M",
        "80 V",
        "LFPAK88",
        "1.2 mOhm",
        "3.84 W",
        "IAUTN08S5N012L",
        "BUK7J2R4-80M",
        "not approved substitutes",
        "0.5mΩ",
        "VBAT_REV_PROT",
        "IIN_SHUNT_HI/IIN_SHUNT_LO",
        "JLCPCB PCBWay",
    ):
        if token not in trace_text:
            fail(f"input reverse package trace must include {token}")

    controller_text = " ".join(rows_by_item["Controller gate path"].values())
    for token in ("LM74700QDBVRQ1", "INPUT_FET_GATE", "controller-unpowered off"):
        if token not in controller_text:
            fail(f"input reverse controller trace must include {token}")

    selected_text = " ".join(rows_by_item["Selected 80 V LFPAK88 path"].values())
    for token in ("BUK7S1R2-80M", "26.7 V", "40 A", "production-source"):
        if token not in selected_text:
            fail(f"selected 80 V Q1 trace must include {token}")

    alternatives_text = " ".join(rows_by_item["80 V alternatives"].values())
    for token in ("IAUTN08S5N012L", "BUK7J2R4-80M", "non-drop-in", "rejected"):
        if token not in alternatives_text:
            fail(f"80 V Q1 alternatives trace must include {token}")

    input_doc = read_text(PB100_DIR / "PB-100-input-reverse-protection.md")
    for token in (
        "BUK7S1R2-80M",
        "80 V LFPAK88",
        "IAUTN08S5N012L",
        "BUK7J2R4-80M",
        "not approved Rev.1 assembly substitutions",
    ):
        if token not in input_doc:
            fail(f"input reverse strategy document must include {token}")

    thermal_rows = list(csv.DictReader((PB100_DIR / "PB-100-thermal-estimates.csv").open(newline="", encoding="utf-8")))
    thermal_by_path = {row["Path"].strip(): row for row in thermal_rows}
    expected_thermal = {
        "BUK7S1R2-80M 80 V input reverse MOSFET": ("40", "0.0012", "3.84"),
        "IAUTN08S5N012L 80 V input reverse alternate": ("40", "0.0012", "3.84"),
        "BUK7J2R4-80M 80 V input reverse alternate": ("40", "0.0024", "7.68"),
    }
    for thermal_path, (current, rds, dissipation) in expected_thermal.items():
        row = thermal_by_path.get(thermal_path)
        if row is None:
            fail(f"thermal estimates must include {thermal_path}")
        if row["Current A"].strip() != current:
            fail(f"{thermal_path} current must remain {current}")
        if row["Rds or Ron ohm"].strip() != rds:
            fail(f"{thermal_path} Rds must remain {rds}")
        if row["Estimated dissipation W"].strip() != dissipation:
            fail(f"{thermal_path} dissipation must remain {dissipation}")

    pin_contract_rows = list(csv.DictReader((PB100_DIR / "PB-100-input-protection-pin-contract.csv").open(newline="", encoding="utf-8")))
    q1_nets = {row["Planned net"].strip() for row in pin_contract_rows if row["Ref"].strip() == "Q1"}
    if q1_nets != {"VBAT_RAW", "VBAT_REV_PROT", "INPUT_FET_GATE"}:
        fail("Q1 input pin contract must map VBAT_RAW VBAT_REV_PROT and INPUT_FET_GATE")

    input_power_text = read_text(PB100_DIR / "PB-100-input-power-design-values.csv")
    for token in ("BUK7S1R2-80M LFPAK88 selected", "40 A SOA copper thermal", "0.5mΩ"):
        if token not in input_power_text:
            fail(f"input power values must preserve input reverse token {token}")

    protection_text = read_text(PB100_DIR / "PB-100-protection-validation.csv")
    for token in (
        "BUK7S1R2-80M input reverse MOSFET,80V VDS",
        "Selected with 26.7V nominal margin",
        "Rejected Rev.1 baseline",
    ):
        if token not in protection_text:
            fail(f"protection validation must preserve input reverse token {token}")

    checked_paths = (
        PB100_DIR / "PB-100-symbol-mpn-readiness.csv",
        PB100_DIR / "PB-100-kicad-footprint-plan.csv",
        REPO_ROOT / "production" / "bom" / "factory_bom_draft.csv",
        REPO_ROOT / "production" / "bom" / "pb100_assembly_sourcing_recheck.csv",
        REPO_ROOT / "production" / "bom" / "pb100_sourcing_evidence_snapshot.csv",
        REPO_ROOT / "docs" / "production" / "component-family-shortlist.md",
    )
    for checked_path in checked_paths:
        checked_text = read_text(checked_path)
        for token in ("BUK7S1R2-80M", "IAUTN08S5N012", "BUK7J2R4-80M"):
            if token not in checked_text:
                fail(f"{checked_path.relative_to(REPO_ROOT)} must retain input reverse alternate {token}")


def validate_input_reverse_freeze_review() -> None:
    path = PB100_DIR / "PB-100-input-reverse-freeze-review.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty input reverse freeze review: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in OUTPUT_FREEZE_REVIEW_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_item: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        review_item = row["Review item"].strip()
        if review_item not in REQUIRED_INPUT_REVERSE_FREEZE_REVIEW_ITEMS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown input reverse review item {review_item}")
        if review_item in rows_by_item:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate input reverse review item {review_item}")
        rows_by_item[review_item] = row
        for column in OUTPUT_FREEZE_REVIEW_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)

    missing_items = sorted(REQUIRED_INPUT_REVERSE_FREEZE_REVIEW_ITEMS - rows_by_item.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing input reverse review items: "
            f"{', '.join(missing_items)}"
        )

    review_text = read_text(path)
    for token in (
        "LM74700-Q1",
        "INPUT_FET_GATE",
        "controller-unpowered off state",
        "LM74502-Q1",
        "IAUTN06S5N008ATMA1",
        "Rejected 60V",
        "BUK7S1R2-80M",
        "80V LFPAK88",
        "3.84W at 40A",
        "IAUTN08S5N012L",
        "BUK7J2R4-80M",
        "non-drop-in alternatives",
        "VBAT_REV_PROT",
        "VBAT_PROT",
        "IIN_SHUNT_HI",
        "IIN_SHUNT_LO",
        "HM3 TVS",
        "JLCPCB PCBWay",
        "critical alternatives",
        "No PCB layout",
        "PB-100.kicad_pcb",
    ):
        if token not in review_text:
            fail(f"input reverse freeze review must include {token}")

    trace_text = read_text(PB100_DIR / "PB-100-input-reverse-package-trace.csv")
    for token in ("IAUTN06S5N008ATMA1", "BUK7S1R2-80M", "IAUTN08S5N012L", "BUK7J2R4-80M", "40 A", "JLCPCB PCBWay"):
        if token not in trace_text:
            fail(f"input reverse package trace must support freeze review token {token}")

    pin_contract_text = read_text(PB100_DIR / "PB-100-input-protection-pin-contract.csv")
    for token in ("Q1", "VBAT_RAW", "VBAT_REV_PROT", "INPUT_FET_GATE", "IIN_SHUNT_HI", "IIN_SHUNT_LO"):
        if token not in pin_contract_text:
            fail(f"input protection pin contract must support freeze review token {token}")

    tvs_margin_text = read_text(PB100_DIR / "PB-100-tvs-load-dump-margin-trace.csv")
    for token in ("IAUTN06S5N008", "60 V", "BUK7S1R2-80M", "80 V", "SM8S33AHM3/I"):
        if token not in tvs_margin_text:
            fail(f"TVS margin trace must support input reverse freeze review token {token}")

    sourcing_text = read_text(REPO_ROOT / "production" / "bom" / "pb100_assembly_sourcing_recheck.csv")
    for token in ("INPUT_REVERSE_FET", "LFPAK88", "BUK7S1R2-80M", "IAUTN08S5N012L", "BUK7J2R4-80M"):
        if token not in sourcing_text:
            fail(f"assembly sourcing recheck must support input reverse freeze review token {token}")


def validate_input_reverse_q1_freeze_checklist() -> None:
    path = PB100_DIR / "PB-100-input-reverse-q1-freeze-checklist.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty input reverse Q1 freeze checklist: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in INPUT_REVERSE_Q1_FREEZE_CHECKLIST_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_check: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        check_id = row["Check ID"].strip()
        if check_id not in REQUIRED_INPUT_REVERSE_Q1_FREEZE_CHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown input reverse Q1 check {check_id}")
        if check_id in rows_by_check:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate input reverse Q1 check {check_id}")
        rows_by_check[check_id] = row
        for column in INPUT_REVERSE_Q1_FREEZE_CHECKLIST_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        row_text = " ".join(row.values()).lower()
        if check_id == "Q1-FRZ-002" and ("input_fet_gate" not in row_text or "turn-off timing" not in row_text):
            fail("Q1 gate checklist row must keep INPUT_FET_GATE and turn-off timing explicit")
        if check_id == "Q1-FRZ-003" and not all(
            token in row_text for token in ("iautn06s5n008atma1", "dual sidr626ldp", "not approved")
        ):
            fail("Q1 rejected-60V checklist row must keep historical paths and exclusion explicit")
        if check_id == "Q1-FRZ-004" and not all(
            token in row_text for token in ("buk7s1r2-80m", "80 v", "lfpak88", "3.84w at 40a")
        ):
            fail("Q1 selected checklist row must keep BUK7S1R2-80M 80 V LFPAK88 explicit")
        if check_id == "Q1-FRZ-005" and not all(
            token in row_text for token in ("iautn08s5n012l", "buk7j2r4-80m", "non-drop-in")
        ):
            fail("Q1 alternatives checklist row must preserve two 80 V non-drop-in alternatives")
        if check_id == "Q1-FRZ-006" and ("vbat_rev_prot" not in row_text or "iin_shunt_hi" not in row_text or "vbat_prot" not in row_text):
            fail("Q1 measurement sequence checklist row must keep protected telemetry sequence explicit")
        if check_id == "Q1-FRZ-009" and ("no pcb layout" not in row_text or "pb-100.kicad_pcb" not in row_text):
            fail("Q1 no-layout checklist row must block PCB layout explicitly")

    missing_checks = sorted(REQUIRED_INPUT_REVERSE_Q1_FREEZE_CHECKS - rows_by_check.keys())
    if missing_checks:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing input reverse Q1 checks: "
            f"{', '.join(missing_checks)}"
        )

    checklist_text = read_text(path)
    for token in (
        "LM74700-Q1",
        "LM74502-Q1",
        "INPUT_FET_GATE",
        "IAUTN06S5N008ATMA1",
        "not approved Rev.1 assembly substitutions",
        "BUK7S1R2-80M",
        "80 V LFPAK88",
        "3.84W at 40A",
        "IAUTN08S5N012L",
        "BUK7J2R4-80M",
        "non-drop-in alternatives",
        "VBAT_REV_PROT",
        "IIN_SHUNT_HI",
        "IIN_SHUNT_LO",
        "VBAT_PROT",
        "40 A thermal",
        "JLCPCB PCBWay",
        "No PCB layout",
        "PB-100.kicad_pcb",
    ):
        if token not in checklist_text:
            fail(f"input reverse Q1 freeze checklist must include {token}")


def validate_input_reverse_q1_derivation_precheck() -> None:
    path = PB100_DIR / "PB-100-input-reverse-q1-derivation-precheck.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty input reverse Q1 derivation precheck: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in INPUT_REVERSE_Q1_DERIVATION_PRECHECK_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_id: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        derivation_id = row["Derivation ID"].strip()
        if derivation_id not in REQUIRED_INPUT_REVERSE_Q1_DERIVATION_CHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown Q1 derivation item {derivation_id}")
        if derivation_id in rows_by_id:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate Q1 derivation item {derivation_id}")
        rows_by_id[derivation_id] = row
        for column in INPUT_REVERSE_Q1_DERIVATION_PRECHECK_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        row_text = " ".join(row.values()).lower()
        if derivation_id == "Q1-DER-002" and ("equation 1" not in row_text or "0.1uf" not in row_text):
            fail("Q1 derivation precheck must include VCAP Equation 1 and 0.1uF minimum")
        if derivation_id == "Q1-DER-003" and ("gate" not in row_text or "anode" not in row_text or "disabled" not in row_text):
            fail("Q1 derivation precheck must keep gate default-off conditions explicit")
        if derivation_id == "Q1-DER-005" and ("0.5mω" not in row_text or "1.25mω" not in row_text):
            fail("Q1 derivation precheck must include 40 A RDS(on) operating window")
        if derivation_id == "Q1-DER-010" and ("pb-100.kicad_pcb" not in row_text or "manufacturing" not in row_text):
            fail("Q1 derivation precheck must block layout and manufacturing outputs")

    missing_items = sorted(REQUIRED_INPUT_REVERSE_Q1_DERIVATION_CHECKS - rows_by_id.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing Q1 derivation items: "
            f"{', '.join(missing_items)}"
        )

    precheck_text = read_text(path)
    for token in (
        "TI LM74700-Q1",
        "LM74502-Q1",
        "INPUT_FET_GATE",
        "LM74700_VCAP",
        "Equation 1",
        "6.6V",
        "0.1uF",
        "10 times MOSFET CISS",
        "20mV",
        "50mV",
        "-11mV",
        "0.5mΩ",
        "1.25mΩ",
        "BUK7S1R2-80M",
        "80V LFPAK88",
        "IAUTN08S5N012L",
        "BUK7J2R4-80M",
        "60V paths are rejected",
        "SM8S33AHM3/I",
        "VBAT_REV_PROT",
        "IIN_SHUNT_HI",
        "IIN_SHUNT_LO",
        "VBAT_PROT",
        "JLCPCB PCBWay",
        "PB-100.kicad_pcb",
    ):
        if token not in precheck_text:
            fail(f"input reverse Q1 derivation precheck must include {token}")


def validate_input_reverse_q1_closeout_precheck() -> None:
    path = PB100_DIR / "PB-100-input-reverse-q1-closeout-precheck.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty input reverse Q1 closeout precheck: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in INPUT_REVERSE_Q1_CLOSEOUT_PRECHECK_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_id: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        precheck_id = row["Precheck ID"].strip()
        if precheck_id not in REQUIRED_INPUT_REVERSE_Q1_CLOSEOUT_PRECHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown Q1 closeout precheck {precheck_id}")
        if precheck_id in rows_by_id:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate Q1 closeout precheck {precheck_id}")
        rows_by_id[precheck_id] = row
        for column in INPUT_REVERSE_Q1_CLOSEOUT_PRECHECK_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        row_text = " ".join(row.values()).lower()
        if "do not" not in row["Blocked action"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: blocked action must be explicit")
        if precheck_id == "Q1-CLS-005" and not all(
            token in row_text
            for token in ("buk7s1r2-80m", "iautn08s5n012l", "buk7j2r4-80m", "60 v paths are rejected")
        ):
            fail("Q1 closeout package row must keep selected and two 80 V alternate paths explicit")
        if precheck_id == "Q1-CLS-010" and ("no pcb layout" not in row_text or "pb-100.kicad_pcb" not in row_text):
            fail("Q1 closeout no-layout row must block PCB layout explicitly")

    missing_items = sorted(REQUIRED_INPUT_REVERSE_Q1_CLOSEOUT_PRECHECKS - rows_by_id.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing Q1 closeout prechecks: "
            f"{', '.join(missing_items)}"
        )

    precheck_text = read_text(path)
    for token in (
        "TI LM74700-Q1",
        "LM74700QDBVRQ1",
        "LM74502-Q1",
        "Equation 1",
        "TDRV_EN",
        "C(VCAP)",
        "V(VCAP_UVLOR)",
        "300uA",
        "0.1uF",
        "VCAP",
        "CISS",
        "EN",
        "VCAP-to-ANODE",
        "GATE internally connected to ANODE",
        "INPUT_FET_GATE",
        "20mV forward regulation",
        "50mV conduction",
        "-11mV reverse-current shutdown",
        "VBAT_RAW",
        "VBAT_REV_PROT",
        "VBAT_PROT",
        "0.5mΩ to 1.25mΩ",
        "RDS(on)",
        "40A",
        "BUK7S1R2-80M",
        "80 V",
        "LFPAK88",
        "1.2mΩ",
        "3.84W at 40A",
        "IAUTN08S5N012L",
        "BUK7J2R4-80M",
        "non-drop-in 80 V alternatives",
        "60 V paths are rejected",
        "SM8S33AHM3/I",
        "TVS",
        "peak stress margin",
        "80V limit",
        "IIN_SHUNT_HI",
        "IIN_SHUNT_LO",
        "0.5mΩ shunt",
        "50A fuse",
        "JLCPCB PCBWay",
        "at least two alternatives",
        "input-protection.kicad_sch",
        "CAP-INP",
        "PB-100-input-power-design-values.csv",
        "PB-100-input-protection-pin-contract.csv",
        "PB-100-input-controller-pin-template.csv",
        "No PCB layout",
        "PB-100.kicad_pcb",
        "Q1 placement",
        "high-current copper",
        "thermal relief",
        "Gerbers",
        "drills",
        "pick-place",
        "manufacturing ZIP",
    ):
        if token not in precheck_text:
            fail(f"input reverse Q1 closeout precheck must include {token}")

    for supporting_artifact, tokens in {
        "PB-100-input-reverse-q1-freeze-checklist.csv": ("Q1-FRZ-003", "Q1-FRZ-009"),
        "PB-100-input-reverse-q1-derivation-precheck.csv": ("Q1-DER-002", "Q1-DER-010"),
        "PB-100-input-reverse-package-trace.csv": ("BUK7S1R2-80M", "IAUTN08S5N012L", "BUK7J2R4-80M"),
    }.items():
        supporting_text = read_text(PB100_DIR / supporting_artifact)
        for token in tokens:
            if token not in supporting_text:
                fail(f"Q1 closeout precheck requires {supporting_artifact} token {token}")


def validate_logic_power_design_values() -> None:
    path = PB100_DIR / "PB-100-logic-power-design-values.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty logic-power design values: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in LOGIC_POWER_DESIGN_VALUE_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    allowed_nets = {
        "VBAT_PROT",
        "BUCK_EN_UVLO",
        "BUCK_RON_SET",
        "BUCK_FB",
        "BUCK_BST",
        "BUCK_SW",
        "L1",
        "PB_5V_OUT",
        "PB_PWR_GOOD",
    }
    seen_items = set()
    for row_number, row in enumerate(rows, 2):
        design_item = row["Design item"].strip()
        if design_item not in REQUIRED_LOGIC_POWER_VALUE_ITEMS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: invalid design item {design_item}")
        if design_item in seen_items:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate design item {design_item}")
        seen_items.add(design_item)
        validate_no_role_tokens_in_row(path, row_number, row)
        for column in ("Related net", "Candidate direction", "Freeze dependency", "Notes"):
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_not_final_value_status(path, row_number, row["Value status"])
        if "schematic freeze" not in row["Freeze dependency"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: freeze dependency must reference schematic freeze")
        related_net = row["Related net"].strip()
        if related_net not in allowed_nets:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown logic-power net/ref {related_net}")
        if design_item == "Higher-current fallback" and "LM5013-Q1" not in " ".join(row.values()):
            fail("logic-power higher-current fallback must preserve LM5013-Q1-class option")
        if related_net == "PB_5V_OUT" and "accessory" in " ".join(row.values()).lower() and "must not" not in " ".join(row.values()).lower():
            fail("PB_5V_OUT rows must not allow accessory loads")

    missing_items = sorted(REQUIRED_LOGIC_POWER_VALUE_ITEMS - seen_items)
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing logic-power design items: "
            f"{', '.join(missing_items)}"
        )


def validate_logic_power_freeze_review() -> None:
    path = PB100_DIR / "PB-100-logic-power-freeze-review.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty logic-power freeze review: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in OUTPUT_FREEZE_REVIEW_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_item: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        review_item = row["Review item"].strip()
        if review_item not in REQUIRED_LOGIC_POWER_FREEZE_REVIEW_ITEMS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown logic-power review item {review_item}")
        if review_item in rows_by_item:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate logic-power review item {review_item}")
        rows_by_item[review_item] = row
        for column in OUTPUT_FREEZE_REVIEW_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)

    missing_items = sorted(REQUIRED_LOGIC_POWER_FREEZE_REVIEW_ITEMS - rows_by_item.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing logic-power review items: "
            f"{', '.join(missing_items)}"
        )

    review_text = read_text(path)
    for token in (
        "LM5164-Q1-class",
        "100 V 1 A",
        "LM5013-Q1-class",
        "TPS54360B-Q1-class",
        "TVS margin",
        "VBAT_PROT",
        "VBAT_RAW",
        "PB_5V_OUT",
        "1000 mA",
        "accessory loads",
        "BUCK_EN_UVLO",
        "OUT1..OUT10",
        "LB_3V3_IO",
        "BUCK_RON_SET",
        "BUCK_FB",
        "BUCK_BST",
        "BUCK_SW",
        "L1",
        "CIN",
        "COUT",
        "AEC-Q200",
        "PB_PWR_GOOD",
        "LOGIC_BUCK",
        "LOGIC_BUCK_INDUCTOR",
        "LM5164QDDATQ1",
        "SO PowerPAD",
        "JLCPCB PCBWay",
        "critical alternatives",
        "No PCB layout",
        "PB-100.kicad_pcb",
    ):
        if token not in review_text:
            fail(f"logic-power freeze review must include {token}")

    rail_text = read_text(PB100_DIR / "PB-100-logic-power-rail-trace.csv")
    for token in (
        "LM5164-Q1-class 100 V 1 A",
        "LM5013-Q1-class 100 V fallback",
        "TPS54360B-Q1-class 60 V path remains conditional",
        "PB_5V_OUT must not power accessory loads",
        "PB_PWR_GOOD",
        "default off",
    ):
        if token not in rail_text:
            fail(f"logic power rail trace must support freeze review token {token}")

    budget_text = read_text(PB100_DIR / "PB-100-logic-power-budget.csv")
    for token in ("Initial total", "1000", "LM5013-Q1-class"):
        if token not in budget_text:
            fail(f"logic power budget must support freeze review token {token}")

    design_text = read_text(PB100_DIR / "PB-100-logic-power-design-values.csv")
    for token in (
        "BUCK_EN_UVLO",
        "BUCK_RON_SET",
        "BUCK_FB",
        "BUCK_BST",
        "BUCK_SW",
        "PB_PWR_GOOD",
        "TBD not final",
        "No layout geometry before freeze",
    ):
        if token not in design_text:
            fail(f"logic power design values must support freeze review token {token}")

    pin_template_text = read_text(PB100_DIR / "PB-100-logic-buck-pin-template.csv")
    for token in ("VIN", "EN/UVLO", "RON", "FB", "PGOOD", "BST", "SW", "EP"):
        if token not in pin_template_text:
            fail(f"logic buck pin template must support freeze review token {token}")

    sourcing_text = read_text(REPO_ROOT / "production" / "bom" / "pb100_assembly_sourcing_recheck.csv")
    for token in ("LOGIC_BUCK", "LOGIC_BUCK_INDUCTOR", "LM5164QDDATQ1", "LM5013-Q1", "TPS54360B-Q1"):
        if token not in sourcing_text:
            fail(f"assembly sourcing recheck must support logic-power freeze review token {token}")


def validate_logic_power_value_freeze_checklist() -> None:
    path = PB100_DIR / "PB-100-logic-power-value-freeze-checklist.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty logic-power value freeze checklist: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in LOGIC_POWER_VALUE_FREEZE_CHECKLIST_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_check: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        check_id = row["Check ID"].strip()
        if check_id not in REQUIRED_LOGIC_POWER_VALUE_FREEZE_CHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown logic-power freeze check {check_id}")
        if check_id in rows_by_check:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate logic-power freeze check {check_id}")
        rows_by_check[check_id] = row
        for column in LOGIC_POWER_VALUE_FREEZE_CHECKLIST_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)

    missing_checks = sorted(REQUIRED_LOGIC_POWER_VALUE_FREEZE_CHECKS - rows_by_check.keys())
    if missing_checks:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing logic-power freeze checks: "
            f"{', '.join(missing_checks)}"
        )

    checklist_text = read_text(path)
    for token in (
        "LM5164-Q1-class",
        "100 V 1 A",
        "LM5013-Q1-class",
        "100 V 3.5 A",
        "TPS54360B-Q1-class",
        "TVS margin",
        "PB_5V_OUT",
        "1000 mA",
        "500 mA LB-100",
        "accessory loads",
        "VBAT_PROT",
        "VBAT_RAW",
        "2.2µF 100V X7R",
        "10µF 100V",
        "BUCK_EN_UVLO",
        "332kΩ",
        "100kΩ",
        "6.48V rising UVLO",
        "4.75V shutdown",
        "OUT1..OUT10",
        "LB_3V3_IO",
        "BUCK_RON_SET",
        "41.2kΩ",
        "300kHz",
        "BUCK_FB",
        "158kΩ",
        "49.9kΩ",
        "5.0V",
        "1.2V reference",
        "BUCK_BST",
        "2.2nF 50V X7R",
        "L1",
        "47µH",
        "AEC-Q200",
        "Isat at least 2.2A",
        "Irms at least 1.2A",
        "COUT",
        "2x22µF 10V X7R",
        "DC-bias",
        "PB_PWR_GOOD",
        "47kΩ",
        "10nF DNP",
        "BUCK_SW",
        "DNP RC snubber",
        "LOGIC_BUCK",
        "LOGIC_BUCK_INDUCTOR",
        "JLCPCB PCBWay",
        "LM5164QDDATQ1",
        "LM5164QDDARQ1",
        "No PCB layout",
        "PB-100.kicad_pcb",
        "Gerbers",
        "drills",
        "pick-place",
    ):
        if token not in checklist_text:
            fail(f"logic-power value freeze checklist must include {token}")

    design_text = read_text(PB100_DIR / "PB-100-logic-power-design-values.csv")
    for token in ("41.2kΩ", "158kΩ", "49.9kΩ", "47µH", "PB_PWR_GOOD", "TBD not final"):
        if token not in design_text:
            fail(f"logic-power design values must support freeze checklist token {token}")

    calculation_text = read_text(PB100_DIR / "PB-100-logic-power-design-calculation.md")
    for token in ("6.48 V", "4.75 V", "2.2 nF", "47 µH", "47 kΩ"):
        if token not in calculation_text:
            fail(f"logic-power design calculation must support freeze checklist token {token}")

    lb_precheck_text = read_text(REPO_ROOT / "hardware" / "logic-board" / "LB-100" / "LB-100-power-budget-precheck.md")
    for token in ("500 mA", "PB_5V_OUT", "LM5013-Q1-class", "PB_PWR_GOOD"):
        if token not in lb_precheck_text:
            fail(f"LB-100 power-budget precheck must support logic-power freeze checklist token {token}")


def validate_logic_power_value_derivation_precheck() -> None:
    path = PB100_DIR / "PB-100-logic-power-value-derivation-precheck.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty logic-power value derivation precheck: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in LOGIC_POWER_VALUE_DERIVATION_PRECHECK_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_id: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        derivation_id = row["Derivation ID"].strip()
        if derivation_id not in REQUIRED_LOGIC_POWER_VALUE_DERIVATION_CHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown logic-power derivation item {derivation_id}")
        if derivation_id in rows_by_id:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate logic-power derivation item {derivation_id}")
        rows_by_id[derivation_id] = row
        for column in LOGIC_POWER_VALUE_DERIVATION_PRECHECK_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        row_text = " ".join(row.values()).lower()
        if derivation_id == "LOGIC-DER-004" and ("vin =" not in row_text or "uvlo" not in row_text):
            fail("logic-power derivation precheck must include UVLO threshold equation")
        if derivation_id == "LOGIC-DER-005" and ("fsw" not in row_text or "rron" not in row_text):
            fail("logic-power derivation precheck must include RON frequency equation")
        if derivation_id == "LOGIC-DER-006" and ("vout =" not in row_text or "1.2v" not in row_text):
            fail("logic-power derivation precheck must include feedback equation and 1.2V reference")
        if derivation_id == "LOGIC-DER-010" and ("pb-100.kicad_pcb" not in row_text or "manufacturing" not in row_text):
            fail("logic-power derivation precheck must block layout and manufacturing outputs")

    missing_items = sorted(REQUIRED_LOGIC_POWER_VALUE_DERIVATION_CHECKS - rows_by_id.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing logic-power derivation items: "
            f"{', '.join(missing_items)}"
        )

    precheck_text = read_text(path)
    for token in (
        "TI LM5164-Q1",
        "6 V to 100 V input 1 A",
        "TI LM5013-Q1",
        "100 V 3.5 A",
        "TPS54360B-Q1",
        "60 V conditional alternate",
        "PB_5V_OUT",
        "1000 mA",
        "500 mA LB-100",
        "accessory loads",
        "VBAT_PROT",
        "VBAT_RAW",
        "2.2µF 100V X7R",
        "0.1µF",
        "10µF 100V",
        "PB-100-tvs-overshoot-validation-precheck.csv",
        "332kΩ",
        "100kΩ",
        "6.48 V rising UVLO",
        "4.75 V shutdown",
        "OUT1..OUT10",
        "LB_3V3_IO",
        "fSW ≈ VOUT × 2500 / RRON(kΩ)",
        "41.2kΩ",
        "300kHz",
        "VOUT = VFB × (1 + RFB_TOP / RFB_BOT)",
        "158kΩ",
        "49.9kΩ",
        "5.0V",
        "1.2V",
        "2.2nF 50V X7R",
        "PB_PWR_GOOD",
        "47kΩ",
        "10nF DNP",
        "47µH",
        "AEC-Q200",
        "Isat at least 2.2A",
        "Irms at least 1.2A",
        "2x22µF 10V X7R",
        "DC-bias",
        "DNP RC snubber",
        "JLCPCB PCBWay",
        "LM5164QDDATQ1",
        "LM5164QDDARQ1",
        "LOGIC_BUCK_INDUCTOR",
        "PB-100.kicad_pcb",
        "Gerbers",
        "drills",
        "pick-place",
    ):
        if token not in precheck_text:
            fail(f"logic-power value derivation precheck must include {token}")

    checklist_text = read_text(PB100_DIR / "PB-100-logic-power-value-freeze-checklist.csv")
    for token in ("LOGIC-FRZ-004", "LOGIC-FRZ-005", "LOGIC-FRZ-006", "LOGIC-FRZ-007"):
        if token not in checklist_text:
            fail(f"logic-power value freeze checklist must support derivation token {token}")


def validate_logic_power_closeout_precheck() -> None:
    path = PB100_DIR / "PB-100-logic-power-closeout-precheck.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty logic-power closeout precheck: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in LOGIC_POWER_CLOSEOUT_PRECHECK_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_id: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        precheck_id = row["Precheck ID"].strip()
        if precheck_id not in REQUIRED_LOGIC_POWER_CLOSEOUT_PRECHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown logic-power closeout precheck {precheck_id}")
        if precheck_id in rows_by_id:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate logic-power closeout precheck {precheck_id}")
        rows_by_id[precheck_id] = row
        for column in LOGIC_POWER_CLOSEOUT_PRECHECK_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        row_text = " ".join(row.values()).lower()
        if "do not" not in row["Blocked action"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: blocked action must be explicit")
        if precheck_id == "LOGIC-CLS-002" and ("pb_5v_out" not in row_text or "accessory loads" not in row_text):
            fail("logic-power closeout load budget row must keep PB_5V_OUT accessory-load boundary")
        if precheck_id == "LOGIC-CLS-010" and ("no pcb layout" not in row_text or "pb-100.kicad_pcb" not in row_text):
            fail("logic-power closeout no-layout row must block PCB layout explicitly")

    missing_items = sorted(REQUIRED_LOGIC_POWER_CLOSEOUT_PRECHECKS - rows_by_id.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing logic-power closeout prechecks: "
            f"{', '.join(missing_items)}"
        )

    precheck_text = read_text(path)
    for token in (
        "LM5164-Q1-class",
        "100 V 1 A",
        "LM5013-Q1-class",
        "100 V 3.5 A",
        "TPS54360B-Q1-class",
        "TVS margin",
        "PBREL-007",
        "PB_5V_OUT",
        "1000 mA",
        "500 mA LB-100",
        "500 mA PB-side",
        "accessory loads",
        "hardware/logic-board/LB-100/LB-100-power-budget-precheck.md",
        "VBAT_PROT",
        "U3 VIN",
        "VBAT_RAW",
        "2.2µF 100V X7R",
        "0.1µF",
        "10µF 100V",
        "PB-100-tvs-overshoot-closeout-precheck.csv",
        "BUCK_EN_UVLO",
        "332kΩ",
        "100kΩ",
        "6.48 V rising UVLO",
        "4.75 V shutdown",
        "OUT1..OUT10",
        "LB_3V3_IO",
        "PB_PWR_GOOD",
        "BUCK_RON_SET",
        "41.2kΩ",
        "300kHz",
        "BUCK_FB",
        "158kΩ",
        "49.9kΩ",
        "5.0V",
        "1.2V reference",
        "BUCK_BST",
        "2.2nF 50V X7R",
        "L1",
        "47µH",
        "AEC-Q200",
        "Isat at least 2.2A",
        "Irms at least 1.2A",
        "COUT",
        "2x22µF 10V X7R",
        "DC-bias",
        "47kΩ",
        "10nF DNP",
        "BUCK_SW",
        "DNP RC snubber",
        "switch-node ringing",
        "LOGIC_BUCK",
        "LOGIC_BUCK_INDUCTOR",
        "JLCPCB PCBWay",
        "LM5164QDDATQ1",
        "LM5164QDDARQ1",
        "LM5013-Q1",
        "TPS54360B-Q1",
        "No PCB layout",
        "PB-100.kicad_pcb",
        "U3 placement",
        "L1 placement",
        "switch-node copper",
        "thermal-pad vias",
        "Gerbers",
        "drills",
        "pick-place",
        "manufacturing ZIP",
    ):
        if token not in precheck_text:
            fail(f"logic-power closeout precheck must include {token}")

    for supporting_artifact, tokens in {
        "PB-100-logic-power-value-freeze-checklist.csv": ("LOGIC-FRZ-002", "LOGIC-FRZ-010"),
        "PB-100-logic-power-value-derivation-precheck.csv": ("LOGIC-DER-004", "LOGIC-DER-010"),
        "PB-100-logic-power-design-values.csv": ("BUCK_EN_UVLO", "TBD not final", "PB_PWR_GOOD"),
    }.items():
        supporting_text = read_text(PB100_DIR / supporting_artifact)
        for token in tokens:
            if token not in supporting_text:
                fail(f"logic-power closeout precheck requires {supporting_artifact} token {token}")


def validate_can1_tx_disable_trace() -> None:
    path = PB100_DIR / "PB-100-can1-tx-disable-trace.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty CAN1 TX-disable trace: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in CAN1_TX_DISABLE_TRACE_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    required_items = {
        "Policy baseline",
        "TX missing-link",
        "Disable command default",
        "Disabled status readback",
        "RX independence",
        "Firmware listen-only",
        "Production ownership",
    }
    rows_by_item: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        item = row["Trace item"].strip()
        if item in rows_by_item:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate trace item {item}")
        if item not in required_items:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown trace item {item}")
        rows_by_item[item] = row
        for column in CAN1_TX_DISABLE_TRACE_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        if "schematic freeze" not in " ".join(row.values()).lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: freeze dependency must reference schematic freeze")

    missing_items = sorted(required_items - rows_by_item.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing CAN1 trace items: "
            f"{', '.join(missing_items)}"
        )

    trace_text = read_text(path)
    for token in (
        "ADR-0002",
        "Architecture v1.0",
        "configuration cannot enable TX",
        "future ADR",
        "explicit hardware action",
        "CAN1_TX_ROUTE",
        "JP_CAN1",
        "DNP/open",
        "no default-populated TX",
        "CAN1_TX_DISABLE_CMD",
        "U_CAN1",
        "hardware pull",
        "LB-100 is reset unpowered or absent",
        "CAN1_TX_DISABLED_STATUS",
        "physical disabled state",
        "not firmware-only",
        "CAN1_RX_ROUTE",
        "listen-only RX",
        "firmware/services/can_safety.c",
        "CAN1 TX denied",
        "CAN2 expansion TX remains separate",
        "CAN1_TX_DISABLE",
        "Default DNP/open",
        "JLCPCB PCBWay",
    ):
        if token not in trace_text:
            fail(f"CAN1 TX-disable trace must include {token}")

    safety_rows = list(csv.DictReader((PB100_DIR / "PB-100-can1-safety-verification.csv").open(newline="", encoding="utf-8")))
    safety_by_requirement = {row["Requirement"].strip(): row for row in safety_rows}
    for requirement in REQUIRED_CAN1_SAFETY_REQUIREMENTS:
        if requirement not in safety_by_requirement:
            fail(f"CAN1 safety matrix must include {requirement}")
    tx_path_text = " ".join(safety_by_requirement["TX physical path"].values()).lower()
    for token in ("can1_tx_route", "dnp/open", "no default-populated tx", "future-adr"):
        if token not in tx_path_text:
            fail(f"CAN1 TX physical path safety row must include {token}")
    status_text = " ".join(safety_by_requirement["Disabled status"].values()).lower()
    if "physical disabled state" not in status_text or "not firmware-only" not in status_text:
        fail("CAN1 disabled-status safety row must require physical non-firmware-only readback")
    firmware_row_text = " ".join(safety_by_requirement["Firmware safety"].values()).lower()
    if "listen-only" not in firmware_row_text or "blocks tx" not in firmware_row_text:
        fail("CAN1 firmware safety row must keep listen-only TX block explicit")

    net_domain_rows = list(csv.DictReader((PB100_DIR / "PB-100-schematic-net-domain-plan.csv").open(newline="", encoding="utf-8")))
    net_domain_by_pattern = {row["Net pattern"].strip(): row for row in net_domain_rows}
    expected_net_defaults = {
        "CAN1_TX_DISABLE_CMD": "Disable asserted by hardware pull",
        "CAN1_TX_DISABLED_STATUS": "Asserted when disabled",
        "CAN1_RX_ROUTE": "DNP unless CAN1 crosses PB-100",
        "CAN1_TX_ROUTE": "DNP/open by default",
    }
    for net_pattern, expected_default in expected_net_defaults.items():
        row = net_domain_by_pattern.get(net_pattern)
        if row is None:
            fail(f"CAN1 net-domain plan must include {net_pattern}")
        if row["Default state"].strip() != expected_default:
            fail(f"CAN1 net-domain default for {net_pattern} must remain {expected_default}")

    b2b_rows = list(csv.DictReader((PB100_DIR / "PB-100-b2b-pin-map.csv").open(newline="", encoding="utf-8")))
    b2b_nets = {row["Net"].strip() for row in b2b_rows}
    for net in expected_net_defaults:
        if net not in b2b_nets:
            fail(f"CAN1 signal {net} must remain visible in JPB1 pin map")

    capabilities = json.loads(read_text(REPO_ROOT / "firmware" / "configs" / "hardware" / "pb-100-capabilities.json"))
    can1 = capabilities["safety"]["can1"]
    if can1["vehicle_can_read_only_default"] is not True:
        fail("PB-100 capability manifest must keep CAN1 vehicle_can_read_only_default true")
    if can1["tx_route_population"] != "DNP/open":
        fail("PB-100 capability manifest must keep CAN1 tx_route_population DNP/open")
    if can1["tx_requires_future_adr"] is not True:
        fail("PB-100 capability manifest must keep CAN1 tx_requires_future_adr true")
    if can1["hardware_action_required_for_tx"] is not True:
        fail("PB-100 capability manifest must keep CAN1 hardware_action_required_for_tx true")
    if can1["disabled_status_signal"] != "CAN1_TX_DISABLED_STATUS":
        fail("PB-100 capability manifest must keep CAN1 disabled status signal")

    firmware_text = read_text(REPO_ROOT / "firmware" / "services" / "can_safety.c")
    for token in ("SVC_CAN_TX_DENY", "SVC_CAN_PORT_CAN2_EXPANSION", "SVC_CAN_TX_ALLOW"):
        if token not in firmware_text:
            fail(f"CAN safety firmware must include {token}")
    firmware_tests = read_text(REPO_ROOT / "firmware" / "tests" / "test_can_safety.c")
    for token in (
        "test_can1_tx_is_denied_when_disabled_status_true",
        "test_can1_tx_is_denied_when_disabled_status_false",
        "test_can2_tx_is_allowed_for_expansion",
    ):
        if token not in firmware_tests:
            fail(f"CAN safety tests must include {token}")

    checked_texts = {
        "CAN1 TX-disable input": read_text(PB100_DIR / "PB-100-can1-tx-disable.md"),
        "CAN safety doc": read_text(REPO_ROOT / "docs" / "can" / "can-safety.md"),
        "BOM map": read_text(REPO_ROOT / "production" / "bom" / "pb100_symbol_bom_map.csv"),
        "Factory BOM": read_text(REPO_ROOT / "production" / "bom" / "factory_bom_draft.csv"),
        "Assembly recheck": read_text(REPO_ROOT / "production" / "bom" / "pb100_assembly_sourcing_recheck.csv"),
        "Sourcing evidence": read_text(REPO_ROOT / "production" / "bom" / "pb100_sourcing_evidence_snapshot.csv"),
        "Assembly readiness": read_text(PB100_DIR / "PB-100-assembly-readiness-trace.csv"),
        "Test plan": read_text(REPO_ROOT / "docs" / "testing" / "test-plan.md"),
    }
    for label, text in checked_texts.items():
        lower_text = text.lower()
        if "can1" not in lower_text:
            fail(f"{label} must retain CAN1 safety content")
        if label in {"BOM map", "Factory BOM", "Assembly recheck", "Sourcing evidence", "Assembly readiness"}:
            for token in ("dnp/open", "no default-populated"):
                if token not in lower_text:
                    fail(f"{label} must retain CAN1 {token} production boundary")


def validate_can1_safety_verification() -> None:
    path = PB100_DIR / "PB-100-can1-safety-verification.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty CAN1 safety verification matrix: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in CAN1_SAFETY_VERIFICATION_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_requirement: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        requirement = row["Requirement"].strip()
        if requirement not in REQUIRED_CAN1_SAFETY_REQUIREMENTS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown CAN1 requirement {requirement}")
        if requirement in rows_by_requirement:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate CAN1 requirement {requirement}")
        rows_by_requirement[requirement] = row
        for column in CAN1_SAFETY_VERIFICATION_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        row_text = " ".join(row.values()).lower()
        if "enabled by default" in row_text:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: CAN1 TX must not be enabled/populated by default")
        if "default-populated tx" in row_text and "no default-populated tx" not in row_text:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: CAN1 TX must not be default-populated")
        if requirement != "Future TX change process" and "configuration only" in row_text:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: CAN1 TX cannot be changed by configuration only")

    missing_requirements = sorted(REQUIRED_CAN1_SAFETY_REQUIREMENTS - rows_by_requirement.keys())
    if missing_requirements:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing CAN1 requirements: "
            f"{', '.join(missing_requirements)}"
        )

    tx_row_text = " ".join(rows_by_requirement["TX physical path"].values()).lower()
    if "can1_tx_route" not in tx_row_text or "dnp/open" not in tx_row_text or "future-adr" not in tx_row_text:
        fail("CAN1 TX physical path verification must keep CAN1_TX_ROUTE DNP/open and future-ADR explicit")
    disable_row_text = " ".join(rows_by_requirement["Disable command"].values()).lower()
    if "disable asserted" not in disable_row_text or "reset" not in disable_row_text or "unpowered" not in disable_row_text:
        fail("CAN1 disable command verification must keep reset/unpowered disable explicit")
    status_row_text = " ".join(rows_by_requirement["Disabled status"].values()).lower()
    if "disabled state" not in status_row_text:
        fail("CAN1 disabled-status verification must require physical disabled-state readback")
    bom_row_text = " ".join(rows_by_requirement["DNP BOM ownership"].values()).lower()
    if "dnp/open" not in bom_row_text or "default" not in bom_row_text:
        fail("CAN1 DNP BOM verification must keep default DNP/open explicit")
    future_row_text = " ".join(rows_by_requirement["Future TX change process"].values()).lower()
    if "future adr" not in future_row_text or "hardware action" not in future_row_text:
        fail("CAN1 future TX process must require future ADR and hardware action")


def validate_can1_production_dnp_review() -> None:
    path = PB100_DIR / "PB-100-can1-production-dnp-review.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty CAN1 production DNP review: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in CAN1_PRODUCTION_DNP_REVIEW_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_item: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        review_item = row["Review item"].strip()
        if review_item not in REQUIRED_CAN1_PRODUCTION_DNP_REVIEW_ITEMS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown CAN1 review item {review_item}")
        if review_item in rows_by_item:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate CAN1 review item {review_item}")
        rows_by_item[review_item] = row
        for column in CAN1_PRODUCTION_DNP_REVIEW_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        row_text = " ".join(row.values()).lower()
        if review_item in {"Physical missing link", "Factory DNP ownership"}:
            if "dnp/open" not in row_text or "no default-populated" not in row_text:
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: CAN1 DNP rows must keep no-default-populated TX explicit")
        if review_item == "Future change process":
            if "future adr" not in row_text or "hardware action" not in row_text or "configuration" not in row_text:
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: CAN1 future process must block configuration-only TX enable")

    missing_items = sorted(REQUIRED_CAN1_PRODUCTION_DNP_REVIEW_ITEMS - rows_by_item.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing CAN1 production DNP review items: "
            f"{', '.join(missing_items)}"
        )

    review_text = read_text(path)
    for token in (
        "JP_CAN1",
        "U_CAN1",
        "DNP/open",
        "no default-populated",
        "future ADR",
        "explicit hardware action",
        "physical disabled state",
        "not firmware-only",
        "CAN2 expansion TX remains separate",
        "Configuration alone cannot enable vehicle-CAN TX",
        "Do not enable vehicle-CAN TX through configuration only",
    ):
        if token not in review_text:
            fail(f"CAN1 production DNP review must include {token}")

    tx_row_text = " ".join(rows_by_item["Physical missing link"].values()).lower()
    if "can1_tx_route" not in tx_row_text or "jp_can1" not in tx_row_text:
        fail("CAN1 production DNP review must bind JP_CAN1 to CAN1_TX_ROUTE")
    gate_row_text = " ".join(rows_by_item["Default disabled gate"].values()).lower()
    if "can1_tx_disable_cmd" not in gate_row_text or "u_can1" not in gate_row_text or "reset" not in gate_row_text:
        fail("CAN1 production DNP review must bind U_CAN1 disable default to reset/unpowered state")
    status_row_text = " ".join(rows_by_item["Physical status readback"].values()).lower()
    if "can1_tx_disabled_status" not in status_row_text or "physical disabled state" not in status_row_text:
        fail("CAN1 production DNP review must bind disabled-status readback to physical state")
    rx_row_text = " ".join(rows_by_item["RX independence"].values()).lower()
    if "can1_rx_route" not in rx_row_text or "listen-only rx" not in rx_row_text:
        fail("CAN1 production DNP review must keep RX independent for listen-only RX")

    production_texts = {
        "Factory BOM": read_text(REPO_ROOT / "production" / "bom" / "factory_bom_draft.csv"),
        "Symbol BOM map": read_text(REPO_ROOT / "production" / "bom" / "pb100_symbol_bom_map.csv"),
        "Assembly recheck": read_text(REPO_ROOT / "production" / "bom" / "pb100_assembly_sourcing_recheck.csv"),
        "Assembly readiness": read_text(PB100_DIR / "PB-100-assembly-readiness-trace.csv"),
    }
    for label, text in production_texts.items():
        lower_text = text.lower()
        for token in ("can1_tx_disable", "dnp/open", "no default-populated"):
            if token not in lower_text:
                fail(f"{label} must retain CAN1 production DNP token {token}")

    firmware_readme = read_text(REPO_ROOT / "firmware" / "README.md").lower()
    if "can1" not in firmware_readme or "listen-only" not in firmware_readme or "can2" not in firmware_readme:
        fail("firmware README must keep CAN1 listen-only and CAN2 expansion boundary")
    firmware_tests = read_text(REPO_ROOT / "firmware" / "tests" / "test_can_safety.c")
    for token in (
        "test_can1_tx_is_denied_when_disabled_status_true",
        "test_can1_tx_is_denied_when_disabled_status_false",
        "test_can2_tx_is_allowed_for_expansion",
    ):
        if token not in firmware_tests:
            fail(f"CAN1 production DNP review requires firmware test {token}")


def validate_can1_default_disable_freeze_checklist() -> None:
    path = PB100_DIR / "PB-100-can1-default-disable-freeze-checklist.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty CAN1 default-disable freeze checklist: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [
        column for column in CAN1_DEFAULT_DISABLE_FREEZE_CHECKLIST_COLUMNS if column not in fieldnames
    ]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_check: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        check_id = row["Check ID"].strip()
        if check_id not in REQUIRED_CAN1_DEFAULT_DISABLE_FREEZE_CHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown CAN1 freeze check {check_id}")
        if check_id in rows_by_check:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate CAN1 freeze check {check_id}")
        rows_by_check[check_id] = row
        for column in CAN1_DEFAULT_DISABLE_FREEZE_CHECKLIST_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        row_text = " ".join(row.values()).lower()
        if "do not" not in row["Blocked action"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: blocked action must be explicit")
        if "can1_tx_route" in row_text and "dnp/open" not in row_text:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: CAN1_TX_ROUTE rows must keep DNP/open explicit")
        if "configuration" in row_text and "cannot enable tx" not in row_text and "do not use firmware capability configuration" not in row_text:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: configuration must not enable CAN1 TX")

    missing_checks = sorted(REQUIRED_CAN1_DEFAULT_DISABLE_FREEZE_CHECKS - rows_by_check.keys())
    if missing_checks:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing CAN1 freeze checks: "
            f"{', '.join(missing_checks)}"
        )

    checklist_text = read_text(path)
    for token in (
        "ADR-0002",
        "read-only by default",
        "future ADR",
        "explicit hardware action",
        "CAN1_TX_ROUTE",
        "JP_CAN1",
        "0Ω 0603",
        "DNP/open",
        "no default-populated vehicle-CAN TX path",
        "U_CAN1",
        "SN74LVC1G125-Q1",
        "OE high disabled",
        "47k",
        "CAN1_TX_DISABLE_CMD",
        "LB_3V3_IO",
        "TXD recessive",
        "transceiver VIO",
        "CAN1_TX_DISABLED_STATUS",
        "1k",
        "100k",
        "1nF DNP",
        "not firmware-only",
        "physical disabled state",
        "DNP link detect",
        "CAN1_RX_ROUTE",
        "listen-only RX",
        "can_safety",
        "CAN2 expansion TX remains separate",
        "vehicle_can_read_only_default",
        "hardware_action_required_for_tx",
        "PB-BENCH-012",
        "CAN1-RST-001",
        "CAN1-RST-006",
        "no vehicle-CAN transmit frame",
        "No PCB layout",
        "PB-100.kicad_pcb",
        "Gerbers",
        "drills",
        "pick-place",
    ):
        if token not in checklist_text:
            fail(f"CAN1 default-disable freeze checklist must include {token}")

    design_text = read_text(PB100_DIR / "PB-100-can1-tx-disable-design-calculation.md")
    for token in ("0 Ω 0603", "SN74LVC1G125-Q1", "47 kΩ", "1 kΩ", "100 kΩ", "1 nF DNP"):
        if token not in design_text:
            fail(f"CAN1 design calculation must support checklist token {token}")

    reset_text = read_text(PB100_DIR / "PB-100-can1-reset-bench-checklist.csv")
    for token in ("PB-BENCH-012", "no vehicle-CAN transmit frame", "not from firmware-only"):
        if token not in reset_text:
            fail(f"CAN1 reset bench checklist must support freeze checklist token {token}")


def validate_can1_default_disable_derivation_precheck() -> None:
    path = PB100_DIR / "PB-100-can1-default-disable-derivation-precheck.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty CAN1 default-disable derivation precheck: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [
        column for column in CAN1_DEFAULT_DISABLE_DERIVATION_PRECHECK_COLUMNS if column not in fieldnames
    ]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_id: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        derivation_id = row["Derivation ID"].strip()
        if derivation_id not in REQUIRED_CAN1_DEFAULT_DISABLE_DERIVATION_CHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown CAN1 derivation item {derivation_id}")
        if derivation_id in rows_by_id:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate CAN1 derivation item {derivation_id}")
        rows_by_id[derivation_id] = row
        for column in CAN1_DEFAULT_DISABLE_DERIVATION_PRECHECK_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        row_text = " ".join(row.values()).lower()
        if "do not" not in row["Blocked action"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: blocked action must be explicit")
        if "can1_tx_route" in row_text and "dnp/open" not in row_text:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: CAN1_TX_ROUTE derivation rows must keep DNP/open explicit")
        if "configuration" in row_text and "cannot enable tx" not in row_text:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: CAN1 configuration rows must state configuration cannot enable TX")

    missing_items = sorted(REQUIRED_CAN1_DEFAULT_DISABLE_DERIVATION_CHECKS - rows_by_id.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing CAN1 derivation items: "
            f"{', '.join(missing_items)}"
        )

    precheck_text = read_text(path)
    for token in (
        "ADR-0002",
        "read-only by default",
        "configuration cannot enable TX",
        "future ADR",
        "explicit hardware action",
        "CAN1_TX_ROUTE",
        "JP_CAN1",
        "0Ω 0603",
        "0 Ω 0603",
        "DNP/open",
        "no default-populated vehicle-CAN TX path",
        "normally-open solder bridge",
        "U_CAN1",
        "SN74LVC1G125-Q1",
        "OE high disabled",
        "47 kΩ",
        "47k",
        "CAN1_TX_DISABLE_CMD",
        "LB_3V3_IO",
        "TXD recessive",
        "transceiver VIO",
        "CAN1_TX_DISABLED_STATUS",
        "1 kΩ",
        "1k",
        "100 kΩ",
        "100k",
        "1 nF DNP",
        "1nF DNP",
        "not firmware-only",
        "physical disabled state",
        "DNP link detect",
        "CAN1_RX_ROUTE",
        "listen-only RX",
        "can_safety",
        "CAN2 expansion TX remains separate",
        "vehicle_can_read_only_default",
        "tx_route_population DNP/open",
        "tx_requires_future_adr",
        "hardware_action_required_for_tx",
        "PB-BENCH-012",
        "CAN1-RST-001",
        "CAN1-RST-006",
        "no vehicle-CAN transmit frame",
        "factory_bom_draft.csv",
        "pb100_symbol_bom_map.csv",
        "pb100_assembly_sourcing_recheck.csv",
        "JLCPCB/PCBWay",
        "DNP 0R",
        "No PCB layout",
        "PB-100.kicad_pcb",
        "Gerbers",
        "drills",
        "pick-place",
        "CAN1 TX route layout",
        "jumper footprint",
        "fabrication package",
    ):
        if token not in precheck_text:
            fail(f"CAN1 default-disable derivation precheck must include {token}")

    design_text = read_text(PB100_DIR / "PB-100-can1-tx-disable-design-calculation.md")
    for token in ("0 Ω 0603", "SN74LVC1G125-Q1", "47 kΩ", "1 kΩ", "100 kΩ", "1 nF DNP"):
        if token not in design_text:
            fail(f"CAN1 design calculation must support derivation token {token}")

    reset_text = read_text(PB100_DIR / "PB-100-can1-reset-bench-checklist.csv")
    for token in ("PB-BENCH-012", "no vehicle-CAN transmit frame", "future ADR", "explicit hardware action"):
        if token not in reset_text:
            fail(f"CAN1 reset bench checklist must support derivation token {token}")

    sourcing_text = read_text(REPO_ROOT / "production" / "bom" / "pb100_assembly_sourcing_recheck.csv")
    for token in ("CAN1_TX_DISABLE", "DNP/open", "no default-populated TX", "future ADR"):
        if token not in sourcing_text:
            fail(f"assembly sourcing recheck must support CAN1 derivation token {token}")


def validate_can1_default_disable_closeout_precheck() -> None:
    path = PB100_DIR / "PB-100-can1-default-disable-closeout-precheck.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty CAN1 default-disable closeout precheck: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [
        column for column in CAN1_DEFAULT_DISABLE_CLOSEOUT_PRECHECK_COLUMNS if column not in fieldnames
    ]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_id: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        precheck_id = row["Precheck ID"].strip()
        if precheck_id not in REQUIRED_CAN1_DEFAULT_DISABLE_CLOSEOUT_PRECHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown CAN1 closeout precheck {precheck_id}")
        if precheck_id in rows_by_id:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate CAN1 closeout precheck {precheck_id}")
        rows_by_id[precheck_id] = row
        for column in CAN1_DEFAULT_DISABLE_CLOSEOUT_PRECHECK_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        row_text = " ".join(row.values()).lower()
        if "do not" not in row["Blocked action"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: blocked action must be explicit")
        if "can1_tx_route" in row_text and "dnp/open" not in row_text:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: CAN1_TX_ROUTE rows must keep DNP/open explicit")
        if "configuration" in row_text and "cannot enable tx" not in row_text:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: CAN1 configuration rows must state configuration cannot enable TX")
        if precheck_id == "CAN1-CLS-010" and ("no pcb layout" not in row_text or "pb-100.kicad_pcb" not in row_text):
            fail("CAN1 closeout no-layout row must block PCB layout explicitly")

    missing_items = sorted(REQUIRED_CAN1_DEFAULT_DISABLE_CLOSEOUT_PRECHECKS - rows_by_id.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing CAN1 closeout prechecks: "
            f"{', '.join(missing_items)}"
        )

    precheck_text = read_text(path)
    for token in (
        "ADR-0002",
        "read-only by default",
        "configuration cannot enable TX",
        "future ADR plus explicit hardware action",
        "CAN1_TX_ROUTE",
        "JP_CAN1",
        "DNP/open",
        "no default-populated vehicle-CAN TX path",
        "0Ω 0603",
        "normally-open solder bridge",
        "U_CAN1",
        "SN74LVC1G125-Q1",
        "OE high disabled",
        "47k",
        "CAN1_TX_DISABLE_CMD",
        "enable command",
        "TXD",
        "recessive",
        "CAN1_TX_DISABLED_STATUS",
        "1k",
        "100k",
        "1nF DNP",
        "firmware-only",
        "DNP link detect",
        "CAN1_RX_ROUTE",
        "CAN2 expansion TX remains separate",
        "can_safety",
        "vehicle_can_read_only_default true",
        "tx_route_population DNP/open",
        "tx_requires_future_adr true",
        "hardware_action_required_for_tx true",
        "PB-BENCH-012",
        "CAN1-RST-001",
        "CAN1-RST-006",
        "CAN1_TX_DISABLE",
        "JLCPCB PCBWay",
        "PB-100-assembly-readiness-trace.csv",
        "No PCB layout",
        "PB-100.kicad_pcb",
        "Gerbers",
        "drills",
        "pick-place",
        "manufacturing ZIP",
        "CAN1 TX route layout",
        "jumper footprint lock",
        "fabrication package",
    ):
        if token not in precheck_text:
            fail(f"CAN1 default-disable closeout precheck must include {token}")

    for supporting_artifact, tokens in {
        "PB-100-can1-default-disable-freeze-checklist.csv": ("CAN1-FRZ-001", "CAN1-FRZ-010"),
        "PB-100-can1-default-disable-derivation-precheck.csv": ("CAN1-DER-001", "CAN1-DER-010"),
        "PB-100-can1-production-dnp-review.csv": ("Physical missing link", "Future change process"),
        "PB-100-can1-reset-bench-checklist.csv": ("CAN1-RST-001", "CAN1-RST-006"),
    }.items():
        supporting_text = read_text(PB100_DIR / supporting_artifact)
        for token in tokens:
            if token not in supporting_text:
                fail(f"CAN1 closeout precheck requires {supporting_artifact} token {token}")


def validate_can1_reset_bench_checklist() -> None:
    path = PB100_DIR / "PB-100-can1-reset-bench-checklist.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty CAN1 reset bench checklist: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in CAN1_RESET_BENCH_CHECKLIST_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_check: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        check_id = row["Check ID"].strip()
        if check_id not in REQUIRED_CAN1_RESET_BENCH_CHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown CAN1 reset check {check_id}")
        if check_id in rows_by_check:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate CAN1 reset check {check_id}")
        rows_by_check[check_id] = row
        for column in CAN1_RESET_BENCH_CHECKLIST_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        row_text = " ".join(row.values()).lower()
        if "can1_tx_route" in row_text and "dnp/open" not in row_text:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: CAN1_TX_ROUTE checks must keep DNP/open explicit")
        if "vehicle-can transmit" in row_text and "no vehicle-can transmit" not in row_text:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: CAN1 checks must prohibit vehicle-CAN transmit frames")
        if check_id == "CAN1-RST-004" and "not from firmware-only" not in row_text:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: disabled status must reject firmware-only evidence")
        if check_id == "CAN1-RST-006" and ("future adr" not in row_text or "explicit hardware action" not in row_text):
            fail("CAN1 future TX checklist row must require future ADR plus explicit hardware action")

    missing_checks = sorted(REQUIRED_CAN1_RESET_BENCH_CHECKS - rows_by_check.keys())
    if missing_checks:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing CAN1 reset checks: "
            f"{', '.join(missing_checks)}"
        )

    checklist_text = read_text(path)
    for token in (
        "PB-BENCH-012",
        "CAN1_TX_DISABLE_CMD",
        "CAN1_TX_DISABLED_STATUS",
        "CAN1_TX_ROUTE",
        "JP_CAN1",
        "U_CAN1",
        "DNP/open",
        "47k",
        "1k/100k",
        "no vehicle-CAN transmit frame",
        "future ADR",
        "explicit hardware action",
    ):
        if token not in checklist_text:
            fail(f"CAN1 reset bench checklist must include {token}")


def validate_board_current_budget_trace() -> None:
    path = PB100_DIR / "PB-100-board-current-budget-trace.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty board-current budget trace: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in BOARD_CURRENT_BUDGET_TRACE_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    required_checks = {
        "Main fuse target",
        "Board continuous target",
        "Default configuration limit",
        "Total input telemetry range",
        "Shunt operating point",
        "Output limit oversubscription",
    }
    rows_by_check: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        check = row["Check"].strip()
        if check in rows_by_check:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate Check {check}")
        if check not in required_checks:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown current-budget check {check}")
        rows_by_check[check] = row
        for column in BOARD_CURRENT_BUDGET_TRACE_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        row_text = " ".join(row.values()).lower()
        if "schematic freeze" not in row_text and check != "Default configuration limit":
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: remaining work must reference schematic freeze")

    missing_checks = sorted(required_checks - rows_by_check.keys())
    if missing_checks:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing current-budget checks: "
            f"{', '.join(missing_checks)}"
        )

    capabilities = json.loads(read_text(REPO_ROOT / "firmware" / "configs" / "hardware" / "pb-100-capabilities.json"))
    config_example = json.loads(read_text(REPO_ROOT / "firmware" / "configs" / "config-example.json"))
    power_budget = capabilities["power_budget"]
    if power_budget["main_fuse_target_a"] != 50:
        fail("PB-100 capability manifest must keep 50 A main fuse target")
    if power_budget["board_continuous_target_a"] != 40:
        fail("PB-100 capability manifest must keep 40 A board continuous target")
    if power_budget["default_total_current_limit_a"] != 40:
        fail("PB-100 capability manifest must keep 40 A default total-current limit")
    if config_example["power_budget"]["total_current_limit_a"] != 40:
        fail("config example must keep 40 A total_current_limit_a")

    output_limit_sum = sum(output["target_current_limit_a"] for output in capabilities["outputs"])
    if output_limit_sum != 82:
        fail(f"PB-100 output current-limit sum must remain 82 A, got {output_limit_sum} A")
    if "IIN_SENSE" not in capabilities["telemetry"]["current_signals"]:
        fail("PB-100 capability manifest must expose IIN_SENSE total-current telemetry")

    current_rows = list(csv.DictReader((PB100_DIR / "PB-100-current-telemetry-map.csv").open(newline="", encoding="utf-8")))
    total_current_row = next((row for row in current_rows if row["Signal"].strip() == "IIN_SENSE"), None)
    if total_current_row is None:
        fail("current telemetry map must include IIN_SENSE")
    total_current_text = " ".join(total_current_row.values())
    for token in ("0-60", "0.5mΩ", "40A"):
        if token not in total_current_text:
            fail(f"IIN_SENSE telemetry map row must include {token}")

    input_power_text = read_text(PB100_DIR / "PB-100-input-power-design-values.csv")
    for token in ("0.5mΩ", "20mV at 40A", "0.8W board-budget"):
        if token not in input_power_text:
            fail(f"input power design values must include {token}")

    trace_text = read_text(path)
    for token in ("50 A", "40 A", "0-60 A", "0.5 mOhm", "82 A", "configuration separate from firmware"):
        if token not in trace_text:
            fail(f"board-current budget trace must include {token}")


def validate_board_current_budget_freeze_review() -> None:
    path = PB100_DIR / "PB-100-board-current-budget-freeze-review.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty board-current budget freeze review: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in BOARD_CURRENT_BUDGET_FREEZE_REVIEW_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_item: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        review_item = row["Review item"].strip()
        if review_item not in REQUIRED_BOARD_CURRENT_BUDGET_FREEZE_REVIEW_ITEMS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown board-current review item {review_item}")
        if review_item in rows_by_item:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate board-current review item {review_item}")
        rows_by_item[review_item] = row
        for column in BOARD_CURRENT_BUDGET_FREEZE_REVIEW_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        row_text = " ".join(row.values()).lower()
        if review_item == "Layout authorization boundary":
            if "no pcb layout" not in row_text or "pb-100.kicad_pcb" not in row_text:
                fail("board-current freeze review must block PCB layout explicitly")
        if review_item == "Firmware configuration budget":
            if "total_current_limit_a" not in row_text or "configuration stays separate from firmware" not in row_text:
                fail("board-current freeze review must keep config/firmware separation explicit")

    missing_items = sorted(REQUIRED_BOARD_CURRENT_BUDGET_FREEZE_REVIEW_ITEMS - rows_by_item.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing board-current review items: "
            f"{', '.join(missing_items)}"
        )

    review_text = read_text(path)
    for token in (
        "50 A",
        "40 A",
        "0.5mΩ",
        "20mV at 40A",
        "0.8W",
        "30mV at 60A",
        "1.8W",
        "82 A",
        "Q1",
        "TOLL",
        "LFPAK88",
        "dual PowerPAK",
        "Kelvin",
        "ADC or I2C",
        "configuration stays separate from firmware",
        "No PCB layout copper geometry",
        "PB-100.kicad_pcb",
    ):
        if token not in review_text:
            fail(f"board-current budget freeze review must include {token}")

    capabilities = json.loads(read_text(REPO_ROOT / "firmware" / "configs" / "hardware" / "pb-100-capabilities.json"))
    power_budget = capabilities["power_budget"]
    if power_budget["main_fuse_target_a"] != 50:
        fail("board-current freeze review requires 50 A main fuse target")
    if power_budget["board_continuous_target_a"] != 40:
        fail("board-current freeze review requires 40 A board continuous target")
    if power_budget["default_total_current_limit_a"] != 40:
        fail("board-current freeze review requires 40 A default total-current limit")
    output_limit_sum = sum(output["target_current_limit_a"] for output in capabilities["outputs"])
    if output_limit_sum != 82:
        fail(f"board-current freeze review expects 82 A output oversubscription, got {output_limit_sum} A")

    config_example = json.loads(read_text(REPO_ROOT / "firmware" / "configs" / "config-example.json"))
    if config_example["power_budget"]["total_current_limit_a"] != 40:
        fail("board-current freeze review requires config example 40 A total_current_limit_a")

    input_power_text = read_text(PB100_DIR / "PB-100-input-power-design-values.csv")
    for token in ("0.5mΩ", "20mV at 40A", "0.8W board-budget", "30mV at 60A", "Kelvin"):
        if token not in input_power_text:
            fail(f"input power design values must support board-current freeze review token {token}")

    board_current_text = read_text(PB100_DIR / "PB-100-board-current-budget-trace.csv")
    for token in ("50 A", "40 A", "0-60 A", "0.5 mOhm", "82 A", "configuration separate from firmware"):
        if token not in board_current_text:
            fail(f"board-current trace must support freeze review token {token}")

    kicad_prep_text = read_text(PB100_DIR / "PB-100-kicad-prep.md").lower()
    for token in ("copper", "current-carrying", "layout"):
        if token not in kicad_prep_text:
            fail(f"KiCad prep must retain board-current layout blocker token {token}")


def validate_board_current_budget_design_calculation() -> None:
    path = PB100_DIR / "PB-100-board-current-budget-design-calculation.md"
    text = read_text(path)
    lower_text = text.lower()
    for token in ("not a pcb layout package", "no pcb layout copper geometry", "pb-100.kicad_pcb"):
        if token not in lower_text:
            fail(f"{path.relative_to(REPO_ROOT)} must keep no-layout boundary token: {token}")
    for token in (
        "50 A",
        "40 A",
        "0-60 A",
        "0.5 mΩ",
        "82 A",
        "Configuration stays separate from firmware",
        "Kelvin",
        "Vshunt = I * Rshunt",
        "Pshunt = I^2 * Rshunt",
        "20 mV at 40 A",
        "0.8 W at 40 A",
        "25 mV at 50 A",
        "1.25 W at 50 A",
        "30 mV at 60 A",
        "1.8 W at 60 A",
        "Pfet = I^2 * Rds(on) * 2.0",
        "BUK7S1R2-80M",
        "selected 80 V LFPAK88",
        "LFPAK88",
        "3.84 W",
        "IAUTN08S5N012L",
        "BUK7J2R4-80M",
        "retained in historical decision artifacts only",
        "Every 1 mΩ",
        "1.6 W at 40 A",
        "2.5 W at 50 A",
        "3.6 W at 60 A",
    ):
        if token not in text:
            fail(f"board-current design calculation must include {token}")


def validate_board_current_budget_value_freeze_checklist() -> None:
    path = PB100_DIR / "PB-100-board-current-budget-value-freeze-checklist.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty board-current budget value freeze checklist: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [
        column for column in BOARD_CURRENT_BUDGET_VALUE_FREEZE_CHECKLIST_COLUMNS if column not in fieldnames
    ]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_check: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        check_id = row["Check ID"].strip()
        if check_id not in REQUIRED_BOARD_CURRENT_BUDGET_VALUE_FREEZE_CHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown board-current check {check_id}")
        if check_id in rows_by_check:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate board-current check {check_id}")
        rows_by_check[check_id] = row
        for column in BOARD_CURRENT_BUDGET_VALUE_FREEZE_CHECKLIST_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        if "do not" not in row["Blocked action"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: blocked action must be explicit")

    missing_checks = sorted(REQUIRED_BOARD_CURRENT_BUDGET_VALUE_FREEZE_CHECKS - rows_by_check.keys())
    if missing_checks:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing board-current checks: "
            f"{', '.join(missing_checks)}"
        )

    checklist_text = read_text(path)
    for token in (
        "ADR-0008",
        "50A main harness fuse",
        "40 A board continuous-current target",
        "40 A default total_current_limit_a",
        "0-60 A telemetry range",
        "82 A summed output limits",
        "VBAT_RAW",
        "INPUT_REVERSE_FET",
        "VBAT_REV_PROT",
        "0.5mΩ",
        "VBAT_PROT",
        "MAXI",
        "6mm2 / 10AWG",
        "BUK7S1R2-80M",
        "selected BUK7S1R2-80M 80 V LFPAK88",
        "LFPAK88",
        "3.84 W at 40 A",
        "IAUTN08S5N012L 80 V TOLL",
        "BUK7J2R4-80M 80 V LFPAK56E",
        "former IAUTN06S5N008 and SIDR626LDP 60 V paths are rejected",
        "TOTAL_CURRENT_SHUNT",
        "20mV and 0.8W at 40A",
        "25mV and 1.25W at 50A",
        "30mV and 1.8W at 60A",
        "Kelvin",
        "1.6W at 40A",
        "2.5W at 50A",
        "3.6W at 60A",
        "power_budget",
        "stale telemetry denial",
        "configuration separate from firmware",
        "TOTAL_CURRENT_MONITOR",
        "IIN_SENSE",
        "PB-BENCH-006",
        "PB-BENCH-010",
        "No PCB layout",
        "PB-100.kicad_pcb",
        "Gerbers",
        "drills",
        "pick-place",
        "high-current copper",
        "shunt copper",
        "Q1 copper",
    ):
        if token not in checklist_text:
            fail(f"board-current budget value freeze checklist must include {token}")

    design_text = read_text(PB100_DIR / "PB-100-board-current-budget-design-calculation.md")
    for token in ("20 mV at 40 A", "0.8 W at 40 A", "1.6 W at 40 A", "3.6 W at 60 A"):
        if token not in design_text:
            fail(f"board-current design calculation must support value checklist token {token}")

    firmware_text = "\n".join(
        (
            read_text(REPO_ROOT / "firmware" / "configs" / "config-example.json"),
            read_text(REPO_ROOT / "firmware" / "tests" / "test_power_budget.c"),
            read_text(REPO_ROOT / "firmware" / "tests" / "test_rule_runtime.c"),
        )
    )
    for token in (
        "total_current_limit_a",
        "40",
        "shed_priority_order",
        "test_denies_output_over_budget",
        "test_shed_order_uses_configured_priority_order",
        "stale",
    ):
        if token not in firmware_text:
            fail(f"firmware/config budget evidence must support board-current checklist token {token}")


def validate_board_current_budget_value_derivation_precheck() -> None:
    path = PB100_DIR / "PB-100-board-current-budget-value-derivation-precheck.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty board-current budget value derivation precheck: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [
        column for column in BOARD_CURRENT_BUDGET_VALUE_DERIVATION_PRECHECK_COLUMNS if column not in fieldnames
    ]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_id: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        derivation_id = row["Derivation ID"].strip()
        if derivation_id not in REQUIRED_BOARD_CURRENT_BUDGET_VALUE_DERIVATION_CHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown board-current derivation item {derivation_id}")
        if derivation_id in rows_by_id:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate board-current derivation item {derivation_id}")
        rows_by_id[derivation_id] = row
        for column in BOARD_CURRENT_BUDGET_VALUE_DERIVATION_PRECHECK_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        if "do not" not in row["Blocked action"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: blocked action must be explicit")

    missing_items = sorted(REQUIRED_BOARD_CURRENT_BUDGET_VALUE_DERIVATION_CHECKS - rows_by_id.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing board-current derivation items: "
            f"{', '.join(missing_items)}"
        )

    precheck_text = read_text(path)
    for token in (
        "ADR-0008",
        "50A main harness fuse",
        "50 A main fuse",
        "40 A board continuous-current target",
        "40 A default total_current_limit_a",
        "82 A summed output limits",
        "configuration separate from firmware",
        "VBAT_RAW",
        "INPUT_REVERSE_FET",
        "VBAT_REV_PROT",
        "TOTAL_CURRENT_SHUNT",
        "0.5mΩ",
        "VBAT_PROT",
        "Vshunt = I * Rshunt",
        "Pshunt = I^2 * Rshunt",
        "20mV and 0.8W at 40A",
        "25mV and 1.25W at 50A",
        "30mV and 1.8W at 60A",
        "BUK7S1R2-80M",
        "selected BUK7S1R2-80M 80 V LFPAK88",
        "LFPAK88",
        "2.4mΩ",
        "3.84 W at 40 A",
        "IAUTN08S5N012L 80 V TOLL",
        "BUK7J2R4-80M 80 V LFPAK56E",
        "former 60 V paths are rejected",
        "Every 1 mΩ",
        "1.6 W at 40 A",
        "2.5 W at 50 A",
        "6mm2 / 10AWG",
        "MAXI",
        "total_current_limit_a",
        "power_budget",
        "PB-BENCH-010",
        "PB-BENCH-006",
        "stale telemetry denial",
        "IIN_SENSE",
        "IIN_SHUNT_HI",
        "IIN_SHUNT_LO",
        "0-60 A",
        "Kelvin",
        "ADC or I2C",
        "INPUT_CONNECTOR",
        "MAIN_FUSE_HOLDER",
        "factory_bom_draft.csv",
        "garage_bom_draft.csv",
        "pb100_assembly_sourcing_recheck.csv",
        "No PCB layout",
        "PB-100.kicad_pcb",
        "Gerbers",
        "drills",
        "pick-place",
        "high-current copper",
        "shunt copper",
        "Q1 copper",
    ):
        if token not in precheck_text:
            fail(f"board-current budget value derivation precheck must include {token}")

    design_text = read_text(PB100_DIR / "PB-100-board-current-budget-design-calculation.md")
    for token in ("20 mV at 40 A", "0.8 W at 40 A", "1.6 W at 40 A", "3.6 W at 60 A"):
        if token not in design_text:
            fail(f"board-current design calculation must support derivation token {token}")

    firmware_text = "\n".join(
        (
            read_text(REPO_ROOT / "firmware" / "configs" / "config-example.json"),
            read_text(REPO_ROOT / "firmware" / "tests" / "test_power_budget.c"),
            read_text(REPO_ROOT / "firmware" / "tests" / "test_rule_runtime.c"),
        )
    )
    for token in ("total_current_limit_a", "40", "test_denies_output_over_budget", "stale"):
        if token not in firmware_text:
            fail(f"firmware/config budget evidence must support board-current derivation token {token}")


def validate_board_current_budget_closeout_precheck() -> None:
    path = PB100_DIR / "PB-100-board-current-budget-closeout-precheck.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty board-current budget closeout precheck: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in BOARD_CURRENT_BUDGET_CLOSEOUT_PRECHECK_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_id: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        precheck_id = row["Precheck ID"].strip()
        if precheck_id not in REQUIRED_BOARD_CURRENT_BUDGET_CLOSEOUT_PRECHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown board-current closeout precheck {precheck_id}")
        if precheck_id in rows_by_id:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate board-current closeout precheck {precheck_id}")
        rows_by_id[precheck_id] = row
        for column in BOARD_CURRENT_BUDGET_CLOSEOUT_PRECHECK_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        row_text = " ".join(row.values()).lower()
        if "do not" not in row["Blocked action"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: blocked action must be explicit")
        if precheck_id == "BUDGET-CLS-005" and ("vshunt" not in row_text or "pshunt" not in row_text):
            fail("board-current closeout shunt row must include Vshunt and Pshunt formulas")
        if precheck_id == "BUDGET-CLS-010" and ("no pcb layout" not in row_text or "pb-100.kicad_pcb" not in row_text):
            fail("board-current closeout no-layout row must block PCB layout explicitly")

    missing_items = sorted(REQUIRED_BOARD_CURRENT_BUDGET_CLOSEOUT_PRECHECKS - rows_by_id.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing board-current closeout prechecks: "
            f"{', '.join(missing_items)}"
        )

    precheck_text = read_text(path)
    for token in (
        "ADR-0008",
        "50A main harness fuse",
        "40 A board continuous-current target",
        "40 A default total_current_limit_a",
        "0-60 A telemetry range",
        "82 A summed output limits",
        "configuration separate from firmware",
        "50 A MAXI fuse",
        "VBAT_RAW",
        "INPUT_REVERSE_FET",
        "VBAT_REV_PROT",
        "TOTAL_CURRENT_SHUNT",
        "0.5mΩ",
        "VBAT_PROT",
        "6mm2 / 10AWG",
        "BUK7S1R2-80M",
        "selected BUK7S1R2-80M 80 V LFPAK88",
        "LFPAK88",
        "3.84 W at 40 A",
        "IAUTN08S5N012L 80 V TOLL",
        "BUK7J2R4-80M 80 V LFPAK56E",
        "former IAUTN06S5N008 and SIDR626LDP 60 V paths are rejected",
        "Vshunt = I * Rshunt",
        "Pshunt = I^2 * Rshunt",
        "20mV and 0.8W at 40A",
        "25mV and 1.25W at 50A",
        "30mV and 1.8W at 60A",
        "Kelvin",
        "1.6W at 40A",
        "2.5W at 50A",
        "3.6W at 60A",
        "power_budget",
        "total_current_limit_a",
        "startup refusal",
        "load shedding",
        "stale telemetry denial",
        "TOTAL_CURRENT_MONITOR",
        "IIN_SENSE",
        "IIN_SHUNT_HI",
        "IIN_SHUNT_LO",
        "ADC or I2C",
        "summed per-output IMON alone is not acceptable",
        "PB-BENCH-006",
        "PB-BENCH-010",
        "INPUT_CONNECTOR",
        "MAIN_FUSE_HOLDER",
        "factory_bom_draft.csv",
        "garage_bom_draft.csv",
        "pb100_assembly_sourcing_recheck.csv",
        "pb100_sourcing_evidence_snapshot.csv",
        "No PCB layout",
        "PB-100.kicad_pcb",
        "Gerbers",
        "drills",
        "pick-place",
        "manufacturing ZIP",
        "high-current copper",
        "shunt copper",
        "Q1 copper",
        "connector placement",
        "fabrication package",
    ):
        if token not in precheck_text:
            fail(f"board-current budget closeout precheck must include {token}")

    for supporting_artifact, tokens in {
        "PB-100-board-current-budget-value-freeze-checklist.csv": ("BUDGET-FRZ-001", "BUDGET-FRZ-010"),
        "PB-100-board-current-budget-value-derivation-precheck.csv": ("BUDGET-DER-001", "BUDGET-DER-010"),
        "PB-100-board-current-budget-freeze-review.csv": ("Main fuse and input connector", "Layout authorization boundary"),
        "PB-100-current-telemetry-closeout-precheck.csv": ("TOTAL_CURRENT_SHUNT", "IIN_SENSE"),
    }.items():
        supporting_text = read_text(PB100_DIR / supporting_artifact)
        for token in tokens:
            if token not in supporting_text:
                fail(f"board-current closeout precheck requires {supporting_artifact} token {token}")


def validate_current_telemetry_trace() -> None:
    path = PB100_DIR / "PB-100-current-telemetry-trace.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty current telemetry trace: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in CURRENT_TELEMETRY_TRACE_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    expected_groups = {
        "OUT2 high-current telemetry": ("0-30", {"OUT2_IMON"}),
        "OUT1 medium 12A telemetry": ("0-20", {"OUT1_IMON"}),
        "Medium 8A telemetry": ("0-15", {"OUT3_IMON", "OUT4_IMON", "OUT6_IMON", "OUT7_IMON", "OUT10_IMON"}),
        "Low 4A telemetry": ("0-8", {"OUT5_IMON", "OUT8_IMON", "OUT9_IMON"}),
        "Total input telemetry": ("0-60", {"IIN_SENSE"}),
    }
    rows_by_group: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        group = row["Measurement group"].strip()
        if group in rows_by_group:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate measurement group {group}")
        if group not in expected_groups:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown measurement group {group}")
        rows_by_group[group] = row
        for column in CURRENT_TELEMETRY_TRACE_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        expected_range, expected_signals = expected_groups[group]
        if row["Range target A"].strip() != expected_range:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: range must be {expected_range}")
        if set(row["Signals"].split()) != expected_signals:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: signals must be {' '.join(sorted(expected_signals))}")
        row_text = " ".join(row.values()).lower()
        for token in ("schematic freeze", "calibration"):
            if token not in row_text:
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: current telemetry row must include {token}")

    missing_groups = sorted(set(expected_groups) - set(rows_by_group))
    if missing_groups:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing telemetry groups: "
            f"{', '.join(missing_groups)}"
        )

    map_rows = list(csv.DictReader((PB100_DIR / "PB-100-current-telemetry-map.csv").open(newline="", encoding="utf-8")))
    map_by_signal = {row["Signal"].strip(): row for row in map_rows}
    capabilities = json.loads(read_text(REPO_ROOT / "firmware" / "configs" / "hardware" / "pb-100-capabilities.json"))
    capability_signals = set(capabilities["telemetry"]["current_signals"])
    expected_all_signals = set().union(*(signals for _, signals in expected_groups.values()))
    if not expected_all_signals <= capability_signals:
        fail("current telemetry trace signals must be exposed in PB-100 capability manifest")

    for expected_range, signals in expected_groups.values():
        for signal in signals:
            row = map_by_signal.get(signal)
            if row is None:
                fail(f"current telemetry map must include {signal}")
            if row["Range A"].strip() != expected_range:
                fail(f"{signal} current telemetry map range must be {expected_range}")
            if signal == "IIN_SENSE":
                row_text = " ".join(row.values())
                for token in ("0.5mΩ", "40A", "60A"):
                    if token not in row_text:
                        fail(f"IIN_SENSE map row must preserve {token}")

    trace_text = read_text(path)
    for token in ("0.5 mOhm", "40 A budget", "stale-telemetry safe-off", "ADC or I2C"):
        if token not in trace_text:
            fail(f"current telemetry trace must include {token}")

    firmware_readme = read_text(REPO_ROOT / "firmware" / "README.md").lower()
    for token in ("telemetry snapshot", "staleness", "stale-data fail", "safe behavior"):
        if token not in firmware_readme:
            fail(f"firmware README must keep telemetry safety coverage token: {token}")


def validate_current_telemetry_freeze_review() -> None:
    path = PB100_DIR / "PB-100-current-telemetry-freeze-review.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty current telemetry freeze review: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in CURRENT_TELEMETRY_FREEZE_REVIEW_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_item: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        review_item = row["Review item"].strip()
        if review_item not in REQUIRED_CURRENT_TELEMETRY_FREEZE_REVIEW_ITEMS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown current telemetry review item {review_item}")
        if review_item in rows_by_item:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate current telemetry review item {review_item}")
        rows_by_item[review_item] = row
        for column in CURRENT_TELEMETRY_FREEZE_REVIEW_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        row_text = " ".join(row.values()).lower()
        if review_item == "Calibration configuration" and "not firmware constants" not in row_text:
            fail("current telemetry freeze review must keep calibration out of firmware constants")
        if review_item == "Stale telemetry safe fault" and "safe" not in row_text:
            fail("current telemetry freeze review must keep stale telemetry fail-safe behavior")

    missing_items = sorted(REQUIRED_CURRENT_TELEMETRY_FREEZE_REVIEW_ITEMS - rows_by_item.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing current telemetry review items: "
            f"{', '.join(missing_items)}"
        )

    review_text = read_text(path)
    for token in (
        "0.5mΩ",
        "20mV at 40A",
        "30mV at 60A",
        "±40.96mV",
        "INA228-Q1",
        "INA229-Q1",
        "INA226",
        "IIN_SHUNT_HI",
        "IIN_SHUNT_LO",
        "Kelvin",
        "IIN_SENSE",
        "PB_I2C_SCL",
        "PB_I2C_SDA",
        "PB_I2C_INT",
        "ADC I2C",
        "OUT1_IMON",
        "OUT10_IMON",
        "configuration data not firmware constants",
        "stale-telemetry denial",
        "PB-BENCH-005",
        "PB-BENCH-006",
        "PB-BENCH-010",
    ):
        if token not in review_text:
            fail(f"current telemetry freeze review must include {token}")

    current_doc = read_text(PB100_DIR / "PB-100-current-telemetry.md")
    for token in ("0.5 mΩ", "20 mV", "0.8 W", "30 mV", "1.8 W", "±40.96 mV"):
        if token not in current_doc:
            fail(f"current telemetry strategy must support freeze review token {token}")

    net_domain_text = read_text(PB100_DIR / "PB-100-schematic-net-domain-plan.csv")
    for token in ("IIN_SHUNT_HI", "IIN_SHUNT_LO", "Kelvin", "IIN_SENSE"):
        if token not in net_domain_text:
            fail(f"net-domain plan must support current telemetry freeze review token {token}")

    b2b_binding_text = read_text(PB100_DIR / "PB-100-b2b-lb100-resource-binding.csv")
    for token in ("ADC", "I2C", "IIN_SENSE", "PB_I2C_SCL", "PB_I2C_SDA"):
        if token not in b2b_binding_text:
            fail(f"B2B resource binding must support current telemetry freeze review token {token}")

    firmware_joined = "\n".join(
        (
            read_text(REPO_ROOT / "firmware" / "tests" / "test_telemetry.c"),
            read_text(REPO_ROOT / "firmware" / "tests" / "test_rule_runtime.c"),
            read_text(REPO_ROOT / "firmware" / "tests" / "test_system_safety.c"),
        )
    )
    for token in (
        "test_total_current_power_budget_input",
        "test_telemetry_wrapper_denies_stale_matching_rule",
        "test_invalid_telemetry_forces_cutoff",
        "test_stale_telemetry_forces_cutoff",
    ):
        if token not in firmware_joined:
            fail(f"firmware tests must retain current telemetry safe-fault token {token}")


def validate_current_telemetry_value_freeze_checklist() -> None:
    path = PB100_DIR / "PB-100-current-telemetry-value-freeze-checklist.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty current telemetry value freeze checklist: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [
        column for column in CURRENT_TELEMETRY_VALUE_FREEZE_CHECKLIST_COLUMNS if column not in fieldnames
    ]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_check: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        check_id = row["Check ID"].strip()
        if check_id not in REQUIRED_CURRENT_TELEMETRY_VALUE_FREEZE_CHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown current telemetry check {check_id}")
        if check_id in rows_by_check:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate current telemetry check {check_id}")
        rows_by_check[check_id] = row
        for column in CURRENT_TELEMETRY_VALUE_FREEZE_CHECKLIST_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)

    missing_checks = sorted(REQUIRED_CURRENT_TELEMETRY_VALUE_FREEZE_CHECKS - rows_by_check.keys())
    if missing_checks:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing current telemetry checks: "
            f"{', '.join(missing_checks)}"
        )

    checklist_text = read_text(path)
    for token in (
        "0.5mΩ",
        "CSS4J-4026R-L500F",
        "20mV at 40A",
        "0.8W",
        "30mV at 60A",
        "1.8W",
        "81.92A",
        "±40.96mV",
        "INA228-Q1",
        "INA229-Q1",
        "INA226",
        "85 V VBUS",
        "2.7 V to 5.5 V",
        "16 I2C addresses",
        "IIN_SHUNT_HI",
        "IIN_SHUNT_LO",
        "Kelvin",
        "10Ω",
        "1nF C0G",
        "A1 = GND",
        "A0 = GND",
        "0x40",
        "PB_I2C_SCL",
        "PB_I2C_SDA",
        "LB_3V3_IO",
        "4.7kΩ to 10kΩ",
        "DNP",
        "PB_I2C_INT",
        "47kΩ",
        "diagnostic",
        "VBAT_PROT",
        "1kΩ",
        "1nF 100V",
        "OUT1_IMON",
        "OUT10_IMON",
        "0-30A",
        "0-20A",
        "0-15A",
        "0-8A",
        "telemetry.total_current",
        "telemetry.output_current",
        "500µΩ",
        "40960µV",
        "1000 ms",
        "60000 mA",
        "calibration data not firmware constants",
        "PB-BENCH-005",
        "PB-BENCH-006",
        "PB-BENCH-010",
        "stale-telemetry denial",
        "total_current_limit_a 40",
        "TOTAL_CURRENT_MONITOR",
        "TOTAL_CURRENT_SHUNT",
        "JLCPCB PCBWay",
        "1.0mΩ fallback",
        "No PCB layout",
        "PB-100.kicad_pcb",
        "Gerbers",
        "drills",
        "pick-place",
    ):
        if token not in checklist_text:
            fail(f"current telemetry value freeze checklist must include {token}")

    calculation_text = read_text(PB100_DIR / "PB-100-current-telemetry-design-calculation.md")
    for token in ("500 µΩ", "40960 µV", "1000 ms", "60000 mA", "0x40", "10 Ω", "1 nF"):
        if token not in calculation_text:
            fail(f"current telemetry design calculation must support checklist token {token}")

    config_text = read_text(REPO_ROOT / "firmware" / "configs" / "config-example.json")
    for token in ('"shunt_microohm": 500', '"stale_timeout_ms": 1000', '"plausible_max_ma": 60000'):
        if token not in config_text:
            fail(f"config example must support current telemetry checklist token {token}")


def validate_current_telemetry_value_derivation_precheck() -> None:
    path = PB100_DIR / "PB-100-current-telemetry-value-derivation-precheck.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty current telemetry value derivation precheck: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [
        column for column in CURRENT_TELEMETRY_VALUE_DERIVATION_PRECHECK_COLUMNS if column not in fieldnames
    ]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_id: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        derivation_id = row["Derivation ID"].strip()
        if derivation_id not in REQUIRED_CURRENT_TELEMETRY_VALUE_DERIVATION_CHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown current telemetry derivation item {derivation_id}")
        if derivation_id in rows_by_id:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate current telemetry derivation item {derivation_id}")
        rows_by_id[derivation_id] = row
        for column in CURRENT_TELEMETRY_VALUE_DERIVATION_PRECHECK_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        row_text = " ".join(row.values()).lower()
        if derivation_id == "CUR-DER-001" and ("vshunt" not in row_text or "pshunt" not in row_text):
            fail("current telemetry derivation precheck must include shunt voltage and power formulas")
        if derivation_id == "CUR-DER-008" and ("telemetry.total_current" not in row_text or "firmware constants" not in row_text):
            fail("current telemetry derivation precheck must keep calibration out of firmware constants")
        if derivation_id == "CUR-DER-010" and ("pb-100.kicad_pcb" not in row_text or "manufacturing" not in row_text):
            fail("current telemetry derivation precheck must block layout and manufacturing outputs")

    missing_items = sorted(REQUIRED_CURRENT_TELEMETRY_VALUE_DERIVATION_CHECKS - rows_by_id.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing current telemetry derivation items: "
            f"{', '.join(missing_items)}"
        )

    precheck_text = read_text(path)
    for token in (
        "Vshunt = I * Rshunt",
        "Pshunt = I^2 * Rshunt",
        "0.5mΩ",
        "40A gives 20mV",
        "50A gives 25mV",
        "60A gives 30mV",
        "81.92A",
        "40.96mV",
        "INA228-Q1",
        "INA229-Q1",
        "INA226",
        "±40.96mV",
        "±163.84mV",
        "-0.3V to +85V",
        "2.7V to 5.5V",
        "16 I2C addresses",
        "LB_3V3_IO",
        "0x40",
        "IIN_SHUNT_HI",
        "IIN_SHUNT_LO",
        "10Ω",
        "1nF C0G",
        "PB_I2C_SCL",
        "PB_I2C_SDA",
        "4.7kΩ to 10kΩ",
        "PB_I2C_INT",
        "47kΩ",
        "VBAT_PROT",
        "VBAT_RAW",
        "1kΩ",
        "1nF 100V",
        "PB-100-tvs-overshoot-validation-precheck.csv",
        "OUT1_IMON",
        "OUT10_IMON",
        "0-30A",
        "0-20A",
        "0-15A",
        "0-8A",
        "telemetry.total_current",
        "telemetry.output_current",
        "500µΩ",
        "40960µV",
        "1000 ms",
        "60000 mA",
        "PB-BENCH-005",
        "PB-BENCH-006",
        "PB-BENCH-010",
        "total_current_limit_a 40",
        "JLCPCB PCBWay",
        "CSS4J-4026R-L500F",
        "1.0mΩ fallback",
        "Isabellenhuette BVN/BAS",
        "PB-100.kicad_pcb",
        "Gerbers",
        "drills",
        "pick-place",
    ):
        if token not in precheck_text:
            fail(f"current telemetry value derivation precheck must include {token}")

    calculation_text = read_text(PB100_DIR / "PB-100-current-telemetry-design-calculation.md")
    for token in ("Vshunt", "Pshunt", "500 µΩ", "40960 µV", "0x40", "10 Ω", "1 nF"):
        if token not in calculation_text:
            fail(f"current telemetry design calculation must support derivation token {token}")


def validate_current_telemetry_closeout_precheck() -> None:
    path = PB100_DIR / "PB-100-current-telemetry-closeout-precheck.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty current telemetry closeout precheck: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in CURRENT_TELEMETRY_CLOSEOUT_PRECHECK_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_id: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        precheck_id = row["Precheck ID"].strip()
        if precheck_id not in REQUIRED_CURRENT_TELEMETRY_CLOSEOUT_PRECHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown current telemetry closeout precheck {precheck_id}")
        if precheck_id in rows_by_id:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate current telemetry closeout precheck {precheck_id}")
        rows_by_id[precheck_id] = row
        for column in CURRENT_TELEMETRY_CLOSEOUT_PRECHECK_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        row_text = " ".join(row.values()).lower()
        if "do not" not in row["Blocked action"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: blocked action must be explicit")
        if precheck_id == "CUR-CLS-001" and ("vshunt" not in row_text or "pshunt" not in row_text):
            fail("current telemetry closeout shunt row must include Vshunt and Pshunt formulas")
        if precheck_id == "CUR-CLS-006" and (
            "out2" not in row_text or "out10" not in row_text or "external adc/mux" not in row_text
        ):
            fail("current telemetry closeout IMON row must cover output ranges and external ADC/mux escape")
        if precheck_id == "CUR-CLS-010" and ("no pcb layout" not in row_text or "pb-100.kicad_pcb" not in row_text):
            fail("current telemetry closeout no-layout row must block PCB layout explicitly")

    missing_items = sorted(REQUIRED_CURRENT_TELEMETRY_CLOSEOUT_PRECHECKS - rows_by_id.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing current telemetry closeout prechecks: "
            f"{', '.join(missing_items)}"
        )

    precheck_text = read_text(path)
    for token in (
        "Vshunt = I * Rshunt",
        "Pshunt = I^2 * Rshunt",
        "0.5mΩ",
        "40A gives 20mV",
        "50A gives 25mV",
        "60A gives 30mV",
        "81.92A",
        "40.96mV",
        "TOTAL_CURRENT_SHUNT",
        "INA228-Q1",
        "INA229-Q1",
        "INA226",
        "±40.96mV",
        "±163.84mV",
        "-0.3V to +85V",
        "2.7V to 5.5V",
        "16 I2C addresses",
        "TOTAL_CURRENT_MONITOR",
        "IIN_SHUNT_HI",
        "IIN_SHUNT_LO",
        "Kelvin",
        "10Ω",
        "1nF C0G",
        "PB_I2C_SCL",
        "PB_I2C_SDA",
        "PB_I2C_INT",
        "A1 = GND",
        "A0 = GND",
        "0x40",
        "LB_3V3_IO",
        "4.7kΩ to 10kΩ",
        "47kΩ",
        "VBAT_PROT",
        "VBAT_RAW",
        "SM8S33AHM3/I",
        "1kΩ",
        "1nF 100V",
        "85 V VBUS",
        "60 V overshoot",
        "OUT1_IMON",
        "OUT10_IMON",
        "OUT2 0-30A",
        "OUT1 0-20A",
        "0-15A",
        "0-8A",
        "16 ADC",
        "external ADC/mux",
        "RIMON",
        "telemetry.total_current",
        "telemetry.output_current",
        "500µΩ",
        "40960µV",
        "stale_timeout_ms 1000",
        "plausible_max_ma 60000",
        "total_current_limit_a 40",
        "stale-telemetry denial",
        "PB-BENCH-005",
        "PB-BENCH-006",
        "PB-BENCH-010",
        "40 A board budget",
        "PBFLT-CUR-STALE",
        "PBFLT-BUDGET",
        "CSS4J-4026R-L500F",
        "1.0mΩ fallback",
        "Isabellenhuette BVN/BAS",
        "AEC-Q200",
        "JLCPCB PCBWay",
        "PB-100-current-monitor-pin-template.csv",
        "PB-100-symbol-pin-evidence.csv",
        "PB-100-symbol-mpn-readiness.csv",
        "telemetry.kicad_sch",
        "CAP-TEL",
        "No PCB layout",
        "PB-100.kicad_pcb",
        "Gerbers",
        "drills",
        "pick-place",
        "manufacturing ZIP",
        "shunt placement",
        "Kelvin routing",
        "monitor footprint",
        "board outline",
    ):
        if token not in precheck_text:
            fail(f"current telemetry closeout precheck must include {token}")

    for supporting_artifact, tokens in {
        "PB-100-current-telemetry-value-freeze-checklist.csv": ("CUR-FRZ-001", "CUR-FRZ-010"),
        "PB-100-current-telemetry-value-derivation-precheck.csv": ("CUR-DER-001", "CUR-DER-010"),
        "PB-100-current-telemetry-freeze-review.csv": ("Total shunt range", "Bench validation path"),
        "PB-100-b2b-lb100-resource-binding.csv": ("IIN_SENSE", "PB_I2C_SCL", "PB_I2C_SDA"),
    }.items():
        supporting_text = read_text(PB100_DIR / supporting_artifact)
        for token in tokens:
            if token not in supporting_text:
                fail(f"current telemetry closeout precheck requires {supporting_artifact} token {token}")


def validate_thermal_telemetry_trace() -> None:
    path = PB100_DIR / "PB-100-thermal-telemetry-trace.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty thermal telemetry trace: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in THERMAL_TELEMETRY_TRACE_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    expected_signals_by_zone = {
        "PCB reference": "TEMP_PCB",
        "Power zone A": "TEMP_PWR_A",
        "Power zone B": "TEMP_PWR_B",
    }
    rows_by_zone: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        zone = row["Thermal zone"].strip()
        if zone in rows_by_zone:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate thermal zone {zone}")
        if zone not in expected_signals_by_zone:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown thermal zone {zone}")
        rows_by_zone[zone] = row
        for column in THERMAL_TELEMETRY_TRACE_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        if row["Signal"].strip() != expected_signals_by_zone[zone]:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: {zone} signal mismatch")
        row_text = " ".join(row.values())
        for token in (
            "NTCGS103JF103FT8",
            "10k",
            "150C",
            "AEC-Q200",
            "LB ADC",
            "85C warn 105C cutoff 75C recovery",
            "configuration",
            "schematic freeze",
        ):
            if token not in row_text:
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: thermal trace row must include {token}")

    missing_zones = sorted(set(expected_signals_by_zone) - set(rows_by_zone))
    if missing_zones:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing thermal zones: "
            f"{', '.join(missing_zones)}"
        )

    thermal_map_rows = list(csv.DictReader((PB100_DIR / "PB-100-thermal-telemetry-map.csv").open(newline="", encoding="utf-8")))
    map_by_signal = {row["Signal"].strip(): row for row in thermal_map_rows}
    capabilities = json.loads(read_text(REPO_ROOT / "firmware" / "configs" / "hardware" / "pb-100-capabilities.json"))
    capability_signals = set(capabilities["telemetry"]["thermal_signals"])
    for signal in expected_signals_by_zone.values():
        if signal not in capability_signals:
            fail(f"{signal} must be exposed in PB-100 capability manifest")
        map_row = map_by_signal.get(signal)
        if map_row is None:
            fail(f"thermal telemetry map must include {signal}")
        map_text = " ".join(map_row.values())
        for token in ("NTCGS103JF103FT8", "-40 to 150", "LB ADC", "85C warn 105C cutoff 75C recovery"):
            if token not in map_text:
                fail(f"thermal telemetry map row {signal} must include {token}")

    config_example = json.loads(read_text(REPO_ROOT / "firmware" / "configs" / "config-example.json"))
    for zone_key in ("pcb", "power_zone_a", "power_zone_b"):
        zone_config = config_example["thermal"][zone_key]
        if zone_config != {"warn_c": 85, "cutoff_c": 105, "recovery_c": 75}:
            fail(f"config thermal thresholds for {zone_key} must remain 85/105/75")

    thermal_doc = read_text(PB100_DIR / "PB-100-thermal-telemetry.md")
    for token in ("configuration/calibration values", "Missing, saturated, or implausible", "Output Manager", "85 °C warn"):
        if token not in thermal_doc:
            fail(f"thermal telemetry strategy must preserve {token}")

    firmware_readme = read_text(REPO_ROOT / "firmware" / "README.md").lower()
    for token in ("thermal protection", "thermal system safety", "cutoff/stale", "telemetry"):
        if token not in firmware_readme:
            fail(f"firmware README must keep thermal safety coverage token: {token}")


def validate_thermal_telemetry_freeze_review() -> None:
    path = PB100_DIR / "PB-100-thermal-telemetry-freeze-review.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty thermal telemetry freeze review: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in THERMAL_TELEMETRY_FREEZE_REVIEW_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_item: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        review_item = row["Review item"].strip()
        if review_item not in REQUIRED_THERMAL_TELEMETRY_FREEZE_REVIEW_ITEMS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown thermal telemetry review item {review_item}")
        if review_item in rows_by_item:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate thermal telemetry review item {review_item}")
        rows_by_item[review_item] = row
        for column in THERMAL_TELEMETRY_FREEZE_REVIEW_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        row_text = " ".join(row.values()).lower()
        if review_item == "Configuration thresholds" and "configuration" not in row_text:
            fail("thermal telemetry freeze review must keep thresholds in configuration")
        if review_item == "Firmware fail-safe" and "stale" not in row_text:
            fail("thermal telemetry freeze review must keep stale telemetry fail-safe behavior")

    missing_items = sorted(REQUIRED_THERMAL_TELEMETRY_FREEZE_REVIEW_ITEMS - rows_by_item.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing thermal telemetry review items: "
            f"{', '.join(missing_items)}"
        )

    review_text = read_text(path)
    for token in (
        "NTCGS103JF103FT8",
        "10k",
        "150C",
        "AEC-Q200",
        "TEMP_PCB",
        "TEMP_PWR_A",
        "TEMP_PWR_B",
        "Vishay NTCS0402E3",
        "Murata NCU18",
        "85C warn 105C cutoff",
        "75C recovery",
        "LB_3V3_IO ADC",
        "self-heating",
        "configuration and calibration data not firmware constants",
        "Stale thermal telemetry",
        "test_stale_thermal_telemetry_forces_cutoff",
        "PB-BENCH-009",
        "Do not place sensors or thermal copper before schematic freeze",
    ):
        if token not in review_text:
            fail(f"thermal telemetry freeze review must include {token}")

    thermal_doc = read_text(PB100_DIR / "PB-100-thermal-telemetry.md")
    for token in ("NTCGS103JF103FT8", "10 kΩ", "3435 K", "150 °C", "self-heating", "configuration/calibration"):
        if token not in thermal_doc:
            fail(f"thermal telemetry strategy must support freeze review token {token}")

    thermal_map_text = read_text(PB100_DIR / "PB-100-thermal-telemetry-map.csv")
    for token in ("TEMP_PCB", "TEMP_PWR_A", "TEMP_PWR_B", "-40 to 150", "85C warn 105C cutoff 75C recovery"):
        if token not in thermal_map_text:
            fail(f"thermal telemetry map must support freeze review token {token}")

    config_text = read_text(REPO_ROOT / "firmware" / "configs" / "config-example.json")
    for token in ("\"warn_c\": 85", "\"cutoff_c\": 105", "\"recovery_c\": 75"):
        if token not in config_text:
            fail(f"thermal config example must support freeze review token {token}")

    firmware_joined = "\n".join(
        (
            read_text(REPO_ROOT / "firmware" / "tests" / "test_thermal_service.c"),
            read_text(REPO_ROOT / "firmware" / "tests" / "test_system_safety.c"),
            read_text(REPO_ROOT / "firmware" / "tests" / "test_config_validator.c"),
        )
    )
    for token in (
        "test_default_thermal_config_is_valid",
        "test_invalid_thermal_config_is_rejected",
        "test_thermal_derate_publishes_event_without_disabling_outputs",
        "test_thermal_cutoff_disables_active_outputs",
        "test_stale_thermal_telemetry_disables_active_outputs",
        "test_stale_thermal_telemetry_forces_cutoff",
    ):
        if token not in firmware_joined:
            fail(f"firmware tests must retain thermal freeze review token {token}")


def validate_thermal_telemetry_value_freeze_checklist() -> None:
    path = PB100_DIR / "PB-100-thermal-telemetry-value-freeze-checklist.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty thermal telemetry value freeze checklist: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [
        column for column in THERMAL_TELEMETRY_VALUE_FREEZE_CHECKLIST_COLUMNS if column not in fieldnames
    ]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_check: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        check_id = row["Check ID"].strip()
        if check_id not in REQUIRED_THERMAL_TELEMETRY_VALUE_FREEZE_CHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown thermal telemetry check {check_id}")
        if check_id in rows_by_check:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate thermal telemetry check {check_id}")
        rows_by_check[check_id] = row
        for column in THERMAL_TELEMETRY_VALUE_FREEZE_CHECKLIST_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)

    missing_checks = sorted(REQUIRED_THERMAL_TELEMETRY_VALUE_FREEZE_CHECKS - rows_by_check.keys())
    if missing_checks:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing thermal telemetry checks: "
            f"{', '.join(missing_checks)}"
        )

    checklist_text = read_text(path)
    for token in (
        "NTCGS103JF103FT8",
        "10k",
        "150C",
        "AEC-Q200",
        "TEMP_PCB",
        "TEMP_PWR_A",
        "TEMP_PWR_B",
        "Vishay NTCS0402E3",
        "Murata NCU18",
        "4.7kΩ",
        "LB_3V3_IO",
        "10kΩ NTC",
        "1kΩ",
        "10nF",
        "0.95 V at 75 °C",
        "0.78 V at 85 °C",
        "0.52 V at 105 °C",
        "224µA",
        "0.50mW",
        "0.31mW",
        "ADC settling",
        "85C warn 105C cutoff 75C recovery",
        "telemetry.thermal",
        "10000Ω",
        "3435 K",
        "4700Ω",
        "1000Ω",
        "1000 ms",
        "-40 to 150 °C",
        "test_stale_thermal_telemetry_forces_cutoff",
        "PB-BENCH-009",
        "THERMAL_NTC",
        "JLCPCB PCBWay",
        "TMP117/TMP112",
        "No PCB layout",
        "PB-100.kicad_pcb",
        "Gerbers",
        "drills",
        "pick-place",
    ):
        if token not in checklist_text:
            fail(f"thermal telemetry value freeze checklist must include {token}")

    calculation_text = read_text(PB100_DIR / "PB-100-thermal-telemetry-design-calculation.md")
    for token in ("4.7 kΩ", "1 kΩ", "10 nF", "0.78 V", "0.52 V", "0.50 mW", "3435 K"):
        if token not in calculation_text:
            fail(f"thermal telemetry design calculation must support checklist token {token}")

    config_text = read_text(REPO_ROOT / "firmware" / "configs" / "config-example.json")
    for token in ("\"warn_c\": 85", "\"cutoff_c\": 105", "\"recovery_c\": 75"):
        if token not in config_text:
            fail(f"thermal config example must support value checklist token {token}")


def validate_thermal_telemetry_value_derivation_precheck() -> None:
    path = PB100_DIR / "PB-100-thermal-telemetry-value-derivation-precheck.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty thermal telemetry value derivation precheck: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [
        column for column in THERMAL_TELEMETRY_VALUE_DERIVATION_PRECHECK_COLUMNS if column not in fieldnames
    ]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_id: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        derivation_id = row["Derivation ID"].strip()
        if derivation_id not in REQUIRED_THERMAL_TELEMETRY_VALUE_DERIVATION_CHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown thermal telemetry derivation item {derivation_id}")
        if derivation_id in rows_by_id:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate thermal telemetry derivation item {derivation_id}")
        rows_by_id[derivation_id] = row
        for column in THERMAL_TELEMETRY_VALUE_DERIVATION_PRECHECK_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        row_text = " ".join(row.values()).lower()
        if derivation_id == "THERM-DER-002" and ("rntc =" not in row_text or "exp" not in row_text):
            fail("thermal telemetry derivation precheck must include NTC beta equation")
        if derivation_id == "THERM-DER-003" and "vadc =" not in row_text:
            fail("thermal telemetry derivation precheck must include ADC divider equation")
        if derivation_id == "THERM-DER-010" and ("pb-100.kicad_pcb" not in row_text or "manufacturing" not in row_text):
            fail("thermal telemetry derivation precheck must block layout and manufacturing outputs")

    missing_items = sorted(REQUIRED_THERMAL_TELEMETRY_VALUE_DERIVATION_CHECKS - rows_by_id.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing thermal telemetry derivation items: "
            f"{', '.join(missing_items)}"
        )

    precheck_text = read_text(path)
    for token in (
        "TDK NTCGS103JF103FT8",
        "Vishay NTCS0402E3",
        "Murata NCU18",
        "TEMP_PCB",
        "TEMP_PWR_A",
        "TEMP_PWR_B",
        "RNTC = R25 * exp(B * (1/T - 1/T25))",
        "R25 10000Ω",
        "3435 K",
        "-40 °C to 150 °C",
        "VADC = 3.3 V * RNTC / (4.7 kΩ + RNTC)",
        "4.7kΩ",
        "10kΩ NTC",
        "0.95 V at 75 °C",
        "0.78 V at 85 °C",
        "0.52 V at 105 °C",
        "PNTC = I^2 * RNTC",
        "224µA",
        "0.50mW",
        "0.31mW",
        "1kΩ",
        "10nF X7R",
        "LB ADC",
        "LB_3V3_IO",
        "telemetry.thermal",
        "4700Ω",
        "1000Ω",
        "10 nF",
        "1000 ms",
        "85C warn 105C cutoff 75C recovery",
        "test_stale_thermal_telemetry_forces_cutoff",
        "PB-BENCH-009",
        "THERMAL_NTC",
        "JLCPCB PCBWay",
        "TMP117/TMP112",
        "PB-100.kicad_pcb",
        "Gerbers",
        "drills",
        "pick-place",
    ):
        if token not in precheck_text:
            fail(f"thermal telemetry value derivation precheck must include {token}")

    calculation_text = read_text(PB100_DIR / "PB-100-thermal-telemetry-design-calculation.md")
    for token in ("VADC", "0.78 V", "0.52 V", "0.50 mW", "3435 K"):
        if token not in calculation_text:
            fail(f"thermal telemetry design calculation must support derivation token {token}")


def validate_thermal_telemetry_closeout_precheck() -> None:
    path = PB100_DIR / "PB-100-thermal-telemetry-closeout-precheck.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty thermal telemetry closeout precheck: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in THERMAL_TELEMETRY_CLOSEOUT_PRECHECK_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_id: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        precheck_id = row["Precheck ID"].strip()
        if precheck_id not in REQUIRED_THERMAL_TELEMETRY_CLOSEOUT_PRECHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown thermal telemetry closeout precheck {precheck_id}")
        if precheck_id in rows_by_id:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate thermal telemetry closeout precheck {precheck_id}")
        rows_by_id[precheck_id] = row
        for column in THERMAL_TELEMETRY_CLOSEOUT_PRECHECK_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        row_text = " ".join(row.values()).lower()
        if "do not" not in row["Blocked action"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: blocked action must be explicit")
        if precheck_id == "THERM-CLS-002" and ("rntc =" not in row_text or "vadc =" not in row_text):
            fail("thermal telemetry closeout value row must include RNTC and VADC equations")
        if precheck_id == "THERM-CLS-004" and "pntc" not in row_text:
            fail("thermal telemetry closeout self-heating row must include PNTC")
        if precheck_id == "THERM-CLS-010" and ("no pcb layout" not in row_text or "pb-100.kicad_pcb" not in row_text):
            fail("thermal telemetry closeout no-layout row must block PCB layout explicitly")

    missing_items = sorted(REQUIRED_THERMAL_TELEMETRY_CLOSEOUT_PRECHECKS - rows_by_id.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing thermal telemetry closeout prechecks: "
            f"{', '.join(missing_items)}"
        )

    precheck_text = read_text(path)
    for token in (
        "TDK NTCGS103JF103FT8",
        "10k",
        "150C",
        "AEC-Q200",
        "TEMP_PCB",
        "TEMP_PWR_A",
        "TEMP_PWR_B",
        "Vishay NTCS0402E3",
        "Murata NCU18",
        "THERMAL_NTC",
        "JLCPCB PCBWay",
        "TMP117/TMP112",
        "RNTC = R25 * exp(B * (1/T - 1/T25))",
        "VADC = 3.3 V * RNTC / (4.7 kΩ + RNTC)",
        "R25 10000Ω",
        "3435 K",
        "4.7kΩ",
        "LB_3V3_IO",
        "10kΩ NTC",
        "1kΩ",
        "10nF X7R",
        "0.95 V at 75 °C",
        "0.78 V at 85 °C",
        "0.52 V at 105 °C",
        "OUT2",
        "input reverse hot zone",
        "medium-output or logic-buck hot zone",
        "PNTC = I^2 * RNTC",
        "224µA",
        "0.50mW",
        "0.31mW",
        "LB ADC",
        "ADC settling",
        "external ADC/mux",
        "telemetry.thermal",
        "4700Ω",
        "1000Ω",
        "10 nF",
        "1000 ms",
        "85C warn 105C cutoff 75C recovery",
        "-40 to 150 °C",
        "PBFLT-THERM-HIGH",
        "PBFLT-THERM-STALE",
        "test_stale_thermal_telemetry_forces_cutoff",
        "test_stale_thermal_telemetry_disables_active_outputs",
        "PB-BENCH-009",
        "PB-100-symbol-mpn-readiness.csv",
        "production/bom/factory_bom_draft.csv",
        "production/bom/pb100_sourcing_evidence_snapshot.csv",
        "telemetry.kicad_sch",
        "CAP-TEL",
        "PB-100-thermal-telemetry-map.csv",
        "PB-100-thermal-telemetry-value-freeze-checklist.csv",
        "No PCB layout",
        "PB-100.kicad_pcb",
        "Gerbers",
        "drills",
        "pick-place",
        "manufacturing ZIP",
        "sensor placement",
        "thermal copper",
        "board outline",
    ):
        if token not in precheck_text:
            fail(f"thermal telemetry closeout precheck must include {token}")

    for supporting_artifact, tokens in {
        "PB-100-thermal-telemetry-value-freeze-checklist.csv": ("THERM-FRZ-001", "THERM-FRZ-010"),
        "PB-100-thermal-telemetry-value-derivation-precheck.csv": ("THERM-DER-001", "THERM-DER-010"),
        "PB-100-thermal-telemetry-freeze-review.csv": ("Sensor class", "Bench validation path"),
        "PB-100-b2b-lb100-resource-binding.csv": ("TEMP_PCB", "TEMP_PWR_A", "TEMP_PWR_B"),
    }.items():
        supporting_text = read_text(PB100_DIR / supporting_artifact)
        for token in tokens:
            if token not in supporting_text:
                fail(f"thermal telemetry closeout precheck requires {supporting_artifact} token {token}")


def validate_logic_power_rail_trace() -> None:
    path = PB100_DIR / "PB-100-logic-power-rail-trace.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty logic power rail trace: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in LOGIC_POWER_RAIL_TRACE_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    required_items = {
        "Buck regulator",
        "Buck input rail",
        "Buck output rail",
        "Power good",
        "Safe default off",
        "Higher-current fallback",
    }
    rows_by_item: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        item = row["Trace item"].strip()
        if item in rows_by_item:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate trace item {item}")
        if item not in required_items:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown trace item {item}")
        rows_by_item[item] = row
        for column in LOGIC_POWER_RAIL_TRACE_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        if "schematic freeze" not in " ".join(row.values()).lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: freeze dependency must reference schematic freeze")

    missing_items = sorted(required_items - rows_by_item.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing logic power trace items: "
            f"{', '.join(missing_items)}"
        )

    trace_text = read_text(path)
    for token in (
        "LM5164-Q1-class 100 V 1 A",
        "LM5013-Q1-class 100 V fallback",
        "PB_5V_OUT must not power accessory loads",
        "PB_PWR_GOOD",
        "default off",
        "TPS54360B-Q1-class 60 V path remains conditional",
    ):
        if token not in trace_text:
            fail(f"logic power rail trace must include {token}")

    budget_rows = list(csv.DictReader((PB100_DIR / "PB-100-logic-power-budget.csv").open(newline="", encoding="utf-8")))
    initial_total = next((row for row in budget_rows if row["Load"].strip() == "Initial total"), None)
    if initial_total is None or initial_total["Current mA"].strip() != "1000":
        fail("logic power budget must keep 1000 mA initial total")
    if "LM5013-Q1" not in initial_total["Notes"]:
        fail("logic power budget must keep LM5013-Q1 fallback note")

    placeholder_text = read_text(PB100_DIR / "PB-100-logic-power-design-placeholders.csv")
    for token in ("Preferred LM5164-Q1 class", "LM5013-Q1 remains higher-current alternate", "Must not connect to raw unfused input"):
        if token not in placeholder_text:
            fail(f"logic power placeholders must include {token}")

    design_values_text = read_text(PB100_DIR / "PB-100-logic-power-design-values.csv")
    for token in ("PB_5V_OUT must not power accessory loads", "LM5013-Q1-class", "Outputs default off"):
        if token not in design_values_text:
            fail(f"logic power design values must include {token}")

    capabilities = json.loads(read_text(REPO_ROOT / "firmware" / "configs" / "hardware" / "pb-100-capabilities.json"))
    board_signals = set(capabilities["telemetry"]["board_signals"])
    if "PB_PWR_GOOD" not in board_signals:
        fail("PB-100 capability manifest must expose PB_PWR_GOOD board signal")

    firmware_readme = read_text(REPO_ROOT / "firmware" / "README.md").lower()
    for token in ("runtime boot", "outputs off", "hardware capability"):
        if token not in firmware_readme:
            fail(f"firmware README must keep runtime boot safety token: {token}")


def validate_can1_capture_contract() -> None:
    can1_doc = read_text(PB100_DIR / "PB-100-can1-tx-disable.md").lower()
    for token in (
        "jp_can1",
        "u_can1",
        "dnp/open",
        "no default-populated tx",
        "physical disabled state",
        "configuration cannot enable",
        "future adr",
        "explicit hardware action",
    ):
        if token not in can1_doc:
            fail(f"PB-100 CAN1 TX-disable document must include {token}")

    production_review = read_text(PB100_DIR / "PB-100-can1-production-dnp-review.csv").lower()
    for token in ("jp_can1", "u_can1", "dnp/open", "no default-populated", "firmware-only"):
        if token not in production_review:
            fail(f"CAN1 production DNP review must include {token}")

    reset_checklist = read_text(PB100_DIR / "PB-100-can1-reset-bench-checklist.csv").lower()
    for token in (
        "pb-bench-012",
        "reset",
        "unpowered",
        "dnp/open",
        "physical disabled",
        "no vehicle-can transmit frame",
        "future adr",
        "explicit hardware action",
    ):
        if token not in reset_checklist:
            fail(f"CAN1 reset bench checklist must include {token}")

    can1_sheet = read_text(KICAD_DIR / "sheets" / "can1-safety.kicad_sch").lower()
    for token in (
        "jp_can1",
        "u_can1",
        "dnp/open",
        "no default-populated tx",
        "physical disabled state",
        "pb-100-can1-production-dnp-review.csv",
        "pb-100-can1-reset-bench-checklist.csv",
    ):
        if token not in can1_sheet:
            fail(f"CAN1 safety KiCad sheet capture notes must include {token}")

    if '(lib_id "pb100:pb100_can1_tx_disable_prelim")' in can1_sheet:
        fail("JP_CAN1 and U_CAN1 must not use the generic CAN1_TX_DISABLE preliminary symbol")
    for reference, concrete_symbol in (
        ("JP_CAN1", "PB100:PB100_CAN1_TX_DNP_LINK_PRELIM"),
        ("U_CAN1", "PB100:PB100_SN74LVC1G125_Q1_DBV_PRELIM"),
    ):
        reference_marker = f'(property "reference" "{reference.lower()}"'
        symbol_marker = f'(lib_id "{concrete_symbol.lower()}")'
        reference_index = can1_sheet.find(reference_marker)
        if reference_index < 0:
            fail(f"CAN1 safety sheet is missing reference {reference}")
        symbol_index = can1_sheet.rfind("(lib_id", 0, reference_index)
        if symbol_index < 0 or symbol_marker not in can1_sheet[symbol_index:reference_index]:
            fail(f"{reference} must use concrete symbol {concrete_symbol}")
    if '(property "reference" "jp_can1"' in can1_sheet and "(dnp yes)" not in can1_sheet:
        fail("JP_CAN1 must remain DNP/open in the CAN1 safety sheet")
    if "can1_tx_gate_out" not in can1_sheet:
        fail("CAN1 safety sheet must expose CAN1_TX_GATE_OUT between U_CAN1 and JP_CAN1")

    bom_map = read_text(REPO_ROOT / "production" / "bom" / "pb100_symbol_bom_map.csv").lower()
    for token in ("can1_tx_disable", "default dnp/open", "no default-populated"):
        if token not in bom_map:
            fail(f"CAN1 symbol BOM map must include {token}")


def validate_assembly_sourcing_recheck() -> None:
    path = REPO_ROOT / "production" / "bom" / "pb100_assembly_sourcing_recheck.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty assembly sourcing recheck register: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in ASSEMBLY_SOURCING_RECHECK_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    readiness_rows = list(
        csv.DictReader((PB100_DIR / "PB-100-symbol-mpn-readiness.csv").open(newline="", encoding="utf-8"))
    )
    critical_readiness = {
        row["Symbol key"].strip(): row
        for row in readiness_rows
        if row["Critical"].strip().lower() == "yes"
    }
    bom_rows = list(
        csv.DictReader((REPO_ROOT / "production" / "bom" / "pb100_symbol_bom_map.csv").open(newline="", encoding="utf-8"))
    )
    bom_owner_by_key = {row["Symbol key"].strip(): row["Assembly owner"].strip() for row in bom_rows}

    seen_keys = set()
    for row_number, row in enumerate(rows, 2):
        symbol_key = row["Symbol key"].strip()
        if symbol_key in seen_keys:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate symbol key {symbol_key}")
        seen_keys.add(symbol_key)
        if symbol_key not in critical_readiness:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: symbol key {symbol_key} is not critical readiness key")
        expected_owner = bom_owner_by_key.get(symbol_key)
        if row["Assembly owner"].strip() != expected_owner:
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: assembly owner must be "
                f"{expected_owner}, got {row['Assembly owner'].strip()}"
            )
        for column in ASSEMBLY_SOURCING_RECHECK_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        if "schematic freeze" not in row["Freeze dependency"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: freeze dependency must reference schematic freeze")
        row_text = " ".join(row.values()).lower()
        if symbol_key == "CAN1_TX_DISABLE":
            if "dnp/open" not in row_text or "no default-populated tx" not in row_text:
                fail("CAN1_TX_DISABLE sourcing row must keep DNP/open and no default-populated TX explicit")
        else:
            if "recheck" not in row_text:
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: sourcing row must keep recheck explicit")
        if row["Assembly owner"].strip() == "Factory":
            if row["Factory action"].strip() == "N/A":
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: factory row needs Factory action")
            if row["Garage action"].strip() != "N/A":
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: factory row must use N/A Garage action")
        elif row["Assembly owner"].strip() == "Garage":
            if row["Garage action"].strip() == "N/A":
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: garage row needs Garage action")
            if row["Factory action"].strip() != "N/A":
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: garage row must use N/A Factory action")
        else:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: invalid assembly owner {row['Assembly owner'].strip()}")
        if "alternat" not in row["Alternate coverage"].lower() and symbol_key != "CAN1_TX_DISABLE":
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: alternate coverage must remain explicit")
        if symbol_key == "INPUT_REVERSE_FET":
            if not all(token in row_text for token in ("80 v", "lfpak88", "40 a")):
                fail("INPUT_REVERSE_FET sourcing row must keep selected 80 V LFPAK88 and 40 A review explicit")

    missing_keys = sorted(critical_readiness.keys() - seen_keys)
    extra_keys = sorted(seen_keys - critical_readiness.keys())
    if missing_keys:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing critical sourcing keys: "
            f"{', '.join(missing_keys)}"
        )
    if extra_keys:
        fail(
            f"{path.relative_to(REPO_ROOT)} has non-critical sourcing keys: "
            f"{', '.join(extra_keys)}"
        )


def trace_symbol_keys(value: str) -> set[str]:
    return {part.strip() for part in value.split(";") if part.strip()}


def validate_assembly_readiness_trace() -> None:
    path = PB100_DIR / "PB-100-assembly-readiness-trace.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty assembly readiness trace: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in ASSEMBLY_READINESS_TRACE_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_owner: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        owner = row["Assembly owner"].strip()
        if owner in rows_by_owner:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate assembly owner row {owner}")
        if owner not in {"Factory", "Garage", "Safety DNP"}:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown assembly owner row {owner}")
        rows_by_owner[owner] = row
        for column in ASSEMBLY_READINESS_TRACE_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        row_text = " ".join(row.values()).lower()
        if "schematic freeze" not in row_text:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: freeze action must reference schematic freeze")
        if "do not" not in row["Blocked action"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: blocked action must be explicit")

    for owner in ("Factory", "Garage", "Safety DNP"):
        if owner not in rows_by_owner:
            fail(f"{path.relative_to(REPO_ROOT)} must include {owner} assembly trace row")

    sourcing_rows = list(
        csv.DictReader((REPO_ROOT / "production" / "bom" / "pb100_assembly_sourcing_recheck.csv").open(newline="", encoding="utf-8"))
    )
    expected_keys_by_owner = {
        "Factory": {
            row["Symbol key"].strip()
            for row in sourcing_rows
            if row["Assembly owner"].strip() == "Factory"
        },
        "Garage": {
            row["Symbol key"].strip()
            for row in sourcing_rows
            if row["Assembly owner"].strip() == "Garage"
        },
    }

    for owner in ("Factory", "Garage"):
        trace_keys = trace_symbol_keys(rows_by_owner[owner]["Required symbol keys"])
        expected_keys = expected_keys_by_owner[owner]
        if trace_keys != expected_keys:
            missing = sorted(expected_keys - trace_keys)
            extra = sorted(trace_keys - expected_keys)
            fail(
                f"{path.relative_to(REPO_ROOT)} {owner} keys mismatch; "
                f"missing={','.join(missing)} extra={','.join(extra)}"
            )

    factory_text = " ".join(rows_by_owner["Factory"].values()).lower()
    for token in ("jlcpcb", "pcbway", "alternates", "assembly class", "do not lock"):
        if token not in factory_text:
            fail(f"factory assembly trace must preserve {token}")

    garage_text = " ".join(rows_by_owner["Garage"].values()).lower()
    for token in ("user-installed", "connector", "fuse", "wire gauge", "crimp", "do not move"):
        if token not in garage_text:
            fail(f"garage assembly trace must preserve {token}")

    safety_text = " ".join(rows_by_owner["Safety DNP"].values()).lower()
    for token in ("can1_tx_disable", "dnp/open", "no default-populated", "future adr"):
        if token not in safety_text:
            fail(f"safety DNP assembly trace must preserve {token}")


def validate_factory_assembly_freeze_checklist() -> None:
    path = PB100_DIR / "PB-100-factory-assembly-freeze-checklist.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty factory assembly freeze checklist: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [
        column for column in FACTORY_ASSEMBLY_FREEZE_CHECKLIST_COLUMNS if column not in fieldnames
    ]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_check: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        check_id = row["Check ID"].strip()
        if check_id not in REQUIRED_FACTORY_ASSEMBLY_FREEZE_CHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown factory assembly check {check_id}")
        if check_id in rows_by_check:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate factory assembly check {check_id}")
        rows_by_check[check_id] = row
        for column in FACTORY_ASSEMBLY_FREEZE_CHECKLIST_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        if "do not" not in row["Blocked action"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: blocked action must be explicit")

    missing_checks = sorted(REQUIRED_FACTORY_ASSEMBLY_FREEZE_CHECKS - rows_by_check.keys())
    if missing_checks:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing factory assembly checks: "
            f"{', '.join(missing_checks)}"
        )

    checklist_text = read_text(path)
    for token in (
        "HS_CTRL",
        "OUT_FET",
        "OUT2_ESCAPE_FET",
        "INPUT_IDEAL_DIODE",
        "INPUT_REVERSE_FET",
        "INPUT_TVS",
        "LOGIC_BUCK",
        "LOGIC_BUCK_INDUCTOR",
        "TOTAL_CURRENT_MONITOR",
        "TOTAL_CURRENT_SHUNT",
        "THERMAL_NTC",
        "B2B_CONNECTOR",
        "CAN1_TX_DISABLE",
        "Alternate 1",
        "Alternate 2",
        "JLCPCB PCBWay",
        "assembly class",
        "reel",
        "tray",
        "cut tape",
        "authorized distributor",
        "2026-07-16",
        "date-stamped",
        "TPS48110AQDGXRQ1",
        "SIDR626LDP-T1-RE3",
        "IAUTN06S5N008ATMA1",
        "BUK7S1R2-80M",
        "PowerPAK",
        "TOLL",
        "LFPAK88",
        "19-VSSOP",
        "SM8S33AHM3/I",
        "SLD8S33A",
        "DM8W33AQ-13",
        "SM8S33A-Q",
        "MCC SM8S33A EOL",
        "Vishay HE3 NFD",
        "DO-218AC",
        "LM5164QDDATQ1",
        "LM5013-Q1",
        "TPS54360B-Q1",
        "INA228-Q1",
        "INA229-Q1",
        "INA226",
        "CSS4J-4026R-L500F",
        "1.0mΩ",
        "NTCGS103JF103FT8",
        "Vishay NTCS0402E3",
        "Murata NCU18",
        "FX18-100P-0.8SV10",
        "FX18-100S-0.8SV20",
        "20 mm",
        "DNP/open",
        "no default-populated TX",
        "future ADR",
        "factory_bom_draft.csv",
        "pb100_symbol_bom_map.csv",
        "pb100_assembly_sourcing_recheck.csv",
        "pb100_sourcing_evidence_snapshot.csv",
        "PB-100-review-release-manifest.csv",
        "PB-100-schematic-freeze-checklist.md",
        "No PCB layout",
        "PB-100.kicad_pcb",
        "Gerbers",
        "drills",
        "pick-place",
    ):
        if token not in checklist_text:
            fail(f"factory assembly freeze checklist must include {token}")

    sourcing_text = read_text(REPO_ROOT / "production" / "bom" / "pb100_assembly_sourcing_recheck.csv")
    evidence_text = read_text(REPO_ROOT / "production" / "bom" / "pb100_sourcing_evidence_snapshot.csv")
    for token in ("JLCPCB/PCBWay", "Alternates", "Verify", "schematic freeze"):
        if token not in sourcing_text:
            fail(f"assembly sourcing recheck must support factory checklist token {token}")
    for token in ("2026-07-16", "Open:", "DNP/open"):
        if token not in evidence_text:
            fail(f"sourcing evidence snapshot must support factory checklist token {token}")


def validate_factory_assembly_sourcing_precheck() -> None:
    path = PB100_DIR / "PB-100-factory-assembly-sourcing-precheck.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty factory assembly sourcing precheck: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [
        column for column in FACTORY_ASSEMBLY_SOURCING_PRECHECK_COLUMNS if column not in fieldnames
    ]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_id: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        precheck_id = row["Precheck ID"].strip()
        if precheck_id not in REQUIRED_FACTORY_ASSEMBLY_SOURCING_PRECHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown factory sourcing precheck {precheck_id}")
        if precheck_id in rows_by_id:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate factory sourcing precheck {precheck_id}")
        rows_by_id[precheck_id] = row
        for column in FACTORY_ASSEMBLY_SOURCING_PRECHECK_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        if "do not" not in row["Blocked action"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: blocked action must be explicit")

    missing_checks = sorted(REQUIRED_FACTORY_ASSEMBLY_SOURCING_PRECHECKS - rows_by_id.keys())
    if missing_checks:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing factory assembly sourcing prechecks: "
            f"{', '.join(missing_checks)}"
        )

    precheck_text = read_text(path)
    for token in (
        "HS_CTRL",
        "OUT_FET",
        "OUT2_ESCAPE_FET",
        "INPUT_IDEAL_DIODE",
        "INPUT_REVERSE_FET",
        "INPUT_TVS",
        "LOGIC_BUCK",
        "LOGIC_BUCK_INDUCTOR",
        "TOTAL_CURRENT_MONITOR",
        "TOTAL_CURRENT_SHUNT",
        "THERMAL_NTC",
        "B2B_CONNECTOR",
        "CAN1_TX_DISABLE",
        "PB-100-assembly-readiness-trace.csv",
        "PB-100-factory-assembly-freeze-checklist.csv",
        "PB-100-symbol-mpn-readiness.csv",
        "production/bom/factory_bom_draft.csv",
        "production/bom/pb100_symbol_bom_map.csv",
        "production/bom/pb100_assembly_sourcing_recheck.csv",
        "production/bom/pb100_sourcing_evidence_snapshot.csv",
        "JLCPCB PCBWay",
        "assembly class",
        "reel",
        "tray",
        "cut tape",
        "extended part",
        "orderable suffix",
        "Alternate 1",
        "Alternate 2",
        "TPS48110AQDGXRQ1",
        "SIDR626LDP-T1-RE3",
        "IAUTN06S5N008ATMA1",
        "BUK7S1R2-80M",
        "LM74700QDBVRQ1",
        "19-VSSOP",
        "PowerPAK",
        "TOLL",
        "LFPAK88",
        "SOT-23-6",
        "SM8S33AHM3/I",
        "SLD8S33A",
        "DM8W33AQ-13",
        "SM8S33A-Q",
        "MCC SM8S33A EOL",
        "Vishay HE3 NFD",
        "DO-218AC",
        "LM5164QDDATQ1",
        "LM5013-Q1",
        "TPS54360B-Q1",
        "INA228-Q1",
        "INA229-Q1",
        "INA226",
        "CSS4J-4026R-L500F",
        "1.0mΩ",
        "NTCGS103JF103FT8",
        "Vishay NTCS0402E3",
        "Murata NCU18",
        "FX18-100P-0.8SV10",
        "FX18-100S-0.8SV20",
        "20 mm",
        "DNP/open",
        "no default-populated TX",
        "future ADR",
        "2026-07-16",
        "2026-07-17",
        "authorized distributor",
        "manufacturer evidence",
        "Open:",
        "No PCB layout",
        "PB-100.kicad_pcb",
        "Gerbers",
        "drills",
        "pick-place",
        "centroid",
        "PCBA order package",
        "manufacturing ZIP",
    ):
        if token not in precheck_text:
            fail(f"factory assembly sourcing precheck must include {token}")

    sourcing_text = read_text(REPO_ROOT / "production" / "bom" / "pb100_assembly_sourcing_recheck.csv")
    evidence_text = read_text(REPO_ROOT / "production" / "bom" / "pb100_sourcing_evidence_snapshot.csv")
    for token in ("JLCPCB/PCBWay", "authorized distributor", "schematic freeze"):
        if token not in sourcing_text:
            fail(f"assembly sourcing recheck must support factory sourcing precheck token {token}")
    for token in ("2026-07-16", "Open:", "DNP/open"):
        if token not in evidence_text:
            fail(f"sourcing evidence snapshot must support factory sourcing precheck token {token}")


def validate_factory_assembly_closeout_precheck() -> None:
    path = PB100_DIR / "PB-100-factory-assembly-closeout-precheck.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty factory assembly closeout precheck: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [
        column for column in FACTORY_ASSEMBLY_CLOSEOUT_PRECHECK_COLUMNS if column not in fieldnames
    ]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_id: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        precheck_id = row["Precheck ID"].strip()
        if precheck_id not in REQUIRED_FACTORY_ASSEMBLY_CLOSEOUT_PRECHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown factory closeout precheck {precheck_id}")
        if precheck_id in rows_by_id:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate factory closeout precheck {precheck_id}")
        rows_by_id[precheck_id] = row
        for column in FACTORY_ASSEMBLY_CLOSEOUT_PRECHECK_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        if "do not" not in row["Blocked action"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: blocked action must be explicit")
        row_text = " ".join(row.values()).lower()
        if precheck_id == "FACT-CLS-010" and ("no pcb layout" not in row_text or "pb-100.kicad_pcb" not in row_text):
            fail("factory assembly closeout no-layout row must block PCB layout explicitly")

    missing_checks = sorted(REQUIRED_FACTORY_ASSEMBLY_CLOSEOUT_PRECHECKS - rows_by_id.keys())
    if missing_checks:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing factory assembly closeout prechecks: "
            f"{', '.join(missing_checks)}"
        )

    closeout_text = read_text(path)
    for token in (
        "HS_CTRL",
        "OUT_FET",
        "OUT2_ESCAPE_FET",
        "INPUT_IDEAL_DIODE",
        "INPUT_REVERSE_FET",
        "INPUT_TVS",
        "LOGIC_BUCK",
        "LOGIC_BUCK_INDUCTOR",
        "TOTAL_CURRENT_MONITOR",
        "TOTAL_CURRENT_SHUNT",
        "THERMAL_NTC",
        "B2B_CONNECTOR",
        "CAN1_TX_DISABLE",
        "PB-100-assembly-readiness-trace.csv",
        "PB-100-factory-assembly-freeze-checklist.csv",
        "PB-100-factory-assembly-sourcing-precheck.csv",
        "PB-100-symbol-mpn-readiness.csv",
        "production/bom/factory_bom_draft.csv",
        "production/bom/pb100_symbol_bom_map.csv",
        "production/bom/pb100_assembly_sourcing_recheck.csv",
        "production/bom/pb100_sourcing_evidence_snapshot.csv",
        "PB-100-board-release-blocker-register.csv",
        "JLCPCB PCBWay",
        "JLCPCB/PCBWay",
        "assembly class",
        "reel",
        "tray",
        "cut tape",
        "extended part",
        "orderable suffix",
        "Alternate 1",
        "Alternate 2",
        "TPS48110AQDGXRQ1",
        "SIDR626LDP-T1-RE3",
        "IAUTN06S5N008ATMA1",
        "BUK7S1R2-80M",
        "LM74700QDBVRQ1",
        "19-VSSOP",
        "PowerPAK",
        "TOLL",
        "LFPAK88",
        "SOT-23-6",
        "SM8S33AHM3/I",
        "SLD8S33A",
        "DM8W33AQ-13",
        "SM8S33A-Q",
        "MCC SM8S33A EOL",
        "Vishay HE3 NFD",
        "DO-218AC",
        "LM5164QDDATQ1",
        "LM5013-Q1",
        "TPS54360B-Q1",
        "INA228-Q1",
        "INA229-Q1",
        "INA226",
        "CSS4J-4026R-L500F",
        "1.0mΩ",
        "NTCGS103JF103FT8",
        "Vishay NTCS0402E3",
        "Murata NCU18",
        "FX18-100P-0.8SV10",
        "FX18-100S-0.8SV20",
        "20 mm",
        "DNP/open",
        "no default-populated TX",
        "future ADR",
        "2026-07-16",
        "2026-07-17",
        "authorized distributor",
        "manufacturer evidence",
        "Open:",
        "No PCB layout",
        "PB-100.kicad_pcb",
        "Gerbers",
        "drills",
        "pick-place",
        "centroid",
        "fabrication package",
        "manufacturing ZIP",
        "assembly output",
        "PCBA order package",
    ):
        if token not in closeout_text:
            fail(f"factory assembly closeout precheck must include {token}")

    for supporting_artifact, tokens in {
        "PB-100-factory-assembly-freeze-checklist.csv": ("FACT-FRZ-001", "FACT-FRZ-010"),
        "PB-100-factory-assembly-sourcing-precheck.csv": ("FACT-SRC-001", "FACT-SRC-010"),
        "PB-100-assembly-readiness-trace.csv": ("Factory", "CAN1_TX_DISABLE"),
    }.items():
        supporting_text = read_text(PB100_DIR / supporting_artifact)
        for token in tokens:
            if token not in supporting_text:
                fail(f"factory assembly closeout precheck requires {supporting_artifact} token {token}")

    sourcing_text = read_text(REPO_ROOT / "production" / "bom" / "pb100_assembly_sourcing_recheck.csv")
    evidence_text = read_text(REPO_ROOT / "production" / "bom" / "pb100_sourcing_evidence_snapshot.csv")
    for token in ("JLCPCB/PCBWay", "authorized distributor", "schematic freeze"):
        if token not in sourcing_text:
            fail(f"assembly sourcing recheck must support factory closeout precheck token {token}")
    for token in ("2026-07-16", "Open:", "DNP/open"):
        if token not in evidence_text:
            fail(f"sourcing evidence snapshot must support factory closeout precheck token {token}")


def validate_garage_connector_fuse_plan() -> None:
    csv_path = PB100_DIR / "PB-100-garage-connector-fuse-plan.csv"
    validate_csv(csv_path)
    rows = list(csv.DictReader(csv_path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty garage connector/fuse plan: {csv_path.relative_to(REPO_ROOT)}")
    fieldnames = rows[0].keys()
    missing_columns = [column for column in GARAGE_CONNECTOR_FUSE_PLAN_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{csv_path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    required_interfaces = {
        "Battery input",
        "Main harness fuse",
        "OUT1",
        "OUT2",
        "OUT3",
        "OUT4",
        "OUT5",
        "OUT6",
        "OUT7",
        "OUT8",
        "OUT9",
        "OUT10",
        "CAN/service",
        "External inputs",
        "Per-channel fuses",
    }
    rows_by_interface: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        interface = row["Interface"].strip()
        if interface in rows_by_interface:
            fail(f"{csv_path.relative_to(REPO_ROOT)}:{row_number}: duplicate interface {interface}")
        rows_by_interface[interface] = row
        for column in GARAGE_CONNECTOR_FUSE_PLAN_COLUMNS:
            if not row[column].strip():
                fail(f"{csv_path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        if row["Status"].strip() not in {"Candidate", "Conditional"}:
            fail(f"{csv_path.relative_to(REPO_ROOT)}:{row_number}: invalid Status {row['Status'].strip()}")

    missing_interfaces = sorted(required_interfaces - rows_by_interface.keys())
    if missing_interfaces:
        fail(
            f"{csv_path.relative_to(REPO_ROOT)} is missing interfaces: "
            f"{', '.join(missing_interfaces)}"
        )
    for output in ("OUT1", "OUT2"):
        row_text = " ".join(rows_by_interface[output].values())
        if "DTP" not in row_text or "DT 13A class is too close" not in row_text and output == "OUT1":
            fail(f"{output} garage connector plan must keep DTP class and DT margin note")
    for output in ("OUT3", "OUT4", "OUT5", "OUT6", "OUT7", "OUT8", "OUT9", "OUT10"):
        row_text = " ".join(rows_by_interface[output].values())
        if "DT" not in row_text:
            fail(f"{output} garage connector plan must use DT class")
    if "DTM" not in " ".join(rows_by_interface["CAN/service"].values()):
        fail("CAN/service garage connector plan must use DTM signal class")
    if "MINI/ATO" not in " ".join(rows_by_interface["Per-channel fuses"].values()):
        fail("per-channel fuses must stay on MINI/ATO blade family")
    if rows_by_interface["Battery input"]["Status"].strip() != "Conditional":
        fail("battery input connector must remain conditional until derating review closes")

    doc_path = PB100_DIR / "PB-100-garage-connector-fuse-plan.md"
    doc_text = read_text(doc_path).lower()
    for token in ("wire gauge", "crimp", "service", "enclosure", "does not freeze exact connector mpns"):
        if token not in doc_text:
            fail(f"{doc_path.relative_to(REPO_ROOT)} must preserve garage boundary token {token}")

    garage_bom_text = read_text(REPO_ROOT / "production" / "bom" / "garage_bom_draft.csv")
    for token in ("Deutsch DTP", "Deutsch DT", "Deutsch DTM", "Mini/ATO", "Automotive wire", "Enclosure"):
        if token not in garage_bom_text:
            fail(f"garage BOM must preserve {token}")


def validate_garage_install_freeze_checklist() -> None:
    path = PB100_DIR / "PB-100-garage-install-freeze-checklist.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty garage install freeze checklist: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [
        column for column in GARAGE_INSTALL_FREEZE_CHECKLIST_COLUMNS if column not in fieldnames
    ]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_check: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        check_id = row["Check ID"].strip()
        if check_id not in REQUIRED_GARAGE_INSTALL_FREEZE_CHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown garage install check {check_id}")
        if check_id in rows_by_check:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate garage install check {check_id}")
        rows_by_check[check_id] = row
        for column in GARAGE_INSTALL_FREEZE_CHECKLIST_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        if "do not" not in row["Blocked action"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: blocked action must be explicit")

    missing_checks = sorted(REQUIRED_GARAGE_INSTALL_FREEZE_CHECKS - rows_by_check.keys())
    if missing_checks:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing garage install checks: "
            f"{', '.join(missing_checks)}"
        )

    checklist_text = read_text(path)
    for token in (
        "INPUT_CONNECTOR",
        "OUTPUT_CONNECTOR",
        "OUTPUT_FUSE_HOLDER",
        "MAIN_FUSE_HOLDER",
        "user-installed",
        "MAXI 50A",
        "DT and DTP",
        "50A input path",
        "6mm2 / 10AWG",
        "DEUTSCH DTP",
        "size 12",
        "25A",
        "DT 13A class is too close",
        "DEUTSCH DT",
        "size 16",
        "OUT3 through OUT10",
        "DEUTSCH DTM",
        "DTM 4-pin",
        "DTM 8-pin",
        "size 20",
        "7.5A",
        "MINI/ATO",
        "5A 10A 15A and 20A",
        "service cover",
        "plug/receptacle",
        "contacts",
        "seals",
        "wedgelocks",
        "boots",
        "backshells",
        "crimp tool",
        "insertion/removal tool",
        "spare contacts",
        "2026-07-17",
        "2.5-4 mm2 / 14-12 AWG",
        "0.5-1.0 mm2 / 20-18 AWG",
        "ASA/PETG",
        "2 mm silicone gasket",
        "M3 hardware",
        "PB-BENCH-015",
        "garage_bom_draft.csv",
        "pb100_symbol_bom_map.csv",
        "pb100_assembly_sourcing_recheck.csv",
        "pb100_sourcing_evidence_snapshot.csv",
        "PB-100-garage-connector-fuse-plan.md",
        "PB-100-garage-connector-fuse-plan.csv",
        "PB-100-assembly-readiness-trace.csv",
        "No PCB layout",
        "PB-100.kicad_pcb",
        "Gerbers",
        "drills",
        "pick-place",
        "connector footprints",
        "fuse-holder footprints",
    ):
        if token not in checklist_text:
            fail(f"garage install freeze checklist must include {token}")

    plan_text = read_text(PB100_DIR / "PB-100-garage-connector-fuse-plan.md")
    for token in ("does not freeze exact connector MPNs", "DTP 2-pin", "DT 2-pin", "DTM", "MAXI", "MINI/ATO"):
        if token not in plan_text:
            fail(f"garage connector/fuse plan must support checklist token {token}")

    evidence_text = read_text(REPO_ROOT / "production" / "bom" / "pb100_sourcing_evidence_snapshot.csv")
    for token in ("2026-07-17", "OUTPUT_CONNECTOR", "OUTPUT_FUSE_HOLDER", "MAIN_FUSE_HOLDER", "Open:"):
        if token not in evidence_text:
            fail(f"sourcing evidence snapshot must support garage checklist token {token}")


def validate_garage_install_sourcing_precheck() -> None:
    path = PB100_DIR / "PB-100-garage-install-sourcing-precheck.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty garage install sourcing precheck: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [
        column for column in GARAGE_INSTALL_SOURCING_PRECHECK_COLUMNS if column not in fieldnames
    ]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_id: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        precheck_id = row["Precheck ID"].strip()
        if precheck_id not in REQUIRED_GARAGE_INSTALL_SOURCING_PRECHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown garage sourcing precheck {precheck_id}")
        if precheck_id in rows_by_id:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate garage sourcing precheck {precheck_id}")
        rows_by_id[precheck_id] = row
        for column in GARAGE_INSTALL_SOURCING_PRECHECK_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        if "do not" not in row["Blocked action"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: blocked action must be explicit")

    missing_checks = sorted(REQUIRED_GARAGE_INSTALL_SOURCING_PRECHECKS - rows_by_id.keys())
    if missing_checks:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing garage install sourcing prechecks: "
            f"{', '.join(missing_checks)}"
        )

    precheck_text = read_text(path)
    for token in (
        "INPUT_CONNECTOR",
        "OUTPUT_CONNECTOR",
        "OUTPUT_FUSE_HOLDER",
        "MAIN_FUSE_HOLDER",
        "user-installed",
        "PB-100-assembly-readiness-trace.csv",
        "PB-100-garage-install-freeze-checklist.csv",
        "PB-100-garage-connector-fuse-plan.md",
        "PB-100-garage-connector-fuse-plan.csv",
        "production/bom/garage_bom_draft.csv",
        "production/bom/pb100_symbol_bom_map.csv",
        "production/bom/pb100_assembly_sourcing_recheck.csv",
        "production/bom/pb100_sourcing_evidence_snapshot.csv",
        "ring-lug battery lead",
        "near-battery MAXI 50A",
        "high-current sealed harness entry",
        "serviceable gland",
        "DT and DTP",
        "50A input path",
        "6mm2 / 10AWG",
        "6 mm2 / 10 AWG",
        "DEUTSCH DTP",
        "DTP 2-pin",
        "size 12",
        "25A",
        "DEUTSCH DT",
        "DT 2-pin",
        "size 16",
        "DT 13A class is too close",
        "OUT3 through OUT10",
        "DEUTSCH DTM",
        "DTM 4-pin",
        "DTM 8-pin",
        "size 20",
        "7.5A",
        "MINI/ATO",
        "5A 10A 15A and 20A",
        "service cover",
        "plug/receptacle",
        "contacts",
        "seals",
        "wedgelocks",
        "boots",
        "backshells",
        "crimp tool",
        "insertion/removal tool",
        "spare contacts",
        "2026-07-17",
        "2.5-4 mm2 / 14-12 AWG",
        "0.5-1.0 mm2 / 20-18 AWG",
        "ASA/PETG",
        "2 mm silicone gasket",
        "M3 hardware",
        "PB-BENCH-015",
        "does not freeze exact connector MPNs",
        "Open:",
        "No PCB layout",
        "PB-100.kicad_pcb",
        "Gerbers",
        "drills",
        "pick-place",
        "connector footprints",
        "fuse-holder footprints",
        "enclosure CAD release",
        "manufacturing output",
    ):
        if token not in precheck_text:
            fail(f"garage install sourcing precheck must include {token}")

    plan_text = read_text(PB100_DIR / "PB-100-garage-connector-fuse-plan.md")
    for token in ("does not freeze exact connector MPNs", "DTP 2-pin", "DT 2-pin", "DTM", "MAXI", "MINI/ATO"):
        if token not in plan_text:
            fail(f"garage connector/fuse plan must support sourcing precheck token {token}")

    evidence_text = read_text(REPO_ROOT / "production" / "bom" / "pb100_sourcing_evidence_snapshot.csv")
    for token in ("2026-07-17", "INPUT_CONNECTOR", "OUTPUT_CONNECTOR", "OUTPUT_FUSE_HOLDER", "MAIN_FUSE_HOLDER", "Open:"):
        if token not in evidence_text:
            fail(f"sourcing evidence snapshot must support garage sourcing precheck token {token}")


def validate_garage_install_closeout_precheck() -> None:
    path = PB100_DIR / "PB-100-garage-install-closeout-precheck.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty garage install closeout precheck: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [
        column for column in GARAGE_INSTALL_CLOSEOUT_PRECHECK_COLUMNS if column not in fieldnames
    ]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_id: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        precheck_id = row["Precheck ID"].strip()
        if precheck_id not in REQUIRED_GARAGE_INSTALL_CLOSEOUT_PRECHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown garage closeout precheck {precheck_id}")
        if precheck_id in rows_by_id:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate garage closeout precheck {precheck_id}")
        rows_by_id[precheck_id] = row
        for column in GARAGE_INSTALL_CLOSEOUT_PRECHECK_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        if "do not" not in row["Blocked action"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: blocked action must be explicit")
        row_text = " ".join(row.values()).lower()
        if precheck_id == "GAR-CLS-010" and ("no pcb layout" not in row_text or "pb-100.kicad_pcb" not in row_text):
            fail("garage install closeout no-layout row must block PCB layout explicitly")

    missing_checks = sorted(REQUIRED_GARAGE_INSTALL_CLOSEOUT_PRECHECKS - rows_by_id.keys())
    if missing_checks:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing garage install closeout prechecks: "
            f"{', '.join(missing_checks)}"
        )

    closeout_text = read_text(path)
    for token in (
        "INPUT_CONNECTOR",
        "OUTPUT_CONNECTOR",
        "OUTPUT_FUSE_HOLDER",
        "MAIN_FUSE_HOLDER",
        "user-installed",
        "PB-100-assembly-readiness-trace.csv",
        "PB-100-garage-install-freeze-checklist.csv",
        "PB-100-garage-install-sourcing-precheck.csv",
        "PB-100-garage-connector-fuse-plan.md",
        "PB-100-garage-connector-fuse-plan.csv",
        "PB-100-board-current-budget-closeout-precheck.csv",
        "production/bom/garage_bom_draft.csv",
        "production/bom/pb100_symbol_bom_map.csv",
        "production/bom/pb100_assembly_sourcing_recheck.csv",
        "production/bom/pb100_sourcing_evidence_snapshot.csv",
        "PB-100-board-release-blocker-register.csv",
        "ring-lug battery lead",
        "near-battery MAXI 50A",
        "high-current sealed harness entry",
        "serviceable gland",
        "DT and DTP",
        "50A input path",
        "6mm2 / 10AWG",
        "6 mm2 / 10 AWG",
        "DEUTSCH DTP",
        "DTP 2-pin",
        "size 12",
        "25A",
        "DEUTSCH DT",
        "DT 2-pin",
        "size 16",
        "DT 13A class is too close",
        "OUT3 through OUT10",
        "DEUTSCH DTM",
        "DTM 4-pin",
        "DTM 8-pin",
        "size 20",
        "7.5A",
        "MINI/ATO",
        "5A 10A 15A and 20A",
        "service cover",
        "plug/receptacle",
        "contacts",
        "seals",
        "wedgelocks",
        "boots",
        "backshells",
        "crimp tool",
        "insertion/removal tool",
        "spare contacts",
        "2026-07-17",
        "2.5-4 mm2 / 14-12 AWG",
        "0.5-1.0 mm2 / 20-18 AWG",
        "ASA/PETG",
        "2 mm silicone gasket",
        "M3 hardware",
        "PB-BENCH-015",
        "does not freeze exact connector MPNs",
        "Open:",
        "No PCB layout",
        "PB-100.kicad_pcb",
        "Gerbers",
        "drills",
        "pick-place",
        "connector footprints",
        "fuse-holder footprints",
        "enclosure CAD release",
        "fabrication package",
        "manufacturing output",
        "manufacturing ZIP",
        "PCBA order package",
    ):
        if token not in closeout_text:
            fail(f"garage install closeout precheck must include {token}")

    for supporting_artifact, tokens in {
        "PB-100-garage-install-freeze-checklist.csv": ("GAR-FRZ-001", "GAR-FRZ-010"),
        "PB-100-garage-install-sourcing-precheck.csv": ("GAR-SRC-001", "GAR-SRC-010"),
        "PB-100-assembly-readiness-trace.csv": ("Garage", "MAIN_FUSE_HOLDER"),
    }.items():
        supporting_text = read_text(PB100_DIR / supporting_artifact)
        for token in tokens:
            if token not in supporting_text:
                fail(f"garage install closeout precheck requires {supporting_artifact} token {token}")

    plan_text = read_text(PB100_DIR / "PB-100-garage-connector-fuse-plan.md")
    for token in ("does not freeze exact connector MPNs", "DTP 2-pin", "DT 2-pin", "DTM", "MAXI", "MINI/ATO"):
        if token not in plan_text:
            fail(f"garage connector/fuse plan must support closeout precheck token {token}")

    evidence_text = read_text(REPO_ROOT / "production" / "bom" / "pb100_sourcing_evidence_snapshot.csv")
    for token in ("2026-07-17", "INPUT_CONNECTOR", "OUTPUT_CONNECTOR", "OUTPUT_FUSE_HOLDER", "MAIN_FUSE_HOLDER", "Open:"):
        if token not in evidence_text:
            fail(f"sourcing evidence snapshot must support garage closeout precheck token {token}")


def evidence_link_is_valid(value: str) -> bool:
    return value.startswith(("https://", "http://", "docs/", "hardware/", "production/"))


def validate_sourcing_evidence_date(path: Path, row_number: int, value: str) -> None:
    parts = value.split("-")
    if len(parts) != 3 or any(not part.isdigit() for part in parts):
        fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: invalid evidence date {value}")
    year, month, day = (int(part) for part in parts)
    if year < 2026 or not (1 <= month <= 12) or not (1 <= day <= 31):
        fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: evidence date must be a current snapshot date")


def validate_sourcing_evidence_snapshot() -> None:
    path = REPO_ROOT / "production" / "bom" / "pb100_sourcing_evidence_snapshot.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty sourcing evidence snapshot: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in SOURCING_EVIDENCE_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    readiness_rows = list(
        csv.DictReader((PB100_DIR / "PB-100-symbol-mpn-readiness.csv").open(newline="", encoding="utf-8"))
    )
    critical_keys = {
        row["Symbol key"].strip()
        for row in readiness_rows
        if row["Critical"].strip().lower() == "yes"
    }

    seen_keys = set()
    for row_number, row in enumerate(rows, 2):
        symbol_key = row["Symbol key"].strip()
        if symbol_key in seen_keys:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate symbol key {symbol_key}")
        seen_keys.add(symbol_key)
        if symbol_key not in critical_keys:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: symbol key {symbol_key} is not critical")
        for column in SOURCING_EVIDENCE_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_sourcing_evidence_date(path, row_number, row["Evidence date"].strip())
        for column in ("Primary evidence URL", "Secondary evidence URL"):
            if not evidence_link_is_valid(row[column].strip()):
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: invalid {column}")
        row_text = " ".join(row.values()).lower()
        if "open:" not in row["Open sourcing blocker"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: blocker must remain explicit")
        if symbol_key == "INPUT_TVS":
            for token in ("obsolete", "eol", "do not lock", "active"):
                if token not in row_text:
                    fail(f"INPUT_TVS sourcing evidence must explicitly track {token}")
        if symbol_key == "CAN1_TX_DISABLE":
            for token in ("dnp/open", "no default-populated tx", "future adr"):
                if token not in row_text:
                    fail(f"CAN1_TX_DISABLE evidence must preserve {token}")

    missing_keys = sorted(critical_keys - seen_keys)
    extra_keys = sorted(seen_keys - critical_keys)
    if missing_keys:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing critical sourcing evidence keys: "
            f"{', '.join(missing_keys)}"
        )
    if extra_keys:
        fail(
            f"{path.relative_to(REPO_ROOT)} has non-critical sourcing evidence keys: "
            f"{', '.join(extra_keys)}"
        )


def validate_tvs_candidate_consistency() -> None:
    stale_tvs_source = "https://www.mccsemi.com/products/esd-protection-and-power-tvs/tvs/SM8S33A"
    for relative_path in (
        "hardware/power-board/PB-100/PB-100-symbol-capture-worklist.csv",
        "hardware/power-board/PB-100/PB-100-power-path-candidates.csv",
        "hardware/power-board/PB-100/PB-100-symbol-mpn-readiness.csv",
    ):
        text = read_text(REPO_ROOT / relative_path)
        if stale_tvs_source in text:
            fail(f"{relative_path} must not use MCC SM8S33A as active TVS source")

    active_tvs_paths = (
        "hardware/power-board/PB-100/PB-100-symbol-capture-worklist.csv",
        "hardware/power-board/PB-100/PB-100-power-path-candidates.csv",
        "hardware/power-board/PB-100/PB-100-symbol-mpn-readiness.csv",
        "hardware/power-board/PB-100/PB-100-schematic-instance-plan.csv",
        "hardware/power-board/PB-100/PB-100-preliminary-validation.md",
        "hardware/power-board/PB-100/PB-100-kicad-footprint-plan.csv",
        "hardware/power-board/PB-100/PB-100-protection-validation.csv",
        "hardware/power-board/PB-100/PB-100-logic-power-rails.md",
        "hardware/power-board/PB-100/PB-100-input-power-design-values.csv",
        "hardware/power-board/PB-100/PB-100-tvs-load-dump-margin-trace.csv",
        "hardware/power-board/PB-100/PB-100-tvs-load-dump-freeze-review.csv",
        "hardware/power-board/PB-100/PB-100-tvs-overshoot-escape-checklist.csv",
    )
    for relative_path in active_tvs_paths:
        text = read_text(REPO_ROOT / relative_path)
        if "SM8S33A-class" in text:
            fail(f"{relative_path} must use active SM8S33AHM3-class TVS wording")
        if "SM8S33AHE3-class" in text or "SM8S33AHE3_A/I-class" in text:
            fail(f"{relative_path} must not treat Vishay HE3 TVS as the active baseline")
        if "SM8S33AHM3" not in text:
            fail(f"{relative_path} must reference active SM8S33AHM3 TVS evidence")


def validate_tvs_load_dump_margin_trace() -> None:
    path = PB100_DIR / "PB-100-tvs-load-dump-margin-trace.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty TVS/load-dump margin trace: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in TVS_LOAD_DUMP_MARGIN_TRACE_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    required_items = {
        "TPS48110 high-side controller",
        "BUK7S1R2-80M output MOSFET",
        "SIDR626LDP and IAUTN06S5N008 historical paths",
        "BUK7S1R2-80M input reverse MOSFET",
        "LM5164QDDATQ1 buck",
        "LM5013-Q1 buck alternate",
        "TPS54360B-Q1 buck alternate",
        "TPS2HB35 direct smart switch",
    }
    rows_by_item: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        protected_item = row["Protected item"].strip()
        if protected_item in rows_by_item:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate protected item {protected_item}")
        if protected_item not in required_items:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown protected item {protected_item}")
        rows_by_item[protected_item] = row
        for column in TVS_LOAD_DUMP_MARGIN_TRACE_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        row_text = " ".join(row.values())
        for token in ("SM8S33AHM3", "53.3 V", "schematic freeze"):
            if token not in row_text:
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: TVS margin row must include {token}")

    missing_items = sorted(required_items - rows_by_item.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing TVS margin items: "
            f"{', '.join(missing_items)}"
        )

    historical_text = " ".join(
        rows_by_item["SIDR626LDP and IAUTN06S5N008 historical paths"].values()
    ).lower()
    for token in ("60 v", "rejected", "history", "overshoot"):
        if token not in historical_text:
            fail(f"historical 60 V paths must preserve {token}")

    for protected_item in (
        "BUK7S1R2-80M output MOSFET",
        "BUK7S1R2-80M input reverse MOSFET",
    ):
        selected_text = " ".join(rows_by_item[protected_item].values()).lower()
        for token in ("80 v", "selected", "26.7 v", "overshoot"):
            if token not in selected_text:
                fail(f"{protected_item} must preserve selected 80 V margin evidence: {token}")

    smart_switch_text = " ".join(rows_by_item["TPS2HB35 direct smart switch"].values()).lower()
    for token in ("40 v", "deferred by adr-0011", "future adr", "lower-clamp"):
        if token not in smart_switch_text:
            fail(f"TPS2HB35 TVS margin row must preserve {token}")

    for protected_item in (
        "TPS48110 high-side controller",
        "LM5164QDDATQ1 buck",
        "LM5013-Q1 buck alternate",
    ):
        if "Pass with margin" not in rows_by_item[protected_item]["Margin state"]:
            fail(f"{protected_item} must remain pass-with-margin against active HM3 TVS")

    protection_text = read_text(PB100_DIR / "PB-100-protection-validation.csv")
    for token in (
        "Active SM8S33AHM3-class TVS",
        "53.3V clamp",
        "BUK7S1R2-80M output MOSFET",
        "Selected with 26.7V nominal margin",
        "Rejected Rev.1 baseline",
    ):
        if token not in protection_text:
            fail(f"protection validation must preserve {token}")


def validate_tvs_load_dump_freeze_review() -> None:
    path = PB100_DIR / "PB-100-tvs-load-dump-freeze-review.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty TVS/load-dump freeze review: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in OUTPUT_FREEZE_REVIEW_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_item: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        review_item = row["Review item"].strip()
        if review_item not in REQUIRED_TVS_LOAD_DUMP_FREEZE_REVIEW_ITEMS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown TVS/load-dump review item {review_item}")
        if review_item in rows_by_item:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate TVS/load-dump review item {review_item}")
        rows_by_item[review_item] = row
        for column in OUTPUT_FREEZE_REVIEW_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)

    missing_items = sorted(REQUIRED_TVS_LOAD_DUMP_FREEZE_REVIEW_ITEMS - rows_by_item.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing TVS/load-dump review items: "
            f"{', '.join(missing_items)}"
        )

    review_text = read_text(path)
    for token in (
        "SM8S33AHM3/I",
        "HM3 DO-218AC",
        "53.3 V clamp at 124 A",
        "MCC SM8S33A EOL",
        "Vishay HE3 NFD",
        "TPS48110",
        "LM5164QDDATQ1",
        "LM5013-Q1",
        "100 V",
        "SIDR626LDP",
        "IAUTN06S5N008",
        "60 V",
        "rejected Rev.1 assembly paths",
        "overshoot",
        "BUK7S1R2-80M",
        "80 V",
        "selected for Q1 and Q101 through Q110",
        "26.7 V nominal headroom",
        "TPS54360B-Q1",
        "TPS2HB35",
        "ADR-0011",
        "lower-clamp",
        "OV divider",
        "buck input network",
        "JLCPCB PCBWay",
        "critical alternatives",
        "No PCB layout",
        "PB-100.kicad_pcb",
    ):
        if token not in review_text:
            fail(f"TVS/load-dump freeze review must include {token}")

    margin_text = read_text(PB100_DIR / "PB-100-tvs-load-dump-margin-trace.csv")
    for token in (
        "SM8S33AHM3/I",
        "HM3 DO-218AC",
        "53.3 V clamp at 124 A",
        "Rejected Rev.1 baseline",
        "BUK7S1R2-80M",
        "Selected with 26.7 V nominal margin",
        "TPS54360B-Q1",
        "TPS2HB35",
        "Deferred by ADR-0011",
    ):
        if token not in margin_text:
            fail(f"TVS margin trace must support freeze review token {token}")

    protection_text = read_text(PB100_DIR / "PB-100-protection-validation.csv")
    for token in (
        "Active SM8S33AHM3-class TVS",
        "53.3V clamp",
        "Rejected Rev.1 baseline",
        "Selected with 26.7V nominal margin",
        "Optional future alternate",
        "TPS54360B-Q1",
    ):
        if token not in protection_text:
            fail(f"protection validation must support TVS freeze review token {token}")

    input_values_text = read_text(PB100_DIR / "PB-100-input-power-design-values.csv")
    for token in ("SM8S33AHM3/I", "MCC SM8S33A EOL", "Vishay HE3 NFD", "downstream absolute maximum margin"):
        if token not in input_values_text:
            fail(f"input power values must support TVS freeze review token {token}")

    output_values_text = read_text(PB100_DIR / "PB-100-output-stage-design-values.csv")
    if "OV threshold divider" not in output_values_text or "TVS/load-dump margin" not in output_values_text:
        fail("output stage design values must preserve TVS OV dependency")

    logic_values_text = read_text(PB100_DIR / "PB-100-logic-power-design-values.csv")
    for token in ("Input filter", "surge-tolerant input capacitance", "load-dump stress"):
        if token not in logic_values_text:
            fail(f"logic power design values must support TVS freeze review token {token}")

    sourcing_text = read_text(REPO_ROOT / "production" / "bom" / "pb100_assembly_sourcing_recheck.csv")
    for token in ("INPUT_TVS", "SM8S33AHM3/I", "SLD8S33A", "DM8W33AQ-13", "SM8S33A-Q"):
        if token not in sourcing_text:
            fail(f"assembly sourcing recheck must support TVS freeze review token {token}")


def validate_tvs_overshoot_escape_checklist() -> None:
    path = PB100_DIR / "PB-100-tvs-overshoot-escape-checklist.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty TVS overshoot escape checklist: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in TVS_OVERSHOOT_ESCAPE_CHECKLIST_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_check: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        check_id = row["Check ID"].strip()
        if check_id not in REQUIRED_TVS_OVERSHOOT_ESCAPE_CHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown TVS overshoot check {check_id}")
        if check_id in rows_by_check:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate TVS overshoot check {check_id}")
        rows_by_check[check_id] = row
        for column in TVS_OVERSHOOT_ESCAPE_CHECKLIST_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)

    missing_checks = sorted(REQUIRED_TVS_OVERSHOOT_ESCAPE_CHECKS - rows_by_check.keys())
    if missing_checks:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing TVS overshoot checks: "
            f"{', '.join(missing_checks)}"
        )

    checklist_text = read_text(path)
    for token in (
        "SM8S33AHM3/I",
        "HM3 DO-218AC",
        "AEC-Q101",
        "53.3 V clamp at 124 A",
        "MCC SM8S33A EOL",
        "Vishay HE3 NFD",
        "60 V",
        "6.7 V headroom",
        "80 V",
        "26.7 V headroom",
        "100 V",
        "46.7 V headroom",
        "SIDR626LDP",
        "IAUTN06S5N008",
        "historical evidence",
        "not permitted Rev.1 assembly substitutions",
        "overshoot",
        "BUK7S1R2-80M",
        "LFPAK88",
        "1.2 mOhm",
        "selected for Q1 and Q101 through Q110",
        "TPS48110",
        "LM5164QDDATQ1",
        "LM5013-Q1",
        "TPS54360B-Q1",
        "TPS2HB35",
        "ADR-0011",
        "lower-clamp",
        "OV divider",
        "buck input network",
        "VBAT_PROT",
        "INPUT_TVS",
        "JLCPCB PCBWay",
        "SLD8S33A",
        "DM8W33AQ-13",
        "SM8S33A-Q",
        "No PCB layout",
        "PB-100.kicad_pcb",
        "Gerbers",
        "drills",
        "pick-place",
    ):
        if token not in checklist_text:
            fail(f"TVS overshoot escape checklist must include {token}")

    margin_text = read_text(PB100_DIR / "PB-100-tvs-load-dump-margin-trace.csv")
    for token in (
        "SM8S33AHM3/I",
        "53.3 V clamp at 124 A",
        "Rejected Rev.1 baseline",
        "BUK7S1R2-80M",
        "Selected with 26.7 V nominal margin",
    ):
        if token not in margin_text:
            fail(f"TVS margin trace must support overshoot checklist token {token}")

    voltage_review_text = read_text(PB100_DIR / "PB-100-mosfet-voltage-margin-review.md")
    for token in ("60 V", "80 V", "6.7 V", "26.7 V", "overshoot"):
        if token not in voltage_review_text:
            fail(f"MOSFET voltage-margin review must support TVS overshoot token {token}")


def validate_tvs_overshoot_validation_precheck() -> None:
    path = PB100_DIR / "PB-100-tvs-overshoot-validation-precheck.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty TVS overshoot validation precheck: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in TVS_OVERSHOOT_VALIDATION_PRECHECK_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_id: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        validation_id = row["Validation ID"].strip()
        if validation_id not in REQUIRED_TVS_OVERSHOOT_VALIDATION_CHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown TVS validation item {validation_id}")
        if validation_id in rows_by_id:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate TVS validation item {validation_id}")
        rows_by_id[validation_id] = row
        for column in TVS_OVERSHOOT_VALIDATION_PRECHECK_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        row_text = " ".join(row.values()).lower()
        if validation_id == "TVS-VAL-002" and ("vstress" not in row_text or "lloop" not in row_text):
            fail("TVS validation precheck must include overshoot stress method")
        if validation_id == "TVS-VAL-006" and ("probe" not in row_text or "bandwidth" not in row_text):
            fail("TVS validation precheck must include measurement probe bandwidth")
        if validation_id == "TVS-VAL-007" and ("parasitic" not in row_text or "inductance" not in row_text):
            fail("TVS validation precheck must include simulation parasitic inductance")
        if validation_id == "TVS-VAL-010" and ("pb-100.kicad_pcb" not in row_text or "manufacturing" not in row_text):
            fail("TVS validation precheck must block layout and manufacturing outputs")

    missing_items = sorted(REQUIRED_TVS_OVERSHOOT_VALIDATION_CHECKS - rows_by_id.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing TVS validation items: "
            f"{', '.join(missing_items)}"
        )

    precheck_text = read_text(path)
    for token in (
        "SM8S33AHM3/I",
        "HM3 DO-218AC",
        "53.3 V clamp at 124 A",
        "MCC SM8S33A EOL",
        "Vishay HE3 NFD",
        "Vstress = Vclamp + Lloop * di/dt",
        "SIDR626LDP",
        "IAUTN06S5N008",
        "BUK7S1R2-80M",
        "80 V",
        "100 V",
        "TPS48110",
        "LM5164QDDATQ1",
        "LM5013-Q1",
        "VBAT_RAW",
        "VBAT_PROT",
        "probe bandwidth",
        "fixture inductance",
        "parasitics",
        "SLD8S33A",
        "DM8W33AQ-13",
        "SM8S33A-Q",
        "JLCPCB PCBWay",
        "PB-100.kicad_pcb",
    ):
        if token not in precheck_text:
            fail(f"TVS overshoot validation precheck must include {token}")


def validate_tvs_overshoot_closeout_precheck() -> None:
    path = PB100_DIR / "PB-100-tvs-overshoot-closeout-precheck.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty TVS overshoot closeout precheck: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in TVS_OVERSHOOT_CLOSEOUT_PRECHECK_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_id: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        precheck_id = row["Precheck ID"].strip()
        if precheck_id not in REQUIRED_TVS_OVERSHOOT_CLOSEOUT_PRECHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown TVS closeout precheck {precheck_id}")
        if precheck_id in rows_by_id:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate TVS closeout precheck {precheck_id}")
        rows_by_id[precheck_id] = row
        for column in TVS_OVERSHOOT_CLOSEOUT_PRECHECK_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        row_text = " ".join(row.values()).lower()
        if "do not" not in row["Blocked action"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: blocked action must be explicit")
        if precheck_id == "TVS-CLS-002" and ("vstress" not in row_text or "lloop" not in row_text):
            fail("TVS closeout method row must keep Vstress and Lloop explicit")
        if precheck_id == "TVS-CLS-010" and ("no pcb layout" not in row_text or "pb-100.kicad_pcb" not in row_text):
            fail("TVS closeout no-layout row must block PCB layout explicitly")

    missing_items = sorted(REQUIRED_TVS_OVERSHOOT_CLOSEOUT_PRECHECKS - rows_by_id.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing TVS closeout prechecks: "
            f"{', '.join(missing_items)}"
        )

    precheck_text = read_text(path)
    for token in (
        "SM8S33AHM3/I",
        "HM3 DO-218AC",
        "AEC-Q101",
        "53.3 V clamp at 124 A",
        "MCC SM8S33A EOL",
        "Vishay HE3 NFD",
        "60 V MOSFET exclusion bridge",
        "rejected historical evidence",
        "Vstress = Vclamp + Lloop * di/dt",
        "probe fixture parasitics",
        "source impedance",
        "SIDR626LDP",
        "IAUTN06S5N008",
        "BUK7S1R2-80M",
        "LFPAK88",
        "80 V is selected for Q1 and Q101 through Q110",
        "TPS48110",
        "LM5164QDDATQ1",
        "LM5013-Q1",
        "TPS54360B-Q1",
        "TPS2HB35",
        "ADR-0011",
        "future ADR",
        "OV divider",
        "buck input network",
        "input filter capacitor",
        "TBD not final",
        "VBAT_PROT",
        "INPUT_TVS",
        "SLD8S33A",
        "DM8W33AQ-13",
        "SM8S33A-Q",
        "JLCPCB PCBWay",
        "at least two viable alternates",
        "input-protection.kicad_sch",
        "CAP-INP",
        "PB-100-test-point-plan.csv",
        "PB-100-protection-validation.csv",
        "docs/testing/test-plan.md",
        "No PCB layout",
        "PB-100.kicad_pcb",
        "D1 placement",
        "pulse-current return copper",
        "via strategy",
        "thermal relief",
        "Gerbers",
        "drills",
        "pick-place",
        "manufacturing ZIP",
    ):
        if token not in precheck_text:
            fail(f"TVS overshoot closeout precheck must include {token}")

    for supporting_artifact, tokens in {
        "PB-100-tvs-overshoot-escape-checklist.csv": ("TVS-FRZ-002", "TVS-FRZ-009"),
        "PB-100-tvs-overshoot-validation-precheck.csv": ("TVS-VAL-002", "TVS-VAL-010"),
        "PB-100-tvs-load-dump-freeze-review.csv": ("60V MOSFET historical rejection", "Layout authorization boundary"),
    }.items():
        supporting_text = read_text(PB100_DIR / supporting_artifact)
        for token in tokens:
            if token not in supporting_text:
                fail(f"TVS closeout precheck requires {supporting_artifact} token {token}")


def validate_thermal_telemetry_baseline() -> None:
    map_path = PB100_DIR / "PB-100-thermal-telemetry-map.csv"
    validate_csv(map_path)
    rows = list(csv.DictReader(map_path.open(newline="", encoding="utf-8")))
    rows_by_signal = {row["Signal"].strip(): row for row in rows}
    required_signals = {"TEMP_PCB", "TEMP_PWR_A", "TEMP_PWR_B"}
    missing_signals = sorted(required_signals - rows_by_signal.keys())
    if missing_signals:
        fail(
            f"{map_path.relative_to(REPO_ROOT)} is missing thermal signals: "
            f"{', '.join(missing_signals)}"
        )

    for signal in sorted(required_signals):
        row = rows_by_signal[signal]
        row_text = " ".join(row.values())
        for token in ("NTCGS103JF103FT8", "10k", "150", "85C", "105C", "75C", "TBD"):
            if token not in row_text:
                fail(
                    f"{map_path.relative_to(REPO_ROOT)} thermal row {signal} "
                    f"must include {token}"
                )
        if row["Telemetry path"].strip() != "LB ADC":
            fail(f"{map_path.relative_to(REPO_ROOT)} thermal row {signal} must use LB ADC")

    checked_paths = (
        PB100_DIR / "PB-100-thermal-telemetry.md",
        PB100_DIR / "PB-100-symbol-mpn-readiness.csv",
        PB100_DIR / "PB-100-symbol-capture-worklist.csv",
        PB100_DIR / "PB-100-schematic-instance-plan.csv",
        PB100_DIR / "PB-100-kicad-footprint-plan.csv",
        REPO_ROOT / "production" / "bom" / "factory_bom_draft.csv",
        REPO_ROOT / "production" / "bom" / "pb100_assembly_sourcing_recheck.csv",
        REPO_ROOT / "production" / "bom" / "pb100_sourcing_evidence_snapshot.csv",
        REPO_ROOT / "docs" / "production" / "component-family-shortlist.md",
    )
    for path in checked_paths:
        text = read_text(path)
        if "NTCGS103JF103FT8" not in text:
            fail(f"{path.relative_to(REPO_ROOT)} must reference the TDK thermal NTC candidate")

    thermal_doc = read_text(PB100_DIR / "PB-100-thermal-telemetry.md")
    for token in ("85 °C warn", "105 °C cutoff", "75 °C recovery"):
        if token not in thermal_doc:
            fail(f"thermal telemetry strategy must document default threshold {token}")

    evidence_rows = list(
        csv.DictReader((REPO_ROOT / "production" / "bom" / "pb100_sourcing_evidence_snapshot.csv").open(newline="", encoding="utf-8"))
    )
    thermal_evidence = next((row for row in evidence_rows if row["Symbol key"].strip() == "THERMAL_NTC"), None)
    if thermal_evidence is None:
        fail("missing THERMAL_NTC sourcing evidence row")
    evidence_text = " ".join(thermal_evidence.values()).lower()
    for token in ("ntcgs103jf103ft8", "aec-q200", "150c", "open:", "vishay"):
        if token not in evidence_text:
            fail(f"THERMAL_NTC sourcing evidence must explicitly track {token}")


def validate_b2b_interface_trace() -> None:
    path = PB100_DIR / "PB-100-b2b-interface-trace.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty B2B interface trace: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in B2B_INTERFACE_TRACE_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    required_items = {
        "Connector candidate",
        "Power status and grounds",
        "Output control fault and current",
        "Board telemetry and PB bus",
        "CAN1 safety crossing",
        "Expansion and reserve",
    }
    rows_by_item: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        item = row["Trace item"].strip()
        if item in rows_by_item:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate trace item {item}")
        if item not in required_items:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown trace item {item}")
        rows_by_item[item] = row
        for column in B2B_INTERFACE_TRACE_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        if "schematic freeze" not in " ".join(row.values()).lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: freeze dependency must reference schematic freeze")

    missing_items = sorted(required_items - rows_by_item.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing B2B trace items: "
            f"{', '.join(missing_items)}"
        )

    connector_text = " ".join(rows_by_item["Connector candidate"].values())
    for token in ("FX18-100P-0.8SV10", "FX18-100S-0.8SV20", "No connector placement"):
        if token not in connector_text:
            fail(f"B2B connector trace must include {token}")

    pin_map_path = PB100_DIR / "PB-100-b2b-pin-map.csv"
    validate_csv(pin_map_path)
    pin_rows = list(csv.DictReader(pin_map_path.open(newline="", encoding="utf-8")))
    if len(pin_rows) != 100:
        fail(f"{pin_map_path.relative_to(REPO_ROOT)} must contain exactly 100 JPB1 pins")

    pins = sorted(int(row["Pin"].strip()) for row in pin_rows)
    if pins != list(range(1, 101)):
        fail(f"{pin_map_path.relative_to(REPO_ROOT)} must define contiguous pins 1-100")
    if any(row["Connector"].strip() != "JPB1" for row in pin_rows):
        fail(f"{pin_map_path.relative_to(REPO_ROOT)} must use connector JPB1 for every pin")

    def rows_for_pin_span(start: int, end: int) -> list[dict[str, str]]:
        return [row for row in pin_rows if start <= int(row["Pin"].strip()) <= end]

    def nets_for_pin_span(start: int, end: int) -> set[str]:
        return {row["Net"].strip() for row in rows_for_pin_span(start, end)}

    power_row = rows_by_item["Power status and grounds"]
    if power_row["Pin span"].strip() != "1-19":
        fail("B2B power/status trace must cover JPB1 pins 1-19")
    power_rows = rows_for_pin_span(1, 19)
    if sum(1 for row in power_rows if row["Net"].strip() == "GND") != 10:
        fail("B2B pin map must keep ten GND return pins in pins 1-19")
    if sum(1 for row in power_rows if row["Net"].strip() == "AGND") != 2:
        fail("B2B pin map must keep two AGND return pins in pins 1-19")
    if sum(1 for row in power_rows if row["Net"].strip() == "PB_5V_OUT") != 4:
        fail("B2B pin map must keep four PB_5V_OUT pins in pins 1-19")
    if sum(1 for row in power_rows if row["Net"].strip() == "LB_3V3_IO") != 2:
        fail("B2B pin map must keep two LB_3V3_IO pins in pins 1-19")
    if "PB_PWR_GOOD" not in nets_for_pin_span(1, 19):
        fail("B2B pin map must expose PB_PWR_GOOD in pins 1-19")
    if "PB_PWR_GOOD inactive" not in " ".join(power_row.values()):
        fail("B2B power trace must keep PB_PWR_GOOD inactive-until-valid behavior")

    output_row = rows_by_item["Output control fault and current"]
    if output_row["Pin span"].strip() != "21-50":
        fail("B2B output trace must cover JPB1 pins 21-50")
    output_nets = nets_for_pin_span(21, 50)
    expected_output_nets = {
        f"OUT{output}_{suffix}"
        for output in range(1, 11)
        for suffix in ("CTL", "FLT", "IMON")
    }
    missing_output_nets = sorted(expected_output_nets - output_nets)
    if missing_output_nets:
        fail(f"B2B output trace pin span is missing nets: {', '.join(missing_output_nets)}")
    if "role mapping stays in configuration" not in " ".join(output_row.values()).lower():
        fail("B2B output trace must preserve configuration-owned role mapping")

    telemetry_row = rows_by_item["Board telemetry and PB bus"]
    if telemetry_row["Pin span"].strip() != "51-66":
        fail("B2B telemetry trace must cover JPB1 pins 51-66")
    expected_telemetry_nets = {
        "VBAT_SENSE",
        "IIN_SENSE",
        "TEMP_PCB",
        "TEMP_PWR_A",
        "TEMP_PWR_B",
        "PB_FAULT",
        "PB_I2C_SCL",
        "PB_I2C_SDA",
        "PB_I2C_INT",
        "PB_ID_ADC",
        "ADC_REF",
    }
    missing_telemetry_nets = sorted(expected_telemetry_nets - nets_for_pin_span(51, 66))
    if missing_telemetry_nets:
        fail(f"B2B telemetry trace pin span is missing nets: {', '.join(missing_telemetry_nets)}")
    for token in expected_telemetry_nets:
        if token not in telemetry_row["Signals"]:
            fail(f"B2B telemetry trace must include signal {token}")
    if "calibration stays outside firmware constants" not in " ".join(telemetry_row.values()).lower():
        fail("B2B telemetry trace must keep calibration outside firmware constants")

    can_row = rows_by_item["CAN1 safety crossing"]
    if can_row["Pin span"].strip() != "67-70":
        fail("B2B CAN1 trace must cover JPB1 pins 67-70")
    expected_can_nets = {"CAN1_TX_DISABLE_CMD", "CAN1_TX_DISABLED_STATUS", "CAN1_RX_ROUTE", "CAN1_TX_ROUTE"}
    missing_can_nets = sorted(expected_can_nets - nets_for_pin_span(67, 70))
    if missing_can_nets:
        fail(f"B2B CAN1 trace pin span is missing nets: {', '.join(missing_can_nets)}")
    can_text = " ".join(can_row.values()).lower()
    if "dnp/open" not in can_text or "future adr" not in can_text or "disabled-status" not in can_text:
        fail("B2B CAN1 trace must preserve DNP/open future-ADR disabled-status boundary")

    expansion_row = rows_by_item["Expansion and reserve"]
    if expansion_row["Pin span"].strip() != "71-100":
        fail("B2B expansion trace must cover JPB1 pins 71-100")
    expansion_nets = nets_for_pin_span(71, 100)
    expected_expansion_tokens = {
        "CAN2",
        "LIN",
        "RS485",
        "UART",
        "EXT_ADC",
        "EXT_DIG",
        "EXT_5V_EN",
        "SPARE_01..SPARE_16",
    }
    expansion_text = " ".join(expansion_row.values())
    for token in expected_expansion_tokens:
        if token not in expansion_text:
            fail(f"B2B expansion trace must include {token}")
    expected_spares = {f"SPARE_{index:02d}" for index in range(1, 17)}
    missing_spares = sorted(expected_spares - expansion_nets)
    if missing_spares:
        fail(f"B2B expansion trace pin span is missing reserves: {', '.join(missing_spares)}")


def validate_b2b_connector_candidate() -> None:
    required_tokens = (
        "FX18-100P-0.8SV10",
        "FX18-100S-0.8SV20",
        "100",
        "0.8",
    )
    checked_paths = (
        PB100_DIR / "PB-100-symbol-mpn-readiness.csv",
        PB100_DIR / "PB-100-symbol-capture-worklist.csv",
        PB100_DIR / "PB-100-schematic-instance-plan.csv",
        PB100_DIR / "PB-100-kicad-footprint-plan.csv",
        PB100_DIR / "PB-100-schematic-freeze-gap-register.csv",
        PB100_DIR / "PB-100-schematic-package.md",
        KICAD_DIR / "sheets" / "b2b-interface.kicad_sch",
        REPO_ROOT / "production" / "bom" / "factory_bom_draft.csv",
        REPO_ROOT / "production" / "bom" / "pb100_assembly_sourcing_recheck.csv",
        REPO_ROOT / "production" / "bom" / "pb100_sourcing_evidence_snapshot.csv",
        REPO_ROOT / "docs" / "production" / "component-family-shortlist.md",
    )
    for path in checked_paths:
        text = read_text(path)
        for token in required_tokens:
            if token not in text:
                fail(f"{path.relative_to(REPO_ROOT)} must reference B2B connector candidate token {token}")

    evidence_rows = list(
        csv.DictReader((REPO_ROOT / "production" / "bom" / "pb100_sourcing_evidence_snapshot.csv").open(newline="", encoding="utf-8"))
    )
    b2b_evidence = next((row for row in evidence_rows if row["Symbol key"].strip() == "B2B_CONNECTOR"), None)
    if b2b_evidence is None:
        fail("missing B2B_CONNECTOR sourcing evidence row")
    evidence_text = " ".join(b2b_evidence.values()).lower()
    for token in ("20mm", "500", "open:", "vibration", "assembly"):
        if token not in evidence_text:
            fail(f"B2B_CONNECTOR sourcing evidence must explicitly track {token}")


def validate_b2b_lb100_pin_audit_checklist() -> None:
    path = PB100_DIR / "PB-100-b2b-lb100-pin-audit-checklist.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty B2B LB-100 pin audit checklist: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in B2B_LB100_PIN_AUDIT_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_audit: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        audit_id = row["Audit ID"].strip()
        if audit_id not in REQUIRED_B2B_LB100_PIN_AUDIT_ITEMS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown B2B audit item {audit_id}")
        if audit_id in rows_by_audit:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate B2B audit item {audit_id}")
        rows_by_audit[audit_id] = row
        for column in B2B_LB100_PIN_AUDIT_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        row_text = " ".join(row.values()).lower()
        if audit_id == "B2B-AUD-002" and "16 adc" not in row_text:
            fail("B2B ADC audit must require at least 16 ADC-capable inputs or reviewed mux strategy")
        if audit_id == "B2B-AUD-003" and ("default low" not in row_text or "role-specific" not in row_text):
            fail("B2B output audit must keep default-low and role-free boundaries")
        if audit_id == "B2B-AUD-005" and ("can1_tx_route" not in row_text or "dnp/open" not in row_text or "future-adr" not in row_text):
            fail("B2B CAN1 audit must keep CAN1_TX_ROUTE DNP/open and future-ADR gated")
        if audit_id == "B2B-AUD-007" and ("footprint drawing" not in row_text or "stack height" not in row_text):
            fail("B2B FX18 audit must require footprint drawing and stack-height review")
        if audit_id == "B2B-AUD-009" and ("no pcb layout" not in row_text or "pb-100.kicad_pcb" not in row_text):
            fail("B2B no-layout audit must block PCB layout explicitly")

    missing_items = sorted(REQUIRED_B2B_LB100_PIN_AUDIT_ITEMS - rows_by_audit.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing B2B audit items: "
            f"{', '.join(missing_items)}"
        )

    audit_text = read_text(path)
    for token in (
        "STM32H563",
        "LQFP-100",
        "Exact LB-100 pinout",
        "FX18-100P-0.8SV10",
        "FX18-100S-0.8SV20",
        "vibration",
        "assembly handling",
        "CAN1_TX_ROUTE",
        "DNP/open",
        "No PCB layout",
        "PB-100.kicad_pcb",
    ):
        if token not in audit_text:
            fail(f"B2B LB-100 pin audit checklist must include {token}")


def validate_b2b_interface_freeze_checklist() -> None:
    path = PB100_DIR / "PB-100-b2b-interface-freeze-checklist.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty B2B interface freeze checklist: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in B2B_INTERFACE_FREEZE_CHECKLIST_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_check: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        check_id = row["Check ID"].strip()
        if check_id not in REQUIRED_B2B_INTERFACE_FREEZE_CHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown B2B freeze check {check_id}")
        if check_id in rows_by_check:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate B2B freeze check {check_id}")
        rows_by_check[check_id] = row
        for column in B2B_INTERFACE_FREEZE_CHECKLIST_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        row_text = " ".join(row.values()).lower()
        if check_id == "B2B-FRZ-001" and ("fx18-100p-0.8sv10" not in row_text or "stack" not in row_text):
            fail("B2B connector freeze check must cover FX18 pair and stack evidence")
        if check_id == "B2B-FRZ-003" and ("role-specific" not in row_text or "default-low" not in row_text):
            fail("B2B output freeze check must keep role-free default-low output behavior")
        if check_id == "B2B-FRZ-005" and (
            "can1_tx_route" not in row_text or "dnp/open" not in row_text or "future adr" not in row_text
        ):
            fail("B2B CAN1 freeze check must keep CAN1_TX_ROUTE DNP/open and future ADR gated")
        if check_id == "B2B-FRZ-007" and (
            "stm32h563" not in row_text or "lqfp-100" not in row_text or "exact lb-100" not in row_text
        ):
            fail("B2B MCU freeze check must require exact STM32H563 LQFP-100 LB-100 pinout audit")
        if check_id == "B2B-FRZ-010" and ("no pcb layout" not in row_text or "pb-100.kicad_pcb" not in row_text):
            fail("B2B freeze checklist must explicitly block PCB layout")

    missing_checks = sorted(REQUIRED_B2B_INTERFACE_FREEZE_CHECKS - rows_by_check.keys())
    if missing_checks:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing B2B interface freeze checks: "
            f"{', '.join(missing_checks)}"
        )

    checklist_text = read_text(path)
    for token in (
        "FX18-100P-0.8SV10",
        "FX18-100S-0.8SV20",
        "PB_5V_OUT",
        "LB_3V3_IO",
        "OUT1_CTL",
        "OUT10_IMON",
        "IIN_SENSE",
        "TEMP_PWR_A",
        "PB_I2C_SCL",
        "CAN1_TX_DISABLE_CMD",
        "CAN1_TX_DISABLED_STATUS",
        "CAN1_RX_ROUTE",
        "CAN1_TX_ROUTE",
        "DNP/open",
        "future ADR",
        "STM32H563",
        "LQFP-100",
        "PB-100-b2b-lb100-pin-audit-checklist.csv",
        "No PCB layout",
        "PB-100.kicad_pcb",
    ):
        if token not in checklist_text:
            fail(f"B2B interface freeze checklist must include {token}")


def validate_b2b_interface_closeout_precheck() -> None:
    path = PB100_DIR / "PB-100-b2b-interface-closeout-precheck.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty B2B interface closeout precheck: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in B2B_INTERFACE_CLOSEOUT_PRECHECK_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_id: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        precheck_id = row["Precheck ID"].strip()
        if precheck_id not in REQUIRED_B2B_INTERFACE_CLOSEOUT_PRECHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown B2B closeout precheck {precheck_id}")
        if precheck_id in rows_by_id:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate B2B closeout precheck {precheck_id}")
        rows_by_id[precheck_id] = row
        for column in B2B_INTERFACE_CLOSEOUT_PRECHECK_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        row_text = " ".join(row.values()).lower()
        if "do not" not in row["Blocked action"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: blocked action must be explicit")
        if "can1_tx_route" in row_text and "dnp/open" not in row_text:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: CAN1_TX_ROUTE rows must keep DNP/open explicit")
        if precheck_id == "B2B-CLS-010" and ("no pcb layout" not in row_text or "pb-100.kicad_pcb" not in row_text):
            fail("B2B closeout no-layout row must block PCB layout explicitly")

    missing_items = sorted(REQUIRED_B2B_INTERFACE_CLOSEOUT_PRECHECKS - rows_by_id.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing B2B closeout prechecks: "
            f"{', '.join(missing_items)}"
        )

    precheck_text = read_text(path)
    for token in (
        "JPB1",
        "100-position",
        "0.8 mm",
        "PB-100-b2b-pin-map.csv",
        "100 JPB1 pins",
        "PB-100-b2b-lb100-resource-binding.csv",
        "PB-100-b2b-lb100-pin-binding-precheck.md",
        "PB-100-b2b-lb100-pin-audit-checklist.csv",
        "PB-100-b2b-interface-freeze-checklist.csv",
        "FX18-100P-0.8SV10",
        "FX18-100S-0.8SV20",
        "20 mm",
        "footprint drawing",
        "courtyard",
        "pin-1",
        "stack height",
        "vibration retention",
        "assembly handling",
        "tray",
        "JLCPCB PCBWay",
        "STM32H563",
        "LQFP-100",
        "Exact LB-100 pinout",
        "16 ADC",
        "external ADC/mux",
        "10 GPIO/PWM",
        "default-low",
        "PB_PWR_GOOD",
        "PB_WAKE_REQ",
        "OUT1_CTL",
        "OUT10_IMON",
        "IIN_SENSE",
        "TEMP_PWR_A",
        "PB_I2C_SCL",
        "PB_I2C_SDA",
        "PB_I2C_INT",
        "CAN1_TX_DISABLE_CMD",
        "CAN1_TX_DISABLED_STATUS",
        "CAN1_RX_ROUTE",
        "CAN1_TX_ROUTE",
        "DNP/open",
        "future ADR",
        "CAN2",
        "LIN",
        "RS485",
        "UART",
        "EXT_ADC",
        "architecture review",
        "PB_5V_OUT",
        "LB_3V3_IO",
        "PB_PWR_GOOD",
        "No PCB layout",
        "PB-100.kicad_pcb",
        "Gerbers",
        "drills",
        "pick-place",
        "connector placement",
        "board outline",
        "stack-height lock",
        "manufacturing ZIP",
    ):
        if token not in precheck_text:
            fail(f"B2B interface closeout precheck must include {token}")

    pin_rows = list(csv.DictReader((PB100_DIR / "PB-100-b2b-pin-map.csv").open(newline="", encoding="utf-8")))
    if len(pin_rows) != 100:
        fail("B2B closeout precheck requires PB-100-b2b-pin-map.csv to contain 100 JPB1 pins")

    audit_text = read_text(PB100_DIR / "PB-100-b2b-lb100-pin-audit-checklist.csv")
    for token in ("STM32H563", "LQFP-100", "16 ADC", "FX18-100P-0.8SV10", "FX18-100S-0.8SV20"):
        if token not in audit_text:
            fail(f"B2B pin audit checklist must support closeout precheck token {token}")


def parse_pin_span_set(value: str) -> set[str]:
    pins: set[str] = set()
    for part in value.split(";"):
        token = part.strip()
        if not token:
            continue
        if "-" in token:
            start_text, end_text = [piece.strip() for piece in token.split("-", 1)]
            start = int(start_text)
            end = int(end_text)
            pins.update(str(pin) for pin in range(start, end + 1))
        else:
            pins.add(token)
    return pins


def validate_b2b_resource_binding() -> None:
    path = PB100_DIR / "PB-100-b2b-lb100-resource-binding.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty B2B LB-100 resource binding: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in B2B_RESOURCE_BINDING_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    expected_pins = {
        "Ground and analog return": set(str(pin) for pin in range(1, 13)),
        "Protected 5V supply to LB-100": set(str(pin) for pin in range(13, 17)),
        "LB 3V3 IO reference to PB-100": set(str(pin) for pin in range(17, 19)),
        "Power-good and wake status": set(str(pin) for pin in range(19, 21)),
        "Output control commands": set(str(pin) for pin in range(21, 31)),
        "Output fault inputs": set(str(pin) for pin in range(31, 41)),
        "Per-output current telemetry": set(str(pin) for pin in range(41, 51)),
        "Board analog telemetry and identity": {"51", "52", "53", "54", "55", "60", "66"},
        "Board fault summary": {"56"},
        "PB-side monitor bus and interrupt": set(str(pin) for pin in range(57, 60)),
        "Future SPI monitor bus": set(str(pin) for pin in range(61, 66)),
        "CAN1 safety crossing": set(str(pin) for pin in range(67, 71)),
        "CAN2 expansion route": set(str(pin) for pin in range(71, 73)),
        "LIN RS485 and UART expansion": set(str(pin) for pin in range(73, 80)),
        "External ADC digital and 5V enable": set(str(pin) for pin in range(80, 85)),
        "Spare reserve pins": set(str(pin) for pin in range(85, 101)),
    }
    required_tokens = {
        "Output control commands": ("OUT1_CTL..OUT10_CTL", "GPIO/PWM"),
        "Output fault inputs": ("OUT1_FLT..OUT10_FLT", "GPIO input"),
        "Per-output current telemetry": ("OUT1_IMON..OUT10_IMON", "ADC"),
        "Board analog telemetry and identity": ("VBAT_SENSE", "IIN_SENSE", "TEMP_PCB", "PB_ID_ADC", "ADC"),
        "Board fault summary": ("PB_FAULT", "GPIO input"),
        "PB-side monitor bus and interrupt": ("PB_I2C_SCL", "PB_I2C_SDA", "I2C", "interrupt"),
        "CAN1 safety crossing": ("CAN1_TX_ROUTE", "DNP/open", "FDCAN", "future-ADR"),
        "CAN2 expansion route": ("CAN2_RX_ROUTE", "CAN2_TX_ROUTE", "FDCAN"),
        "LIN RS485 and UART expansion": ("LIN_TX", "RS485_DE", "UART"),
        "Spare reserve pins": ("SPARE_01..SPARE_16", "reserve"),
    }

    pin_map_rows = list(csv.DictReader((PB100_DIR / "PB-100-b2b-pin-map.csv").open(newline="", encoding="utf-8")))
    pin_map_pins = {row["Pin"].strip() for row in pin_map_rows}
    seen_items = set()
    covered_pins: set[str] = set()
    for row_number, row in enumerate(rows, 2):
        item = row["Binding item"].strip()
        if item in seen_items:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate binding item {item}")
        seen_items.add(item)
        if item not in expected_pins:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown binding item {item}")
        for column in B2B_RESOURCE_BINDING_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        row_pins = parse_pin_span_set(row["JPB1 pins"])
        if row_pins != expected_pins[item]:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unexpected pin set for {item}")
        covered_pins.update(row_pins)
        row_text = " ".join(row.values())
        if "No exact STM32H5" not in row_text and "No MCU pin assignment" not in row_text:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: must avoid exact STM32H5 pin assignment")
        for token in required_tokens.get(item, ()):
            if token not in row_text:
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: missing token {token}")

    missing_items = sorted(set(expected_pins) - seen_items)
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing binding items: "
            f"{', '.join(missing_items)}"
        )
    if covered_pins != pin_map_pins:
        missing_pins = sorted(pin_map_pins - covered_pins, key=int)
        extra_pins = sorted(covered_pins - pin_map_pins, key=int)
        fail(
            "B2B LB-100 resource binding pin coverage mismatch: "
            f"missing={missing_pins}, extra={extra_pins}"
        )


def validate_validation_traceability() -> None:
    path = PB100_DIR / "PB-100-validation-traceability.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty PB-100 validation traceability register: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in VALIDATION_TRACEABILITY_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    tracked_gates = set(pbrel_id_by_gate())
    seen_test_ids = set()
    gates_with_tests: dict[str, list[dict[str, str]]] = {gate: [] for gate in tracked_gates}
    allowed_phases = {"Schematic review", "Schematic plus bench", "Production review"}
    for row_number, row in enumerate(rows, 2):
        test_id = row["Test ID"].strip()
        freeze_gate = row["Freeze gate"].strip()
        if test_id in seen_test_ids:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate Test ID {test_id}")
        seen_test_ids.add(test_id)
        if not test_id.startswith("PBVAL-"):
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: Test ID must start with PBVAL-")
        if freeze_gate not in tracked_gates:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown freeze gate {freeze_gate}")
        if row["Validation phase"].strip() not in allowed_phases:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: invalid Validation phase {row['Validation phase'].strip()}")
        for column in VALIDATION_TRACEABILITY_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        row_text = " ".join(row.values()).lower()
        if "before layout" in row_text and "schematic freeze" not in row_text:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: layout boundary must reference schematic freeze")
        if freeze_gate == "CAN1 safety policy":
            if "dnp/open" not in row_text or "read-only" not in row_text or "future adr" not in row_text:
                fail("CAN1 validation trace must keep DNP/open read-only and future ADR explicit")
            if "pb-100-can1-production-dnp-review.csv" not in row_text:
                fail("CAN1 validation trace must include production DNP review")
            if "pb-100-can1-default-disable-freeze-checklist.csv" not in row_text:
                fail("CAN1 validation trace must include default-disable freeze checklist")
            if "pb-100-can1-default-disable-derivation-precheck.csv" not in row_text:
                fail("CAN1 validation trace must include default-disable derivation precheck")
            if "pb-100-can1-default-disable-closeout-precheck.csv" not in row_text:
                fail("CAN1 validation trace must include default-disable closeout precheck")
        if freeze_gate == "Board current budget":
            if "pb-100-board-current-budget-freeze-review.csv" not in row_text:
                fail("Board current validation trace must include 40 A freeze review")
            if "pb-100-board-current-budget-design-calculation.md" not in row_text:
                fail("Board current validation trace must include design calculation")
            if "pb-100-board-current-budget-value-freeze-checklist.csv" not in row_text:
                fail("Board current validation trace must include value freeze checklist")
            if "pb-100-board-current-budget-value-derivation-precheck.csv" not in row_text:
                fail("Board current validation trace must include value derivation precheck")
            if "pb-100-board-current-budget-closeout-precheck.csv" not in row_text:
                fail("Board current validation trace must include closeout precheck")
        if freeze_gate == "Current telemetry":
            if "pb-100-current-telemetry-freeze-review.csv" not in row_text:
                fail("Current telemetry validation trace must include freeze review")
            if "pb-100-current-telemetry-value-freeze-checklist.csv" not in row_text:
                fail("Current telemetry validation trace must include value freeze checklist")
            if "pb-100-current-telemetry-value-derivation-precheck.csv" not in row_text:
                fail("Current telemetry validation trace must include value derivation precheck")
            if "pb-100-current-telemetry-closeout-precheck.csv" not in row_text:
                fail("Current telemetry validation trace must include closeout precheck")
        if freeze_gate == "Thermal telemetry":
            if "pb-100-thermal-telemetry-freeze-review.csv" not in row_text:
                fail("Thermal telemetry validation trace must include freeze review")
            if "pb-100-thermal-telemetry-value-freeze-checklist.csv" not in row_text:
                fail("Thermal telemetry validation trace must include value freeze checklist")
            if "pb-100-thermal-telemetry-value-derivation-precheck.csv" not in row_text:
                fail("Thermal telemetry validation trace must include value derivation precheck")
            if "pb-100-thermal-telemetry-closeout-precheck.csv" not in row_text:
                fail("Thermal telemetry validation trace must include closeout precheck")
        if freeze_gate == "High/medium output stage":
            if "pb-100-high-medium-output-freeze-review.csv" not in row_text:
                fail("High/medium output validation trace must include freeze review")
            if "pb-100-output-stage-value-freeze-checklist.csv" not in row_text:
                fail("High/medium output validation trace must include value freeze checklist")
            if "pb-100-output-stage-value-derivation-precheck.csv" not in row_text:
                fail("High/medium output validation trace must include value derivation precheck")
            if "pb-100-output-stage-closeout-precheck.csv" not in row_text:
                fail("High/medium output validation trace must include closeout precheck")
        if freeze_gate == "Low-current output stage":
            if "pb-100-low-current-output-freeze-review.csv" not in row_text:
                fail("Low-current output validation trace must include freeze review")
            if "pb-100-output-stage-value-freeze-checklist.csv" not in row_text:
                fail("Low-current output validation trace must include value freeze checklist")
            if "pb-100-output-stage-value-derivation-precheck.csv" not in row_text:
                fail("Low-current output validation trace must include value derivation precheck")
            if "pb-100-output-stage-closeout-precheck.csv" not in row_text:
                fail("Low-current output validation trace must include closeout precheck")
        if freeze_gate == "Input reverse protection":
            if "pb-100-input-reverse-freeze-review.csv" not in row_text:
                fail("Input reverse validation trace must include freeze review")
            if "pb-100-input-reverse-q1-freeze-checklist.csv" not in row_text:
                fail("Input reverse validation trace must include Q1 freeze checklist")
            if "pb-100-input-reverse-q1-derivation-precheck.csv" not in row_text:
                fail("Input reverse validation trace must include Q1 derivation precheck")
            if "pb-100-input-reverse-q1-closeout-precheck.csv" not in row_text:
                fail("Input reverse validation trace must include Q1 closeout precheck")
        if freeze_gate == "Input reverse protection":
            if "q1" not in row_text or "40 a" not in row_text:
                fail("Input reverse validation trace must keep Q1 and 40 A explicit")
        if freeze_gate == "TVS/load-dump protection":
            if "pb-100-tvs-load-dump-freeze-review.csv" not in row_text:
                fail("TVS/load-dump validation trace must include freeze review")
            if "pb-100-tvs-overshoot-escape-checklist.csv" not in row_text:
                fail("TVS/load-dump validation trace must include overshoot escape checklist")
            if "pb-100-tvs-overshoot-validation-precheck.csv" not in row_text:
                fail("TVS/load-dump validation trace must include overshoot validation precheck")
            if "60 v" not in row_text or "overshoot" not in row_text:
                fail("TVS/load-dump validation trace must keep 60 V overshoot explicit")
        if freeze_gate == "Logic power rails":
            if "pb-100-logic-power-freeze-review.csv" not in row_text:
                fail("Logic power validation trace must include freeze review")
            if "pb-100-logic-power-value-freeze-checklist.csv" not in row_text:
                fail("Logic power validation trace must include value freeze checklist")
            if "pb-100-logic-power-value-derivation-precheck.csv" not in row_text:
                fail("Logic power validation trace must include value derivation precheck")
            if "pb-100-logic-power-closeout-precheck.csv" not in row_text:
                fail("Logic power validation trace must include closeout precheck")
            if "pb_5v_out" not in row_text or "uvlo" not in row_text:
                fail("Logic power validation trace must keep PB_5V_OUT and UVLO explicit")
        if freeze_gate == "Factory assembly readiness":
            if "sourcing recheck" not in row_text:
                fail("Factory assembly validation trace must require sourcing recheck")
            if "pb-100-factory-assembly-freeze-checklist.csv" not in row_text:
                fail("Factory assembly validation trace must include factory assembly freeze checklist")
            if "pb-100-factory-assembly-sourcing-precheck.csv" not in row_text:
                fail("Factory assembly validation trace must include factory assembly sourcing precheck")
            if "pb-100-factory-assembly-closeout-precheck.csv" not in row_text:
                fail("Factory assembly validation trace must include factory assembly closeout precheck")
        if freeze_gate == "Garage assembly readiness":
            if "garage" not in row_text:
                fail("Garage assembly validation trace must keep garage scope explicit")
            if "pb-100-garage-install-freeze-checklist.csv" not in row_text:
                fail("Garage assembly validation trace must include garage install freeze checklist")
            if "pb-100-garage-install-sourcing-precheck.csv" not in row_text:
                fail("Garage assembly validation trace must include garage install sourcing precheck")
            if "pb-100-garage-install-closeout-precheck.csv" not in row_text:
                fail("Garage assembly validation trace must include garage install closeout precheck")
        gates_with_tests[freeze_gate].append(row)

    required_primary_artifacts = {
        "CAN1 safety policy": "PB-100-can1-tx-disable-trace.csv",
        "Board current budget": "PB-100-board-current-budget-trace.csv",
        "Board-to-board interface": "PB-100-b2b-interface-trace.csv",
        "High/medium output stage": "PB-100-high-medium-output-baseline-trace.csv",
        "Low-current output stage": "PB-100-low-current-output-baseline-trace.csv",
        "Input reverse protection": "PB-100-input-reverse-package-trace.csv",
        "TVS/load-dump protection": "PB-100-tvs-load-dump-margin-trace.csv",
        "Logic power rails": "PB-100-logic-power-rail-trace.csv",
        "Current telemetry": "PB-100-current-telemetry-trace.csv",
        "Thermal telemetry": "PB-100-thermal-telemetry-trace.csv",
        "Factory assembly readiness": "PB-100-assembly-readiness-trace.csv",
        "Garage assembly readiness": "PB-100-assembly-readiness-trace.csv",
    }
    for freeze_gate, token in required_primary_artifacts.items():
        if not any(token in row["Primary artifact"] for row in gates_with_tests[freeze_gate]):
            fail(f"validation traceability for {freeze_gate} must include {token}")
    if not any(
        "PB-100-b2b-lb100-resource-binding.csv" in row["Primary artifact"]
        for row in gates_with_tests["Board-to-board interface"]
    ):
        fail("validation traceability for Board-to-board interface must include PB-100-b2b-lb100-resource-binding.csv")
    if not any(
        "PB-100-b2b-lb100-pin-audit-checklist.csv" in row["Primary artifact"]
        for row in gates_with_tests["Board-to-board interface"]
    ):
        fail("validation traceability for Board-to-board interface must include PB-100-b2b-lb100-pin-audit-checklist.csv")
    if not any(
        "PB-100-b2b-interface-freeze-checklist.csv" in row["Primary artifact"]
        for row in gates_with_tests["Board-to-board interface"]
    ):
        fail("validation traceability for Board-to-board interface must include PB-100-b2b-interface-freeze-checklist.csv")
    if not any(
        "PB-100-b2b-interface-closeout-precheck.csv" in row["Primary artifact"]
        for row in gates_with_tests["Board-to-board interface"]
    ):
        fail("validation traceability for Board-to-board interface must include PB-100-b2b-interface-closeout-precheck.csv")

    missing_gates = sorted(gate for gate, gate_rows in gates_with_tests.items() if not gate_rows)
    if missing_gates:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing validation rows for gates: "
            f"{', '.join(missing_gates)}"
        )


def validate_test_point_plan() -> None:
    path = PB100_DIR / "PB-100-test-point-plan.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty PB-100 test point plan: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in TEST_POINT_PLAN_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    manifest_rows = list(csv.DictReader((PB100_DIR / "PB-100-kicad-sheet-manifest.csv").open(newline="", encoding="utf-8")))
    manifest_sheets = {row["Sheet file"].strip() for row in manifest_rows}
    output_rows = list(csv.DictReader((PB100_DIR / "PB-100-output-channel-matrix.csv").open(newline="", encoding="utf-8")))
    outputs = {row["Output"].strip() for row in output_rows}
    b2b_rows = list(csv.DictReader((PB100_DIR / "PB-100-b2b-pin-map.csv").open(newline="", encoding="utf-8")))
    b2b_nets = {row["Net"].strip() for row in b2b_rows}

    required_nets = {
        "GND",
        "VBAT_RAW",
        "VBAT_REV_PROT",
        "VBAT_PROT",
        "IIN_SHUNT_HI",
        "IIN_SHUNT_LO",
        "VBAT_SENSE",
        "IIN_SENSE",
        "PB_5V_OUT",
        "PB_PWR_GOOD",
        "LB_3V3_IO",
        "TEMP_PCB",
        "TEMP_PWR_A",
        "TEMP_PWR_B",
        "CAN1_TX_DISABLE_CMD",
        "CAN1_TX_DISABLED_STATUS",
    }
    for output in outputs:
        required_nets.update({f"{output}_CTL", f"{output}_FLT", f"{output}_IMON", f"{output}_FUSED"})

    seen_refs = set()
    seen_nets = set()
    for expected_index, row in enumerate(rows, 1):
        row_number = expected_index + 1
        test_point_ref = row["Test point ref"].strip()
        net = row["Net"].strip()
        sheet = row["Sheet"].strip()
        if test_point_ref in seen_refs:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate test point ref {test_point_ref}")
        seen_refs.add(test_point_ref)
        if test_point_ref != f"TP{expected_index:03d}":
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: test point refs must be "
                f"contiguous TP###, expected TP{expected_index:03d}"
            )
        if net in seen_nets:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate test-point net {net}")
        seen_nets.add(net)
        if sheet not in manifest_sheets:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown sheet {sheet}")
        for column in ("Signal class", "Requirement", "Population", "Access intent", "Validation target", "Placement status"):
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        placement_status = row["Placement status"].lower()
        if "schematic-review only" not in placement_status or "tbd" not in placement_status:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: placement status must remain schematic-review only/TBD")
        if "final" in placement_status:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: test point placement must not be final")
        if net == "CAN1_TX_ROUTE":
            fail("CAN1_TX_ROUTE must not receive a test point in Rev.1 default planning")
        if net == "CAN1_RX_ROUTE" and "dnp unless" not in row["Population"].lower():
            fail("CAN1_RX_ROUTE test point row must remain DNP unless CAN1 crosses PB-100")
        if net.endswith("_CTL") or net.endswith("_FLT") or net.endswith("_IMON"):
            if net not in b2b_nets:
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: {net} is missing from JPB1 pin map")
        if net.endswith("_FUSED"):
            if "no pcb test pad locked" not in row["Population"].lower():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: fused outputs must avoid locked PCB test pads")
            if "high-current" not in row["Access intent"].lower():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: fused outputs need guarded high-current access intent")

    missing_nets = sorted(required_nets - seen_nets)
    if missing_nets:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required test-point nets: "
            f"{', '.join(missing_nets)}"
        )


def validate_fault_response_matrix() -> None:
    path = PB100_DIR / "PB-100-fault-response-matrix.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty PB-100 fault response matrix: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in FAULT_RESPONSE_MATRIX_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    seen_fault_ids = set()
    for row_number, row in enumerate(rows, 2):
        fault_id = row["Fault ID"].strip()
        if fault_id in seen_fault_ids:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate Fault ID {fault_id}")
        seen_fault_ids.add(fault_id)
        if fault_id not in REQUIRED_FAULT_IDS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown Fault ID {fault_id}")
        for column in FAULT_RESPONSE_MATRIX_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        row_text = " ".join(row.values()).lower()
        if not any(keyword in row_text for keyword in ("disable", "disabled", "off", "derate", "refuse", "block")):
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: fault response must include a safe action")
        if "log" not in row["Firmware response"].lower() and fault_id not in {"PBFLT-THERM-HIGH"}:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: firmware response must include logging")
        if "role" in row_text and "role-agnostic" not in row_text and "role names" not in row_text:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: role references must preserve role-agnostic behavior")
        if fault_id == "PBFLT-CAN1-TX":
            if "dnp/open" not in row_text or "future adr" not in row_text:
                fail("CAN1 TX fault response must keep DNP/open and future ADR explicit")
        if fault_id == "PBFLT-OUT2-INRUSH" and "soa" not in row_text:
            fail("OUT2 inrush fault response must reference SOA")
        if fault_id == "PBFLT-B2B-MISMATCH" and "accessory role assumptions" not in row_text:
            fail("B2B mismatch fault response must reject accessory role assumptions")
        validation_artifacts = [artifact.strip() for artifact in row["Validation artifact"].split(";")]
        for artifact in validation_artifacts:
            if not (
                artifact.startswith("PB-100-")
                or artifact.startswith("docs/")
                or artifact.startswith("production/")
            ):
                fail(
                    f"{path.relative_to(REPO_ROOT)}:{row_number}: validation artifact "
                    f"must be PB-100*, docs/*, or production/*: {artifact}"
                )

    missing_fault_ids = sorted(REQUIRED_FAULT_IDS - seen_fault_ids)
    if missing_fault_ids:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing fault IDs: "
            f"{', '.join(missing_fault_ids)}"
        )


def resolve_review_artifact(path_text: str) -> Path:
    if path_text.startswith("docs/") or path_text.startswith("production/") or path_text.startswith("hardware/"):
        return REPO_ROOT / path_text
    return PB100_DIR / path_text


def expand_reference_token(token: str) -> set[str]:
    token = token.strip()
    if not token:
        return set()
    if ".." not in token:
        return {token}
    start, end = [part.strip() for part in token.split("..", 1)]
    start_prefix = "".join(character for character in start if not character.isdigit())
    end_prefix = "".join(character for character in end if not character.isdigit())
    if start_prefix != end_prefix:
        return {token}
    start_digits = "".join(character for character in start if character.isdigit())
    end_digits = "".join(character for character in end if character.isdigit())
    if not start_digits or not end_digits:
        return {token}
    width = max(len(start_digits), len(end_digits))
    return {
        f"{start_prefix}{number:0{width}d}"
        for number in range(int(start_digits), int(end_digits) + 1)
    }


def refs_from_cell(cell: str) -> set[str]:
    references = set()
    for token in cell.split(";"):
        references.update(expand_reference_token(token))
    return references


def validate_schematic_capture_work_queue() -> None:
    path = PB100_DIR / "PB-100-schematic-capture-work-queue.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty schematic capture work queue: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in SCHEMATIC_CAPTURE_WORK_QUEUE_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    manifest_rows = list(csv.DictReader((PB100_DIR / "PB-100-kicad-sheet-manifest.csv").open(newline="", encoding="utf-8")))
    manifest_sheets = {row["Sheet file"].strip() for row in manifest_rows}
    allowed_sheets = manifest_sheets | {"cross-sheet-review"}
    sheet_reference_rows = list(
        csv.DictReader((PB100_DIR / "PB-100-schematic-sheet-reference-map.csv").open(newline="", encoding="utf-8"))
    )
    refs_by_sheet: dict[str, set[str]] = {}
    for sheet_row in sheet_reference_rows:
        sheet_file = sheet_row["Sheet file"].strip()
        ref = sheet_row["Ref"].strip()
        if ref == "TP1..TPn":
            continue
        refs_by_sheet.setdefault(sheet_file, set()).add(ref)

    seen_work_items = set()
    sheets_with_queue_rows = set()
    refs_covered_by_sheet: dict[str, set[str]] = {}
    for row_number, row in enumerate(rows, 2):
        work_item = row["Work item"].strip()
        sheet_file = row["Sheet file"].strip()
        if work_item in seen_work_items:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate Work item {work_item}")
        seen_work_items.add(work_item)
        if work_item not in REQUIRED_CAPTURE_WORK_ITEMS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown Work item {work_item}")
        if sheet_file not in allowed_sheets:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown sheet file {sheet_file}")
        sheets_with_queue_rows.add(sheet_file)
        if sheet_file in manifest_sheets:
            sheet_path = KICAD_DIR / sheet_file if sheet_file == "PB-100.kicad_sch" else KICAD_DIR / "sheets" / sheet_file
            sheet_text = read_text(sheet_path)
            if f"Work queue: {work_item}" not in sheet_text:
                fail(
                    f"{sheet_path.relative_to(REPO_ROOT)} must contain Work queue marker "
                    f"for {work_item}"
                )
        if row["Capture status"].strip() not in ALLOWED_CAPTURE_STATUSES:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: invalid Capture status {row['Capture status'].strip()}")
        for column in (
            "Capture scope",
            "Required refs",
            "Primary source artifacts",
            "Blocker",
            "Freeze close evidence",
            "Layout boundary",
        ):
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        layout_boundary = row["Layout boundary"].lower()
        if "no " not in layout_boundary or "layout" not in layout_boundary:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: layout boundary must explicitly block layout")
        if "manufacturing output" in layout_boundary and "no " not in layout_boundary:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: manufacturing output must be blocked")
        for artifact in [part.strip() for part in row["Primary source artifacts"].split(";")]:
            artifact_path = resolve_review_artifact(artifact)
            if not artifact_path.exists():
                fail(
                    f"{path.relative_to(REPO_ROOT)}:{row_number}: missing source artifact "
                    f"{artifact}"
                )
        row_refs = refs_from_cell(row["Required refs"])
        refs_covered_by_sheet.setdefault(sheet_file, set()).update(row_refs)
        if "Q1" in row_refs:
            row_text = " ".join(row.values())
            if not all(token in row_text for token in ("INPUT_REVERSE_FET", "BUK7S1R2-80M", "LFPAK88", "40 A")):
                fail("Q1 capture work must keep selected 80 V LFPAK88 and 40 A review explicit")
        if work_item == "CAP-CAN1":
            row_text = " ".join(row.values()).lower()
            if "dnp/open" not in row_text or "future adr" not in row_text:
                fail("CAN1 capture work must keep DNP/open and future ADR explicit")
        if work_item == "CAP-TOP":
            row_text = " ".join(row.values()).lower()
            if "linked" not in row["Capture status"].lower():
                fail("top-level capture work must mark child sheet links complete")
            if "child sheets linked" not in row_text or "erc/netlist" not in row_text:
                fail("top-level capture work must keep child-link and ERC/netlist evidence")
        if work_item == "CAP-TP" and "footprint" not in row["Blocker"].lower():
            fail("test point capture work must keep footprint/placement blocker explicit")

    rows_by_work_item = {row["Work item"].strip(): row for row in rows}
    for work_item, tokens in CAPTURE_TRACE_ARTIFACTS_BY_WORK_ITEM.items():
        work_row = rows_by_work_item[work_item]
        source_artifacts = work_row["Primary source artifacts"]
        for token in tokens:
            if token not in source_artifacts:
                fail(f"capture work queue {work_item} must include source artifact {token}")
        sheet_file = work_row["Sheet file"].strip()
        if sheet_file in manifest_sheets:
            sheet_path = KICAD_DIR / sheet_file if sheet_file == "PB-100.kicad_sch" else KICAD_DIR / "sheets" / sheet_file
            sheet_text = read_text(sheet_path)
            for token in tokens:
                if token not in sheet_text:
                    fail(f"{sheet_path.relative_to(REPO_ROOT)} must mention source artifact {token}")

    missing_work_items = sorted(REQUIRED_CAPTURE_WORK_ITEMS - seen_work_items)
    if missing_work_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing capture work items: "
            f"{', '.join(missing_work_items)}"
        )
    missing_sheets = sorted(manifest_sheets - sheets_with_queue_rows)
    if missing_sheets:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing KiCad sheet work rows: "
            f"{', '.join(missing_sheets)}"
        )
    for sheet_file, expected_refs in refs_by_sheet.items():
        missing_refs = sorted(expected_refs - refs_covered_by_sheet.get(sheet_file, set()))
        if missing_refs:
            fail(
                f"{path.relative_to(REPO_ROOT)} does not cover refs on {sheet_file}: "
                f"{', '.join(missing_refs)}"
            )


def validate_schematic_capture_plan() -> None:
    path = PB100_DIR / "PB-100-schematic-capture-plan.md"
    text = read_text(path)
    lower_text = text.lower()
    if "does not authorize pcb\nlayout" not in lower_text:
        fail(f"{path.relative_to(REPO_ROOT)} must explicitly avoid PCB layout authorization")
    if "do not create `pb-100.kicad_pcb`" not in lower_text:
        fail(f"{path.relative_to(REPO_ROOT)} must block PB-100.kicad_pcb creation")

    queue_path = PB100_DIR / "PB-100-schematic-capture-work-queue.csv"
    queue_rows = list(csv.DictReader(queue_path.open(newline="", encoding="utf-8")))
    rows_by_work_item = {row["Work item"].strip(): row for row in queue_rows}
    plan_lines = text.splitlines()
    for work_item, tokens in CAPTURE_TRACE_ARTIFACTS_BY_WORK_ITEM.items():
        if work_item not in rows_by_work_item:
            fail(f"{queue_path.relative_to(REPO_ROOT)} is missing capture work item {work_item}")
        sheet_file = rows_by_work_item[work_item]["Sheet file"].strip()
        sheet_lines = [line for line in plan_lines if f"`{sheet_file}`" in line]
        if not sheet_lines:
            fail(f"{path.relative_to(REPO_ROOT)} must include capture row for {sheet_file}")
        sheet_text = " ".join(sheet_lines)
        for token in tokens:
            if token not in sheet_text:
                fail(f"{path.relative_to(REPO_ROOT)} {sheet_file} row must include {token}")


def validate_review_release_manifest() -> None:
    path = PB100_DIR / "PB-100-review-release-manifest.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty PB-100 review release manifest: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in REVIEW_RELEASE_MANIFEST_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    allowed_statuses = {"Frozen", "Ready", "Closed", "Conditional", "Open"}
    seen_artifacts = set()
    for row_number, row in enumerate(rows, 2):
        artifact = row["Artifact"].strip()
        if artifact in seen_artifacts:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate artifact {artifact}")
        seen_artifacts.add(artifact)
        for column in REVIEW_RELEASE_MANIFEST_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        if row["Required for freeze"].strip() != "Required":
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: release manifest artifacts must be Required")
        if row["Status"].strip() not in allowed_statuses:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: invalid Status {row['Status'].strip()}")
        artifact_path = REPO_ROOT / artifact
        if not artifact_path.exists():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: missing release artifact {artifact}")
        if artifact_path.is_file():
            name = artifact_path.name.lower()
            suffix = artifact_path.suffix.lower()
            if name.endswith(".kicad_pcb-bak") or suffix in DISALLOWED_LAYOUT_SUFFIXES:
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: release manifest must not include layout artifact {artifact}")
        hook = row["Validation hook"].strip()
        if hook.startswith("validate_") and hook not in globals():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown validation hook {hook}")

    missing_artifacts = sorted(REQUIRED_RELEASE_MANIFEST_ARTIFACTS - seen_artifacts)
    if missing_artifacts:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing release artifacts: "
            f"{', '.join(missing_artifacts)}"
        )


def validate_schematic_readiness_review() -> None:
    path = PB100_DIR / "PB-100-schematic-readiness-review.md"
    text = read_text(path)
    lower_text = text.lower()
    if "does not authorize pcb layout" not in lower_text:
        fail(f"{path.relative_to(REPO_ROOT)} must explicitly avoid PCB layout authorization")
    for artifact in sorted(REQUIRED_RELEASE_MANIFEST_ARTIFACTS):
        if artifact not in text:
            fail(f"{path.relative_to(REPO_ROOT)} review packet must include {artifact}")
    for tokens in CAPTURE_TRACE_ARTIFACTS_BY_WORK_ITEM.values():
        for token in tokens:
            if token not in text:
                fail(f"{path.relative_to(REPO_ROOT)} review packet must include trace artifact {token}")


def validate_schematic_package() -> None:
    path = PB100_DIR / "PB-100-schematic-package.md"
    text = read_text(path)
    lower_text = text.lower()
    if "not a pcb layout package" not in lower_text:
        fail(f"{path.relative_to(REPO_ROOT)} must explicitly avoid PCB layout scope")
    for artifact in sorted(REQUIRED_RELEASE_MANIFEST_ARTIFACTS):
        if artifact == "hardware/power-board/PB-100/PB-100-schematic-package.md":
            continue
        if artifact not in text:
            fail(f"{path.relative_to(REPO_ROOT)} must include release artifact {artifact}")


def validate_test_plan_traceability() -> None:
    path = REPO_ROOT / "docs" / "testing" / "test-plan.md"
    text = read_text(path)
    required_trace_artifacts = (
        "ADR-0013-pb-100-prelayout-vs-postprototype-validation.md",
        "PB-100-post-prototype-validation-gate.csv",
        "PB-100-logic-power-rail-trace.csv",
        "PB-100-logic-power-freeze-review.csv",
        "PB-100-high-medium-output-baseline-trace.csv",
        "PB-100-high-medium-output-freeze-review.csv",
        "PB-100-low-current-output-baseline-trace.csv",
        "PB-100-low-current-output-freeze-review.csv",
        "PB-100-output-stage-value-freeze-checklist.csv",
        "PB-100-output-stage-value-derivation-precheck.csv",
        "PB-100-output-stage-closeout-precheck.csv",
        "PB-100-can1-tx-disable-trace.csv",
        "PB-100-can1-production-dnp-review.csv",
        "PB-100-can1-default-disable-freeze-checklist.csv",
        "PB-100-can1-default-disable-derivation-precheck.csv",
        "PB-100-can1-reset-bench-checklist.csv",
        "PB-100-input-reverse-package-trace.csv",
        "PB-100-input-reverse-freeze-review.csv",
        "PB-100-input-reverse-q1-freeze-checklist.csv",
        "PB-100-input-reverse-q1-derivation-precheck.csv",
        "PB-100-input-reverse-q1-closeout-precheck.csv",
        "PB-100-tvs-load-dump-margin-trace.csv",
        "PB-100-tvs-load-dump-freeze-review.csv",
        "PB-100-tvs-overshoot-escape-checklist.csv",
        "PB-100-tvs-overshoot-validation-precheck.csv",
        "PB-100-logic-power-rail-trace.csv",
        "PB-100-logic-power-freeze-review.csv",
        "PB-100-logic-power-value-freeze-checklist.csv",
        "PB-100-logic-power-value-derivation-precheck.csv",
        "PB-100-logic-power-closeout-precheck.csv",
        "PB-100-current-telemetry-trace.csv",
        "PB-100-current-telemetry-freeze-review.csv",
        "PB-100-current-telemetry-value-freeze-checklist.csv",
        "PB-100-current-telemetry-value-derivation-precheck.csv",
        "PB-100-current-telemetry-closeout-precheck.csv",
        "PB-100-board-current-budget-trace.csv",
        "PB-100-board-current-budget-freeze-review.csv",
        "PB-100-board-current-budget-design-calculation.md",
        "PB-100-board-current-budget-value-freeze-checklist.csv",
        "PB-100-board-current-budget-value-derivation-precheck.csv",
        "PB-100-thermal-telemetry-trace.csv",
        "PB-100-thermal-telemetry-freeze-review.csv",
        "PB-100-thermal-telemetry-value-freeze-checklist.csv",
        "PB-100-thermal-telemetry-value-derivation-precheck.csv",
        "PB-100-thermal-telemetry-closeout-precheck.csv",
        "PB-100-b2b-interface-trace.csv",
        "PB-100-b2b-lb100-resource-binding.csv",
        "PB-100-b2b-lb100-pin-audit-checklist.csv",
        "PB-100-b2b-interface-freeze-checklist.csv",
        "PB-100-b2b-interface-closeout-precheck.csv",
        "PB-100-assembly-readiness-trace.csv",
        "PB-100-factory-assembly-freeze-checklist.csv",
        "PB-100-factory-assembly-sourcing-precheck.csv",
        "PB-100-factory-assembly-closeout-precheck.csv",
        "PB-100-garage-install-freeze-checklist.csv",
        "PB-100-garage-install-sourcing-precheck.csv",
        "PB-100-garage-install-closeout-precheck.csv",
    )
    for token in required_trace_artifacts:
        if token not in text:
            fail(f"{path.relative_to(REPO_ROOT)} must include trace artifact {token}")
    for bench_id in (f"PB-BENCH-{index:03d}" for index in range(1, 16)):
        if bench_id not in text:
            fail(f"{path.relative_to(REPO_ROOT)} must include bench test {bench_id}")
    lower_text = text.lower()
    if "do not run first-power" not in lower_text or "motorcycle" not in lower_text:
        fail(f"{path.relative_to(REPO_ROOT)} must keep motorcycle first-power safety boundary")
    if "can1 listen-only" not in lower_text or "no vehicle-can transmit frame" not in lower_text:
        fail(f"{path.relative_to(REPO_ROOT)} must keep CAN1 listen-only bench test")


def validate_post_prototype_validation_gate() -> None:
    path = PB100_DIR / "PB-100-post-prototype-validation-gate.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty post-prototype validation gate: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in POST_PROTOTYPE_VALIDATION_GATE_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    expected_bench_ids = {f"PB-BENCH-{index:03d}" for index in range(1, 16)}
    seen_bench_ids = set()
    for row_number, row in enumerate(rows, 2):
        bench_id = row["Bench ID"].strip()
        if bench_id in seen_bench_ids:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate Bench ID {bench_id}")
        seen_bench_ids.add(bench_id)
        if bench_id not in expected_bench_ids:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown Bench ID {bench_id}")
        for column in POST_PROTOTYPE_VALIDATION_GATE_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        requires_board = row["Requires assembled board"].strip()
        if requires_board not in {"Yes", "Board optional"}:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: invalid assembled-board requirement")
        if row["Status"].strip() != "Deferred post-prototype":
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: post-prototype status must remain deferred")
        blocks = row["Blocks until complete"].lower()
        if "first motorcycle power" not in blocks or "production release" not in blocks:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: post-prototype gate must block motorcycle power and production release")
        pre_layout_artifact = row["Pre-layout artifact"].strip()
        if pre_layout_artifact.startswith("docs/"):
            artifact_path = REPO_ROOT / pre_layout_artifact
        else:
            artifact_path = PB100_DIR / pre_layout_artifact
        if not artifact_path.exists():
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: missing pre-layout artifact "
                f"{pre_layout_artifact}"
            )

    missing_bench_ids = sorted(expected_bench_ids - seen_bench_ids)
    if missing_bench_ids:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing post-prototype bench IDs: "
            f"{', '.join(missing_bench_ids)}"
        )


def validate_net_naming_contract() -> None:
    path = PB100_DIR / "PB-100-net-naming.md"
    text = read_text(path)
    warning = (
        "Do not use names such as `FOG_LEFT`, `SEAT`, `USB`, `CHIGEE`, `DVR`, or\n"
        "`BRAKE` in PB-100 schematic nets."
    )
    text_without_warning = text.replace(warning, "")
    for forbidden_token in ("FOG", "SEAT", "USB", "CHIGEE", "DVR", "BRAKE"):
        if forbidden_token in text_without_warning:
            fail(f"role token appears outside net-naming warning: {forbidden_token}")
    if "CAN1_TX_ROUTE` | DNP/open" not in text:
        fail("CAN1_TX_ROUTE must remain DNP/open by default in net naming contract")


def main() -> int:
    csv_paths = sorted(PB100_DIR.glob("*.csv")) + sorted((REPO_ROOT / "production" / "bom").glob("*.csv"))
    for csv_path in csv_paths:
        validate_csv(csv_path)
    validate_kicad_scaffold()
    validate_kicad_cli_checks()
    validate_symbol_library()
    validate_kicad_no_role_tokens()
    validate_instance_plan()
    validate_symbol_mpn_readiness()
    validate_symbol_trace_provenance()
    validate_symbol_capture_worklist()
    validate_symbol_capture_progress()
    validate_symbol_pin_evidence()
    validate_symbol_footprint_pad_map()
    validate_large_mosfet_paste_segmentation()
    validate_input_reverse_fet_symbol_evidence()
    validate_jpb1_symbol_from_pin_map()
    validate_instance_symbol_map()
    validate_sheet_reference_map()
    validate_kicad_sheet_manifest()
    validate_net_domain_plan()
    validate_bom_symbol_map()
    validate_schematic_readiness_dashboard()
    validate_schematic_freeze_gap_register()
    validate_engineering_blocker_closeout()
    validate_schematic_review_closeout()
    validate_board_release_blocker_register()
    validate_board_print_closure_matrix()
    validate_schematic_capture_work_queue()
    validate_schematic_capture_plan()
    validate_review_release_manifest()
    validate_schematic_readiness_review()
    validate_schematic_package()
    validate_test_plan_traceability()
    validate_post_prototype_validation_gate()
    validate_output_channel_pin_contract()
    validate_output_controller_pin_template()
    validate_output_net_expansion()
    validate_low_current_output_baseline_trace()
    validate_low_current_output_freeze_review()
    validate_high_medium_output_baseline_trace()
    validate_high_medium_output_freeze_review()
    validate_output_stage_value_freeze_checklist()
    validate_output_stage_value_derivation_precheck()
    validate_output_stage_closeout_precheck()
    validate_input_and_power_pin_templates()
    validate_input_protection_pin_contract()
    validate_logic_power_design_placeholders()
    validate_output_stage_design_values()
    validate_input_power_design_values()
    validate_input_reverse_package_trace()
    validate_input_reverse_freeze_review()
    validate_input_reverse_q1_freeze_checklist()
    validate_input_reverse_q1_derivation_precheck()
    validate_input_reverse_q1_closeout_precheck()
    validate_board_current_budget_trace()
    validate_board_current_budget_freeze_review()
    validate_board_current_budget_design_calculation()
    validate_board_current_budget_value_freeze_checklist()
    validate_board_current_budget_value_derivation_precheck()
    validate_board_current_budget_closeout_precheck()
    validate_current_telemetry_trace()
    validate_current_telemetry_freeze_review()
    validate_current_telemetry_value_freeze_checklist()
    validate_current_telemetry_value_derivation_precheck()
    validate_current_telemetry_closeout_precheck()
    validate_thermal_telemetry_trace()
    validate_thermal_telemetry_freeze_review()
    validate_thermal_telemetry_value_freeze_checklist()
    validate_thermal_telemetry_value_derivation_precheck()
    validate_thermal_telemetry_closeout_precheck()
    validate_logic_power_rail_trace()
    validate_logic_power_design_values()
    validate_logic_power_freeze_review()
    validate_logic_power_value_freeze_checklist()
    validate_logic_power_value_derivation_precheck()
    validate_logic_power_closeout_precheck()
    validate_can1_tx_disable_trace()
    validate_can1_safety_verification()
    validate_can1_production_dnp_review()
    validate_can1_default_disable_freeze_checklist()
    validate_can1_default_disable_derivation_precheck()
    validate_can1_default_disable_closeout_precheck()
    validate_can1_reset_bench_checklist()
    validate_can1_capture_contract()
    validate_assembly_sourcing_recheck()
    validate_assembly_readiness_trace()
    validate_factory_assembly_freeze_checklist()
    validate_factory_assembly_sourcing_precheck()
    validate_factory_assembly_closeout_precheck()
    validate_garage_connector_fuse_plan()
    validate_garage_install_freeze_checklist()
    validate_garage_install_sourcing_precheck()
    validate_garage_install_closeout_precheck()
    validate_sourcing_evidence_snapshot()
    validate_tvs_candidate_consistency()
    validate_tvs_load_dump_margin_trace()
    validate_tvs_load_dump_freeze_review()
    validate_tvs_overshoot_escape_checklist()
    validate_tvs_overshoot_validation_precheck()
    validate_tvs_overshoot_closeout_precheck()
    validate_thermal_telemetry_baseline()
    validate_b2b_interface_trace()
    validate_b2b_connector_candidate()
    validate_b2b_lb100_pin_audit_checklist()
    validate_b2b_interface_freeze_checklist()
    validate_b2b_interface_closeout_precheck()
    validate_b2b_resource_binding()
    validate_validation_traceability()
    validate_test_point_plan()
    validate_fault_response_matrix()
    validate_net_naming_contract()
    print("PB-100 validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
