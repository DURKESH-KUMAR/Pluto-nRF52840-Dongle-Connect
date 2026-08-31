import serial
import serial.tools.list_ports
import time
import sys
from datetime import datetime


BAUDRATE_DEFAULT = 115200
LOG_FILE = "dongle_log.txt"


# ============================================================
# Display helpers
# ============================================================

def timestamp():
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]


def print_header():
    print()
    print("=" * 70)
    print("           nRF52840 DONGLE / PLUTO MONITOR")
    print("=" * 70)
    print()


def print_status(message):
    print(f"[{timestamp()}] {message}")


# ============================================================
# COM port selection
# ============================================================

def list_ports():

    ports = list(serial.tools.list_ports.comports())

    print()
    print("Available COM ports:")
    print("-" * 70)

    if not ports:
        print("No COM ports found.")
        print()
        return []

    for i, port in enumerate(ports, start=1):

        description = port.description or "Unknown device"

        print(
            f"{i}. {port.device:<10} | {description}"
        )

    print("-" * 70)

    return ports


def choose_port():

    while True:

        ports = list_ports()

        if not ports:

            print(
                "Connect the nRF52840 Dongle and try again."
            )

            time.sleep(2)
            continue

        selection = input(
            "Select COM port number or enter COM name: "
        ).strip()

        # User entered COM8, COM9, etc.
        if selection.upper().startswith("COM"):

            return selection.upper()

        # User entered number
        try:

            number = int(selection)

            if 1 <= number <= len(ports):

                return ports[number - 1].device

        except ValueError:
            pass

        print("Invalid COM port selection.")


# ============================================================
# Log file
# ============================================================

def write_log(line):

    try:

        with open(
            LOG_FILE,
            "a",
            encoding="utf-8"
        ) as f:

            f.write(line + "\n")

    except Exception as e:

        print_status(
            f"Log file error: {e}"
        )


# ============================================================
# Interpret dongle messages
# ============================================================

def interpret_line(line):

    text = line.strip()

    if not text:
        return

    upper = text.upper()

    # --------------------------------------------------------
    # Bluetooth initialization
    # --------------------------------------------------------

    if "BLUETOOTH INITIALIZED" in upper:

        print_status(
            "✓ Bluetooth initialized"
        )

    elif "AUTHENTICATION READY" in upper:

        print_status(
            "✓ Authentication system ready"
        )

    # --------------------------------------------------------
    # Scanning
    # --------------------------------------------------------

    elif "SCANNING FOR PLUTO" in upper:

        print()
        print(
            "=" * 70
        )
        print(
            "[BLE] SCANNING FOR PLUTO"
        )
        print(
            "=" * 70
        )

    elif "SCAN STARTED SUCCESSFULLY" in upper:

        print_status(
            "✓ BLE scanner is running"
        )

    elif "SCANNER ALREADY ACTIVE" in upper:

        print_status(
            "✓ BLE scanner already running"
        )

    elif "SCAN START FAILED" in upper:

        print_status(
            f"✗ {text}"
        )

    # --------------------------------------------------------
    # Pluto discovery
    # --------------------------------------------------------

    elif "PLUTO FOUND" in upper:

        print()
        print(
            "=" * 70
        )
        print(
            "[BLE] ★ PLUTO FOUND ★"
        )
        print(
            "=" * 70
        )

    # --------------------------------------------------------
    # Connection
    # --------------------------------------------------------

    elif "CONNECTION REQUEST SENT" in upper:

        print_status(
            "[BLE] Connecting to Pluto..."
        )

    elif "PLUTO CONNECTED" in upper:

        print()
        print(
            "=" * 70
        )
        print(
            "[BLE] ✓✓ PLUTO CONNECTED ✓✓"
        )
        print(
            "=" * 70
        )

    elif "CONNECTION FAILED" in upper:

        print_status(
            f"[BLE] ✗ {text}"
        )

    # --------------------------------------------------------
    # Security
    # --------------------------------------------------------

    elif "SECURITY REQUEST SENT" in upper:

        print_status(
            "[BLE] Authentication requested"
        )

    elif "PASSKEY REQUESTED" in upper:

        print()
        print(
            "[BLE] Pluto requested passkey"
        )
        print(
            "[BLE] Firmware passkey = 1234"
        )

    elif "SECURITY ESTABLISHED" in upper:

        print_status(
            "[BLE] ✓ Authentication/security established"
        )

    elif "SECURITY FAILED" in upper:

        print_status(
            f"[BLE] ✗ Authentication failed: {text}"
        )

    # --------------------------------------------------------
    # GATT discovery
    # --------------------------------------------------------

    elif "DISCOVERING PLUTO SERVICE" in upper:

        print_status(
            "[GATT] Discovering Pluto service..."
        )

    elif "PLUTO SERVICE FOUND" in upper:

        print_status(
            "[GATT] ✓ Pluto service found"
        )

    elif "DISCOVERING PLUTO DATA CHARACTERISTIC" in upper:

        print_status(
            "[GATT] Discovering data characteristic..."
        )

    elif "DATA VALUE HANDLE" in upper:

        print_status(
            f"[GATT] ✓ {text}"
        )

    elif "DISCOVERING CCC" in upper:

        print_status(
            "[GATT] Discovering CCC descriptor..."
        )

    elif "CCC HANDLE" in upper:

        print_status(
            f"[GATT] ✓ {text}"
        )

    # --------------------------------------------------------
    # Subscription
    # --------------------------------------------------------

    elif "SUBSCRIPTION REQUEST SENT" in upper:

        print_status(
            "[GATT] Subscription request sent"
        )

    elif "SUBSCRIPTION FAILED" in upper:

        print_status(
            f"[GATT] ✗ {text}"
        )

    elif "ALREADY SUBSCRIBED" in upper:

        print_status(
            "[GATT] ✓ Already subscribed"
        )

    elif "PLUTO DATA STREAM ACTIVE" in upper:

        print()
        print(
            "=" * 70
        )
        print(
            "[DATA] ★★★ PLUTO DATA STREAM ACTIVE ★★★"
        )
        print(
            "=" * 70
        )

    # --------------------------------------------------------
    # Data
    # --------------------------------------------------------

    elif upper.startswith("PLUTO_RX"):

        print()
        print(
            f"[{timestamp()}] [DATA] {text}"
        )

    # --------------------------------------------------------
    # Disconnect
    # --------------------------------------------------------

    elif "PLUTO DISCONNECTED" in upper:

        print()
        print(
            "=" * 70
        )
        print(
            "[BLE] !!! PLUTO DISCONNECTED !!!"
        )
        print(
            "=" * 70
        )

    elif "DISCONNECTED" in upper:

        print_status(
            f"[BLE] {text}"
        )

    # --------------------------------------------------------
    # Errors
    # --------------------------------------------------------

    elif (
        "<ERR>" in upper
        or "ERROR" in upper
        or "FAILED" in upper
        or "WARNING" in upper
    ):

        print_status(
            f"[WARNING/ERROR] {text}"
        )

    # --------------------------------------------------------
    # Everything else
    # --------------------------------------------------------

    else:

        print(
            f"[{timestamp()}] {text}"
        )


