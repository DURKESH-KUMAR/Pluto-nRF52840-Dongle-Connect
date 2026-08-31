import asyncio
import sys
from datetime import datetime

from bleak import BleakScanner, BleakClient


# ============================================================
# Configuration
# ============================================================

PASSKEY = "1234"

SCAN_TIME = 8.0


# ============================================================
# Helpers
# ============================================================

def timestamp():
    return datetime.now().strftime("%H:%M:%S")


def separator():
    print("=" * 80)


def property_list(characteristic):
    props = []

    for prop in characteristic.properties:
        props.append(prop)

    return ", ".join(props)


def print_uuid(uuid):
    return str(uuid)


def print_bytes(data):
    if data is None:
        return ""

    return " ".join(f"{b:02X}" for b in data)


# ============================================================
# Scan for BLE devices
# ============================================================

async def scan_devices():

    print()
    separator()
    print("SCANNING FOR BLUETOOTH DEVICES")
    separator()

    print(f"Scan time: {SCAN_TIME} seconds")
    print()

    devices = await BleakScanner.discover(
        timeout=SCAN_TIME,
        return_adv=True
    )

    if not devices:
        print("No Bluetooth devices found.")
        return []

    results = []

    for address, item in devices.items():

        device = item[0]
        advertisement = item[1]

        name = (
            device.name
            or advertisement.local_name
            or "Unknown"
        )

        rssi = advertisement.rssi

        print(
            f"{len(results) + 1:3d}. "
            f"{name:<35} "
            f"{address:<25} "
            f"RSSI={rssi}"
        )

        results.append(
            (
                device,
                advertisement
            )
        )

    return results


# ============================================================
# Device selection
# ============================================================

def select_device(devices):

    if not devices:
        return None

    print()
    separator()

    while True:

        choice = input(
            "Enter device number to inspect "
            "(or Q to quit): "
        ).strip()

        if choice.upper() == "Q":
            return None

        try:

            number = int(choice)

            if 1 <= number <= len(devices):

                return devices[number - 1][0]

        except ValueError:
            pass

        print("Invalid selection.")


# ============================================================
# Print services
# ============================================================

def print_services(client):

    print()
    separator()
    print("GATT SERVICES")
    separator()

    services = client.services

    if not services:

        print("No GATT services discovered.")

        return


    for service_index, service in enumerate(
        services,
        start=1
    ):

        print()
        print(
            f"[SERVICE {service_index}]"
        )

        print(
            f"UUID        : {service.uuid}"
        )

        print(
            f"Handle      : {getattr(service, 'handle', 'N/A')}"
        )

        print(
            f"Description : {service.description}"
        )

        print(
            f"Characteristics: "
            f"{len(service.characteristics)}"
        )


# ============================================================
# Characteristic inspection
# ============================================================

async def inspect_characteristic(
    client,
    characteristic
):

    print()
    print(
        "    CHARACTERISTIC"
    )

    print(
        f"    UUID       : {characteristic.uuid}"
    )

    print(
        f"    Handle     : "
        f"{getattr(characteristic, 'handle', 'N/A')}"
    )

    print(
        f"    Properties : "
        f"{property_list(characteristic)}"
    )

    print(
        f"    Description: "
        f"{characteristic.description}"
    )


    # --------------------------------------------------------
    # Read characteristic
    # --------------------------------------------------------

    if "read" in characteristic.properties:

        try:

            data = await client.read_gatt_char(
                characteristic.uuid
            )

            print(
                f"    READ       : {print_bytes(data)}"
            )

            try:

                text = data.decode(
                    "utf-8",
                    errors="replace"
                )

                print(
                    f"    READ TEXT  : {text!r}"
                )

            except Exception:
                pass

        except Exception as e:

            print(
                f"    READ ERROR : {e}"
            )


    # --------------------------------------------------------
    # Descriptors
    # --------------------------------------------------------

    descriptors = characteristic.descriptors

    if descriptors:

        print(
            f"    Descriptors: {len(descriptors)}"
        )

        for descriptor in descriptors:

            print(
                f"      Descriptor UUID : "
                f"{descriptor.uuid}"
            )

            print(
                f"      Handle          : "
                f"{getattr(descriptor, 'handle', 'N/A')}"
            )

            print(
                f"      Description     : "
                f"{descriptor.description}"
            )

    else:

        print(
            "    Descriptors: none"
        )


# ============================================================
# Inspect complete GATT database
# ============================================================

async def inspect_gatt(client):

    print()
    separator()
    print("COMPLETE GATT DATABASE")
    separator()


    for service_index, service in enumerate(
        client.services,
        start=1
    ):

        print()
        print(
            f"SERVICE {service_index}"
        )

        print(
            f"UUID        : {service.uuid}"
        )

        print(
            f"Handle      : "
            f"{getattr(service, 'handle', 'N/A')}"
        )

        print(
            f"Description : {service.description}"
        )

        print("-" * 80)


        for characteristic in service.characteristics:

            await inspect_characteristic(
                client,
                characteristic
            )


