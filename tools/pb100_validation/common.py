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


REPO_ROOT = Path(__file__).resolve().parents[2]
PB100_DIR = REPO_ROOT / "hardware" / "power-board" / "PB-100"
KICAD_DIR = PB100_DIR / "kicad"
PRODUCTION_DIR = REPO_ROOT / "production"
CONTROLLED_LAYOUT_ALLOWLIST = {
    KICAD_DIR / "PB-100.kicad_pcb",
    PB100_DIR / "qualification" / "Q2-C100" / "kicad" / "Q2-C100.kicad_pcb",
}
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
    "CAP-FOG": (
        "PB-100-fog-switch-interface.md",
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
    "Rejected 60 V history",
    "Selected 80 V TOLL path",
    "80 V alternatives",
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
    "Active cutoff selection",
    "Protected-domain voltage margin",
    "60V historical rejection",
    "80V protected-side Q1",
    "150V raw-side Q2",
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
    "CAP-FOG",
    "CAP-TP",
}
ALLOWED_CAPTURE_STATUSES = {
    "Scaffold ready",
    "Linked scaffold",
    "Planned capture",
    "Blocked pending symbol",
    "Review-defined",
    "Value-bearing EVT capture",
}
REQUIRED_RELEASE_MANIFEST_ARTIFACTS = {
    "docs/adr/ADR-0013-pb-100-prelayout-vs-postprototype-validation.md",
    "docs/adr/ADR-0017-pb-100-staged-release-authorization.md",
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
    "hardware/power-board/PB-100/PB-100-staged-release-readiness.csv",
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

VALIDATION_HOOK_NAMES: set[str] = set()


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
    row_text = (
        " ".join(row.values())
        .replace("FOG_A_SW_IN", "")
        .replace("FOG_B_SW_IN", "")
        .replace("PBVAL-FOG-001", "")
    )
    for forbidden_token in FORBIDDEN_ROLE_TOKENS:
        if forbidden_token == "FOG" and row.get("Work item", "").strip() == "CAP-FOG":
            continue
        if forbidden_token in row_text:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: role token {forbidden_token} is not allowed")


def register_validation_hooks(names: set[str]) -> None:
    VALIDATION_HOOK_NAMES.clear()
    VALIDATION_HOOK_NAMES.update(names)
