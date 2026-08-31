#include <zephyr/kernel.h>
#include <zephyr/sys/printk.h>
#include <zephyr/bluetooth/bluetooth.h>
#include <zephyr/bluetooth/conn.h>
#include <zephyr/bluetooth/gatt.h>
#include <zephyr/bluetooth/hci.h>
#include <zephyr/settings/settings.h>
#include <string.h>

/*
 * ============================================================
 * Pluto configuration discovered from your PC inspection
 * ============================================================
 *
 * Device:
 *     PLEXO-89FE-g2
 *
 * Service:
 *     0000180F-0000-1000-8000-00805F9B34FB
 *
 * Characteristic:
 *     00002A19-0000-1000-8000-00805F9B34FB
 *
 * Properties:
 *     READ + NOTIFY
 *
 * This is the standard Battery Service / Battery Level
 * characteristic.
 */

#define PLUTO_NAME              "PLEXO-89FE-g2"

#define PLUTO_SERVICE_UUID      BT_UUID_16_ENCODE(0x180F)
#define PLUTO_BATTERY_UUID      BT_UUID_16_ENCODE(0x2A19)

/*
 * Rescan delay.
 */
#define SCAN_RETRY_MS           1000

/*
 * Delay before retrying after disconnect.
 */
#define RECONNECT_DELAY_MS      1000


/* ============================================================
 * Global state
 * ============================================================ */

static struct bt_conn *default_conn;

static bool scanning;
static bool connected;
static bool service_found;
static bool characteristic_found;
static bool subscribed;


/* ============================================================
 * GATT UUIDs
 * ============================================================ */

static struct bt_uuid_16 pluto_service_uuid =
	BT_UUID_INIT_16(0x180F);

static struct bt_uuid_16 pluto_battery_uuid =
	BT_UUID_INIT_16(0x2A19);


/* ============================================================
 * Discovery state
 * ============================================================ */

static struct bt_gatt_discover_params discover_params;

static uint16_t service_start_handle;
static uint16_t service_end_handle;

static uint16_t battery_value_handle;


/* ============================================================
 * Subscription
 * ============================================================ */

static struct bt_gatt_subscribe_params subscribe_params;


/* ============================================================
 * Forward declarations
 * ============================================================ */

static void start_scan(void);

static uint8_t discover_service(
	struct bt_conn *conn,
	const struct bt_gatt_attr *attr,
	struct bt_gatt_discover_params *params
);

static uint8_t discover_battery_characteristic(
	struct bt_conn *conn,
	const struct bt_gatt_attr *attr,
	struct bt_gatt_discover_params *params
);

static uint8_t pluto_notify(
	struct bt_conn *conn,
	struct bt_gatt_subscribe_params *params,
	const void *data,
	uint16_t length
);

static void subscribe_complete(
	struct bt_conn *conn,
	uint8_t err,
	struct bt_gatt_subscribe_params *params
);


/* ============================================================
 * Utility
 * ============================================================ */

static void print_hex(
	const uint8_t *data,
	uint16_t length
)
{
	for (uint16_t i = 0; i < length; i++) {
		printk("%02X", data[i]);

		if (i + 1 < length) {
			printk(" ");
		}
	}
}


/* ============================================================
 * BLE scan callback
 * ============================================================ */

