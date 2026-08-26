#include <zephyr/kernel.h>
#include <zephyr/sys/printk.h>

#include <zephyr/bluetooth/bluetooth.h>
#include <zephyr/bluetooth/conn.h>
#include <zephyr/bluetooth/gatt.h>

#include <string.h>


/*
 * ============================================================
 * PLUTO UUIDs
 * ============================================================
 *
 * Pluto service:
 *
 * 594a34fc-31db-11ea-978f-2e728ce88125
 *
 * Characteristic:
 *
 * 594a36e6-31db-11ea-978f-2e728ce88125
 *
 * Characteristic:
 *
 * 594a3010-31db-11ea-978f-2e728ce88125
 */


/*
 * Pluto custom service
 */
#define PLUTO_SERVICE_UUID \
	BT_UUID_DECLARE_128( \
		BT_UUID_128_ENCODE( \
			0x594a34fc, \
			0x31db, \
			0x11ea, \
			0x978f, \
			0x2e728ce88125ULL))


/*
 * Pluto characteristic 1
 *
 * Properties:
 * indicate, write
 */
#define PLUTO_CHAR_INDICATE_UUID \
	BT_UUID_DECLARE_128( \
		BT_UUID_128_ENCODE( \
			0x594a36e6, \
			0x31db, \
			0x11ea, \
			0x978f, \
			0x2e728ce88125ULL))


/*
 * Pluto characteristic 2
 *
 * Properties:
 * write, write without response
 */
#define PLUTO_CHAR_WRITE_UUID \
	BT_UUID_DECLARE_128( \
		BT_UUID_128_ENCODE( \
			0x594a3010, \
			0x31db, \
			0x11ea, \
			0x978f, \
			0x2e728ce88125ULL))


/*
 * ============================================================
 * Global variables
 * ============================================================
 */

static struct bt_conn *pluto_conn;

static struct bt_gatt_discover_params discover_params;

static uint16_t pluto_service_start;
static uint16_t pluto_service_end;

static uint16_t pluto_indicate_handle;
static uint16_t pluto_write_handle;


/*
 * ============================================================
 * Forward declarations
 * ============================================================
 */

static void start_scanning(void);


/*
 * ============================================================
 * UUID helper
 * ============================================================
 */

static bool uuid_is_pluto_service(const struct bt_uuid *uuid)
{
	if (!uuid) {
		return false;
	}

	return bt_uuid_cmp(uuid, PLUTO_SERVICE_UUID) == 0;
}


/*
 * ============================================================
 * Advertisement parser
 * ============================================================
 */

static bool parse_advertisement(struct net_buf_simple *ad)
{
	struct net_buf_simple_state state;

	net_buf_simple_save(ad, &state);

	while (ad->len > 1) {

		uint8_t length;

		length = net_buf_simple_pull_u8(ad);

		if (length == 0) {
			break;
		}

		if (length > ad->len) {
			break;
		}

		uint8_t type;

		type = net_buf_simple_pull_u8(ad);

		/*
		 * Look for 128-bit service UUID.
		 */
		if (type == BT_DATA_UUID128_ALL ||
		    type == BT_DATA_UUID128_SOME) {

			while (ad->len >= 16) {

				const uint8_t *uuid_data;

				uuid_data = ad->data;

				/*
				 * BLE UUID is transmitted
				 * little endian.
				 *
				 * Pluto:
				 *
				 * 594a34fc-31db-11ea-
				 * 978f-2e728ce88125
				 */
				static const uint8_t pluto_uuid[16] = {
					0x25,
					0x81,
					0xCE,
					0x8C,
					0x72,
					0x2E,
					0x8F,
					0x97,
					0xEA,
					0x11,
					0xDB,
					0x31,
					0xFC,
					0x34,
					0x4A,
					0x59
				};

				if (memcmp(uuid_data,
					   pluto_uuid,
					   sizeof(pluto_uuid)) == 0) {

					net_buf_simple_restore(
						ad,
						&state);

					return true;
				}

				net_buf_simple_pull(ad, 16);
			}
		}
	}

	net_buf_simple_restore(ad, &state);

	return false;
}


/*
 * ============================================================
 * Scan callback
 * ============================================================
 */

static void scan_recv(const struct bt_le_scan_recv_info *info,
		      struct net_buf_simple *ad)
{
	char addr[BT_ADDR_LE_STR_LEN];

