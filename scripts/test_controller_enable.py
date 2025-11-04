"""
Test detallado del controller con Enable_limitacion
"""
import asyncio
from pathlib import Path
from modbus_controller import ModbusController

async def main():
    config_path = Path(__file__).parent.parent / "configs" / "medidor_potencia.json"

    async with ModbusController(str(config_path)) as controller:
        print("\n=== TEST DETALLADO CON MODBUS CONTROLLER ===\n")

        # Leer estado inicial
        print("1. Leyendo estado inicial...")
        enable_inicial = await controller.read_register("Enable_limitacion")
        limit_inicial = await controller.read_register("Limitacion_potencia")
        print(f"   Enable: {int(enable_inicial)}")
        print(f"   Limite: {int(limit_inicial)}")

        # Escribir límite primero
        print("\n2. Configurando límite de potencia a 50%...")
        await controller.write_register("Limitacion_potencia", 50)
        await asyncio.sleep(0.5)
        limit_leido = await controller.read_register("Limitacion_potencia")
        print(f"   Límite configurado: {int(limit_leido)}")

        # Escribir enable = 1
        print("\n3. Habilitando limitación (Enable=1)...")
        try:
            await controller.write_register("Enable_limitacion", 1)
            print("   ✓ Escritura completada sin errores")
        except Exception as e:
            print(f"   ✗ Error al escribir: {e}")
            return

        # Leer con diferentes delays
        for delay in [0.1, 0.5, 1.0, 2.0]:
            await asyncio.sleep(delay)
            enable_leido = await controller.read_register("Enable_limitacion")
            print(f"   Enable después de {delay}s: {int(enable_leido)}")

        # Probar con valor 0
        print("\n4. Deshabilitando limitación (Enable=0)...")
        await controller.write_register("Enable_limitacion", 0)
        await asyncio.sleep(0.5)
        enable_leido = await controller.read_register("Enable_limitacion")
        print(f"   Enable: {int(enable_leido)}")

        # Probar secuencia rápida
        print("\n5. Probando secuencia rápida (sin sleep)...")
        await controller.write_register("Enable_limitacion", 1)
        enable_leido = await controller.read_register("Enable_limitacion")
        print(f"   Enable inmediatamente después: {int(enable_leido)}")

if __name__ == "__main__":
    asyncio.run(main())
