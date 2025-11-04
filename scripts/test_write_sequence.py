"""
Script para probar la secuencia correcta de escritura
"""
import asyncio
from pymodbus.client import AsyncModbusTcpClient

async def read_register(client, address, name):
    """Lee un registro y muestra el valor"""
    response = await client.read_holding_registers(address=address, count=1, device_id=1)
    if not response.isError():
        value = response.registers[0]
        print(f"{name} (addr {address}): {value}")
        return value
    else:
        print(f"Error leyendo {name}: {response}")
        return None

async def write_register(client, address, value, name):
    """Escribe un registro y muestra el resultado"""
    response = await client.write_register(address=address, value=value, device_id=1)
    if not response.isError():
        print(f"✓ Escribió {value} en {name} (addr {address})")
    else:
        print(f"✗ Error escribiendo en {name}: {response}")
    return response

async def main():
    # Conectar
    client = AsyncModbusTcpClient(host="10.142.230.136", port=502, timeout=3)
    await client.connect()

    if not client.connected:
        print("No se pudo conectar")
        return

    print("Conectado exitosamente\n")

    # Direcciones
    addr_limitacion = 40242  # Limitacion_potencia (%)
    addr_enable = 40246      # Enable_limitacion

    # Leer estado inicial
    print("=== ESTADO INICIAL ===")
    await read_register(client, addr_limitacion, "Limitacion_potencia")
    await read_register(client, addr_enable, "Enable_limitacion")

    # Probar secuencia 1: Escribir solo enable
    print("\n=== PRUEBA 1: Solo escribir Enable=1 ===")
    await write_register(client, addr_enable, 1, "Enable_limitacion")
    await asyncio.sleep(0.5)
    await read_register(client, addr_enable, "Enable_limitacion")

    # Probar secuencia 2: Escribir límite primero, luego enable
    print("\n=== PRUEBA 2: Escribir Limite=50%, luego Enable=1 ===")
    await write_register(client, addr_limitacion, 50, "Limitacion_potencia")
    await asyncio.sleep(0.5)
    await read_register(client, addr_limitacion, "Limitacion_potencia")

    await write_register(client, addr_enable, 1, "Enable_limitacion")
    await asyncio.sleep(0.5)
    await read_register(client, addr_enable, "Enable_limitacion")

    # Esperar un poco más y leer de nuevo
    await asyncio.sleep(2)
    print("\n=== ESTADO DESPUÉS DE 2 SEGUNDOS ===")
    await read_register(client, addr_limitacion, "Limitacion_potencia")
    await read_register(client, addr_enable, "Enable_limitacion")

    # Probar con diferentes valores de enable
    print("\n=== PRUEBA 3: Escribir Enable con valores enum ===")
    for valor in [0, 1, 2, 65535]:
        print(f"\nProbando Enable={valor}")
        await write_register(client, addr_enable, valor, "Enable_limitacion")
        await asyncio.sleep(0.5)
        result = await read_register(client, addr_enable, "Enable_limitacion")
        if result == valor:
            print(f"  ✓ Valor mantenido!")
            break

    # Cerrar conexión
    connection = await client.protocol.close()

if __name__ == "__main__":
    asyncio.run(main())
