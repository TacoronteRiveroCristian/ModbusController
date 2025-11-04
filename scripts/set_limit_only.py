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
        print("Uso: python set_limit_only.py <valor> [config_path]")
        print("\nEjemplos:")
        print("  python set_limit_only.py 50      # Valor 50")
        print("  python set_limit_only.py 5000    # Valor 5000 (50% escalado)")
        print("  python set_limit_only.py 10000   # Valor 10000 (100% escalado)")
        sys.exit(1)

    try:
        valor = int(sys.argv[1])
        if valor < 0 or valor > 65535:
            print("Error: El valor debe estar entre 0 y 65535")
            sys.exit(1)
    except ValueError:
        print(f"Error: '{sys.argv[1]}' no es un número válido")
        sys.exit(1)

    config_path = sys.argv[2] if len(sys.argv) > 2 else "configs/medidor_potencia.json"

    async with ModbusController(config_path) as controller:
        print(f"\n=== ESTABLECER LIMITACIÓN AL {valor} (sin habilitar) ===\n")

        # Leer valor actual
        limit_actual = await controller.read_register("Limitacion_potencia")
        print(f"Limitación actual: {int(limit_actual)}")

        # Escribir nuevo valor
        print(f"\nEscribiendo limitación: {valor}...")
        await controller.write_register("Limitacion_potencia", valor)
        await asyncio.sleep(0.5)

        # Verificar
        limit_verificado = await controller.read_register("Limitacion_potencia")
        print(f"Limitación verificada: {int(limit_verificado)}")

        if int(limit_verificado) == valor:
            print(f"\n✓ Limitación establecida al {valor}")
            print("  (Nota: La limitación NO está habilitada todavía)")
        else:
            print(f"\n✗ Advertencia: Se escribió {valor} pero se leyó {int(limit_verificado)}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
