"""
Escanear registros alrededor del Enable para entender el contexto
"""
import asyncio
from pymodbus.client import AsyncModbusTcpClient

async def main():
    client = AsyncModbusTcpClient(host="10.142.230.136", port=502, timeout=3)
    await client.connect()

    if not client.connected:
        print("No se pudo conectar")
        return

    print("Conectado exitosamente\n")
    print("=== ESCANEANDO REGISTROS ALREDEDOR DE ENABLE (40240-40250) ===\n")

    # Escanear registros alrededor
    for addr in range(40240, 40251):
        try:
            response = await client.read_holding_registers(address=addr, count=1, device_id=1)
            if not response.isError():
                value = response.registers[0]

                # Nombres conocidos
                names = {
                    40242: "Limitacion_potencia (WMaxLimPct)",
                    40246: "Enable_limitacion (WMaxLim_Ena)"
                }

                name = names.get(addr, "?")
                marker = " <---" if addr in [40242, 40246] else ""
                print(f"Addr {addr}: {value:5d} (0x{value:04X})  {name}{marker}")
            else:
                print(f"Addr {addr}: ERROR - {response}")
        except Exception as e:
            print(f"Addr {addr}: EXCEPTION - {e}")

        await asyncio.sleep(0.1)

    print("\n=== ESCRIBIENDO Enable=1 ===\n")
    response = await client.write_register(address=40246, value=1, device_id=1)
    print(f"Respuesta: {response}")

    # Leer de nuevo inmediatamente
    print("\n=== RELEYENDO INMEDIATAMENTE DESPUÉS DE ESCRIBIR ===\n")
    for addr in range(40240, 40251):
        try:
            response = await client.read_holding_registers(address=addr, count=1, device_id=1)
            if not response.isError():
                value = response.registers[0]
                names = {
                    40242: "Limitacion_potencia (WMaxLimPct)",
                    40246: "Enable_limitacion (WMaxLim_Ena)"
                }
                name = names.get(addr, "?")
                marker = " <---" if addr in [40242, 40246] else ""
                print(f"Addr {addr}: {value:5d} (0x{value:04X})  {name}{marker}")
        except Exception as e:
            print(f"Addr {addr}: EXCEPTION - {e}")
        await asyncio.sleep(0.1)

if __name__ == "__main__":
    asyncio.run(main())
