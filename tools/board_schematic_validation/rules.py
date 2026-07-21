from __future__ import annotations

from pathlib import Path

from .model import Netlist, footprint_pads


def require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def require_component(
    netlist: Netlist,
    ref: str,
    value: str,
    footprint: str,
    failures: list[str],
) -> None:
    component = netlist.components.get(ref)
    require(component is not None, f"missing component {ref}", failures)
    if component is None:
        return
    require(component.value == value, f"{ref}: expected value {value}, got {component.value}", failures)
    require(
        component.footprint == footprint,
        f"{ref}: expected footprint {footprint}, got {component.footprint}",
        failures,
    )


def require_net(
    netlist: Netlist,
    name: str,
    endpoints: set[tuple[str, str]],
    failures: list[str],
    *,
    exact: bool = True,
) -> None:
    actual = set(netlist.nets.get(name, frozenset()))
    if exact:
        require(actual == endpoints, f"{name}: expected {sorted(endpoints)}, got {sorted(actual)}", failures)
    else:
        require(endpoints <= actual, f"{name}: missing endpoints {sorted(endpoints - actual)}", failures)


def validate_footprints(
    netlist: Netlist,
    library_name: str,
    library_dir: Path,
    failures: list[str],
) -> None:
    for ref, component in sorted(netlist.components.items()):
        require(bool(component.footprint), f"{ref}: Footprint is empty", failures)
        if not component.footprint:
            continue
        prefix = f"{library_name}:"
        require(component.footprint.startswith(prefix), f"{ref}: non-local footprint {component.footprint}", failures)
        if not component.footprint.startswith(prefix):
            continue
        path = library_dir / f"{component.footprint.removeprefix(prefix)}.kicad_mod"
        require(path.is_file(), f"{ref}: footprint file is missing: {path}", failures)
        if not path.is_file():
            continue
        missing_pads = component.pins - footprint_pads(path)
        require(not missing_pads, f"{ref}: footprint lacks pads {sorted(missing_pads)}", failures)


def validate_lb(netlist: Netlist, library_dir: Path) -> list[str]:
    failures: list[str] = []
    require(len(netlist.components) >= 60, f"LB-100 remains underspecified: {len(netlist.components)} components", failures)
    validate_footprints(netlist, "LB100", library_dir, failures)
    require_component(netlist, "U1", "STM32H563VIT6", "LB100:LQFP-100_L14.0-W14.0-P0.50-LS16.0-BL", failures)
    require_component(netlist, "U3", "TCA9539QPWRQ1", "LB100:TSSOP-24_4.4x7.8mm_P0.65mm", failures)
    require_component(netlist, "JPB1", "FX18-100S-0.8SV10", "LB100:FX18-100S-0.8SV10_Hirose", failures)
    require_component(netlist, "JFB1", "AFC07-S24ECA-00", "LB100:FPC-SMD_AFC07-S24ECA-00", failures)

    for ref in ("U4", "U5", "U6", "JBT1"):
        require(netlist.components.get(ref) is not None and netlist.components[ref].dnp, f"{ref}: must remain DNP", failures)

    safety_nets = {
        "CAN1_TX_DISABLE_CMD": {("JPB1", "67"), ("U1", "85")},
        "CAN1_TX_DISABLED_STATUS": {("JPB1", "68"), ("U1", "58")},
        "CAN1_RX_ROUTE": {("JPB1", "69"), ("U1", "95")},
        "CAN1_TX_ROUTE": {("JPB1", "70"), ("U1", "96")},
    }
    for name, endpoints in safety_nets.items():
        require_net(netlist, name, endpoints, failures)

    require_net(netlist, "USB_D_N", {("JFB1", "5"), ("U1", "70")}, failures)
    require_net(netlist, "USB_D_P", {("JFB1", "4"), ("U1", "71")}, failures)
    require_net(netlist, "USB_VBUS_SENSE", {("JFB1", "8"), ("U1", "57")}, failures)
    require_net(netlist, "SWDIO", {("JDBG1", "2"), ("U1", "72")}, failures)
    require_net(netlist, "SWCLK", {("JDBG1", "4"), ("U1", "76")}, failures)

    for index in range(1, 11):
        iox_pin = str(index + 3) if index <= 8 else str(index + 4)
        require_net(netlist, f"CH_LED_{index}", {("JFB1", str(index + 9)), ("U3", iox_pin)}, failures)
    require_net(netlist, "STATUS_RGB_DATA", {("JFB1", "9"), ("U3", "15")}, failures)
    require_net(netlist, "SERVICE_BTN", {("JFB1", "20"), ("U3", "16")}, failures)

    mf_pins = {
        ("JPB1", "MF_A_PIN1_51_END"),
        ("JPB1", "MF_B_PIN1_51_END"),
        ("JPB1", "MF_A_PIN50_100_END"),
        ("JPB1", "MF_B_PIN50_100_END"),
    }
    require_net(netlist, "GND", mf_pins, failures, exact=False)
    require(len(netlist.components["JPB1"].pins) == 104, "JPB1 must expose 100 signal and four logical MF pins", failures)
    return failures


