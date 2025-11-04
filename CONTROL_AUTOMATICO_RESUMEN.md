# Resumen: Control Automático de Inversores

## ¿Qué hace el sistema?

Controla automáticamente **dos inversores solares** (IPs .135 y .136) según el horario:

### 📅 Fines de Semana (Sábado y Domingo)
```
🔓 DISABLE → Producción normal (~4000W cada uno)
Razón: No hay gente en la instalación
```

### 🌙 Días Laborables - 16:00 a 06:59 (Horario Nocturno)
```
⛔ LIMIT 0% → Sin producción (0W)
Razón: Evitar excedentes desde tarde hasta mañana temprano
```

### ☀️ Días Laborables - 07:00 a 15:59 (Horario Diurno)
```
🔓 DISABLE → Producción normal (~4000W cada uno)
Razón: Horario normal de trabajo con demanda eléctrica
```

## Archivos Creados

```
ModbusController/
├── configs/
│   ├── medidor_potencia.json        (Inversor .136 - ORIGINAL)
│   └── medidor_potencia_135.json    (Inversor .135 - NUEVO)
│
├── scripts/
│   ├── control_automatico_inversores.py  (Script principal)
│   ├── run_control_automatico.sh         (Wrapper para cron)
│   ├── CONTROL_AUTOMATICO.md             (Documentación completa)
│   └── Makefile                          (Actualizado con nuevos comandos)
│
└── logs/
    └── control_auto.log              (Se crea al ejecutar)
```

## Comandos Disponibles

### Ejecución Manual
```bash
cd scripts/
source ../.venv/bin/activate

# Ejecutar control automático ahora
make auto

# Ver estado de un inversor
make status                                    # .136
python read_status.py configs/medidor_potencia_135.json  # .135
```

### Instalación Automática (Recomendado)
```bash
cd scripts/

# Instalar en cron (se ejecutará cada 15 minutos automáticamente)
make install-cron

# Verificar que se instaló
crontab -l | grep control_automatico

# Ver logs
make logs

# O seguir en tiempo real
tail -f ../logs/control_auto.log
```

### Desinstalación
```bash
cd scripts/

# Desinstalar de cron
make uninstall-cron
```

## Ejemplo de Salida

```
======================================================================
CONTROL AUTOMÁTICO DE INVERSORES
======================================================================

Fecha/Hora: 2025-11-04 16:30:00
Día: Martes
Hora: 16:00

Acción a aplicar: LIMIT 0% (horario 16-19h, evitar excedentes)

----------------------------------------------------------------------

>>> Controlando Inversor 136 (10.142.230.136)
  [Inversor 136] Estado actual:
    Potencia: 3991W
    Enable: 0, Límite: 100%
  [Inversor 136] HORARIO 16:00-18:59 → Aplicando LIMIT 0%
  [Inversor 136] Aplicando límite 0% (sin excedentes)...
  [Inversor 136] ✓ LIMIT 0% aplicado (sin producción)

>>> Controlando Inversor 135 (10.142.230.135)
  [Inversor 135] Estado actual:
    Potencia: 3949W
    Enable: 0, Límite: 0%
  [Inversor 135] HORARIO 16:00-18:59 → Aplicando LIMIT 0%
  [Inversor 135] Aplicando límite 0% (sin excedentes)...
  [Inversor 135] ✓ LIMIT 0% aplicado (sin producción)

======================================================================
RESUMEN
======================================================================
✓ OK - Inversor 136
✓ OK - Inversor 135

✓ Todos los inversores configurados correctamente
```

## Modificar Horarios

Para cambiar los horarios, edita `scripts/control_automatico_inversores.py`:

```python
# Línea aproximada 85-95

if dia_semana >= 5:  # Fines de semana (5=sábado, 6=domingo)
    # Aplicar DISABLE

elif 16 <= hora <= 18:  # Cambiar estos números
    # Por ejemplo: 15 <= hora <= 17  significa 15:00 a 17:59
    # Aplicar LIMIT 0%

else:
    # Resto del tiempo: DISABLE
```

## Solución de Problemas Comunes

### ❌ Un inversor no responde
- El script continúa con el otro
- Verifica conectividad: `ping 10.142.230.135`
- Revisa logs: `make logs`

### ❌ El cron no se ejecuta
```bash
# Ver errores del cron
grep CRON /var/log/syslog | tail

# Verificar que está instalado
crontab -l | grep control_automatico

# Reinstalar
make uninstall-cron
make install-cron
```

### ❌ Quiero cambiar la frecuencia del cron
```bash
# Editar manualmente
crontab -e

# Cambiar la línea a:
*/5 * * * * ...   # Cada 5 minutos
0 * * * * ...     # Cada hora
*/30 * * * * ...  # Cada 30 minutos
```

## Comandos Útiles del Día a Día

```bash
# Ver estado actual de ambos inversores
make auto

# Ver solo el .136
make status

# Ver solo el .135
python read_status.py configs/medidor_potencia_135.json

# Deshabilitar ambos manualmente (producción normal)
make disable  # Solo afecta .136
python toggle_enable.py disable configs/medidor_potencia_135.json  # Para .135

# Ver últimos logs
make logs

# Ver logs en tiempo real
tail -f ../logs/control_auto.log
```

## Resumen de Estados

| Estado | Enable | Límite | Producción | Cuándo |
|--------|--------|--------|------------|--------|
| **DISABLE** | 0 | (guardado) | ~4000W | Normal, fines de semana |
| **LIMIT 0%** | 1 | 0% | 0W | 16:00-18:59 laborables |

**Importante**: NUNCA usar `make limit LIMIT=100` para producción normal, siempre usar `make disable`.

---

**Contacto**: Si necesitas ayuda, revisa `scripts/CONTROL_AUTOMATICO.md` para documentación completa.
