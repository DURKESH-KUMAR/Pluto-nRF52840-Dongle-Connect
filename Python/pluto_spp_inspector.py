import subprocess
import re
import json
import sys
import time

import serial.tools.list_ports


# ============================================================
# Pluto SPP Configuration Inspector
# Windows / Bluetooth Classic / SPP
# ============================================================


def header(title):
    print()
    print("=" * 80)
    print(title)
    print("=" * 80)


def run_powershell(script):
    try:
        result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                script,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
        )

        return result.stdout.strip()

    except Exception as e:
        print("PowerShell error:", e)
        return ""


# ============================================================
# Bluetooth Classic devices known by Windows
# ============================================================

def get_bluetooth_devices():

    header("BLUETOOTH CLASSIC DEVICES")

    script = r'''
Get-PnpDevice -Class Bluetooth -ErrorAction SilentlyContinue |
Select-Object Status, Class, FriendlyName, InstanceId |
ConvertTo-Json -Depth 3
'''

    output = run_powershell(script)

    if not output:
        print("No Bluetooth information returned.")
        return []

    try:
        devices = json.loads(output)

        if isinstance(devices, dict):
            devices = [devices]

    except Exception:
        print("Unable to decode Windows Bluetooth information.")
        print(output)
        return []

    for i, device in enumerate(devices, 1):

        name = device.get("FriendlyName", "")
        status = device.get("Status", "")
        instance = device.get("InstanceId", "")

        print()
        print(f"[{i}]")
        print(f"Name       : {name}")
        print(f"Status     : {status}")
        print(f"Instance ID: {instance}")

    return devices


# ============================================================
# Search Windows Bluetooth registry
# ============================================================

def search_bluetooth_registry():

    header("WINDOWS BLUETOOTH REGISTRY INFORMATION")

    script = r'''
$paths = @(
    "HKLM:\SYSTEM\CurrentControlSet\Services\BTHPORT\Parameters\Devices",
    "HKLM:\SYSTEM\CurrentControlSet\Services\BTHPORT\Parameters\Keys"
)

foreach ($path in $paths) {

    if (Test-Path $path) {

        Write-Output "PATH=$path"

        Get-ChildItem $path -ErrorAction SilentlyContinue |
        ForEach-Object {

            Write-Output ("KEY=" + $_.PSChildName)

            try {
                Get-ItemProperty $_.PSPath |
                Out-String |
                Write-Output
            }
            catch {}
        }
    }
}
'''

    output = run_powershell(script)

    if output:
        print(output)
    else:
        print("No registry information available.")


# ============================================================
# Bluetooth COM ports
# ============================================================

def get_com_ports():

    header("WINDOWS COM PORTS")

    ports = list(serial.tools.list_ports.comports())

    if not ports:
        print("No COM ports detected.")
        return []

    for i, port in enumerate(ports, 1):

        print()
        print(f"[{i}]")
        print(f"COM port     : {port.device}")
        print(f"Description  : {port.description}")
        print(f"Manufacturer : {port.manufacturer}")
        print(f"Product      : {port.product}")
        print(f"Serial       : {port.serial_number}")
        print(f"VID          : {port.vid}")
        print(f"PID          : {port.pid}")
        print(f"HWID         : {port.hwid}")

        combined = " ".join(
            [
                str(port.description or ""),
                str(port.manufacturer or ""),
                str(port.product or ""),
                str(port.hwid or ""),
            ]
        ).lower()

        if (
            "bluetooth" in combined
            or "bthenum" in combined
            or "serial over bluetooth" in combined
            or "spp" in combined
        ):
            print("Protocol hint : BLUETOOTH / POSSIBLE SPP")

    return ports


# ============================================================
# Extract Bluetooth address
# ============================================================

def extract_addresses(text):

    pattern = r"\b[0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2}){5}\b"

    return sorted(
        set(re.findall(pattern, text))
    )


# ============================================================
# RFCOMM / SPP information
# ============================================================

def get_rfcomm_information():

    header("RFCOMM / SPP INFORMATION")

    print("""
Searching Windows for Bluetooth serial/RFCOMM information.

SPP normally operates through:
    Bluetooth Classic
          |
        RFCOMM
          |
       Serial Port
""")

    script = r'''
Get-PnpDevice -ErrorAction SilentlyContinue |
Where-Object {
    $_.FriendlyName -match
    "Bluetooth|Serial|RFCOMM|SPP|COM"
} |
Select-Object Status, Class, FriendlyName, InstanceId |
Format-List
'''

    output = run_powershell(script)

    if output:
        print(output)
    else:
        print("No RFCOMM-related device information found.")


# ============================================================
# Check Bluetooth services
# ============================================================

def get_bluetooth_services():

    header("BLUETOOTH SERVICES")

    script = r'''
Get-Service |
Where-Object {
    $_.Name -match "Bluetooth|bth" -or
    $_.DisplayName -match "Bluetooth"
} |
Select-Object Status, Name, DisplayName |
Format-Table -AutoSize
'''

    output = run_powershell(script)

    if output:
        print(output)
    else:
        print("Bluetooth service information unavailable.")


