"""
Script para probar diferentes parámetros de escritura en pymodbus
"""
import asyncio
from pymodbus.client import AsyncModbusTcpClient

async def main():
    # Conectar al servidor
    client = AsyncModbusTcpClient(host="10.142.230.136", port=502, timeout=3)
    await client.connect()

    if not client.connected:
        print("No se pudo conectar")
        return

    print("Conectado exitosamente\n")

    # Dirección del registro Enable_limitacion
    address = 40246

    # Probar lectura primero
    print(f"=== Leyendo dirección {address} ===")
    response = await client.read_holding_registers(address=address, count=1, device_id=1)
    if not response.isError():
        print(f"Valor actual: {response.registers[0]}")
    else:
        print(f"Error al leer: {response}")

    # Probar escritura SIN device_id parameter
    print(f"\n=== Escribiendo valor 1 SIN device_id parameter (default=1) ===")
    response = await client.write_register(address=address, value=1)
    print(f"Respuesta: {response}")
    print(f"Is Error: {response.isError()}")

    await asyncio.sleep(1)

    # Leer de nuevo
    response = await client.read_holding_registers(address=address, count=1, device_id=1)
    if not response.isError():
        print(f"Valor después de escribir: {response.registers[0]}")

    # Probar escritura CON device_id parameter
    print(f"\n=== Escribiendo valor 1 CON device_id=1 ===")
    response = await client.write_register(address=address, value=1, device_id=1)
    print(f"Respuesta: {response}")
    print(f"Is Error: {response.isError()}")

    await asyncio.sleep(1)

    # Leer de nuevo
    response = await client.read_holding_registers(address=address, count=1, device_id=1)
    if not response.isError():
        print(f"Valor después de escribir: {response.registers[0]}")

    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
