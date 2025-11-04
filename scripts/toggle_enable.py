#!/usr/bin/env python3
"""Script para habilitar/deshabilitar la limitación de potencia"""
import asyncio
import sys
from pathlib import Path

# Añadir el directorio padre al path para importar modbus_controller
sys.path.insert(0, str(Path(__file__).parent.parent))

from modbus_controller import ModbusController


async def main():
    if len(sys.argv) < 2:
        print("Uso: python toggle_enable.py [enable|disable|1|0] [config_path]")
        print("\nEjemplos:")
        print("  python toggle_enable.py enable")
        print("  python toggle_enable.py disable")
        print("  python toggle_enable.py 1")
        print("  python toggle_enable.py 0")
        sys.exit(1)

    # Interpretar argumento
    arg = sys.argv[1].lower()
    if arg in ['enable', '1', 'on', 'enabled']:
        nuevo_valor = 1
        accion = "HABILITAR"
    elif arg in ['disable', '0', 'off', 'disabled']:
        nuevo_valor = 0
        accion = "DESHABILITAR"
    else:
        print(f"Argumento inválido: {sys.argv[1]}")
        print("Use: enable, disable, 1 o 0")
        sys.exit(1)

    config_path = sys.argv[2] if len(sys.argv) > 2 else "configs/medidor_potencia.json"

    async with ModbusController(config_path) as controller:
        print(f"\n=== {accion} LIMITACIÓN DE POTENCIA ===\n")

        # Estado actual
        estado_actual = await controller.read_register("Enable_limitacion")
        estado_texto = "HABILITADO" if estado_actual == 1 else "DESHABILITADO"
        print(f"Estado actual: {estado_texto} ({int(estado_actual)})")

        # Escribir nuevo valor
        print(f"\nEscribiendo: {nuevo_valor} ({'HABILITADO' if nuevo_valor == 1 else 'DESHABILITADO'})...")
        await controller.write_register("Enable_limitacion", nuevo_valor)
        await asyncio.sleep(0.5)

        # Verificar
        estado_verificado = await controller.read_register("Enable_limitacion")
        estado_verificado_texto = "HABILITADO" if estado_verificado == 1 else "DESHABILITADO"
        print(f"Estado verificado: {estado_verificado_texto} ({int(estado_verificado)})")

        if int(estado_verificado) == nuevo_valor:
            print(f"\n✓ Limitación {accion.lower()}da correctamente")
        else:
            print(f"\n✗ Advertencia: Se escribió {nuevo_valor} pero se leyó {int(estado_verificado)}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