# ============================================================
# Search for SPP UUID
# ============================================================

def show_spp_uuid():

    header("STANDARD SPP UUID")

    print("Bluetooth Serial Port Profile commonly uses:")

    print()
    print("Service UUID : 00001101-0000-1000-8000-00805F9B34FB")

    print()
    print("This is the standard Serial Port Profile UUID.")
    print("The RFCOMM channel is assigned by the Bluetooth")
    print("device/service and is NOT the same thing as the UUID.")


# ============================================================
# Test COM port
# ============================================================

def inspect_com_port(port):

    header(f"INSPECTING {port}")

    print("The following is the serial-side configuration.")
    print()

    print("Port       :", port)
    print("Baudrate   : usually determined by the UART side")
    print("Data bits  : normally 8")
    print("Parity     : normally NONE")
    print("Stop bits  : normally 1")
    print("Flow       : normally NONE")

    print()
    print("IMPORTANT:")
    print("These serial settings are NOT Bluetooth RF settings.")


# ============================================================
# Generate configuration report
# ============================================================

def generate_report(devices, ports):

    header("CONFIGURATION SUMMARY")

    print("""
============================================================
BLUETOOTH CLASSIC / SPP CONFIGURATION
============================================================
""")

    print("SPP UUID")
    print("  00001101-0000-1000-8000-00805F9B34FB")

    print()
    print("Bluetooth device name")
    print("  Obtain from Windows Bluetooth device list")

    print()
    print("Bluetooth address")
    print("  Obtain from Windows Bluetooth device information")

    print()
    print("RFCOMM channel")
    print("  Must be obtained from the SPP service/device.")

    print()
    print("Authentication")
    print("  Device dependent")

    print()
    print("Encryption")
    print("  Device dependent")

    print()
    print("Passkey")
    print("  Device dependent")
    print("  If Pluto requires one, use the configured Pluto passkey.")

    print()
    print("Serial parameters")
    print("  Common starting point: 115200, 8-N-1")

    print()
    print("COM/RFCOMM port")

    spp_found = False

    for port in ports:

        text = " ".join(
            [
                str(port.description or ""),
                str(port.manufacturer or ""),
                str(port.product or ""),
                str(port.hwid or ""),
            ]
        ).lower()

        if (
            "bluetooth" in text
            or "bthenum" in text
            or "serial over bluetooth" in text
            or "spp" in text
        ):

            print(f"  {port.device} - {port.description}")
            spp_found = True

    if not spp_found:
        print("  NOT FOUND")


# ============================================================
# Main
# ============================================================

def main():

    header("PLUTO SPP CONFIGURATION INSPECTOR")

    print("""
Purpose:

Find the information required to understand/configure
a Bluetooth Classic SPP connection to Pluto.

This program does NOT use BLE.
This program does NOT use GATT.
This program does NOT use Bleak.
""")

    # --------------------------------------------------------
    # Bluetooth devices
    # --------------------------------------------------------

    devices = get_bluetooth_devices()

    # --------------------------------------------------------
    # Addresses
    # --------------------------------------------------------

    print()
    header("POSSIBLE BLUETOOTH ADDRESSES")

    all_text = json.dumps(
        devices,
        ensure_ascii=False
    )

    addresses = extract_addresses(all_text)

    if addresses:

        for address in addresses:
            print("Address:", address)

    else:

        print("No Bluetooth address found in PnP information.")

    # --------------------------------------------------------
    # Registry
    # --------------------------------------------------------

    search_bluetooth_registry()

    # --------------------------------------------------------
    # RFCOMM
    # --------------------------------------------------------

    get_rfcomm_information()

    # --------------------------------------------------------
    # COM ports
    # --------------------------------------------------------

    ports = get_com_ports()

    # --------------------------------------------------------
    # Bluetooth services
    # --------------------------------------------------------

    get_bluetooth_services()

    # --------------------------------------------------------
    # SPP UUID
    # --------------------------------------------------------

    show_spp_uuid()

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    generate_report(
        devices,
        ports
    )

    # --------------------------------------------------------
    # Optional COM test
    # --------------------------------------------------------

    print()
    answer = input(
        "Enter a Bluetooth COM port to inspect "
        "(or press ENTER to finish): "
    ).strip().upper()

    if answer:

        inspect_com_port(answer)

    print()
    header("INSPECTION COMPLETE")

    print("""
The important values to provide for the next firmware step are:

1. Pluto Bluetooth Classic address
2. Pluto device name
3. SPP UUID
4. RFCOMM channel
5. Authentication requirement
6. Encryption requirement
7. Passkey requirement
8. Serial/UART parameters
9. Windows SPP COM port, if available

NOTE:
An nRF52840 cannot directly implement Bluetooth Classic SPP.
If Pluto is truly Classic SPP, the Bluetooth controller used
for the Pluto link must support Bluetooth Classic/RFCOMM.
""")


if __name__ == "__main__":

    try:
        main()

    except KeyboardInterrupt:
        print()
        print("Stopped by user.")

    except Exception as e:
        print()
        print("ERROR:")
        print(e)