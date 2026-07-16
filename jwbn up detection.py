from bleak import BleakScanner, BleakClient
import asyncio

TARGET_ADDRESS = "CD:6D:1C:A7:43:9D"

async def main():
    print("Scanning for nearby BLE devices...")
    devices = await BleakScanner.discover(timeout=10)

    if devices:
        print("Nearby BLE devices:")
        for device in devices:
            print(f"- {device.name or 'Unknown device'} ({device.address})")

    target = next((d for d in devices if d.address.upper() == TARGET_ADDRESS.upper()), None)

    if not target:
        print(f"Target device not found in scan: {TARGET_ADDRESS}")
        return

    print(f"Discovered target device: {target.name or 'Unknown device'} ({target.address})")
    print(f"Connecting using MAC address {TARGET_ADDRESS}...")

    try:
        async with BleakClient(target.address, timeout=10) as client:
            connected = client.is_connected
            print("Connected:", connected)

            print("Reading GATT services...")
            for service in client.services:
                print(service.uuid)
                for char in service.characteristics:
                    print(" ", char.uuid, char.properties)
    except Exception as ex:
        print("Connection failed:", ex)

asyncio.run(main())