# ============================================================
# Notification callback
# ============================================================

def make_notification_callback(uuid):

    def callback(sender, data):

        print()
        separator()
        print("BLE DATA RECEIVED")
        separator()

        print(
            f"Time          : {timestamp()}"
        )

        print(
            f"Characteristic: {uuid}"
        )

        print(
            f"Length        : {len(data)} bytes"
        )

        print(
            f"HEX           : {print_bytes(data)}"
        )

        try:

            text = bytes(data).decode(
                "utf-8",
                errors="replace"
            )

            print(
                f"TEXT          : {text!r}"
            )

        except Exception:
            pass

        print()

    return callback


# ============================================================
# Subscribe to notifications
# ============================================================

async def test_notifications(client):

    print()
    separator()
    print("NOTIFICATION / INDICATION TEST")
    separator()

    candidates = []


    for service in client.services:

        for characteristic in service.characteristics:

            props = characteristic.properties

            if (
                "notify" in props
                or "indicate" in props
            ):

                candidates.append(
                    characteristic
                )


    if not candidates:

        print(
            "No Notify/Indicate characteristics found."
        )

        return


    print(
        f"Found {len(candidates)} "
        "Notify/Indicate characteristic(s)."
    )

    print()


    for index, characteristic in enumerate(
        candidates,
        start=1
    ):

        print(
            f"{index}. "
            f"{characteristic.uuid} "
            f"[{property_list(characteristic)}]"
        )


    print()
    print(
        "The script will listen to these "
        "characteristics for 10 seconds."
    )


    subscribed = []


    for characteristic in candidates:

        try:

            callback = make_notification_callback(
                characteristic.uuid
            )

            await client.start_notify(
                characteristic.uuid,
                callback
            )

            subscribed.append(
                (
                    characteristic.uuid,
                    callback
                )
            )

            print(
                f"✓ Subscribed: "
                f"{characteristic.uuid}"
            )

        except Exception as e:

            print(
                f"✗ Cannot subscribe to "
                f"{characteristic.uuid}: {e}"
            )


    print()
    print(
        "Listening for Pluto data..."
    )

    print(
        "Press Ctrl+C to stop."
    )


    try:

        await asyncio.sleep(10)

    except KeyboardInterrupt:

        pass


    for uuid, callback in subscribed:

        try:

            await client.stop_notify(
                uuid
            )

        except Exception:
            pass


# ============================================================
# Main inspection
# ============================================================

async def inspect_pluto(device):

    print()
    separator()
    print("CONNECTING TO PLUTO")
    separator()

    print(
        f"Name    : {device.name}"
    )

    print(
        f"Address : {device.address}"
    )


    client = BleakClient(
        device,
        timeout=15.0
    )


    try:

        print()
        print(
            "Connecting..."
        )

        await client.connect()


        if not client.is_connected:

            print(
                "Connection failed."
            )

            return


        print()
        print(
            "✓ PLUTO CONNECTED"
        )


        print()
        print(
            "Connection details:"
        )

        print(
            f"Connected : {client.is_connected}"
        )


        # ----------------------------------------------------
        # GATT database
        # ----------------------------------------------------

        print_services(client)

        await inspect_gatt(client)


        # ----------------------------------------------------
        # Notification test
        # ----------------------------------------------------

        await test_notifications(client)


    except KeyboardInterrupt:

        print()
        print(
            "Inspection stopped by user."
        )


    except Exception as e:

        print()
        print(
            "ERROR:"
        )

        print(
            repr(e)
        )


    finally:

        if client.is_connected:

            print()
            print(
                "Disconnecting from Pluto..."
            )

            try:

                await client.disconnect()

            except Exception as e:

                print(
                    f"Disconnect error: {e}"
                )


        print()
        print(
            "Pluto connection closed."
        )


# ============================================================
# Program
# ============================================================

async def main():

    print()
    separator()
    print("PLUTO BLE GATT INSPECTOR")
    separator()

    print(
        "This program scans for nearby BLE devices,"
    )

    print(
        "connects to the selected device, and"
    )

    print(
        "prints its GATT configuration."
    )

    print()
    print(
        "Known Pluto passkey: 1234"
    )


    devices = await scan_devices()


    device = select_device(
        devices
    )


    if device is None:

        print(
            "No device selected."
        )

        return


    await inspect_pluto(
        device
    )


# ============================================================
# Entry point
# ============================================================

if __name__ == "__main__":

    try:

        asyncio.run(
            main()
        )

    except KeyboardInterrupt:

        print()
        print(
            "Program stopped."
        )

        sys.exit(0)