static void device_found(
	const bt_addr_le_t *addr,
	int8_t rssi,
	uint8_t type,
	struct net_buf_simple *ad
)
{
	char addr_str[BT_ADDR_LE_STR_LEN];

	if (scanning == false) {
		return;
	}

	/*
	 * Ignore non-connectable advertisements.
	 */
	if (type != BT_GAP_ADV_TYPE_ADV_IND &&
	    type != BT_GAP_ADV_TYPE_ADV_DIRECT_IND &&
	    type != BT_GAP_ADV_TYPE_EXT_ADV) {
		return;
	}

	bt_addr_le_to_str(
		addr,
		addr_str,
		sizeof(addr_str)
	);

	/*
	 * Parse advertisement data for the device name.
	 */
	struct net_buf_simple_state state;
	net_buf_simple_save(ad, &state);

	while (ad->len > 1) {

		uint8_t field_len = net_buf_simple_pull_u8(ad);

		if (field_len == 0 ||
		    field_len > ad->len) {
			break;
		}

		uint8_t field_type =
			net_buf_simple_pull_u8(ad);

		uint8_t data_len = field_len - 1;

		if (field_type == BT_DATA_NAME_COMPLETE ||
		    field_type == BT_DATA_NAME_SHORTENED) {

			char name[32];

			size_t copy_len =
				MIN(data_len, sizeof(name) - 1);

			memcpy(
				name,
				ad->data,
				copy_len
			);

			name[copy_len] = '\0';

			if (strcmp(name, PLUTO_NAME) == 0) {

				printk("\n");
				printk("========================================\n");
				printk("PLUTO FOUND\n");
				printk("========================================\n");

				printk(
					"Name : %s\n",
					name
				);

				printk(
					"Addr : %s\n",
					addr_str
				);

				printk(
					"RSSI : %d dBm\n",
					rssi
				);

				/*
				 * Stop scanning before connecting.
				 */
				int err =
					bt_le_scan_stop();

				if (err) {

					printk(
						"Scan stop failed: %d\n",
						err
					);

					return;
				}

				scanning = false;

				printk(
					"Connecting to Pluto...\n"
				);

				err =
					bt_conn_le_create(
						addr,
						BT_CONN_LE_CREATE_CONN,
						BT_LE_CONN_PARAM_DEFAULT,
						&default_conn
					);

				if (err) {

					printk(
						"Connection create failed: %d\n",
						err
					);

					default_conn = NULL;

					k_msleep(
						RECONNECT_DELAY_MS
					);

					start_scan();
				}

				break;
			}
		}

		net_buf_simple_pull(
			ad,
			data_len
		);
	}

	net_buf_simple_restore(ad, &state);
}


/* ============================================================
 * Start scanning
 * ============================================================ */

static void start_scan(void)
{
	int err;

	if (scanning) {
		return;
	}

	if (connected) {
		return;
	}

	printk("\n");
	printk("========================================\n");
	printk("SCANNING FOR PLUTO\n");
	printk("========================================\n");

	err = bt_le_scan_start(
		BT_LE_SCAN_ACTIVE,
		device_found
	);

	if (err == 0) {

		scanning = true;

		printk(
			"Scanner started successfully.\n"
		);

		return;
	}

	printk(
		"Scan start failed: %d\n",
		err
	);

	k_msleep(
		SCAN_RETRY_MS
	);
}


/* ============================================================
 * Connection callbacks
 * ============================================================ */

static void connected_cb(
	struct bt_conn *conn,
	uint8_t err
)
{
	if (err) {

		printk(
			"\nPLUTO CONNECTION FAILED: %u\n",
			err
		);

		if (default_conn) {

			bt_conn_unref(
				default_conn
			);

			default_conn = NULL;
		}

		connected = false;

		k_msleep(
			RECONNECT_DELAY_MS
		);

		start_scan();

		return;
	}

	printk("\n");
	printk("========================================\n");
	printk("PLUTO CONNECTED\n");
	printk("========================================\n");

	connected = true;

	default_conn = bt_conn_ref(conn);

	printk(
		"Connection successful.\n"
	);

	printk(
		"Starting GATT service discovery...\n"
	);

	memset(
		&discover_params,
		0,
		sizeof(discover_params)
	);

	discover_params.uuid =
		&pluto_service_uuid.uuid;

	discover_params.func =
		discover_service;

	discover_params.start_handle =
		BT_ATT_FIRST_ATTRIBUTE_HANDLE;

	discover_params.end_handle =
		BT_ATT_LAST_ATTRIBUTE_HANDLE;

	discover_params.type =
		BT_GATT_DISCOVER_PRIMARY;

	err = bt_gatt_discover(
		conn,
		&discover_params
	);

	if (err) {

		printk(
			"Service discovery failed: %d\n",
			err
		);
	}
}


