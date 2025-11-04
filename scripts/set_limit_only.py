#!/usr/bin/env python3
"""Script para establecer solo el límite de potencia (sin habilitar)"""
import asyncio
import sys
from pathlib import Path

# Añadir el directorio padre al path para importar modbus_controller
sys.path.insert(0, str(Path(__file__).parent.parent))

from modbus_controller import ModbusController


async def main():
    if len(sys.argv) < 2:
        print("Uso: python set_limit_only.py <porcentaje> [config_path]")
        print("\nEjemplos:")
        print("  python set_limit_only.py 50")
        print("  python set_limit_only.py 75 configs/otro.json")
        sys.exit(1)

    try:
        porcentaje = int(sys.argv[1])
        if porcentaje < 0 or porcentaje > 100:
            print("Error: El porcentaje debe estar entre 0 y 100")
            sys.exit(1)
    except ValueError:
        print(f"Error: '{sys.argv[1]}' no es un número válido")
        sys.exit(1)

    config_path = sys.argv[2] if len(sys.argv) > 2 else "configs/medidor_potencia.json"

    async with ModbusController(config_path) as controller:
        print(f"\n=== ESTABLECER LIMITACIÓN AL {porcentaje}% (sin habilitar) ===\n")

        # Leer valor actual
        limit_actual = await controller.read_register("Limitacion_potencia")
        print(f"Limitación actual: {int(limit_actual)}% WMax")

        # Escribir nuevo valor
        print(f"\nEscribiendo limitación: {porcentaje}% WMax...")
        await controller.write_register("Limitacion_potencia", porcentaje)
        await asyncio.sleep(0.5)

        # Verificar
        limit_verificado = await controller.read_register("Limitacion_potencia")
        print(f"Limitación verificada: {int(limit_verificado)}% WMax")

        if int(limit_verificado) == porcentaje:
            print(f"\n✓ Limitación establecida al {porcentaje}%")
            print("  (Nota: La limitación NO está habilitada todavía)")
        else:
            print(f"\n✗ Advertencia: Se escribió {porcentaje} pero se leyó {int(limit_verificado)}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