def validate_fb(netlist: Netlist, library_dir: Path) -> list[str]:
    failures: list[str] = []
    require(len(netlist.components) >= 40, f"FB-100 remains underspecified: {len(netlist.components)} components", failures)
    validate_footprints(netlist, "FB100", library_dir, failures)
    require_component(netlist, "J1", "USB4105-GF-A", "FB100:TYPE-C-SMD_SBC-160S1A-20-S412", failures)
    require_component(netlist, "D1", "USBLC6-2SC6", "FB100:SOT-23-6_L2.9-W1.6-P0.95-LS2.8-BL", failures)
    require_component(netlist, "U1", "LTC3212EDDB#TRPBF", "FB100:DFN-12-1EP_2x3mm_P0.45mm", failures)
    require_component(netlist, "JFB1", "AFC07-S24ECA-00", "FB100:FPC-SMD_AFC07-S24ECA-00", failures)
    require(netlist.components.get("J2") is not None and netlist.components["J2"].dnp, "J2 OLED option must remain DNP", failures)

    require_net(netlist, "USB_VBUS", {("J1", pin) for pin in ("A4", "A9", "B4", "B9")} | {("D1", "5"), ("R13", "1")}, failures)
    require_net(netlist, "USB_CC1", {("J1", "A5"), ("JFB1", "6"), ("R11", "1")}, failures)
    require_net(netlist, "USB_CC2", {("J1", "B5"), ("JFB1", "7"), ("R12", "1")}, failures)
    require_net(netlist, "USB_D_P_CONN", {("J1", "A6"), ("J1", "B6"), ("D1", "1")}, failures)
    require_net(netlist, "USB_D_N_CONN", {("J1", "A7"), ("J1", "B7"), ("D1", "3")}, failures)
    require_net(netlist, "USB_D_P", {("D1", "6"), ("JFB1", "4")}, failures)
    require_net(netlist, "USB_D_N", {("D1", "4"), ("JFB1", "5")}, failures)
    require_net(netlist, "USB_VBUS_SENSE", {("C1", "1"), ("JFB1", "8"), ("R13", "2"), ("R14", "1")}, failures)
    require(not ({("J1", "A4"), ("J1", "A9"), ("J1", "B4"), ("J1", "B9")} & set(netlist.nets.get("FB_3V3_OR_IO", frozenset()))), "USB VBUS back-powers FB_3V3_OR_IO", failures)

    for index in range(1, 11):
        require_net(netlist, f"CH_LED_{index}", {("JFB1", str(index + 9)), (f"D{index + 2}", "2")}, failures)
    require_net(netlist, "STATUS_RGB_DATA", {("JFB1", "9"), ("U1", "3")}, failures)
    require_net(netlist, "RGB_R_K", {("D2", "2"), ("U1", "8")}, failures)
    require_net(netlist, "RGB_G_K", {("D2", "3"), ("U1", "7")}, failures)
    require_net(netlist, "RGB_B_K", {("D2", "4"), ("U1", "9")}, failures)
    require_net(netlist, "SERVICE_BTN", {("C6", "1"), ("JFB1", "20"), ("R17", "2"), ("SW1", "A"), ("SW1", "A1")}, failures)
    require_net(netlist, "RESET_BTN", {("C7", "1"), ("JFB1", "21"), ("R18", "2"), ("SW2", "A"), ("SW2", "A1")}, failures)
    return failures