static void disconnected_cb(
	struct bt_conn *conn,
	uint8_t reason
)
{
	printk("\n");
	printk("========================================\n");
	printk("PLUTO DISCONNECTED\n");
	printk("========================================\n");

	printk(
		"Reason: 0x%02X\n",
		reason
	);

	connected = false;
	service_found = false;
	characteristic_found = false;
	subscribed = false;

	memset(
		&subscribe_params,
		0,
		sizeof(subscribe_params)
	);

	if (default_conn) {

		bt_conn_unref(
			default_conn
		);

		default_conn = NULL;
	}

	printk(
		"Restarting scan...\n"
	);

	k_msleep(
		RECONNECT_DELAY_MS
	);

	start_scan();
}


BT_CONN_CB_DEFINE(conn_callbacks) = {
	.connected = connected_cb,
	.disconnected = disconnected_cb,
};


/* ============================================================
 * Service discovery
 * ============================================================ */

static uint8_t discover_service(
	struct bt_conn *conn,
	const struct bt_gatt_attr *attr,
	struct bt_gatt_discover_params *params
)
{
	if (attr == NULL) {

		printk(
			"Pluto Battery Service not found.\n"
		);

		return BT_GATT_ITER_STOP;
	}

	const struct bt_gatt_service_val *service =
		attr->user_data;

	service_start_handle =
		attr->handle + 1;

	service_end_handle =
		service->end_handle;

	service_found = true;

	printk("\n");
	printk("========================================\n");
	printk("PLUTO SERVICE FOUND\n");
	printk("========================================\n");

	printk(
		"Service UUID : 0x180F\n"
	);

	printk(
		"Start handle : %u\n",
		service_start_handle
	);

	printk(
		"End handle   : %u\n",
		service_end_handle
	);


	/*
	 * Now discover the Battery Level characteristic.
	 */

	memset(
		&discover_params,
		0,
		sizeof(discover_params)
	);

	discover_params.uuid =
		&pluto_battery_uuid.uuid;

	discover_params.func =
		discover_battery_characteristic;

	discover_params.start_handle =
		service_start_handle;

	discover_params.end_handle =
		service_end_handle;

	discover_params.type =
		BT_GATT_DISCOVER_CHARACTERISTIC;

	int err =
		bt_gatt_discover(
			conn,
			&discover_params
		);

	if (err) {

		printk(
			"Characteristic discovery failed: %d\n",
			err
		);
	}

	return BT_GATT_ITER_STOP;
}


/* ============================================================
 * Battery characteristic discovery
 * ============================================================ */

static uint8_t discover_battery_characteristic(
	struct bt_conn *conn,
	const struct bt_gatt_attr *attr,
	struct bt_gatt_discover_params *params
)
{
	if (attr == NULL) {

		printk(
			"Battery Level characteristic not found.\n"
		);

		return BT_GATT_ITER_STOP;
	}

	const struct bt_gatt_chrc *chrc =
		attr->user_data;

	battery_value_handle =
		chrc->value_handle;

	characteristic_found = true;

	printk("\n");
	printk("========================================\n");
	printk("BATTERY CHARACTERISTIC FOUND\n");
	printk("========================================\n");

	printk(
		"UUID          : 0x2A19\n"
	);

	printk(
		"Value handle  : %u\n",
		battery_value_handle
	);

	printk(
		"Properties    : 0x%02X\n",
		chrc->properties
	);

	printk(
		"Subscribing to notifications...\n"
	);


	/*
	 * Let Zephyr discover the CCC descriptor automatically.
	 */
	memset(
		&subscribe_params,
		0,
		sizeof(subscribe_params)
	);

	subscribe_params.notify =
		pluto_notify;

	subscribe_params.subscribe =
		subscribe_complete;

	subscribe_params.value_handle =
		battery_value_handle;

	subscribe_params.ccc_handle =
		BT_GATT_AUTO_DISCOVER_CCC_HANDLE;

	subscribe_params.value =
		BT_GATT_CCC_NOTIFY;


	int err =
		bt_gatt_subscribe(
			conn,
			&subscribe_params
		);

	if (err) {

		printk(
			"Subscribe failed: %d\n",
			err
		);

		return BT_GATT_ITER_STOP;
	}

	printk(
		"Subscription request sent.\n"
	);

	return BT_GATT_ITER_STOP;
}


