import asyncio
from bleak import BleakScanner, BleakClient


async def scan_devices():

    print("=" * 90)
    print("BLUETOOTH / BLE DEVICE SCANNER")
    print("=" * 90)

    discovered = await BleakScanner.discover(
        timeout=10,
        return_adv=True
    )

    devices = []

    for index, (device, adv) in enumerate(discovered.values()):

        devices.append((device, adv))

        print("\n" + "-" * 90)

        print(f"[{index}]")

        # Bluetooth address
        print(f"Bluetooth Address       : {device.address}")

        # BLE name reported by OS
        print(f"BLE Device Name         : {device.name}")

        # Name contained in BLE advertisement
        print(f"BLE Advertised Name     : {adv.local_name}")

        # Some platforms expose a separate display name
        if hasattr(device, "details"):
            print(f"Bluetooth OS Details    : {device.details}")

        # RSSI
        print(f"Signal Strength (RSSI)  : {adv.rssi} dBm")

        # Advertised services
        print("\nAdvertised Service UUIDs:")

        if adv.service_uuids:
            for uuid in adv.service_uuids:
                print(f"    {uuid}")
        else:
            print("    None")

        # Manufacturer information
        print("\nManufacturer Data:")

        if adv.manufacturer_data:

            for company_id, data in adv.manufacturer_data.items():

                print(f"    Company ID : 0x{company_id:04X}")
                print(f"    Raw Data   : {data.hex(' ')}")

        else:
            print("    None")

        # Service data
        print("\nService Data:")

        if adv.service_data:

            for uuid, data in adv.service_data.items():

                print(f"    UUID : {uuid}")
                print(f"    Data : {data.hex(' ')}")

        else:
            print("    None")

    return devices


async def inspect_device(device, adv):

    print("\n")
    print("=" * 90)
    print("CONNECTING TO DEVICE")
    print("=" * 90)

    print(f"Bluetooth Address   : {device.address}")
    print(f"BLE Device Name     : {device.name}")
    print(f"Advertised Name     : {adv.local_name}")

    try:

        async with BleakClient(device) as client:

            print("\nCONNECTED")
            print(f"Connection Status   : {client.is_connected}")

            print("\n" + "=" * 90)
            print("DEVICE INFORMATION")
            print("=" * 90)

            # Try Device Information Service
            device_info_found = False

            for service in client.services:

                # Standard Device Information Service
                if service.uuid.lower() == "0000180a-0000-1000-8000-00805f9b34fb":

                    device_info_found = True

                    print("\nDevice Information Service found!")

                    for char in service.characteristics:

                        print(f"\nCharacteristic UUID : {char.uuid}")
                        print(f"Properties          : {char.properties}")

                        if "read" in char.properties:

                            try:

                                value = await client.read_gatt_char(
                                    char.uuid
                                )

                                try:
                                    text = value.decode(
                                        "utf-8",
                                        errors="replace"
                                    )
                                except:
                                    text = str(value)

                                print(f"Value               : {text}")
                                print(f"Raw                 : {value.hex(' ')}")

                            except Exception as e:

                                print(f"Read failed         : {e}")

            if not device_info_found:

                print(
                    "\nStandard Device Information Service "
                    "was not found."
                )

            print("\n" + "=" * 90)
            print("ALL GATT SERVICES")
            print("=" * 90)

            for service in client.services:

                print("\nSERVICE")
                print(f"UUID        : {service.uuid}")
                print(f"Description : {service.description}")

                for char in service.characteristics:

                    print("\n  CHARACTERISTIC")

                    print(f"    UUID        : {char.uuid}")
                    print(f"    Description : {char.description}")
                    print(
                        f"    Properties  : "
                        f"{', '.join(char.properties)}"
                    )

                    for descriptor in char.descriptors:

                        print(
                            f"      Descriptor: "
                            f"{descriptor.uuid}"
                        )

            print("\n" + "=" * 90)
            print("INSPECTION COMPLETE")
            print("=" * 90)

    except Exception as e:

        print("\nCONNECTION ERROR")
        print(f"{type(e).__name__}: {e}")


async def main():

    devices = await scan_devices()

    if not devices:

        print("\nNo Bluetooth/BLE devices found.")
        return

    print("\n" + "=" * 90)

    choice = input("Enter device number to inspect: ")

    try:

        index = int(choice)

        device, adv = devices[index]

    except (ValueError, IndexError):

        print("Invalid selection.")
        return

    await inspect_device(device, adv)


asyncio.run(main())