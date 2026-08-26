import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import serial
import serial.tools.list_ports
import threading
import queue
from datetime import datetime


class SerialMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("nRF / PLUTO Serial Monitor")
        self.root.geometry("1100x700")
        self.root.minsize(900, 600)

        self.ser = None
        self.reader_thread = None
        self.stop_event = threading.Event()
        self.data_queue = queue.Queue()
        self.log_lines = []
        self.total_bytes = 0
        self.packet_count = 0
        self.start_time = None

        self.port_var = tk.StringVar(value="COM8")
        self.baud_var = tk.StringVar(value="115200")
        self.data_bits_var = tk.StringVar(value="8")
        self.parity_var = tk.StringVar(value="None")
        self.stop_bits_var = tk.StringVar(value="1")
        self.timeout_var = tk.StringVar(value="1")
        self.display_var = tk.StringVar(value="HEX + ASCII")
        self.auto_scroll_var = tk.BooleanVar(value=True)
        self.status_var = tk.StringVar(value="Disconnected")
        self.bytes_var = tk.StringVar(value="0")
        self.packets_var = tk.StringVar(value="0")

        self.build_ui()
        self.refresh_ports()
        self.process_queue()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # ---------------- UI ----------------

    def build_ui(self):
        top = ttk.Frame(self.root, padding=8)
        top.pack(fill="x")

        ttk.Label(top, text="COM Port:").grid(row=0, column=0, sticky="w")
        self.port_combo = ttk.Combobox(
            top, textvariable=self.port_var, width=12, state="readonly"
        )
        self.port_combo.grid(row=0, column=1, padx=5)

        ttk.Button(top, text="Refresh", command=self.refresh_ports).grid(
            row=0, column=2, padx=5
        )

        ttk.Label(top, text="Baud:").grid(row=0, column=3, padx=(15, 0))
        ttk.Combobox(
            top,
            textvariable=self.baud_var,
            values=["9600", "19200", "38400", "57600", "115200", "230400", "460800", "921600"],
            width=10
        ).grid(row=0, column=4, padx=5)

        ttk.Label(top, text="Data:").grid(row=0, column=5, padx=(15, 0))
        ttk.Combobox(
            top, textvariable=self.data_bits_var,
            values=["5", "6", "7", "8"], width=5, state="readonly"
        ).grid(row=0, column=6, padx=5)

        ttk.Label(top, text="Parity:").grid(row=0, column=7, padx=(15, 0))
        ttk.Combobox(
            top, textvariable=self.parity_var,
            values=["None", "Even", "Odd", "Mark", "Space"],
            width=8, state="readonly"
        ).grid(row=0, column=8, padx=5)

        ttk.Label(top, text="Stop:").grid(row=0, column=9, padx=(15, 0))
        ttk.Combobox(
            top, textvariable=self.stop_bits_var,
            values=["1", "1.5", "2"], width=5, state="readonly"
        ).grid(row=0, column=10, padx=5)

        ttk.Label(top, text="Timeout:").grid(row=0, column=11, padx=(15, 0))
        ttk.Entry(top, textvariable=self.timeout_var, width=6).grid(
            row=0, column=12, padx=5
        )

        self.connect_btn = ttk.Button(top, text="Connect", command=self.toggle_connection)
        self.connect_btn.grid(row=0, column=13, padx=(15, 5))

        # Port details
        details = ttk.LabelFrame(self.root, text="Selected Port Details", padding=8)
        details.pack(fill="x", padx=8, pady=(0, 8))

        self.details_text = tk.Text(details, height=4, wrap="word", state="disabled")
        self.details_text.pack(fill="x")

        # Controls
        controls = ttk.Frame(self.root, padding=(8, 0, 8, 8))
        controls.pack(fill="x")

        ttk.Label(controls, text="Display:").pack(side="left")
        ttk.Combobox(
            controls,
            textvariable=self.display_var,
            values=["HEX + ASCII", "HEX only", "ASCII only", "Decimal"],
            state="readonly",
            width=14
        ).pack(side="left", padx=5)

        ttk.Checkbutton(
            controls, text="Auto scroll", variable=self.auto_scroll_var
        ).pack(side="left", padx=15)

        ttk.Button(controls, text="Clear", command=self.clear_output).pack(side="left", padx=5)
        ttk.Button(controls, text="Save Log", command=self.save_log).pack(side="left", padx=5)

        ttk.Label(
            controls, textvariable=self.status_var
        ).pack(side="right", padx=10)

        # Data output
        output_frame = ttk.LabelFrame(self.root, text="Received Data", padding=5)
        output_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self.output = tk.Text(
            output_frame,
            wrap="none",
            font=("Consolas", 10),
            bg="#101010",
            fg="#E8E8E8",
            insertbackground="white"
        )
        self.output.pack(side="left", fill="both", expand=True)

        yscroll = ttk.Scrollbar(output_frame, orient="vertical", command=self.output.yview)
        yscroll.pack(side="right", fill="y")
        self.output.configure(yscrollcommand=yscroll.set)

        xscroll = ttk.Scrollbar(self.root, orient="horizontal", command=self.output.xview)
        xscroll.pack(fill="x", padx=8)
        self.output.configure(xscrollcommand=xscroll.set)

        # Status bar
        status = ttk.Frame(self.root, padding=8)
        status.pack(fill="x")

        ttk.Label(status, text="Packets:").pack(side="left")
        ttk.Label(status, textvariable=self.packets_var).pack(side="left", padx=(4, 20))

        ttk.Label(status, text="Bytes:").pack(side="left")
        ttk.Label(status, textvariable=self.bytes_var).pack(side="left", padx=(4, 20))

        ttk.Label(
            status,
            text="Data shown is raw data received from the selected serial port."
        ).pack(side="right")

        self.port_combo.bind("<<ComboboxSelected>>", self.on_port_selected)

    # ---------------- Port handling ----------------

    def refresh_ports(self):
        ports = list(serial.tools.list_ports.comports())
        values = [p.device for p in ports]

        self.port_combo["values"] = values

        if values:
            if self.port_var.get() not in values:
                self.port_var.set(values[0])
            self.update_port_details()
        else:
            self.port_var.set("")
            self.show_details("No serial ports detected.")

    def on_port_selected(self, _event=None):
        self.update_port_details()

    def update_port_details(self):
        selected = self.port_var.get()
        info = None

        for port in serial.tools.list_ports.comports():
            if port.device == selected:
                info = port
                break

        if not info:
            self.show_details("No information available for this port.")
            return

        lines = [
            f"Port        : {info.device}",
            f"Description : {info.description}",
            f"Manufacturer: {info.manufacturer or 'N/A'}",
            f"Product     : {info.product or 'N/A'}",
            f"VID:PID     : {info.vid if info.vid is not None else 'N/A'}:"
            f"{info.pid if info.pid is not None else 'N/A'}",
            f"Serial      : {info.serial_number or 'N/A'}",
            f"HWID        : {info.hwid}",
            f"Location    : {info.location or 'N/A'}",
        ]
        self.show_details("\n".join(lines))

    def show_details(self, text):
        self.details_text.configure(state="normal")
        self.details_text.delete("1.0", "end")
        self.details_text.insert("1.0", text)
        self.details_text.configure(state="disabled")

    # ---------------- Connection ----------------

    def toggle_connection(self):
        if self.ser and self.ser.is_open:
            self.disconnect()
        else:
            self.connect()

    def connect(self):
        port = self.port_var.get().strip()

        if not port:
            messagebox.showwarning("Serial Monitor", "Select a COM port first.")
            return

        try:
            baud = int(self.baud_var.get())
            timeout = float(self.timeout_var.get())
        except ValueError:
            messagebox.showerror("Serial Monitor", "Invalid baud rate or timeout.")
            return

        data_bits = {
            "5": serial.FIVEBITS,
            "6": serial.SIXBITS,
            "7": serial.SEVENBITS,
            "8": serial.EIGHTBITS,
        }[self.data_bits_var.get()]

        parity = {
            "None": serial.PARITY_NONE,
            "Even": serial.PARITY_EVEN,
            "Odd": serial.PARITY_ODD,
            "Mark": serial.PARITY_MARK,
            "Space": serial.PARITY_SPACE,
        }[self.parity_var.get()]

        stop_bits = {
            "1": serial.STOPBITS_ONE,
            "1.5": serial.STOPBITS_ONE_POINT_FIVE,
            "2": serial.STOPBITS_TWO,
        }[self.stop_bits_var.get()]

        try:
            self.ser = serial.Serial(
                port=port,
                baudrate=baud,
                bytesize=data_bits,
                parity=parity,
                stopbits=stop_bits,
                timeout=timeout
            )
        except serial.SerialException as exc:
            messagebox.showerror(
                "Could not open port",
                f"{port}\n\n{exc}"
            )
            return

        self.stop_event.clear()
        self.total_bytes = 0
        self.packet_count = 0
        self.bytes_var.set("0")
        self.packets_var.set("0")
        self.start_time = datetime.now()

        self.status_var.set(f"Connected: {port}")
        self.connect_btn.configure(text="Disconnect")

        self.append_output(
            f"\n[{datetime.now():%Y-%m-%d %H:%M:%S}] "
            f"CONNECTED TO {port} @ {baud} baud\n"
        )

        self.reader_thread = threading.Thread(
            target=self.read_serial,
            daemon=True
        )
        self.reader_thread.start()

    def disconnect(self):
        self.stop_event.set()

        if self.ser:
            try:
                self.ser.close()
            except Exception:
                pass

        self.ser = None
        self.status_var.set("Disconnected")
        self.connect_btn.configure(text="Connect")

        self.append_output(
            f"\n[{datetime.now():%Y-%m-%d %H:%M:%S}] DISCONNECTED\n"
        )

    # ---------------- Data reading ----------------

    def read_serial(self):
        while not self.stop_event.is_set():

            if not self.ser or not self.ser.is_open:
                break

            try:
                waiting = self.ser.in_waiting
                data = self.ser.read(waiting if waiting else 1)

                if data:
                    self.data_queue.put(data)

            except serial.SerialException as exc:
                self.data_queue.put(("ERROR", str(exc)))
                break

    def process_queue(self):
        try:
            while True:
                item = self.data_queue.get_nowait()

                if isinstance(item, tuple) and item[0] == "ERROR":
                    self.root.after(
                        0,
                        lambda msg=item[1]: messagebox.showerror(
                            "Serial Error", msg
                        )
                    )
                    self.disconnect()
                    continue

                data = item
                self.total_bytes += len(data)
                self.packet_count += 1

                self.bytes_var.set(str(self.total_bytes))
                self.packets_var.set(str(self.packet_count))

                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                mode = self.display_var.get()

                hex_data = " ".join(f"{b:02X}" for b in data)
                ascii_data = "".join(
                    chr(b) if 32 <= b <= 126 else "."
                    for b in data
                )
                decimal_data = " ".join(str(b) for b in data)

                if mode == "HEX + ASCII":
                    line = (
                        f"[{timestamp}] "
                        f"{len(data):4} bytes | "
                        f"HEX: {hex_data} | "
                        f"ASCII: {ascii_data}\n"
                    )
                elif mode == "HEX only":
                    line = (
                        f"[{timestamp}] "
                        f"{len(data):4} bytes | "
                        f"{hex_data}\n"
                    )
                elif mode == "ASCII only":
                    line = (
                        f"[{timestamp}] "
                        f"{len(data):4} bytes | "
                        f"{ascii_data}\n"
                    )
                else:
                    line = (
                        f"[{timestamp}] "
                        f"{len(data):4} bytes | "
                        f"{decimal_data}\n"
                    )

                self.append_output(line)

        except queue.Empty:
            pass

        self.root.after(50, self.process_queue)

    def append_output(self, text):
        self.log_lines.append(text)

        # Prevent unlimited RAM usage during long captures.
        if len(self.log_lines) > 100000:
            self.log_lines = self.log_lines[-50000:]

        self.output.insert("end", text)

        if self.auto_scroll_var.get():
            self.output.see("end")

    # ---------------- Utilities ----------------

    def clear_output(self):
        self.output.delete("1.0", "end")
        self.log_lines.clear()
        self.total_bytes = 0
        self.packet_count = 0
        self.bytes_var.set("0")
        self.packets_var.set("0")

    def save_log(self):
        if not self.log_lines:
            messagebox.showinfo("Save Log", "There is no data to save.")
            return

        path = filedialog.asksaveasfilename(
            title="Save Serial Log",
            defaultextension=".txt",
            filetypes=[
                ("Text files", "*.txt"),
                ("Log files", "*.log"),
                ("All files", "*.*"),
            ]
        )

        if not path:
            return

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("nRF / PLUTO Serial Monitor Log\n")
                f.write("=" * 80 + "\n")
                f.write(f"Port: {self.port_var.get()}\n")
                f.write(f"Baud: {self.baud_var.get()}\n")
                f.write(f"Packets: {self.packet_count}\n")
                f.write(f"Bytes: {self.total_bytes}\n")
                f.write("=" * 80 + "\n\n")
                f.writelines(self.log_lines)

            messagebox.showinfo("Save Log", f"Saved:\n{path}")

        except OSError as exc:
            messagebox.showerror("Save Log", str(exc))

    def on_close(self):
        self.disconnect()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = SerialMonitorApp(root)
    root.mainloop()