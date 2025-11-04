"""
Probar si el timeout se mantiene en 0 después de deshabilitar/habilitar
"""
import asyncio
from pymodbus.client import AsyncModbusTcpClient

async def read_registers(client, description):
    """Lee los 3 registros principales"""
    print(f"\n{description}")

    limit = await client.read_holding_registers(address=40242, count=1, device_id=1)
    timeout = await client.read_holding_registers(address=40244, count=1, device_id=1)
    enable = await client.read_holding_registers(address=40246, count=1, device_id=1)

    print(f"  Límite:  {limit.registers[0]}")
    print(f"  Timeout: {timeout.registers[0]} ({'PERSISTENTE' if timeout.registers[0] == 0 else 'AUTO-RESET'})")
    print(f"  Enable:  {enable.registers[0]} ({'ON' if enable.registers[0] == 1 else 'OFF'})")

    return timeout.registers[0]

async def main():
    client = AsyncModbusTcpClient(host="10.142.230.136", port=502, timeout=3)
    await client.connect()

    if not client.connected:
        print("No se pudo conectar")
        return

    print("="*70)
    print("PRUEBA DE PERSISTENCIA DEL TIMEOUT")
    print("="*70)

    # Estado inicial
    timeout_inicial = await read_registers(client, ">>> ESTADO INICIAL")

    # Configurar timeout a 0
    print("\n>>> PASO 1: Configurar Timeout=0")
    await client.write_register(address=40244, value=0, device_id=1)
    await asyncio.sleep(0.2)
    await read_registers(client, "    Estado después de escribir Timeout=0")

    # Habilitar
    print("\n>>> PASO 2: Habilitar limitación")
    await client.write_register(address=40246, value=1, device_id=1)
    await asyncio.sleep(0.2)
    await read_registers(client, "    Estado después de Enable=1")

    # Esperar 2 segundos para confirmar que se mantiene
    print("\n>>> PASO 3: Esperar 2 segundos...")
    await asyncio.sleep(2)
    timeout_con_enable = await read_registers(client, "    Estado después de 2s")

    # Deshabilitar
    print("\n>>> PASO 4: Deshabilitar limitación")
    await client.write_register(address=40246, value=0, device_id=1)
    await asyncio.sleep(0.2)
    timeout_despues_disable = await read_registers(client, "    Estado después de Disable")

    # Esperar 2 segundos más
    print("\n>>> PASO 5: Esperar otros 2 segundos...")
    await asyncio.sleep(2)
    timeout_final = await read_registers(client, "    Estado final")

    # Resumen
    print("\n" + "="*70)
    print("RESUMEN")
    print("="*70)
    print(f"Timeout inicial:              {timeout_inicial}")
    print(f"Timeout con Enable activo:    {timeout_con_enable}")
    print(f"Timeout después de Disable:   {timeout_despues_disable}")
    print(f"Timeout final (después de 2s):{timeout_final}")

    if timeout_despues_disable == 0 and timeout_final == 0:
        print("\n✓ El Timeout se MANTIENE en 0 después de deshabilitar")
        print("  → Puedes habilitar/deshabilitar sin reconfigurarlo")
    else:
        print("\n✗ El Timeout se RESETEA a 1")
        print("  → Necesitas configurarlo a 0 cada vez que habilites")

if __name__ == "__main__":
    asyncio.run(main())
