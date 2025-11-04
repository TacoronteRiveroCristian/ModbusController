"""
Test con logging detallado del controller
"""
import asyncio
import logging
from pathlib import Path
from modbus_controller import ModbusController

# Habilitar logging detallado
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    config_path = Path(__file__).parent.parent / "configs" / "medidor_potencia.json"

    async with ModbusController(str(config_path)) as controller:
        print("\n" + "="*70)
        print("TEST CON LOGGING DETALLADO")
        print("="*70)

        # Configurar límite primero
        print("\n>>> Paso 1: Configurar límite a 50%")
        await controller.write_register("Limitacion_potencia", 50)
        await asyncio.sleep(0.3)

        # Verificar límite
        limit = await controller.read_register("Limitacion_potencia")
        print(f"    Límite verificado: {int(limit)}%")

        # Escribir Enable
        print("\n>>> Paso 2: Escribir Enable=1")
        print("    Llamando a write_register...")

        try:
            await controller.write_register("Enable_limitacion", 1)
            print("    ✓ write_register completado sin excepciones")
        except Exception as e:
            print(f"    ✗ EXCEPCIÓN: {e}")
            import traceback
            traceback.print_exc()
            return

        # Verificar inmediatamente
        print("\n>>> Paso 3: Verificar Enable inmediatamente")
        enable = await controller.read_register("Enable_limitacion")
        print(f"    Enable leído: {int(enable)}")

        # Verificar después de delay
        for delay in [0.1, 0.5, 1.0]:
            await asyncio.sleep(delay)
            enable = await controller.read_register("Enable_limitacion")
            print(f"    Enable después de {delay}s: {int(enable)}")

if __name__ == "__main__":
    asyncio.run(main())
