"""
Escanear registros SunSpec alrededor de WMaxLim para encontrar Conn_RvrtTms y otros
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
    print("="*80)
    print("ESCANEANDO REGISTROS SUNSPEC (MODELO 123 - IMMEDIATE CONTROLS)")
    print("="*80)

    # Según SunSpec, los registros suelen estar agrupados
    # Escanear un rango más amplio alrededor de WMaxLimPct (40242) y WMaxLim_Ena (40246)
    ranges_to_scan = [
        (40230, 40260, "Área alrededor de WMaxLim"),
        (40240, 40255, "Área inmediata (detallada)"),
    ]

    for start, end, description in ranges_to_scan:
        print(f"\n### {description} (registros {start}-{end}) ###\n")

        for addr in range(start, end + 1):
            try:
                response = await client.read_holding_registers(address=addr, count=1, device_id=1)

                if not response.isError():
                    value = response.registers[0]

                    # Nombres conocidos
                    known_names = {
                        40242: "WMaxLimPct (Limit %)",
                        40246: "WMaxLim_Ena (Enable)",
                    }

                    # Posibles candidatos para Conn_RvrtTms basados en el offset
                    # En SunSpec Model 123, típicamente:
                    # - Conn está antes de WMaxLim
                    # - Conn_WinTms y Conn_RvrtTms están juntos
                    possible_names = {
                        40240: "Conn? o WinTms?",
                        40241: "Conn_WinTms? o RvrtTms?",
                        40243: "WMaxLimPct_SF? (scale factor)",
                        40244: "¿Timeout/RvrtTms?",
                        40245: "¿WinTms?",
                        40247: "WMaxLimPct_RvrtTms?",
                        40248: "¿Otro parámetro?",
                    }

                    name = known_names.get(addr) or possible_names.get(addr, "")
                    marker = " <<<" if addr in [40242, 40246] else ""

                    # Resaltar registros con valores interesantes
                    if value > 0 and value < 1000:
                        highlight = " *"
                    else:
                        highlight = ""

                    print(f"  {addr}: {value:6d} (0x{value:04X})  {name}{marker}{highlight}")

                else:
                    print(f"  {addr}: ERROR - {response}")

            except Exception as e:
                print(f"  {addr}: EXCEPTION - {e}")

            await asyncio.sleep(0.05)

    # Ahora intentar escribir en posibles candidatos
    print(f"\n\n{'='*80}")
    print("PROBANDO ESCRITURA EN POSIBLES REGISTROS DE TIMEOUT")
    print(f"{'='*80}\n")

    candidates_for_timeout = [40240, 40241, 40244, 40245, 40247, 40248]

    for addr in candidates_for_timeout:
        print(f"\n>>> Probando registro {addr}")

        # Leer valor actual
        response = await client.read_holding_registers(address=addr, count=1, device_id=1)
        if response.isError():
            print(f"    Error al leer: {response}")
            continue

        original_value = response.registers[0]
        print(f"    Valor original: {original_value}")

        # Intentar escribir 0 (timeout infinito)
        print(f"    Intentando escribir 0...")
        response = await client.write_register(address=addr, value=0, device_id=1)

        if response.isError():
            print(f"    ✗ Error al escribir: {response}")
        else:
            print(f"    ✓ Escritura exitosa")

            # Restaurar valor original
            await asyncio.sleep(0.1)
            await client.write_register(address=addr, value=original_value, device_id=1)

if __name__ == "__main__":
    asyncio.run(main())
