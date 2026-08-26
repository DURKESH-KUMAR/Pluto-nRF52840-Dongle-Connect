import asyncio
import threading
import queue
import tkinter as tk
from tkinter import ttk, messagebox
from bleak import BleakScanner, BleakClient


# ============================================================
# APPLICATION CONFIGURATION
# ============================================================

APP_TITLE = "BLE Command Center"
APP_VERSION = "1.0.0"

BG = "#0B1120"
SIDEBAR_BG = "#111827"
PANEL_BG = "#151E2E"
CARD_BG = "#1B2638"
CARD_HOVER = "#243249"

TEXT = "#E5E7EB"
TEXT_SECONDARY = "#94A3B8"
TEXT_MUTED = "#64748B"

ACCENT = "#38BDF8"
ACCENT_DARK = "#0284C7"

SUCCESS = "#22C55E"
WARNING = "#F59E0B"
ERROR = "#EF4444"

BORDER = "#263449"

FONT = "Segoe UI"


# ============================================================
# MAIN APPLICATION
# ============================================================

class BLECommandCenter:

    def __init__(self, root):

        self.root = root

        self.root.title(
            f"{APP_TITLE}  v{APP_VERSION}"
        )

        self.root.geometry(
            "1500x900"
        )

        self.root.minsize(
            1200,
            700
        )

        self.root.configure(
            bg=BG
        )

        # ----------------------------------------------------
        # Runtime state
        # ----------------------------------------------------

        self.devices = []

        self.selected_device = None
        self.selected_adv = None

        self.client = None

        self.connected = False

        self.scan_thread = None
        self.inspect_thread = None

        self.event_queue = queue.Queue()

        self.current_service_item = None
        self.current_characteristic_item = None

        # ----------------------------------------------------
        # Variables
        # ----------------------------------------------------

        self.status_var = tk.StringVar(
            value="Ready"
        )

        self.device_count_var = tk.StringVar(
            value="0 Devices"
        )

        self.connection_var = tk.StringVar(
            value="DISCONNECTED"
        )

        self.device_name_var = tk.StringVar(
            value="No device selected"
        )

        self.device_address_var = tk.StringVar(
            value="—"
        )

        self.device_rssi_var = tk.StringVar(
            value="—"
        )

        self.device_services_var = tk.StringVar(
            value="—"
        )

        self.search_var = tk.StringVar()

        # ----------------------------------------------------
        # Build UI
        # ----------------------------------------------------

        self.configure_styles()

        self.create_main_layout()

        self.create_sidebar()

        self.create_header()

        self.create_device_area()

        self.create_bottom_area()

        self.create_status_bar()

        # ----------------------------------------------------
        # Events
        # ----------------------------------------------------

        self.search_var.trace_add(
            "write",
            lambda *args: self.filter_devices()
        )

        self.root.after(
            100,
            self.process_queue
        )

        self.root.protocol(
            "WM_DELETE_WINDOW",
            self.close_application
        )

    # ========================================================
    # STYLE
    # ========================================================

    def configure_styles(self):

        style = ttk.Style()

        try:
            style.theme_use(
                "clam"
            )
        except:
            pass

        style.configure(
            "Treeview",
            background=PANEL_BG,
            foreground=TEXT,
            fieldbackground=PANEL_BG,
            borderwidth=0,
            rowheight=34,
            font=(FONT, 9)
        )

        style.configure(
            "Treeview.Heading",
            background=CARD_BG,
            foreground=TEXT_SECONDARY,
            relief="flat",
            borderwidth=0,
            font=(FONT, 9, "bold")
        )

        style.map(
            "Treeview",
            background=[
                ("selected", "#164E63")
            ],
            foreground=[
                ("selected", "#FFFFFF")
            ]
        )

        style.configure(
            "Vertical.TScrollbar",
            background=PANEL_BG,
            troughcolor=BG,
            borderwidth=0
        )

        style.configure(
            "Horizontal.TScrollbar",
            background=PANEL_BG,
            troughcolor=BG,
            borderwidth=0
        )

    # ========================================================
    # MAIN LAYOUT
    # ========================================================

    def create_main_layout(self):

        self.main_container = tk.Frame(
            self.root,
            bg=BG
        )

        self.main_container.pack(
            fill="both",
            expand=True
        )

    # ========================================================
    # SIDEBAR
    # ========================================================

    def create_sidebar(self):

        self.sidebar = tk.Frame(
            self.main_container,
            bg=SIDEBAR_BG,
            width=230
        )

        self.sidebar.pack(
            side="left",
            fill="y"
        )

        self.sidebar.pack_propagate(
            False
        )

        # ----------------------------------------------------
        # Logo
        # ----------------------------------------------------

        logo_frame = tk.Frame(
            self.sidebar,
            bg=SIDEBAR_BG
        )

        logo_frame.pack(
            fill="x",
            padx=20,
            pady=(25, 30)
        )

        logo_icon = tk.Label(
            logo_frame,
            text="◉",
            font=(FONT, 25, "bold"),
            fg=ACCENT,
            bg=SIDEBAR_BG
        )

        logo_icon.pack(
            side="left"
        )

        logo_text = tk.Label(
            logo_frame,
            text="BLE\nCOMMAND",
            justify="left",
            font=(FONT, 12, "bold"),
            fg=TEXT,
            bg=SIDEBAR_BG
        )

        logo_text.pack(
            side="left",
            padx=10
        )

        # ----------------------------------------------------
        # Navigation
        # ----------------------------------------------------

        self.create_sidebar_button(
            "⌕",
            "Device Scanner",
            self.show_scanner
        )

        self.create_sidebar_button(
            "⌘",
            "GATT Explorer",
            self.show_gatt
        )

        self.create_sidebar_button(
            "▣",
            "Advertisement",
            self.show_advertisement
        )

        self.create_sidebar_button(
            "≡",
            "Activity Log",
            self.show_log
        )

        # ----------------------------------------------------
        # Spacer
        # ----------------------------------------------------

        tk.Frame(
            self.sidebar,
            bg=SIDEBAR_BG
        ).pack(
            fill="both",
            expand=True
        )

        # ----------------------------------------------------
        # Version
        # ----------------------------------------------------

        tk.Label(
            self.sidebar,
            text="BLE ENGINEERING TOOL\nBleak / Python",
            justify="left",
            font=(FONT, 8),
            fg=TEXT_MUTED,
            bg=SIDEBAR_BG
        ).pack(
            anchor="w",
            padx=20,
            pady=20
        )

    def create_sidebar_button(
        self,
        icon,
        text,
        command
    ):

        button = tk.Button(
            self.sidebar,
            text=f"  {icon}    {text}",
            command=command,
            anchor="w",
            relief="flat",
            bd=0,
            padx=20,
            pady=12,
            font=(FONT, 10),
            fg=TEXT_SECONDARY,
            bg=SIDEBAR_BG,
            activeforeground=TEXT,
            activebackground=CARD_BG,
            cursor="hand2"
        )

        button.pack(
            fill="x",
            padx=10,
            pady=2
        )

    # ========================================================
    # HEADER
    # ========================================================

    def create_header(self):

        self.content = tk.Frame(
            self.main_container,
            bg=BG
        )

        self.content.pack(
            side="left",
            fill="both",
            expand=True
        )

        header = tk.Frame(
            self.content,
            bg=BG,
            height=75
        )

        header.pack(
            fill="x"
        )

        header.pack_propagate(
            False
        )

        title_frame = tk.Frame(
            header,
            bg=BG
        )

        title_frame.pack(
            side="left",
            padx=25
        )

        tk.Label(
            title_frame,
            text="Bluetooth / BLE Inspector",
            font=(FONT, 20, "bold"),
            fg=TEXT,
            bg=BG
        ).pack(
            anchor="w",
            pady=(12, 0)
        )

        tk.Label(
            title_frame,
            text="Discover • Connect • Inspect • Debug",
            font=(FONT, 9),
            fg=TEXT_SECONDARY,
            bg=BG
        ).pack(
            anchor="w"
        )

        # ----------------------------------------------------
        # Connection indicator
        # ----------------------------------------------------

        connection_frame = tk.Frame(
            header,
            bg=CARD_BG
        )

        connection_frame.pack(
            side="right",
            padx=25,
            pady=17
        )

        self.connection_dot = tk.Label(
            connection_frame,
            text="●",
            font=(FONT, 11),
            fg=TEXT_MUTED,
            bg=CARD_BG
        )

        self.connection_dot.pack(
            side="left",
            padx=(12, 5)
        )

        self.connection_label = tk.Label(
            connection_frame,
            textvariable=self.connection_var,
            font=(FONT, 9, "bold"),
            fg=TEXT_SECONDARY,
            bg=CARD_BG
        )

        self.connection_label.pack(
            side="left",
            padx=(0, 12),
            pady=8
        )

    # ========================================================
    # DEVICE AREA
    # ========================================================

    def create_device_area(self):

        self.device_section = tk.Frame(
            self.content,
            bg=BG
        )

        self.device_section.pack(
            fill="both",
            expand=True,
            padx=25
        )

        # ----------------------------------------------------
        # Toolbar
        # ----------------------------------------------------

        toolbar = tk.Frame(
            self.device_section,
            bg=BG
        )

        toolbar.pack(
            fill="x",
            pady=(0, 10)
        )

        # Scan button

        self.scan_button = tk.Button(
            toolbar,
            text="  🔍  Scan Devices",
            command=self.start_scan,
            relief="flat",
            bd=0,
            bg=ACCENT_DARK,
            fg="white",
            activebackground=ACCENT,
            activeforeground="white",
            font=(FONT, 10, "bold"),
            padx=15,
            pady=9,
            cursor="hand2"
        )

        self.scan_button.pack(
            side="left"
        )

        # Connect button

        self.connect_button = tk.Button(
            toolbar,
            text="  🔗  Connect & Inspect",
            command=self.start_inspection,
            relief="flat",
            bd=0,
            bg=CARD_BG,
            fg=TEXT_SECONDARY,
            activebackground=CARD_HOVER,
            activeforeground=TEXT,
            font=(FONT, 10),
            padx=15,
            pady=9,
            state="disabled",
            cursor="hand2"
        )

        self.connect_button.pack(
            side="left",
            padx=8
        )

        # Disconnect

        self.disconnect_button = tk.Button(
            toolbar,
            text="  Disconnect",
            command=self.disconnect_device,
            relief="flat",
            bd=0,
            bg=CARD_BG,
            fg=ERROR,
            activebackground=CARD_HOVER,
            font=(FONT, 10),
            padx=15,
            pady=9,
            state="disabled",
            cursor="hand2"
        )

        self.disconnect_button.pack(
            side="left"
        )

        # ----------------------------------------------------
        # Search
        # ----------------------------------------------------

        search_frame = tk.Frame(
            toolbar,
            bg=CARD_BG
        )

        search_frame.pack(
            side="right"
        )

        tk.Label(
            search_frame,
            text="⌕",
            font=(FONT, 14),
            fg=TEXT_MUTED,
            bg=CARD_BG
        ).pack(
            side="left",
            padx=(10, 3)
        )

        self.search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            width=25,
            relief="flat",
            bd=0,
            bg=CARD_BG,
            fg=TEXT,
            insertbackground=TEXT,
            font=(FONT, 9)
        )

        self.search_entry.pack(
            side="left",
            padx=5,
            pady=8
        )

        # ----------------------------------------------------
        # Device count
        # ----------------------------------------------------

        tk.Label(
            toolbar,
            textvariable=self.device_count_var,
            font=(FONT, 9),
            fg=TEXT_SECONDARY,
            bg=BG
        ).pack(
            side="right",
            padx=15
        )

        # ----------------------------------------------------
        # Device table card
        # ----------------------------------------------------

        table_card = tk.Frame(
            self.device_section,
            bg=PANEL_BG
        )

        table_card.pack(
            fill="both",
            expand=True
        )

        columns = (
            "index",
            "name",
            "address",
            "advertised",
            "rssi",
            "services",
            "manufacturer"
        )

        self.device_tree = ttk.Treeview(
            table_card,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        headings = {
            "index": "#",
            "name": "DEVICE",
            "address": "BLUETOOTH ADDRESS",
            "advertised": "ADVERTISEMENT",
            "rssi": "RSSI",
            "services": "SERVICES",
            "manufacturer": "MANUFACTURER"
        }

        for column, heading in headings.items():

            self.device_tree.heading(
                column,
                text=heading
            )

        widths = {
            "index": 45,
            "name": 190,
            "address": 190,
            "advertised": 190,
            "rssi": 90,
            "services": 300,
            "manufacturer": 150
        }

        for column, width in widths.items():

            self.device_tree.column(
                column,
                width=width,
                minwidth=50
            )

        scrollbar = ttk.Scrollbar(
            table_card,
            orient="vertical",
            command=self.device_tree.yview
        )

        self.device_tree.configure(
            yscrollcommand=scrollbar.set
        )

        self.device_tree.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        self.device_tree.bind(
            "<<TreeviewSelect>>",
            self.device_selected
        )

        self.device_tree.bind(
            "<Double-1>",
            lambda e: self.start_inspection()
        )

    # ========================================================
    # BOTTOM AREA
    # ========================================================

    def create_bottom_area(self):

        bottom = tk.Frame(
            self.content,
            bg=BG,
            height=300
        )

        bottom.pack(
            fill="x",
            padx=25,
            pady=(10, 0)
        )

        bottom.pack_propagate(
            False
        )

        # ----------------------------------------------------
        # Device summary
        # ----------------------------------------------------

        self.summary_card = tk.Frame(
            bottom,
            bg=CARD_BG,
            width=330
        )

        self.summary_card.pack(
            side="left",
            fill="y",
            padx=(0, 10)
        )

        self.summary_card.pack_propagate(
            False
        )

        tk.Label(
            self.summary_card,
            text="SELECTED DEVICE",
            font=(FONT, 8, "bold"),
            fg=TEXT_MUTED,
            bg=CARD_BG
        ).pack(
            anchor="w",
            padx=18,
            pady=(18, 4)
        )

        tk.Label(
            self.summary_card,
            textvariable=self.device_name_var,
            font=(FONT, 15, "bold"),
            fg=TEXT,
            bg=CARD_BG
        ).pack(
            anchor="w",
            padx=18
        )

        self.create_summary_row(
            "Address",
            self.device_address_var
        )

        self.create_summary_row(
            "RSSI",
            self.device_rssi_var
        )

        self.create_summary_row(
            "Services",
            self.device_services_var
        )

        # ----------------------------------------------------
        # Notebook
        # ----------------------------------------------------

        self.notebook = ttk.Notebook(
            bottom
        )

        self.notebook.pack(
            side="left",
            fill="both",
            expand=True
        )

        # Advertisement

        self.advertisement_tab = tk.Frame(
            self.notebook,
            bg=PANEL_BG
        )

        self.notebook.add(
            self.advertisement_tab,
            text="  Advertisement  "
        )

        self.create_advertisement_panel()

        # GATT

        self.gatt_tab = tk.Frame(
            self.notebook,
            bg=PANEL_BG
        )

        self.notebook.add(
            self.gatt_tab,
            text="  GATT Explorer  "
        )

        self.create_gatt_panel()

        # Log

        self.log_tab = tk.Frame(
            self.notebook,
            bg=PANEL_BG
        )

        self.notebook.add(
            self.log_tab,
            text="  Activity Log  "
        )

        self.create_log_panel()

    # ========================================================
    # SUMMARY ROW
    # ========================================================

    def create_summary_row(
        self,
        label,
        variable
    ):

        frame = tk.Frame(
            self.summary_card,
            bg=CARD_BG
        )

        frame.pack(
            fill="x",
            padx=18,
            pady=7
        )

        tk.Label(
            frame,
            text=label,
            font=(FONT, 8),
            fg=TEXT_MUTED,
            bg=CARD_BG
        ).pack(
            anchor="w"
        )

        tk.Label(
            frame,
            textvariable=variable,
            font=(FONT, 9),
            fg=TEXT_SECONDARY,
            bg=CARD_BG
        ).pack(
            anchor="w"
        )

    # ========================================================
    # ADVERTISEMENT PANEL
    # ========================================================

    def create_advertisement_panel(self):

        self.advertisement_text = tk.Text(
            self.advertisement_tab,
            bg=PANEL_BG,
            fg=TEXT,
            insertbackground=TEXT,
            selectbackground="#164E63",
            relief="flat",
            bd=0,
            font=("Consolas", 9),
            wrap="none"
        )

        scrollbar = ttk.Scrollbar(
            self.advertisement_tab,
            orient="vertical",
            command=self.advertisement_text.yview
        )

        self.advertisement_text.configure(
            yscrollcommand=scrollbar.set
        )

        self.advertisement_text.pack(
            side="left",
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

    # ========================================================
    # GATT PANEL
    # ========================================================

    def create_gatt_panel(self):

        self.gatt_tree = ttk.Treeview(
            self.gatt_tab,
            columns=(
                "type",
                "uuid",
                "description",
                "properties",
                "value"
            ),
            show="tree headings"
        )

        self.gatt_tree.heading(
            "#0",
            text="GATT STRUCTURE"
        )

        self.gatt_tree.heading(
            "type",
            text="TYPE"
        )

        self.gatt_tree.heading(
            "uuid",
            text="UUID"
        )

        self.gatt_tree.heading(
            "description",
            text="DESCRIPTION"
        )

        self.gatt_tree.heading(
            "properties",
            text="PROPERTIES"
        )

        self.gatt_tree.heading(
            "value",
            text="VALUE"
        )

        self.gatt_tree.column(
            "#0",
            width=210
        )

        self.gatt_tree.column(
            "type",
            width=110
        )

        self.gatt_tree.column(
            "uuid",
            width=280
        )

        self.gatt_tree.column(
            "description",
            width=220
        )

        self.gatt_tree.column(
            "properties",
            width=200
        )

        self.gatt_tree.column(
            "value",
            width=300
        )

        scrollbar = ttk.Scrollbar(
            self.gatt_tab,
            orient="vertical",
            command=self.gatt_tree.yview
        )

        self.gatt_tree.configure(
            yscrollcommand=scrollbar.set
        )

        self.gatt_tree.pack(
            side="left",
            fill="both",
            expand=True,
            padx=5,
            pady=5
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        self.gatt_tree.bind(
            "<Double-1>",
            self.gatt_double_click
        )

    # ========================================================
    # LOG PANEL
    # ========================================================

    def create_log_panel(self):

        self.log_text = tk.Text(
            self.log_tab,
            bg="#080D17",
            fg="#9FE7FF",
            insertbackground=TEXT,
            relief="flat",
            bd=0,
            font=("Consolas", 9),
            wrap="none"
        )

        scrollbar = ttk.Scrollbar(
            self.log_tab,
            orient="vertical",
            command=self.log_text.yview
        )

        self.log_text.configure(
            yscrollcommand=scrollbar.set
        )

        self.log_text.pack(
            side="left",
            fill="both",
            expand=True,
            padx=8,
            pady=8
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

    # ========================================================
    # STATUS BAR
    # ========================================================

    def create_status_bar(self):

        status = tk.Frame(
            self.content,
            bg=SIDEBAR_BG,
            height=30
        )

        status.pack(
            fill="x",
            side="bottom"
        )

        status.pack_propagate(
            False
        )

        tk.Label(
            status,
            text="●",
            fg=SUCCESS,
            bg=SIDEBAR_BG,
            font=(FONT, 8)
        ).pack(
            side="left",
            padx=(15, 5)
        )

        tk.Label(
            status,
            textvariable=self.status_var,
            fg=TEXT_SECONDARY,
            bg=SIDEBAR_BG,
            font=(FONT, 8)
        ).pack(
            side="left"
        )

        tk.Label(
            status,
            text="Bleak BLE Engine",
            fg=TEXT_MUTED,
            bg=SIDEBAR_BG,
            font=(FONT, 8)
        ).pack(
            side="right",
            padx=15
        )

    # ========================================================
    # NAVIGATION
    # ========================================================

    def show_scanner(self):

        self.notebook.select(
            self.advertisement_tab
        )

    def show_gatt(self):

        self.notebook.select(
            self.gatt_tab
        )

    def show_advertisement(self):

        self.notebook.select(
            self.advertisement_tab
        )

    def show_log(self):

        self.notebook.select(
            self.log_tab
        )

    # ========================================================
    # LOG
    # ========================================================

    def log(
        self,
        message
    ):

        self.log_text.insert(
            "end",
            message + "\n"
        )

        self.log_text.see(
            "end"
        )

    # ========================================================
    # START SCAN
    # ========================================================

    def start_scan(self):

        if (
            self.scan_thread
            and self.scan_thread.is_alive()
        ):
            return

        self.scan_button.config(
            state="disabled",
            text="  ⟳  Scanning..."
        )

        self.connect_button.config(
            state="disabled"
        )

        self.status_var.set(
            "Scanning for nearby BLE devices..."
        )

        self.log(
            "[SCAN] Starting BLE scan..."
        )

        # Clear table

        for item in self.device_tree.get_children():

            self.device_tree.delete(
                item
            )

        self.devices.clear()

        self.device_count_var.set(
            "Scanning..."
        )

        self.scan_thread = threading.Thread(
            target=self.scan_worker,
            daemon=True
        )

        self.scan_thread.start()

    # ========================================================
    # SCAN WORKER
    # ========================================================

    def scan_worker(self):

        try:

            asyncio.run(
                self.async_scan()
            )

        except Exception as e:

            self.event_queue.put(
                (
                    "error",
                    f"Scan failed: {type(e).__name__}: {e}"
                )
            )

    # ========================================================
    # ASYNC SCAN
    # ========================================================

    async def async_scan(self):

        discovered = await BleakScanner.discover(
            timeout=10,
            return_adv=True
        )

        devices = []

        for device, adv in discovered.values():

            devices.append(
                (
                    device,
                    adv
                )
            )

        self.event_queue.put(
            (
                "scan_complete",
                devices
            )
        )

    # ========================================================
    # FILTER
    # ========================================================

    def filter_devices(self):

        search = self.search_var.get().lower().strip()

        for item in self.device_tree.get_children():

            self.device_tree.delete(
                item
            )

        for index, (
            device,
            adv
        ) in enumerate(self.devices):

            text = " ".join([
                str(device.name or ""),
                str(device.address or ""),
                str(adv.local_name or "")
            ]).lower()

            if search and search not in text:
                continue

            self.insert_device_row(
                index,
                device,
                adv
            )

    # ========================================================
    # INSERT DEVICE
    # ========================================================

    def insert_device_row(
        self,
        index,
        device,
        adv
    ):

        name = (
            device.name
            or "Unknown Device"
        )

        advertised = (
            adv.local_name
            or "—"
        )

        services = (
            ", ".join(
                adv.service_uuids
            )
            if adv.service_uuids
            else "—"
        )

        manufacturer = "—"

        if adv.manufacturer_data:

            manufacturer = ", ".join(
                f"0x{company:04X}"
                for company in adv.manufacturer_data
            )

        self.device_tree.insert(
            "",
            "end",
            values=(
                index,
                name,
                device.address,
                advertised,
                f"{adv.rssi} dBm",
                services,
                manufacturer
            )
        )

    # ========================================================
    # DEVICE SELECTED
    # ========================================================

    def device_selected(
        self,
        event=None
    ):

        selection = self.device_tree.selection()

        if not selection:
            return

        item = self.device_tree.item(
            selection[0]
        )

        values = item.get(
            "values"
        )

        if not values:
            return

        try:

            index = int(
                values[0]
            )

        except:

            return

        if index >= len(
            self.devices
        ):
            return

        device, adv = self.devices[
            index
        ]

        self.selected_device = device

        self.selected_adv = adv

        # ----------------------------------------------------
        # Summary
        # ----------------------------------------------------

        self.device_name_var.set(
            device.name
            or adv.local_name
            or "Unknown Device"
        )

        self.device_address_var.set(
            device.address
        )

        self.device_rssi_var.set(
            f"{adv.rssi} dBm"
        )

        self.device_services_var.set(
            str(
                len(
                    adv.service_uuids
                    or []
                )
            )
        )

        self.connect_button.config(
            state="normal"
        )

        self.show_advertisement_data(
            device,
            adv
        )

        self.log(
            f"[DEVICE] Selected: {device.address}"
        )

    # ========================================================
    # SHOW ADVERTISEMENT DATA
    # ========================================================

    def show_advertisement_data(
        self,
        device,
        adv
    ):

        self.advertisement_text.delete(
            "1.0",
            "end"
        )

        lines = []

        lines.append(
            "DEVICE ADVERTISEMENT"
        )

        lines.append(
            "=" * 80
        )

        lines.append(
            f"Device Name        : {device.name}"
        )

        lines.append(
            f"Bluetooth Address  : {device.address}"
        )

        lines.append(
            f"Advertised Name    : {adv.local_name}"
        )

        lines.append(
            f"RSSI               : {adv.rssi} dBm"
        )

        lines.append("")

        # ----------------------------------------------------
        # Services
        # ----------------------------------------------------

        lines.append(
            "ADVERTISED SERVICES"
        )

        lines.append(
            "-" * 80
        )

        if adv.service_uuids:

            for uuid in adv.service_uuids:

                lines.append(
                    f"  {uuid}"
                )

        else:

            lines.append(
                "  None"
            )

        lines.append("")

        # ----------------------------------------------------
        # Manufacturer
        # ----------------------------------------------------

        lines.append(
            "MANUFACTURER DATA"
        )

        lines.append(
            "-" * 80
        )

        if adv.manufacturer_data:

            for company_id, data in adv.manufacturer_data.items():

                lines.append(
                    f"Company ID : 0x{company_id:04X}"
                )

                lines.append(
                    f"HEX        : {data.hex(' ')}"
                )

                lines.append("")

        else:

            lines.append(
                "  None"
            )

        # ----------------------------------------------------
        # Service Data
        # ----------------------------------------------------

        lines.append(
            "SERVICE DATA"
        )

        lines.append(
            "-" * 80
        )

        if adv.service_data:

            for uuid, data in adv.service_data.items():

                lines.append(
                    f"UUID : {uuid}"
                )

                lines.append(
                    f"HEX  : {data.hex(' ')}"
                )

                lines.append("")

        else:

            lines.append(
                "  None"
            )

        # ----------------------------------------------------
        # OS details
        # ----------------------------------------------------

        lines.append(
            "BLUETOOTH OS DETAILS"
        )

        lines.append(
            "-" * 80
        )

        if hasattr(
            device,
            "details"
        ):

            lines.append(
                str(
                    device.details
                )
            )

        else:

            lines.append(
                "Unavailable"
            )

        self.advertisement_text.insert(
            "1.0",
            "\n".join(lines)
        )

    # ========================================================
    # CONNECT
    # ========================================================

    def start_inspection(self):

        if not self.selected_device:

            messagebox.showwarning(
                "No Device Selected",
                "Select a BLE device first."
            )

            return

        if (
            self.inspect_thread
            and self.inspect_thread.is_alive()
        ):
            return

        device = self.selected_device

        adv = self.selected_adv

        self.connect_button.config(
            state="disabled",
            text="  ⟳  Connecting..."
        )

        self.scan_button.config(
            state="disabled"
        )

        self.status_var.set(
            f"Connecting to {device.address}..."
        )

        self.log(
            f"[CONNECT] Connecting to {device.address}"
        )

        self.inspect_thread = threading.Thread(
            target=self.inspect_worker,
            args=(
                device,
                adv
            ),
            daemon=True
        )

        self.inspect_thread.start()

    # ========================================================
    # INSPECTION WORKER
    # ========================================================

    def inspect_worker(
        self,
        device,
        adv
    ):

        try:

            asyncio.run(
                self.async_inspect(
                    device,
                    adv
                )
            )

        except Exception as e:

            self.event_queue.put(
                (
                    "error",
                    f"{type(e).__name__}: {e}"
                )
            )

    # ========================================================
    # ASYNC INSPECTION
    # ========================================================

    async def async_inspect(
        self,
        device,
        adv
    ):

        try:

            async with BleakClient(
                device
            ) as client:

                self.client = client

                if not client.is_connected:

                    raise RuntimeError(
                        "BLE connection failed."
                    )

                self.event_queue.put(
                    (
                        "connected",
                        True
                    )
                )

                self.event_queue.put(
                    (
                        "log",
                        "[CONNECT] Connection established."
                    )
                )

                # ------------------------------------------------
                # Clear GATT
                # ------------------------------------------------

                self.event_queue.put(
                    (
                        "clear_gatt",
                        None
                    )
                )

                # ------------------------------------------------
                # Inspect services
                # ------------------------------------------------

                for service in client.services:

                    service_data = {
                        "uuid": service.uuid,
                        "description":
                            service.description or ""
                    }

                    self.event_queue.put(
                        (
                            "gatt_service",
                            service_data
                        )
                    )

                    for char in service.characteristics:

                        properties = ", ".join(
                            char.properties
                        )

                        value_text = ""

                        if "read" in char.properties:

                            try:

                                value = await client.read_gatt_char(
                                    char.uuid
                                )

                                decoded = value.decode(
                                    "utf-8",
                                    errors="replace"
                                )

                                value_text = (
                                    f"{decoded}   "
                                    f"[{value.hex(' ')}]"
                                )

                            except Exception as e:

                                value_text = (
                                    f"Read failed: {e}"
                                )

                        char_data = {
                            "uuid": char.uuid,
                            "description":
                                char.description or "",
                            "properties": properties,
                            "value": value_text
                        }

                        self.event_queue.put(
                            (
                                "gatt_characteristic",
                                char_data
                            )
                        )

                        # ----------------------------------------
                        # Descriptors
                        # ----------------------------------------

                        for descriptor in char.descriptors:

                            descriptor_data = {
                                "uuid":
                                    descriptor.uuid
                            }

                            self.event_queue.put(
                                (
                                    "gatt_descriptor",
                                    descriptor_data
                                )
                            )

                self.event_queue.put(
                    (
                        "inspection_complete",
                        None
                    )
                )

        except Exception as e:

            self.event_queue.put(
                (
                    "error",
                    f"Connection error: {type(e).__name__}: {e}"
                )
            )

        finally:

            self.client = None

            self.event_queue.put(
                (
                    "disconnected",
                    None
                )
            )

    # ========================================================
    # GATT SERVICE
    # ========================================================

    def add_gatt_service(
        self,
        data
    ):

        item = self.gatt_tree.insert(
            "",
            "end",
            text="▰  SERVICE",
            values=(
                "SERVICE",
                data["uuid"],
                data["description"],
                "",
                ""
            )
        )

        self.current_service_item = item

        self.current_characteristic_item = None

    # ========================================================
    # GATT CHARACTERISTIC
    # ========================================================

    def add_gatt_characteristic(
        self,
        data
    ):

        parent = (
            self.current_service_item
            or ""
        )

        item = self.gatt_tree.insert(
            parent,
            "end",
            text="  ◇  CHARACTERISTIC",
            values=(
                "CHARACTERISTIC",
                data["uuid"],
                data["description"],
                data["properties"],
                data["value"]
            )
        )

        self.current_characteristic_item = item

    # ========================================================
    # GATT DESCRIPTOR
    # ========================================================

    def add_gatt_descriptor(
        self,
        data
    ):

        parent = (
            self.current_characteristic_item
            or self.current_service_item
            or ""
        )

        self.gatt_tree.insert(
            parent,
            "end",
            text="      ▫  DESCRIPTOR",
            values=(
                "DESCRIPTOR",
                data["uuid"],
                "",
                "",
                ""
            )
        )

    # ========================================================
    # GATT DOUBLE CLICK
    # ========================================================

    def gatt_double_click(
        self,
        event
    ):

        selection = self.gatt_tree.selection()

        if not selection:
            return

        item = self.gatt_tree.item(
            selection[0]
        )

        values = item.get(
            "values"
        )

        if not values:
            return

        uuid = values[1]

        value = values[4]

        # ----------------------------------------------------
        # Copy UUID
        # ----------------------------------------------------

        popup = tk.Toplevel(
            self.root
        )

        popup.title(
            "GATT Characteristic"
        )

        popup.geometry(
            "650x400"
        )

        popup.configure(
            bg=BG
        )

        tk.Label(
            popup,
            text="GATT ITEM DETAILS",
            font=(FONT, 15, "bold"),
            fg=TEXT,
            bg=BG
        ).pack(
            anchor="w",
            padx=20,
            pady=(20, 10)
        )

        details = tk.Text(
            popup,
            bg=PANEL_BG,
            fg=TEXT,
            font=("Consolas", 10),
            relief="flat",
            bd=0
        )

        details.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=10
        )

        details.insert(
            "1.0",
            f"TYPE\n"
            f"{values[0]}\n\n"
            f"UUID\n"
            f"{uuid}\n\n"
            f"DESCRIPTION\n"
            f"{values[2]}\n\n"
            f"PROPERTIES\n"
            f"{values[3]}\n\n"
            f"VALUE\n"
            f"{value}"
        )

        tk.Button(
            popup,
            text="Copy UUID",
            command=lambda: self.copy_to_clipboard(
                uuid
            ),
            bg=ACCENT_DARK,
            fg="white",
            relief="flat",
            bd=0,
            padx=20,
            pady=8
        ).pack(
            pady=(0, 15)
        )

    # ========================================================
    # COPY
    # ========================================================

    def copy_to_clipboard(
        self,
        text
    ):

        self.root.clipboard_clear()

        self.root.clipboard_append(
            text
        )

        self.root.update()

        self.log(
            "[SYSTEM] Copied to clipboard."
        )

    # ========================================================
    # DISCONNECT
    # ========================================================

    def disconnect_device(self):

        self.log(
            "[CONNECT] Disconnect requested."
        )

        self.connected = False

        self.connection_var.set(
            "DISCONNECTED"
        )

        self.connection_dot.config(
            fg=TEXT_MUTED
        )

        self.connection_label.config(
            fg=TEXT_SECONDARY
        )

        self.disconnect_button.config(
            state="disabled"
        )

        self.status_var.set(
            "Disconnected"
        )

    # ========================================================
    # QUEUE PROCESSOR
    # ========================================================

    def process_queue(self):

        try:

            while True:

                event, data = (
                    self.event_queue.get_nowait()
                )

                # --------------------------------------------
                # Scan complete
                # --------------------------------------------

                if event == "scan_complete":

                    self.devices = data

                    self.filter_devices()

                    count = len(
                        self.devices
                    )

                    self.device_count_var.set(
                        f"{count} Devices"
                    )

                    self.scan_button.config(
                        state="normal",
                        text="  🔍  Scan Devices"
                    )

                    self.status_var.set(
                        f"Scan complete — {count} device(s) found."
                    )

                    self.log(
                        f"[SCAN] Found {count} BLE device(s)."
                    )

                # --------------------------------------------
                # Connected
                # --------------------------------------------

                elif event == "connected":

                    self.connected = True

                    self.connection_var.set(
                        "CONNECTED"
                    )

                    self.connection_dot.config(
                        fg=SUCCESS
                    )

                    self.connection_label.config(
                        fg=SUCCESS
                    )

                    self.disconnect_button.config(
                        state="normal"
                    )

                    self.connect_button.config(
                        text="  ✓  Connected"
                    )

                    self.status_var.set(
                        "Connected — inspecting GATT..."
                    )

                # --------------------------------------------
                # Disconnected
                # --------------------------------------------

                elif event == "disconnected":

                    self.connected = False

                    self.connection_var.set(
                        "DISCONNECTED"
                    )

                    self.connection_dot.config(
                        fg=TEXT_MUTED
                    )

                    self.connection_label.config(
                        fg=TEXT_SECONDARY
                    )

                    self.disconnect_button.config(
                        state="disabled"
                    )

                    self.scan_button.config(
                        state="normal"
                    )

                    if self.selected_device:

                        self.connect_button.config(
                            state="normal",
                            text="  🔗  Connect & Inspect"
                        )

                # --------------------------------------------
                # Clear GATT
                # --------------------------------------------

                elif event == "clear_gatt":

                    for item in (
                        self.gatt_tree.get_children()
                    ):

                        self.gatt_tree.delete(
                            item
                        )

                    self.current_service_item = None

                    self.current_characteristic_item = None

                # --------------------------------------------
                # Service
                # --------------------------------------------

                elif event == "gatt_service":

                    self.add_gatt_service(
                        data
                    )

                # --------------------------------------------
                # Characteristic
                # --------------------------------------------

                elif event == "gatt_characteristic":

                    self.add_gatt_characteristic(
                        data
                    )

                # --------------------------------------------
                # Descriptor
                # --------------------------------------------

                elif event == "gatt_descriptor":

                    self.add_gatt_descriptor(
                        data
                    )

                # --------------------------------------------
                # Inspection complete
                # --------------------------------------------

                elif event == "inspection_complete":

                    self.status_var.set(
                        "GATT inspection complete."
                    )

                    self.notebook.select(
                        self.gatt_tab
                    )

                    self.log(
                        "[GATT] Inspection completed successfully."
                    )

                # --------------------------------------------
                # Log
                # --------------------------------------------

                elif event == "log":

                    self.log(
                        data
                    )

                # --------------------------------------------
                # Error
                # --------------------------------------------

                elif event == "error":

                    self.log(
                        "[ERROR] " + data
                    )

                    self.status_var.set(
                        "Operation failed."
                    )

                    self.scan_button.config(
                        state="normal"
                    )

                    if self.selected_device:

                        self.connect_button.config(
                            state="normal",
                            text="  🔗  Connect & Inspect"
                        )

                    messagebox.showerror(
                        "BLE Error",
                        data
                    )

        except queue.Empty:

            pass

        self.root.after(
            100,
            self.process_queue
        )

    # ========================================================
    # CLOSE
    # ========================================================

    def close_application(self):

        self.root.destroy()


# ============================================================
# MAIN
# ============================================================

def main():

    root = tk.Tk()

    app = BLECommandCenter(
        root
    )

    root.mainloop()


if __name__ == "__main__":
    main()