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
    require_component(netlist, "U14", "SN74LVC1G17QDBVRQ1", "LB100:SOT-25_L3.0-W1.6-P0.95-LS2.8-TL", failures)
    for ref in ("U18", "U19"):
        require_component(netlist, ref, "SN74LVC1G17QDBVRQ1", "LB100:SOT-25_L3.0-W1.6-P0.95-LS2.8-TL", failures)
    for ref in ("U15", "U16", "U17"):
        require_component(netlist, ref, "SN74LVC1G125QDBVRQ1", "LB100:SOT-25_L3.0-W1.6-P0.95-LS2.8-TL", failures)
    require_component(netlist, "JPB1", "FX18-100S-0.8SV10", "LB100:FX18-100S-0.8SV10_Hirose", failures)
    require_component(netlist, "JFB1", "AFC07-S24ECA-00", "LB100:FPC-SMD_AFC07-S24ECA-00", failures)
    for ref, value in (
        ("TP1", "E73_SWDIO"),
        ("TP2", "E73_SWDCLK"),
        ("TP3", "BLE_RESET_N"),
        ("TP4", "RADIO_SENSOR_3V3"),
        ("TP5", "GND"),
    ):
        require_component(netlist, ref, value, "LB100:TestPoint_SMD_1.2mm", failures)

    for ref in ("U4", "U5", "U6", "JBT1", "Q18", "Q19", "R24", "R25", "R28", "R29"):
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
    require_net(netlist, "USB_VBUS_DETECT_RAW", {("JFB1", "8"), ("U14", "2")}, failures)
    require_net(netlist, "USB_VBUS_PRESENT", {("U1", "57"), ("U14", "4")}, failures)
    require_net(netlist, "SWDIO", {("JDBG1", "2"), ("U1", "72")}, failures)
    require_net(netlist, "SWCLK", {("JDBG1", "4"), ("U1", "76")}, failures)

    for index in range(1, 11):
        iox_pin = str(index + 3) if index <= 8 else str(index + 4)
        require_net(netlist, f"CH_LED_{index}", {("JFB1", str(index + 9)), ("U3", iox_pin)}, failures)
    require_net(netlist, "STATUS_RGB_DATA", {("JFB1", "9"), ("U1", "88")}, failures)
    require_net(netlist, "SERVICE_BTN", {("JFB1", "20"), ("U3", "16")}, failures)
    require_net(netlist, "ADC_REF", {("U1", "21"), ("R16", "2"), ("C28", "1"), ("C29", "1"), ("JPB1", "66")}, failures)
    require_net(netlist, "AGND", {("U1", "19"), ("U1", "20"), ("R17", "1")}, failures, exact=False)
    require_net(netlist, "GND", {("R17", "2")}, failures, exact=False)
    require_net(netlist, "LB_3V3_IO", {("U10", "5"), ("U10", "12"), ("U11", "2")}, failures, exact=False)
    require_net(
        netlist,
        "RADIO_SENSOR_3V3",
        {
            ("U7", "19"), ("U10", "8"), ("U15", "5"), ("U16", "5"),
            ("U17", "5"), ("R9", "1"), ("R18", "2"), ("R19", "2"),
            ("TP4", "1"),
        },
        failures,
        exact=False,
    )
    require_net(netlist, "UART_TX", {("JPB1", "78"), ("R22", "2"), ("U1", "78"), ("U15", "2")}, failures)
    require_net(netlist, "BLE_UART_RX_MODULE", {("U7", "22"), ("U15", "4"), ("R18", "1")}, failures)
    require_net(netlist, "BLE_UART_TX_MODULE", {("U7", "20"), ("U16", "2"), ("R19", "1")}, failures)
    require_net(netlist, "UART_RX", {("JPB1", "79"), ("U1", "79"), ("U16", "4"), ("R20", "2")}, failures)
    require_net(netlist, "BLE_RESET_N_MCU", {("R21", "1"), ("U1", "97"), ("U17", "2")}, failures)
    require_net(netlist, "BLE_RESET_N", {("U7", "26"), ("U17", "4"), ("R9", "2"), ("TP3", "1")}, failures)
    require_net(netlist, "E73_SWDIO", {("U7", "37"), ("TP1", "1")}, failures)
    require_net(netlist, "E73_SWDCLK", {("U7", "39"), ("TP2", "1")}, failures)
    require_net(
        netlist,
        "GND",
        {
            ("U15", "1"), ("U15", "3"), ("U16", "1"), ("U16", "3"),
            ("U17", "1"), ("U17", "3"), ("R21", "2"),
            ("TP5", "1"),
        },
        failures,
        exact=False,
    )
    require_component(netlist, "R9", "10k 1% switched reset pull-up", "LB100:R_C_0603_1608Metric", failures)
    require_component(netlist, "R18", "22k 1% switched UART idle clamp", "LB100:R_C_0603_1608Metric", failures)
    require_component(netlist, "R19", "22k 1% switched UART idle clamp", "LB100:R_C_0603_1608Metric", failures)
    require_component(netlist, "R20", "100k 1% MCU UART idle pull-up", "LB100:R_C_0603_1608Metric", failures)
    require_component(netlist, "R21", "100k 1% reset default assert", "LB100:R_C_0603_1608Metric", failures)
    require_component(netlist, "R22", "100k 1% MCU UART idle pull-up", "LB100:R_C_0603_1608Metric", failures)
    for ref in ("D19", "D20"):
        require_component(netlist, ref, "BZT52H-B4V3-Q", "LB100:SOD-123F_L2.6-W1.6", failures)
    require_component(netlist, "R23", "4.7k 1% FOG_A dry-contact series", "LB100:R_C_0603_1608Metric", failures)
    require_component(netlist, "R26", "47k 1% FOG_A pull-up", "LB100:R_C_0603_1608Metric", failures)
    require_component(netlist, "R27", "4.7k 1% FOG_B dry-contact series", "LB100:R_C_0603_1608Metric", failures)
    require_component(netlist, "R30", "47k 1% FOG_B pull-up", "LB100:R_C_0603_1608Metric", failures)
    require_component(netlist, "C35", "47nF 50V X7R FOG_A filter", "LB100:R_C_0603_1608Metric", failures)
    require_component(netlist, "C36", "47nF 50V X7R FOG_B filter", "LB100:R_C_0603_1608Metric", failures)
    require_net(netlist, "LB_3V3_MAIN", {("R20", "1"), ("R22", "1")}, failures, exact=False)
    require_net(netlist, "LB_3V3_IO", {("R26", "1"), ("R30", "1"), ("U18", "5"), ("U19", "5")}, failures, exact=False)
    require_net(netlist, "FOG_A_SW_IN", {("JPB1", "82"), ("R23", "1"), ("R24", "1")}, failures)
    require_net(netlist, "FOG_B_SW_IN", {("JPB1", "83"), ("R27", "1"), ("R28", "1")}, failures)
    require_net(netlist, "FOG_A_FILTERED", {("R23", "2"), ("R26", "2"), ("C35", "1"), ("D19", "1"), ("Q18", "3"), ("U18", "2")}, failures)
    require_net(netlist, "FOG_B_FILTERED", {("R27", "2"), ("R30", "2"), ("C36", "1"), ("D20", "1"), ("Q19", "3"), ("U19", "2")}, failures)
    require_net(netlist, "FOG_A_SW_IN_MCU", {("U1", "67"), ("U18", "4")}, failures)
    require_net(netlist, "FOG_B_SW_IN_MCU", {("U1", "68"), ("U19", "4")}, failures)
    require_net(netlist, "GND", {("C35", "2"), ("C36", "2"), ("D19", "2"), ("D20", "2"), ("U18", "3"), ("U19", "3")}, failures, exact=False)

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
    require_net(netlist, "USB_VBUS_DETECT_RAW", {("C1", "1"), ("JFB1", "8"), ("R13", "2"), ("R14", "1")}, failures)
    require_net(netlist, "GND", {("C1", "2"), ("R14", "2")}, failures, exact=False)
    require_component(netlist, "R13", "3.9k 1% current limit", "FB100:R_C_0603_1608Metric", failures)
    require_component(netlist, "R14", "15k 1% defined pulldown", "FB100:R_C_0603_1608Metric", failures)
    require_component(netlist, "C1", "100nF 16V X7R 10%", "FB100:R_C_0603_1608Metric", failures)
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