/* ============================================================
 * Subscription complete
 * ============================================================ */

static void subscribe_complete(
	struct bt_conn *conn,
	uint8_t err,
	struct bt_gatt_subscribe_params *params
)
{
	if (err) {

		printk("\n");
		printk(
			"PLUTO SUBSCRIPTION FAILED: %u\n",
			err
		);

		subscribed = false;

		return;
	}

	subscribed = true;

	printk("\n");
	printk("========================================\n");
	printk("PLUTO DATA STREAM ACTIVE\n");
	printk("========================================\n");

	printk(
		"Battery Level notifications enabled.\n"
	);

	printk(
		"Value handle : %u\n",
		params->value_handle
	);

	printk(
		"CCC handle   : %u\n",
		params->ccc_handle
	);
}


/* ============================================================
 * Notification callback
 * ============================================================ */

static uint8_t pluto_notify(
	struct bt_conn *conn,
	struct bt_gatt_subscribe_params *params,
	const void *data,
	uint16_t length
)
{
	if (data == NULL) {

		printk(
			"PLUTO notification subscription removed.\n"
		);

		subscribed = false;

		return BT_GATT_ITER_STOP;
	}

	printk(
		"PLUTO_RX length=%u data=",
		length
	);

	print_hex(
		data,
		length
	);

	printk("\n");


	/*
	 * Battery Level is one byte.
	 */
	if (length >= 1) {

		const uint8_t battery =
			((const uint8_t *)data)[0];

		printk(
			"PLUTO_BATTERY=%u%%\n",
			battery
		);
	}

	return BT_GATT_ITER_CONTINUE;
}


/* ============================================================
 * Bluetooth initialization
 * ============================================================ */

static void bt_ready(int err)
{
	if (err) {

		printk(
			"Bluetooth initialization failed: %d\n",
			err
		);

		return;
	}

	printk("\n");
	printk("========================================\n");
	printk("BLUETOOTH INITIALIZED\n");
	printk("========================================\n");

	printk(
		"Target : %s\n",
		PLUTO_NAME
	);

	printk(
		"Service: 0x180F\n"
	);

	printk(
		"Data   : 0x2A19\n"
	);

#if defined(CONFIG_BT_SETTINGS)

	settings_load();

#endif

	start_scan();
}


/* ============================================================
 * Main
 * ============================================================ */

int main(void)
{
	printk("\n");
	printk("========================================\n");
	printk("nRF52840 PLUTO CENTRAL\n");
	printk("========================================\n");

	printk(
		"Target device: %s\n",
		PLUTO_NAME
	);

	printk(
		"Battery Service: 0x180F\n"
	);

	printk(
		"Battery Level : 0x2A19\n"
	);

	printk(
		"Mode: BLE Central\n"
	);

	printk("\n");

	int err =
		bt_enable(bt_ready);

	if (err) {

		printk(
			"Bluetooth enable failed: %d\n",
			err
		);

		return 0;
	}

	while (1) {

		/*
		 * Safety net:
		 *
		 * If we somehow become disconnected and
		 * scanning has stopped, restart scanning.
		 */

		if (!connected && !scanning) {

			start_scan();
		}

		k_sleep(
			K_SECONDS(2)
		);
	}

	return 0;
}