	bt_addr_le_to_str(
		info->addr,
		addr,
		sizeof(addr));

	printk(
		"BLE DEVICE: %s  RSSI: %d\n",
		addr,
		info->rssi);

	/*
	 * Check advertisement for Pluto service.
	 */
	if (!parse_advertisement(ad)) {
		return;
	}

	printk("\n");
	printk("========================================\n");
	printk("       PLUTO DEVICE FOUND!\n");
	printk("========================================\n");

	printk("Address : %s\n", addr);
	printk("RSSI    : %d dBm\n", info->rssi);

	printk("Pluto Service UUID detected.\n");

	/*
	 * Stop scanning.
	 */
	int err = bt_le_scan_stop();

	if (err) {

		printk(
			"Failed to stop scanning: %d\n",
			err);

		return;
	}

	/*
	 * Connect to Pluto.
	 */
	printk("Connecting to Pluto...\n");

	err = bt_conn_le_create(
		info->addr,
		BT_CONN_LE_CREATE_CONN,
		BT_LE_CONN_PARAM_DEFAULT,
		&pluto_conn);

	if (err) {

		printk(
			"Connection creation failed: %d\n",
			err);

		pluto_conn = NULL;

		start_scanning();
	}
}


/*
 * ============================================================
 * Scan callback structure
 * ============================================================
 */

static struct bt_le_scan_cb scan_cb = {
	.recv = scan_recv,
};


/*
 * ============================================================
 * Start scanning
 * ============================================================
 */

static void start_scanning(void)
{
	int err;

	printk("\n");
	printk("========================================\n");
	printk("       SCANNING FOR PLUTO\n");
	printk("========================================\n");

	err = bt_le_scan_start(
		BT_LE_SCAN_ACTIVE,
		NULL);

	if (err) {

		printk(
			"Scanning failed: %d\n",
			err);

		return;
	}

	printk("BLE scanning started.\n");
}


/*
 * ============================================================
 * GATT discovery callback
 * ============================================================
 */

static uint8_t discovery_func(
	struct bt_conn *conn,
	const struct bt_gatt_attr *attr,
	struct bt_gatt_discover_params *params)
{
	if (!attr) {

		printk("\n");
		printk("GATT discovery complete.\n");

		memset(
			params,
			0,
			sizeof(*params));

		return BT_GATT_ITER_STOP;
	}


	/*
	 * Primary service found.
	 */
	if (params->type == BT_GATT_DISCOVER_PRIMARY) {

		struct bt_gatt_service_val *service;

		service = (struct bt_gatt_service_val *)
			attr->user_data;

		printk("\n");
		printk("SERVICE FOUND\n");

		printk(
			"Handle start : %u\n",
			attr->handle);

		printk(
			"UUID         : ");

		if (service->uuid->type ==
		    BT_UUID_TYPE_128) {

			printk(
				"%s\n",
				"128-bit UUID");

		} else {

			printk(
				"non-128-bit UUID\n");
		}

		/*
		 * Check for Pluto service.
		 */
		if (uuid_is_pluto_service(
			service->uuid)) {

			printk("\n");
			printk(
				"********************************\n");

			printk(
				"PLUTO SERVICE FOUND!\n");

			printk(
				"Service Handle: %u\n",
				attr->handle);

			printk(
				"********************************\n");

			pluto_service_start =
				attr->handle;

			/*
			 * The end handle will be discovered
			 * when the next primary service is
			 * found.
			 */
		}

		return BT_GATT_ITER_CONTINUE;
	}


	/*
	 * Characteristic discovery.
	 */
	if (params->type ==
	    BT_GATT_DISCOVER_CHARACTERISTIC) {

		const struct bt_gatt_chrc *chrc;

		chrc = attr->user_data;

		printk("\n");
		printk("CHARACTERISTIC FOUND\n");

		printk(
			"Declaration handle : %u\n",
			attr->handle);

		printk(
			"Value handle       : %u\n",
			chrc->value_handle);

		printk(
			"Properties         : 0x%02x\n",
			chrc->properties);

		/*
		 * Check indication/write characteristic.
		 */
		if (bt_uuid_cmp(
			chrc->uuid,
			PLUTO_CHAR_INDICATE_UUID) == 0) {

			pluto_indicate_handle =
				chrc->value_handle;

			printk(
				"*** PLUTO INDICATE CHARACTERISTIC ***\n");

			printk(
				"Handle: %u\n",
				pluto_indicate_handle);
		}


		/*
		 * Check write characteristic.
		 */
		if (bt_uuid_cmp(
			chrc->uuid,
			PLUTO_CHAR_WRITE_UUID) == 0) {

			pluto_write_handle =
				chrc->value_handle;

			printk(
				"*** PLUTO WRITE CHARACTERISTIC ***\n");

			printk(
				"Handle: %u\n",
				pluto_write_handle);
		}

		return BT_GATT_ITER_CONTINUE;
	}


