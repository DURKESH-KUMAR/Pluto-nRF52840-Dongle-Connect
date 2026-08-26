# Pluto nRF52840 Dongle Connect

A Bluetooth Low Energy (BLE) communication and device-management project built around the **Nordic nRF52840 Dongle** and designed for integration with the **Pluto** platform.

The project combines **Zephyr-based nRF52840 firmware** with **Python-based desktop tools** for BLE discovery, connection, communication, and Pluto device information.

---

## Overview

**Pluto nRF52840 Dongle Connect** provides a development framework for connecting a computer to BLE devices through an nRF52840 Dongle.

The project consists of two main components:

* **nRF52840 firmware** — BLE Central/Observer firmware running on the dongle.
* **Python desktop utilities** — tools for scanning BLE devices, connecting to devices, exchanging data, and displaying Pluto information through a graphical interface.

The repository is intended for development, testing, debugging, and future expansion of BLE connectivity for the Pluto platform.

---

## Features

### nRF52840 Firmware

* Bluetooth Low Energy support
* BLE Central role
* BLE Observer role
* GATT Client support
* Bluetooth Security Manager Protocol (SMP)
* Single BLE connection configuration
* Logging and diagnostic output
* Zephyr RTOS based firmware
* nRF52840 Dongle target

### Python Tools

* BLE device discovery
* BLE device information display
* BLE connection handling
* Device communication
* Pluto device information
* Desktop graphical interface
* Connection status monitoring
* Diagnostic information

---

## Project Architecture

```text
                    ┌──────────────────────────┐
                    │        PC / Laptop       │
                    │                          │
                    │      Python Tools        │
                    │  ┌────────────────────┐  │
                    │  │ BLE Scanner        │  │
                    │  │ Device Information │  │
                    │  │ Pluto UI           │  │
                    │  └────────────────────┘  │
                    └────────────┬─────────────┘
                                 │
                              USB / BLE
                                 │
                    ┌────────────▼─────────────┐
                    │     nRF52840 Dongle      │
                    │                          │
                    │    Zephyr Firmware       │
                    │                          │
                    │  ┌────────────────────┐  │
                    │  │ BLE Central        │  │
                    │  │ BLE Observer       │  │
                    │  │ GATT Client        │  │
                    │  │ Security / SMP     │  │
                    │  └────────────────────┘  │
                    └────────────┬─────────────┘
                                 │
                                 │ Bluetooth LE
                                 │
                    ┌────────────▼─────────────┐
                    │      Pluto / BLE Device  │
                    │                          │
                    │   BLE Services / Data    │
                    └──────────────────────────┘
```

---

## Repository Structure

```text
Pluto-nRF52840-Dongle-Connect/
│
├── Python/
│   ├── main.py
│   ├── pluto_info.py
│   └── pluto_info_UI.py
│
├── src/
│   └── main.c
│
├── build/
│   └── Build output
│
├── CMakeLists.txt
├── prj.conf
├── .gitignore
├── .gitattributes
└── README.md
```

### `src/`

Contains the nRF52840 firmware source code.

```text
src/
└── main.c
```

`main.c` contains the embedded application logic running on the nRF52840.

### `prj.conf`

Contains the Zephyr configuration for the application.

The current configuration enables:

```text
CONFIG_BT=y
CONFIG_BT_CENTRAL=y
CONFIG_BT_OBSERVER=y
CONFIG_BT_GATT_CLIENT=y
CONFIG_BT_SMP=y
CONFIG_BT_MAX_CONN=1
```

This configures the dongle primarily as a BLE Central/Observer with GATT Client functionality.

### `Python/`

Contains the PC-side Python applications.

```text
Python/
├── main.py
├── pluto_info.py
└── pluto_info_UI.py
```

These scripts provide the desktop-side BLE and Pluto interaction layer.

---

# Requirements

## Hardware

* nRF52840 Dongle
* Windows PC recommended for the current development workflow
* USB connection to the nRF52840 Dongle
* BLE-compatible target device / Pluto device

---

## Software

### Embedded Development

Install:

* Nordic nRF Connect SDK
* Zephyr / `west`
* Python
* CMake
* Ninja
* Required Nordic toolchain

The project uses a Zephyr-style application structure with `CMakeLists.txt`, `prj.conf`, and `src/main.c`.

### Python

Install Python 3.x.

The Python tools use BLE functionality and may require the following package:

```bash
pip install bleak
```

If additional Python dependencies are introduced later, install them using the project's requirements file when available.

---

# Getting the Repository

Clone the repository:

```bash
git clone https://github.com/DURKESH-KUMAR/Pluto-nRF52840-Dongle-Connect.git
```

Enter the project directory:

```bash
cd Pluto-nRF52840-Dongle-Connect
```

---

# Building the nRF52840 Firmware

Make sure the Nordic toolchain and `west` are available in your terminal.

From the project root:

```bash
west build -b nrf52840dongle/nrf52840
```

For a clean rebuild:

```bash
west build -b nrf52840dongle/nrf52840 --pristine
```

The build output will normally be generated inside:

```text
build/
```

The generated firmware files can be found under the build directory after a successful compilation.

---

# Flashing the nRF52840 Dongle

Connect the nRF52840 Dongle to the PC.

The firmware can be programmed using Nordic's supported programming tools.

A typical workflow is:

```text
Build firmware
      │
      ▼
Generate firmware image
      │
      ▼
Connect nRF52840 Dongle
      │
      ▼
Enter programming / DFU mode
      │
      ▼
Program firmware
      │
      ▼
Reset Dongle
      │
      ▼
Start BLE application
```

