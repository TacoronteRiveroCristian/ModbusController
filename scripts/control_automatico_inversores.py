#!/usr/bin/env python3
"""
Script de control automático de inversores según horario y día de la semana

Lógica:
- Fines de semana (sábado y domingo): DISABLE (producción normal, no hay gente)
- Entre 16:00 y 18:59 en días laborables: LIMIT 0% (evitar excedentes)
- Resto del tiempo: DISABLE (producción normal)

Se aplica a ambos inversores:
- 10.142.230.136 (config: medidor_potencia.json)
- 10.142.230.135 (config: medidor_potencia_135.json)
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Añadir el directorio padre al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modbus_controller import ModbusController


# Configuración de inversores (rutas absolutas calculadas desde el directorio del script)
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent

INVERSORES = [
    {
        "nombre": "Inversor 136",
        "config": str(PROJECT_DIR / "configs" / "medidor_potencia.json"),
        "ip": "10.142.230.136"
    },
    {
        "nombre": "Inversor 135",
        "config": str(PROJECT_DIR / "configs" / "medidor_potencia_135.json"),
        "ip": "10.142.230.135"
    }
]


async def aplicar_disable(controller, nombre):
    """Deshabilita la limitación (producción normal)"""
    print(f"  [{nombre}] Deshabilitando limitación...")
    await controller.write_register("Enable_limitacion", 0)
    await asyncio.sleep(0.3)

    # Verificar
    enable = await controller.read_register("Enable_limitacion")
    if int(enable) == 0:
        print(f"  [{nombre}] ✓ DISABLE aplicado (producción normal)")
        return True
    else:
        print(f"  [{nombre}] ✗ Error: Enable={int(enable)}")
        return False


async def aplicar_limit_cero(controller, nombre):
    """Aplica límite 0% con enable (sin excedentes)"""
    print(f"  [{nombre}] Aplicando límite 0% (sin excedentes)...")

    # 1. Configurar timeout
    await controller.write_register("Timeout_limitacion", 0)
    await asyncio.sleep(0.2)

    # 2. Configurar límite a 0%
    await controller.write_register("Limitacion_potencia", 0)
    await asyncio.sleep(0.2)

    # 3. Habilitar
    await controller.write_register("Enable_limitacion", 1)
    await asyncio.sleep(0.3)

    # Verificar
    enable = await controller.read_register("Enable_limitacion")
    limit = await controller.read_register("Limitacion_potencia")

    if int(enable) == 1 and abs(limit) < 0.1:
        print(f"  [{nombre}] ✓ LIMIT 0% aplicado (sin producción)")
        return True
    else:
        print(f"  [{nombre}] ✗ Error: Enable={int(enable)}, Limit={limit:.1f}%")
        return False


async def controlar_inversor(config_path, nombre):
    """Controla un inversor según la lógica horaria"""
    try:
        async with ModbusController(config_path) as controller:
            # Obtener fecha/hora actual
            now = datetime.now()
            dia_semana = now.weekday()  # 0=lunes, 6=domingo
            hora = now.hour

            # Leer estado actual
            potencia = await controller.read_register("Potencia")
            enable_actual = await controller.read_register("Enable_limitacion")
            limit_actual = await controller.read_register("Limitacion_potencia")

            print(f"\n  [{nombre}] Estado actual:")
            print(f"    Potencia: {potencia:.0f}W")
            print(f"    Enable: {int(enable_actual)}, Límite: {limit_actual:.1f}%")

            # Determinar acción según horario
            if dia_semana >= 5:  # Sábado (5) o Domingo (6)
                print(f"  [{nombre}] FIN DE SEMANA → Aplicando DISABLE")
                return await aplicar_disable(controller, nombre)

            elif hora >= 16 or hora <= 6:  # Entre 16:00-23:59 o 00:00-06:59
                print(f"  [{nombre}] HORARIO 16:00-06:59 → Aplicando LIMIT 0%")
                return await aplicar_limit_cero(controller, nombre)

            else:  # Resto del tiempo (07:00-15:59)
                print(f"  [{nombre}] HORARIO NORMAL 07:00-15:59 → Aplicando DISABLE")
                return await aplicar_disable(controller, nombre)

    except Exception as e:
        print(f"  [{nombre}] ✗ ERROR: {e}")
        return False


async def main():
    """Controla todos los inversores"""
    now = datetime.now()
    dia_nombres = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

    print("="*70)
    print("CONTROL AUTOMÁTICO DE INVERSORES")
    print("="*70)
    print(f"\nFecha/Hora: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Día: {dia_nombres[now.weekday()]}")
    print(f"Hora: {now.hour}:00")

    # Determinar acción esperada
    if now.weekday() >= 5:
        accion_esperada = "DISABLE (fin de semana, no hay gente)"
    elif now.hour >= 16 or now.hour <= 6:
        accion_esperada = "LIMIT 0% (horario 16:00-06:59, evitar excedentes noche)"
    else:
        accion_esperada = "DISABLE (horario normal 07:00-15:59, producción libre)"

    print(f"\nAcción a aplicar: {accion_esperada}")
    print("\n" + "-"*70)

    # Controlar cada inversor
    resultados = []
    for inv in INVERSORES:
        print(f"\n>>> Controlando {inv['nombre']} ({inv['ip']})")
        resultado = await controlar_inversor(inv['config'], inv['nombre'])
        resultados.append({
            'nombre': inv['nombre'],
            'exito': resultado
        })

    # Resumen final
    print("\n" + "="*70)
    print("RESUMEN")
    print("="*70)

    todos_ok = all(r['exito'] for r in resultados)

    for r in resultados:
        estado = "✓ OK" if r['exito'] else "✗ ERROR"
        print(f"{estado} - {r['nombre']}")

    if todos_ok:
        print("\n✓ Todos los inversores configurados correctamente")
        sys.exit(0)
    else:
        print("\n✗ Algunos inversores tuvieron errores")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
