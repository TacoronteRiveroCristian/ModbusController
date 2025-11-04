"""
Probar diferentes formatos de dirección
"""
import asyncio
from pymodbus.client import AsyncModbusTcpClient

async def test_address(client, address, name):
    """Prueba leer y escribir en una dirección"""
    print(f"\n=== Probando dirección {address} ({name}) ===")

    # Leer
    print(f"Leyendo...")
    response = await client.read_holding_registers(address=address, count=1, device_id=1)
    if not response.isError():
        value = response.registers[0]
        print(f"  Valor actual: {value}")
    else:
        print(f"  Error al leer: {response}")
        return

    # Escribir valor de prueba
    test_value = 1
    print(f"Escribiendo {test_value}...")
    response = await client.write_register(address=address, value=test_value, device_id=1)
    if not response.isError():
        print(f"  ✓ Escritura exitosa")
    else:
        print(f"  ✗ Error al escribir: {response}")
        return

    # Leer de nuevo inmediatamente
    await asyncio.sleep(0.1)
    response = await client.read_holding_registers(address=address, count=1, device_id=1)
    if not response.isError():
        value = response.registers[0]
        print(f"  Valor después de escribir: {value}")
        if value == test_value:
            print(f"  ✓ Valor se mantuvo!")
        else:
            print(f"  ✗ Valor se cambió a {value}")
    else:
        print(f"  Error al leer: {response}")

async def main():
    client = AsyncModbusTcpClient(host="10.142.230.136", port=502, timeout=3)
    await client.connect()

    if not client.connected:
        print("No se pudo conectar")
        return

    print("Conectado exitosamente")

    # Probar dirección 40246 (notación Modbus con prefijo)
    await test_address(client, 40246, "Dirección 40246 (con prefijo)")

    # Probar dirección 245 (40246 - 40001 = 245, dirección física)
    await test_address(client, 245, "Dirección 245 (sin prefijo, 40246-40001)")

    # Probar Limitacion_potencia también
    print("\n" + "="*60)
    await test_address(client, 40242, "Limitacion_potencia con prefijo (40242)")
    await test_address(client, 241, "Limitacion_potencia sin prefijo (241)")

if __name__ == "__main__":
    asyncio.run(main())
