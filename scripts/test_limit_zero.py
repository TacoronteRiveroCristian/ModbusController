"""
Probar si el dispositivo acepta Enable=1 cuando el límite es 0%
"""
import asyncio
from pymodbus.client import AsyncModbusTcpClient

async def test_scenario(client, limit_value, enable_value, description):
    """Prueba un escenario específico"""
    addr_limit = 40242
    addr_enable = 40246

    print(f"\n{'='*60}")
    print(f"ESCENARIO: {description}")
    print(f"  Límite: {limit_value}%")
    print(f"  Enable: {enable_value}")
    print(f"{'='*60}")

    # Escribir límite
    print(f"\n1. Escribiendo límite={limit_value}%...")
    response = await client.write_register(address=addr_limit, value=limit_value, device_id=1)
    if response.isError():
        print(f"   ✗ Error: {response}")
        return
    print(f"   ✓ Límite escrito")

    await asyncio.sleep(0.2)

    # Leer límite
    response = await client.read_holding_registers(address=addr_limit, count=1, device_id=1)
    if not response.isError():
        print(f"   Límite verificado: {response.registers[0]}%")

    # Escribir enable
    print(f"\n2. Escribiendo Enable={enable_value}...")
    response = await client.write_register(address=addr_enable, value=enable_value, device_id=1)
    if response.isError():
        print(f"   ✗ Error: {response}")
        return
    print(f"   ✓ Enable escrito")

    # Verificar en diferentes momentos
    for delay in [0.05, 0.1, 0.2, 0.5, 1.0, 2.0]:
        await asyncio.sleep(delay - (0.05 if delay > 0.05 else 0))
        response = await client.read_holding_registers(address=addr_enable, count=1, device_id=1)

        if not response.isError():
            enable_read = response.registers[0]
            status = "✓" if enable_read == enable_value else "✗"
            print(f"   {status} Enable después de {delay}s: {enable_read}")

            if enable_read != enable_value:
                print(f"      (cambió de {enable_value} a {enable_read})")
                break


async def main():
    client = AsyncModbusTcpClient(host="10.142.230.136", port=502, timeout=3)
    await client.connect()

    if not client.connected:
        print("No se pudo conectar")
        return

    print("Conectado exitosamente\n")

    # Escenarios a probar
    await test_scenario(client, 0, 1, "Límite 0% + Enable")
    await asyncio.sleep(1)

    await test_scenario(client, 10, 1, "Límite 10% + Enable")
    await asyncio.sleep(1)

    await test_scenario(client, 50, 1, "Límite 50% + Enable")
    await asyncio.sleep(1)

    # Probar escribir ambos muy rápido (sin sleep)
    print(f"\n{'='*60}")
    print("PRUEBA ESPECIAL: Escribir límite y enable SIN delay")
    print(f"{'='*60}")

    addr_limit = 40242
    addr_enable = 40246

    print("\nEscribiendo límite=30% y enable=1 inmediatamente...")
    await client.write_register(address=addr_limit, value=30, device_id=1)
    await client.write_register(address=addr_enable, value=1, device_id=1)

    # Verificar
    for delay in [0.05, 0.2, 0.5, 1.0, 2.0]:
        await asyncio.sleep(delay - (0.05 if delay > 0.05 else 0))
        response = await client.read_holding_registers(address=addr_enable, count=1, device_id=1)

        if not response.isError():
            enable_read = response.registers[0]
            print(f"   Enable después de {delay}s: {enable_read}")

if __name__ == "__main__":
    asyncio.run(main())
