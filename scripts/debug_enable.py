import asyncio
from pathlib import Path
from modbus_controller import ModbusController

async def main():
    config_path = Path(__file__).parent.parent / "configs" / "medidor_potencia.json"
    async with ModbusController(str(config_path)) as controller:
        print("\n=== TEST DE ESCRITURA ENABLE ===\n")

        # Intentar diferentes valores
        valores_a_probar = [1, 1000, 65535, 0, 1]

        for valor in valores_a_probar:
            print(f"\n--- Probando escribir valor: {valor} ---")

            # Escribir
            await controller.write_register("Enable_limitacion", valor)
            await asyncio.sleep(1)

            # Leer inmediatamente
            leido = await controller.read_register("Enable_limitacion")
            print(f"Valor leído después de escribir: {int(leido)}")

            if int(leido) == valor:
                print(f"✓ El valor {valor} se mantuvo!")
                break
            else:
                print(f"✗ Se escribió {valor} pero se leyó {int(leido)}")

asyncio.run(main())
