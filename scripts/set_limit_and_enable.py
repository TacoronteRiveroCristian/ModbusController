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
        print("Uso: python set_limit_and_enable.py <valor> [config_path]")
        print("\nEjemplos:")
        print("  python set_limit_and_enable.py 50      # 50%")
        print("  python set_limit_and_enable.py 5000    # 50% (valor escalado)")
        print("  python set_limit_and_enable.py 10000   # 100% (valor escalado)")
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
        print(f"\n=== LIMITAR POTENCIA AL {valor} (valor raw) Y HABILITAR ===\n")

        # Estado inicial
        print("Estado inicial:")
        limit_inicial = await controller.read_register("Limitacion_potencia")
        enable_inicial = await controller.read_register("Enable_limitacion")
        timeout_inicial = await controller.read_register("Timeout_limitacion")
        print(f"  Limitación: {int(limit_inicial)}")
        print(f"  Enable: {int(enable_inicial)} ({'HABILITADO' if enable_inicial == 1 else 'DESHABILITADO'})")
        print(f"  Timeout: {int(timeout_inicial)}")

        # Paso 1: Desactivar timeout (CRÍTICO para que el enable se mantenga)
        print(f"\n[1/3] Desactivando timeout automático...")
        await controller.write_register("Timeout_limitacion", 0)
        await asyncio.sleep(0.3)

        timeout_verificado = await controller.read_register("Timeout_limitacion")
        print(f"      Verificado: {int(timeout_verificado)}")

        # Paso 2: Escribir limitación
        print(f"\n[2/3] Escribiendo limitación: {valor}...")
        await controller.write_register("Limitacion_potencia", valor)
        await asyncio.sleep(0.3)

        limit_verificado = await controller.read_register("Limitacion_potencia")
        print(f"      Verificado: {int(limit_verificado)}")

        # Paso 3: Habilitar
        print(f"\n[3/3] Habilitando limitación...")
        await controller.write_register("Enable_limitacion", 1)
        await asyncio.sleep(0.3)

        enable_verificado = await controller.read_register("Enable_limitacion")
        print(f"      Verificado: {int(enable_verificado)} ({'HABILITADO' if enable_verificado == 1 else 'DESHABILITADO'})")

        # Estado final
        print(f"\nEstado final:")
        await asyncio.sleep(1.0)  # Esperar más tiempo para confirmar que se mantiene
        limit_final = await controller.read_register("Limitacion_potencia")
        enable_final = await controller.read_register("Enable_limitacion")
        timeout_final = await controller.read_register("Timeout_limitacion")
        print(f"  Limitación: {int(limit_final)}")
        print(f"  Enable: {int(enable_final)} ({'HABILITADO' if enable_final == 1 else 'DESHABILITADO'})")
        print(f"  Timeout: {int(timeout_final)}")

        if int(enable_final) == 1 and int(limit_final) == valor and int(timeout_final) == 0:
            print(f"\n✓ Limitación al {valor} habilitada correctamente")
        else:
            print(f"\n✗ Advertencia: La configuración no se aplicó correctamente")
            if int(enable_final) != 1:
                print(f"   - Enable debería ser 1 pero es {int(enable_final)}")
            if int(limit_final) != valor:
                print(f"   - Límite debería ser {valor} pero es {int(limit_final)}")
            if int(timeout_final) != 0:
                print(f"   - Timeout debería ser 0 pero es {int(timeout_final)}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
