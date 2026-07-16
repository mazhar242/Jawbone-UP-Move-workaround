from bleak import BleakScanner, BleakClient
import asyncio
import logging
import sys

TARGET_ADDRESS = "CD:6D:1C:A7:43:9D"
DEVICE_NAME = "UP MOVE"
SESSION_DURATION_SECONDS = 30 * 60
OUTPUT_LOG = "upmove_output.log"

logging.basicConfig(
    filename=OUTPUT_LOG,
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    force=True,
)
logger = logging.getLogger("upmove")
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(sys.stdout))

KEEPALIVE_UUIDS = [
    "00002a00-0000-1000-8000-00805f9b34fb",
    "00002a01-0000-1000-8000-00805f9b34fb",
    "00002a04-0000-1000-8000-00805f9b34fb",
]

NOTIFY_UUIDS = [
    "f7c9b162-6658-4390-b53c-1de5e1453654",
    "f7c9ba82-6658-4390-b53c-1de5e1453654",
    "f7c9ba91-6658-4390-b53c-1de5e1453654",
]

WRITE_UUID = "f7c9b162-6658-4390-b53c-1de5e1453654"

client = None


def log(msg):
    logger.info(msg)
    print(msg)


def notify_handler(sender, data):
    log(f"NOTIFY {sender}: {data.hex()}")


async def scan():
    print("Scanning...")
    devices = await BleakScanner.discover(timeout=5)

    for device in devices:
        device_name = (device.name or "").upper()
        if device.address.upper() == TARGET_ADDRESS.upper() or device_name == DEVICE_NAME.upper():
            print(f"Found {device.name or 'Unknown device'} {device.address}")
            return device

    return None


async def connect():
    global client

    while True:
        device = await scan()

        if device is None:
            print("Device not found, retrying...")
            await asyncio.sleep(2)
            continue

        try:
            client = BleakClient(device, timeout=15)
            await client.connect(timeout=15)

            if client.is_connected:
                log("CONNECTED")
                return

        except Exception as exc:
            print(f"Connect failed: {exc}")

        await asyncio.sleep(2)


async def discover():
    print("\nServices\n")

    for service in client.services:
        print(service.uuid)
        for characteristic in service.characteristics:
            print("   ", characteristic.uuid, characteristic.properties)


async def subscribe():
    subscribed = False
    notify_candidates = []

    for service in client.services:
        for characteristic in service.characteristics:
            if "notify" in characteristic.properties:
                notify_candidates.append(characteristic.uuid)

    if not notify_candidates:
        log("No notify-capable characteristics were found on this device.")
        return

    for uuid in notify_candidates:
        try:
            await client.start_notify(uuid, notify_handler)
            log(f"Subscribed {uuid}")
            subscribed = True
        except Exception as exc:
            log(f"Cannot subscribe {uuid}: {exc}")

    if not subscribed:
        log("No notify subscriptions could be established.")


async def keepalive():
    while True:
        if client is None or not client.is_connected:
            return

        for uuid in KEEPALIVE_UUIDS:
            try:
                await client.read_gatt_char(uuid)
            except Exception as exc:
                log(f"Keepalive error {uuid}: {exc}")

        await asyncio.sleep(1)


async def console():
    while True:
        cmd = await asyncio.to_thread(input, "\nUPMOVE> ")

        if cmd == "quit":
            return

        if cmd == "services":
            await discover()

        elif cmd.startswith("read "):
            uuid = cmd.split()[1]
            try:
                data = await client.read_gatt_char(uuid)
                print(data.hex())
            except Exception as exc:
                print(exc)

        elif cmd.startswith("write "):
            parts = cmd.split()
            uuid = parts[1]
            data = bytes.fromhex(parts[2])
            try:
                await client.write_gatt_char(uuid, data)
                log(f"WRITE {uuid}: {data.hex()}")
            except Exception as exc:
                print(exc)

        elif cmd == "info":
            for uuid in [
                "00002a29-0000-1000-8000-00805f9b34fb",
                "00002a24-0000-1000-8000-00805f9b34fb",
                "00002a26-0000-1000-8000-00805f9b34fb",
            ]:
                try:
                    data = await client.read_gatt_char(uuid)
                    print(uuid, data.decode(errors="ignore"))
                except Exception:
                    pass

        else:
            print("Commands:")
            print(" info")
            print(" services")
            print(" read <uuid>")
            print(" write <uuid> <hex>")
            print(" quit")


async def session():
    keepalive_task = None

    try:
        await connect()
        await discover()
        await subscribe()

        keepalive_task = asyncio.create_task(keepalive())
        print(f"Keeping connection alive for {SESSION_DURATION_SECONDS // 60} minutes...")
        await asyncio.sleep(SESSION_DURATION_SECONDS)

    finally:
        if keepalive_task is not None:
            keepalive_task.cancel()
            try:
                await keepalive_task
            except asyncio.CancelledError:
                pass

        if client is not None and client.is_connected:
            await client.disconnect()


asyncio.run(session())