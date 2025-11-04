#!/usr/bin/env python3
"""Script para establecer límite de potencia y habilitarlo"""
import asyncio
import sys
from pathlib import Path

# Añadir el directorio padre al path para importar modbus_controller
sys.path.insert(0, str(Path(__file__).parent.parent))

from modbus_controller import ModbusController


async def main():
    if len(sys.argv) < 2:
        print("Uso: python set_limit_and_enable.py <porcentaje> [config_path]")
        print("\nEjemplos:")
        print("  python set_limit_and_enable.py 50")
        print("  python set_limit_and_enable.py 75 configs/otro.json")
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
        print(f"\n=== LIMITAR POTENCIA AL {porcentaje}% Y HABILITAR ===\n")

        # Estado inicial
        print("Estado inicial:")
        limit_inicial = await controller.read_register("Limitacion_potencia")
        enable_inicial = await controller.read_register("Enable_limitacion")
        print(f"  Limitación: {int(limit_inicial)}% WMax")
        print(f"  Enable: {int(enable_inicial)} ({'HABILITADO' if enable_inicial == 1 else 'DESHABILITADO'})")

        # Paso 1: Escribir limitación
        print(f"\n[1/2] Escribiendo limitación: {porcentaje}% WMax...")
        await controller.write_register("Limitacion_potencia", porcentaje)
        await asyncio.sleep(0.5)

        limit_verificado = await controller.read_register("Limitacion_potencia")
        print(f"      Verificado: {int(limit_verificado)}% WMax")

        # Paso 2: Habilitar
        print(f"\n[2/2] Habilitando limitación...")
        await controller.write_register("Enable_limitacion", 1)
        await asyncio.sleep(0.5)

        enable_verificado = await controller.read_register("Enable_limitacion")
        print(f"      Verificado: {int(enable_verificado)} ({'HABILITADO' if enable_verificado == 1 else 'DESHABILITADO'})")

        # Estado final
        print(f"\nEstado final:")
        await asyncio.sleep(0.5)
        limit_final = await controller.read_register("Limitacion_potencia")
        enable_final = await controller.read_register("Enable_limitacion")
        print(f"  Limitación: {int(limit_final)}% WMax")
        print(f"  Enable: {int(enable_final)} ({'HABILITADO' if enable_final == 1 else 'DESHABILITADO'})")

        if int(enable_final) == 1 and int(limit_final) == porcentaje:
            print(f"\n✓ Limitación al {porcentaje}% habilitada correctamente")
        else:
            print(f"\n✗ Advertencia: La configuración no se aplicó correctamente")
        print()


if __name__ == "__main__":
    asyncio.run(main())
