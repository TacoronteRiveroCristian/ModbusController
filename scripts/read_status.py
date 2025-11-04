#!/usr/bin/env python3
"""Script para leer el estado actual de limitación de potencia"""
import asyncio
import sys
from pathlib import Path

# Añadir el directorio padre al path para importar modbus_controller
sys.path.insert(0, str(Path(__file__).parent.parent))

from modbus_controller import ModbusController


async def main():
    config_path = sys.argv[1] if len(sys.argv) > 1 else "configs/medidor_potencia.json"

    async with ModbusController(config_path) as controller:
        print("\n=== ESTADO ACTUAL ===\n")

        # Leer valores
        potencia = await controller.read_register("Potencia")
        limit = await controller.read_register("Limitacion_potencia")
        enable = await controller.read_register("Enable_limitacion")

        print(f"Potencia actual: {potencia:.2f} W")
        print(f"Limitación: {int(limit)}% WMax")

        estado = "HABILITADO" if int(enable) == 1 else "DESHABILITADO"
        print(f"Estado: {estado} ({int(enable)})")

        print()
        if int(enable) == 1:
            print(f"→ La potencia está limitada al {int(limit)}%")
        else:
            print("→ No hay limitación activa")
        print()


if __name__ == "__main__":
    asyncio.run(main())
