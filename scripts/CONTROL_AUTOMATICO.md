# Control Automático de Inversores

## Descripción

Script que controla automáticamente dos inversores solares según el horario y día de la semana.

## Lógica de Control

### Fines de Semana (Sábado y Domingo)
- **Acción**: `DISABLE` (Enable=0)
- **Motivo**: No hay gente, no se necesita control
- **Resultado**: Producción normal (~4000W por inversor)

### Días Laborables - Horario 16:00 a 06:59 (Nocturno)
- **Acción**: `LIMIT 0%` (Enable=1, Límite=0%)
- **Motivo**: Evitar excedentes desde tarde hasta mañana temprano
- **Resultado**: Sin producción (0W)

### Días Laborables - Horario 07:00 a 15:59 (Diurno)
- **Acción**: `DISABLE` (Enable=0)
- **Motivo**: Horario normal de trabajo con demanda
- **Resultado**: Producción normal (~4000W por inversor)

## Inversores Controlados

1. **Inversor 136**: IP 10.142.230.136
2. **Inversor 135**: IP 10.142.230.135

## Ejecución Manual

```bash
# Desde el directorio scripts/
./run_control_automatico.sh

# O directamente con Python (requiere venv activado)
source ../.venv/bin/activate
python control_automatico_inversores.py
```

## Configuración Automática con Cron

Para que el script se ejecute automáticamente cada 15 minutos:

### Opción 1: Editar crontab directamente

```bash
crontab -e
```

Agregar esta línea:
```cron
*/15 * * * * /home/ctacoronte/GitHub/ModbusController/scripts/run_control_automatico.sh >> /home/ctacoronte/GitHub/ModbusController/logs/control_auto.log 2>&1
```

### Opción 2: Usar el comando de instalación

```bash
# Crear directorio de logs
mkdir -p /home/ctacoronte/GitHub/ModbusController/logs

# Agregar al cron (ejecutar este comando)
(crontab -l 2>/dev/null; echo "*/15 * * * * /home/ctacoronte/GitHub/ModbusController/scripts/run_control_automatico.sh >> /home/ctacoronte/GitHub/ModbusController/logs/control_auto.log 2>&1") | crontab -
```

### Verificar que se instaló correctamente

```bash
crontab -l | grep control_automatico
```

### Otras frecuencias útiles

```cron
# Cada 5 minutos
*/5 * * * * /path/to/run_control_automatico.sh

# Cada hora
0 * * * * /path/to/run_control_automatico.sh

# Cada 30 minutos
*/30 * * * * /path/to/run_control_automatico.sh

# Solo a las 15:50, 16:00, 18:50, 19:00 (transiciones de horario)
50,0 15,16,18,19 * * * /path/to/run_control_automatico.sh
```

## Ver Logs

```bash
# Ver últimas ejecuciones
tail -50 /home/ctacoronte/GitHub/ModbusController/logs/control_auto.log

# Seguir en tiempo real
tail -f /home/ctacoronte/GitHub/ModbusController/logs/control_auto.log

# Ver solo resúmenes
grep "RESUMEN" -A 5 /home/ctacoronte/GitHub/ModbusController/logs/control_auto.log
```

## Desinstalar Cron

```bash
# Editar y eliminar la línea manualmente
crontab -e

# O eliminar automáticamente
crontab -l | grep -v "control_automatico" | crontab -
```

## Modificar Horarios

Para cambiar los horarios, edita el archivo `control_automatico_inversores.py`:

```python
# Línea ~85-95, cambiar las condiciones:

if dia_semana >= 5:  # Fines de semana
    # ...

elif hora >= 16 or hora <= 6:  # Cambiar estos números para modificar el horario
    # Actualmente: 16:00-23:59 O 00:00-06:59
    # Para cambiar solo tarde: elif 16 <= hora <= 20:  (16:00-20:59)
    # Para cambiar solo noche: elif hora <= 7:  (00:00-07:59)
    # ...
```

## Pruebas

```bash
# Ejecutar y ver resultado inmediato
./run_control_automatico.sh

# Verificar estado de inversores después
make status  # Para el inversor .136

# Para el inversor .135
python read_status.py configs/medidor_potencia_135.json
```

## Solución de Problemas

### El script no se ejecuta en cron

1. Verificar permisos:
```bash
ls -la run_control_automatico.sh
# Debe mostrar: -rwxr-xr-x (ejecutable)
```

2. Verificar rutas absolutas en cron (nunca usar rutas relativas)

3. Ver errores en syslog:
```bash
grep CRON /var/log/syslog | tail
```

### Un inversor falla

El script continúa con el otro inversor y reporta el error en el resumen final.

Ver logs para detalles:
```bash
tail -100 logs/control_auto.log
```

## Códigos de Salida

- `0`: Todo OK
- `1`: Algunos inversores tuvieron errores