After programming, reconnect the dongle and verify the firmware output through the appropriate logging/console interface.

---

# Running the Python Application

Move into the Python directory:

```bash
cd Python
```

Run the main application:

```bash
python main.py
```

For the Pluto information utility:

```bash
python pluto_info.py
```

For the graphical Pluto information interface:

```bash
python pluto_info_UI.py
```

> The exact Python entry point may change as the desktop application develops. Keep the Python utilities synchronized with the firmware's BLE service and communication protocol.

---

# BLE Communication Flow

The expected communication flow is:

```text
PC
 │
 │
 ▼
Python Application
 │
 │ BLE discovery / communication
 ▼
nRF52840 Dongle
 │
 │ BLE Central
 ▼
Pluto BLE Device
 │
 ├── Service Discovery
 │
 ├── Characteristic Discovery
 │
 ├── Read
 │
 ├── Write
 │
 └── Notifications
```

The nRF52840 firmware is configured for BLE Central, Observer, and GATT Client functionality.

---

# Development Workflow

A typical development workflow is:

### 1. Modify firmware

Edit:

```text
src/main.c
```

### 2. Modify Bluetooth configuration

Edit:

```text
prj.conf
```

### 3. Build

```bash
west build -b nrf52840dongle/nrf52840 --pristine
```

### 4. Flash

Program the generated firmware onto the nRF52840 Dongle.

### 5. Test BLE communication

Run the Python tools:

```bash
cd Python
python main.py
```

### 6. Debug

Check:

* BLE advertisement
* Device discovery
* Connection status
* GATT service discovery
* Characteristic discovery
* Read/write operations
* Notifications
* Serial/log output

---

# Troubleshooting

## Build directory does not contain the expected firmware

First perform a clean build:

```bash
west build -b nrf52840dongle/nrf52840 --pristine
```

Then check:

```text
build/
```

If the build fails, inspect the terminal output from the `west build` command.

---

## nRF52840 Dongle is not detected

Check:

* USB connection
* Dongle programming/DFU mode
* USB drivers
* Nordic programming tools
* Windows Device Manager
* Whether another application is using the device

Try disconnecting and reconnecting the dongle.

---

## BLE device is not discovered

Check:

* Target device is powered on
* Target device is advertising
* BLE is enabled
* Device is within range
* Correct BLE role is being used
* nRF52840 firmware is running correctly

The firmware uses the BLE Observer and Central roles.

---

## Python application cannot find BLE devices

Verify the Python environment:

```bash
python --version
```

Install/update the BLE library:

```bash
pip install bleak
```

Then run:

```bash
python main.py
```

---

# Configuration

Bluetooth configuration is primarily controlled through:

```text
prj.conf
```

Current important settings include:

| Configuration           | Purpose                           |
| ----------------------- | --------------------------------- |
| `CONFIG_BT`             | Enables Bluetooth                 |
| `CONFIG_BT_CENTRAL`     | Enables BLE Central role          |
| `CONFIG_BT_OBSERVER`    | Enables BLE scanning/observation  |
| `CONFIG_BT_GATT_CLIENT` | Enables GATT Client functionality |
| `CONFIG_BT_SMP`         | Enables Bluetooth security        |
| `CONFIG_BT_MAX_CONN=1`  | Allows one BLE connection         |
| `CONFIG_LOG`            | Enables logging                   |
| `CONFIG_PRINTK`         | Enables printk output             |

These settings are present in the current project configuration.

---

# Future Development

Potential improvements include:

* Multiple simultaneous BLE connections
* Automatic Pluto device detection
* Improved GATT service discovery
* Automatic characteristic mapping
* Firmware version detection
* Device configuration
* OTA firmware update support
* Connection recovery
* BLE connection history
* Improved desktop UI
* Device diagnostics
* Logging/export functionality
* Automated firmware flashing
* Production test functionality

---

# Technology Stack

| Component          | Technology           |
| ------------------ | -------------------- |
| MCU                | Nordic nRF52840      |
| RTOS               | Zephyr               |
| Embedded Language  | C                    |
| BLE                | Bluetooth Low Energy |
| BLE Role           | Central / Observer   |
| GATT               | GATT Client          |
| Security           | Bluetooth SMP        |
| PC Application     | Python               |
| BLE Python Library | Bleak                |
| Build System       | CMake / west         |
| Build Tool         | Ninja                |
| Source Control     | Git / GitHub         |

The nRF52840 Dongle is supported as a target in Nordic's nRF Connect SDK ecosystem, including Bluetooth-related applications.

---

# Project Status

**Development / Experimental**

This repository is actively being developed for Pluto BLE connectivity and nRF52840 Dongle integration.

Interfaces, BLE services, Python utilities, and firmware behavior may change as development continues.

---

# Contributing

Contributions, bug reports, and development suggestions are welcome.

Before submitting changes:

1. Test the firmware build.
2. Test BLE discovery and connection.
3. Verify Python functionality.
4. Avoid committing generated build artifacts where possible.
5. Provide a clear commit message.
6. Document significant protocol or configuration changes.

---

# License

License information will be added when the project license is finalized.

---

# Author

**Durkesh Kumar**

GitHub:

`DURKESH-KUMAR`

Repository:

`Pluto-nRF52840-Dongle-Connect`

---

## Repository

[Pluto-nRF52840-Dongle-Connect on GitHub](https://github.com/DURKESH-KUMAR/Pluto-nRF52840-Dongle-Connect?utm_source=chatgpt.com)

---

## Disclaimer

This project is intended for development, testing, and integration purposes.

Always verify firmware behavior and BLE communication on the intended hardware before using the software in a production environment.