# ============================================================
# Serial reader
# ============================================================

def read_serial(port, baudrate):

    ser = None

    while True:

        try:

            if ser is None:

                print()
                print("=" * 70)
                print("CONNECTING TO DONGLE")
                print("=" * 70)

                print_status(
                    f"COM Port : {port}"
                )

                print_status(
                    f"Baudrate : {baudrate}"
                )

                ser = serial.Serial(
                    port=port,
                    baudrate=baudrate,
                    timeout=1,
                    write_timeout=1
                )

                print_status(
                    "✓ Serial port opened"
                )

                print()
                print(
                    "Waiting for nRF52840 data..."
                )

                print(
                    "Press Ctrl+C to stop."
                )

                print("=" * 70)

                # Give USB serial a moment
                time.sleep(0.5)

            raw = ser.readline()

            if not raw:

                continue

            try:

                line = raw.decode(
                    "utf-8",
                    errors="replace"
                ).rstrip()

            except Exception:

                line = repr(raw)

            if not line:
                continue

            # Save original dongle output
            log_line = (
                f"[{timestamp()}] {line}"
            )

            write_log(log_line)

            interpret_line(line)

        except serial.SerialException as e:

            print()
            print("=" * 70)
            print("SERIAL CONNECTION LOST")
            print("=" * 70)

            print_status(
                str(e)
            )

            if ser is not None:

                try:
                    ser.close()
                except Exception:
                    pass

            ser = None

            print_status(
                "Waiting for dongle..."
            )

            time.sleep(2)

        except KeyboardInterrupt:

            print()
            print("=" * 70)
            print("STOPPED BY USER")
            print("=" * 70)

            if ser is not None:

                try:
                    ser.close()
                except Exception:
                    pass

            break

        except Exception as e:

            print_status(
                f"Reader error: {e}"
            )

            time.sleep(1)


# ============================================================
# Main
# ============================================================

def main():

    print_header()

    print(
        "Log file:"
    )

    print(
        LOG_FILE
    )

    print()

    port = choose_port()

    baud_input = input(
        "Enter baudrate [115200]: "
    ).strip()

    if baud_input:

        try:

            baudrate = int(
                baud_input
            )

        except ValueError:

            print(
                "Invalid baudrate. Using 115200."
            )

            baudrate = BAUDRATE_DEFAULT

    else:

        baudrate = BAUDRATE_DEFAULT


    print()

    print("=" * 70)
    print("nRF52840 DONGLE / PLUTO SERIAL MONITOR")
    print("=" * 70)

    print(
        f"COM Port : {port}"
    )

    print(
        f"Baudrate : {baudrate}"
    )

    print(
        f"Log     : {LOG_FILE}"
    )

    print("=" * 70)


    read_serial(
        port,
        baudrate
    )


if __name__ == "__main__":

    main()

