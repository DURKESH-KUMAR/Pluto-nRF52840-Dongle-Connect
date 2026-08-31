import subprocess
import re
import serial.tools.list_ports


def separator():
    print("=" * 80)


def find_bluetooth_devices():
    """
    Find Bluetooth devices known to Windows.
    This includes Classic Bluetooth devices.
    """

    print()
    separator()
    print("BLUETOOTH DEVICES")
    separator()

    command = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        r"""
        Get-PnpDevice -Class Bluetooth |
        Where-Object {
            $_.Status -eq 'OK' -or
            $_.FriendlyName
        } |
        Select-Object Status, FriendlyName, InstanceId |
        Format-List
        """
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )

        output = result.stdout.strip()

        if not output:
            print("No Bluetooth devices found in Windows.")
            return

        print(output)

    except Exception as e:
        print("Bluetooth query failed:")
        print(e)


def find_spp_com_ports():
    """
    Find COM ports created by Bluetooth Serial/SPP.
    """

    print()
    separator()
    print("BLUETOOTH SERIAL / SPP COM PORTS")
    separator()

    ports = list(serial.tools.list_ports.comports())

    found = False

    for port in ports:

        text = (
            f"{port.device} "
            f"{port.description or ''} "
            f"{port.manufacturer or ''}"
        )

        lower = text.lower()

        if (
            "bluetooth" in lower
            or "serial over bluetooth" in lower
            or "spp" in lower
        ):

            found = True

            print()
            print(f"COM PORT     : {port.device}")
            print(f"DESCRIPTION  : {port.description}")
            print(f"MANUFACTURER : {port.manufacturer}")
            print(f"HWID         : {port.hwid}")

    if not found:

        print()
        print("No Bluetooth SPP COM ports found.")


def find_all_com_ports():

    print()
    separator()
    print("ALL COM PORTS")
    separator()

    ports = list(serial.tools.list_ports.comports())

    if not ports:

        print("No COM ports found.")
        return

    for port in ports:

        print(
            f"{port.device:<10} | "
            f"{port.description or 'Unknown'}"
        )


def main():

    print()
    separator()
    print("PLUTO SPP DEVICE FINDER")
    separator()

    print()
    print("This program searches Windows for:")
    print("  1. Bluetooth Classic devices")
    print("  2. Bluetooth SPP / Serial COM ports")
    print("  3. All available COM ports")

    find_bluetooth_devices()
    find_spp_com_ports()
    find_all_com_ports()

    print()
    separator()
    print("DONE")
    separator()


if __name__ == "__main__":
    main()