	return BT_GATT_ITER_CONTINUE;
}


/*
 * ============================================================
 * Start GATT discovery
 * ============================================================
 */

static void start_gatt_discovery(struct bt_conn *conn)
{
	printk("\n");
	printk("========================================\n");
	printk("       STARTING GATT DISCOVERY\n");
	printk("========================================\n");

	memset(
		&discover_params,
		0,
		sizeof(discover_params));

	discover_params.uuid =
		BT_UUID_DECLARE_16(
			BT_UUID_GATT_PRIMARY_VAL);

	discover_params.func =
		discovery_func;

	discover_params.start_handle =
		BT_ATT_FIRST_ATTRIBUTE_HANDLE;

	discover_params.end_handle =
		BT_ATT_LAST_ATTRIBUTE_HANDLE;

	discover_params.type =
		BT_GATT_DISCOVER_PRIMARY;

	int err = bt_gatt_discover(
		conn,
		&discover_params);

	if (err) {

		printk(
			"GATT discovery failed: %d\n",
			err);
	}
}


/*
 * ============================================================
 * Connected callback
 * ============================================================
 */

static void connected(
	struct bt_conn *conn,
	uint8_t err)
{
	if (err) {

		printk("\n");
		printk("========================================\n");
		printk("       PLUTO CONNECTION FAILED\n");
		printk("========================================\n");

		printk(
			"Error: %u\n",
			err);

		if (pluto_conn) {

			bt_conn_unref(
				pluto_conn);

			pluto_conn = NULL;
		}

		start_scanning();

		return;
	}


	printk("\n");
	printk("========================================\n");
	printk("       PLUTO CONNECTED!\n");
	printk("========================================\n");


	if (!pluto_conn) {

		pluto_conn =
			bt_conn_ref(conn);
	}


	/*
	 * Reset discovered handles.
	 */
	pluto_service_start = 0;
	pluto_service_end = 0;

	pluto_indicate_handle = 0;
	pluto_write_handle = 0;


	/*
	 * Start GATT discovery.
	 */
	start_gatt_discovery(conn);
}


/*
 * ============================================================
 * Disconnected callback
 * ============================================================
 */

static void disconnected(
	struct bt_conn *conn,
	uint8_t reason)
{
	printk("\n");
	printk("========================================\n");
	printk("       PLUTO DISCONNECTED\n");
	printk("========================================\n");

	printk(
		"Reason: 0x%02X\n",
		reason);


	if (pluto_conn) {

		bt_conn_unref(
			pluto_conn);

		pluto_conn = NULL;
	}


	printk("Restarting scan...\n");

	k_sleep(K_MSEC(500));

	start_scanning();
}


/*
 * ============================================================
 * Connection callbacks
 * ============================================================
 */

BT_CONN_CB_DEFINE(pluto_connection_callbacks) = {

	.connected = connected,

	.disconnected = disconnected,
};


/*
 * ============================================================
 * Main
 * ============================================================
 */

int main(void)
{
	int err;


	printk("\n\n");

	printk("========================================\n");
	printk("        PLUTO nRF52840 RECEIVER\n");
	printk("========================================\n");

	printk("Firmware starting...\n");


	/*
	 * Initialize Bluetooth.
	 */
	err = bt_enable(NULL);

	if (err) {

		printk(
			"Bluetooth initialization FAILED: %d\n",
			err);

		return 0;
	}


	printk("Bluetooth initialized successfully.\n");


	/*
	 * Register scanner callback.
	 */
	bt_le_scan_cb_register(
		&scan_cb);


	printk("Scanner callback registered.\n");


	/*
	 * Start scanning.
	 */
	start_scanning();


	while (1) {

		k_sleep(
			K_SECONDS(1));
	}


	return 0;
}