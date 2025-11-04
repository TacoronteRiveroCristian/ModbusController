#!/usr/bin/env python3
"""
Script para probar la lógica de horarios sin conectar a los inversores
"""
from datetime import datetime

def determinar_accion(dia_semana, hora):
    """Determina qué acción se debe tomar según día y hora"""
    if dia_semana >= 5:  # Fin de semana
        return "DISABLE", "Fin de semana"
    elif hora >= 16 or hora <= 6:  # 16:00-06:59
        return "LIMIT 0%", "Horario nocturno"
    else:  # 07:00-15:59
        return "DISABLE", "Horario normal"

print("="*70)
print("PRUEBA DE LÓGICA DE HORARIOS")
print("="*70)

# Probar todos los días y horas
dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

print("\nHorarios que aplican LIMIT 0%:")
print("-" * 70)
for dia_num, dia_nombre in enumerate(dias):
    for hora in range(24):
        accion, razon = determinar_accion(dia_num, hora)
        if accion == "LIMIT 0%":
            print(f"  {dia_nombre:10s} {hora:02d}:00 - {hora:02d}:59 → {accion} ({razon})")

print("\nHorarios que aplican DISABLE (producción normal):")
print("-" * 70)
for dia_num, dia_nombre in enumerate(dias):
    for hora in range(24):
        accion, razon = determinar_accion(dia_num, hora)
        if accion == "DISABLE":
            print(f"  {dia_nombre:10s} {hora:02d}:00 - {hora:02d}:59 → {accion} ({razon})")
            break  # Solo mostrar primer hora de cada día

print("\n" + "="*70)
print("RESUMEN")
print("="*70)

# Contar horas totales
total_limit = 0
total_disable = 0

for dia_num in range(7):
    for hora in range(24):
        accion, _ = determinar_accion(dia_num, hora)
        if accion == "LIMIT 0%":
            total_limit += 1
        else:
            total_disable += 1

print(f"\nHoras semanales con LIMIT 0% (sin producción):   {total_limit} horas")
print(f"Horas semanales con DISABLE (producción normal): {total_disable} horas")
print(f"Total: {total_limit + total_disable} horas (7 días x 24h)")

# Porcentajes
pct_limit = (total_limit / (7*24)) * 100
pct_disable = (total_disable / (7*24)) * 100

print(f"\nProducción limitada: {pct_limit:.1f}% del tiempo")
print(f"Producción normal:   {pct_disable:.1f}% del tiempo")

# Estado actual
now = datetime.now()
accion_actual, razon_actual = determinar_accion(now.weekday(), now.hour)
print(f"\n>>> AHORA ({now.strftime('%A %H:%M')}): {accion_actual} ({razon_actual})")
