# Control Automático de Inversores por Horario

Script de ejemplo para controlar inversores solares basándose en horarios laborables usando APScheduler.

## Descripción

`scheduled_inverter_control.py` controla inversores solares automáticamente según el horario laboral:

- **ENABLE (producción completa)**: Lunes-Viernes 07:00-15:59
- **DISABLE (sin producción)**: Lunes-Viernes 16:00-06:59 + Fines de semana completos

El script está diseñado para ejecutarse como servicio Linux, manteniéndose activo 24/7.

## Terminología Importante

**CUIDADO**: La terminología puede ser confusa. En este script:

- **ENABLE** = Producción completa (inversor produce toda la energía posible)
  - Técnicamente: `Enable_limitacion = 0` (desactiva la limitación Modbus)

- **DISABLE** = Sin producción (inversor no produce energía)
  - Técnicamente: `Enable_limitacion = 1` + `Limitacion_potencia = 0%` (activa limitación al 0%)

## Requisitos

### Dependencias Python

```bash
pip install apscheduler pytz
```

O instalar todas las dependencias del proyecto:

```bash
pip install -r requirements.txt
```

### Configuración del Inversor

El script requiere un archivo de configuración JSON con los registros Modbus necesarios:

- `Limitacion_potencia` (address 40242): Control de potencia (0-100%)
- `Timeout_limitacion` (address 40244): Control de timeout (0=persistente)
- `Enable_limitacion` (address 40246): Habilitar/deshabilitar limitación (0/1)

Ejemplo: `configs/medidor_potencia.json` (ya incluido en el proyecto)

## Uso

### 1. Ejecución Manual (Pruebas)

```bash
# Desde el directorio raíz del proyecto
python examples/scheduled_inverter_control.py
```

El script comenzará inmediatamente:
1. Verificará el horario actual
2. Aplicará el estado correspondiente al inversor
3. Programará verificaciones periódicas cada 5 minutos
4. Ejecutará cambios automáticos a las 07:00 y 16:00

Presiona `Ctrl+C` para detener el script.

### 2. Personalizar Configuración

Edita las constantes al inicio del script:

```python
# Ruta a la configuración del inversor
DEFAULT_CONFIG = str(PROJECT_DIR / "configs" / "medidor_potencia.json")

# Horario laboral (hora en formato 24h)
HORA_INICIO_LABORAL = 7   # 07:00
HORA_FIN_LABORAL = 15      # 15:59

# Intervalo de verificación periódica (minutos)
INTERVALO_VERIFICACION = 5

# Timezone
TIMEZONE = pytz.timezone('Atlantic/Canary')
```

### 3. Configurar como Servicio Systemd (Linux)

Para que el script se ejecute automáticamente al iniciar el sistema:

#### Paso 1: Crear archivo de servicio

```bash
sudo nano /etc/systemd/system/inverter-control.service
```

#### Paso 2: Contenido del servicio

```ini
[Unit]
Description=Control Automático de Inversores Solares
After=network.target

[Service]
Type=simple
User=cristiantr
WorkingDirectory=/home/cristiantr/GitHub/ModbusController
ExecStart=/home/cristiantr/GitHub/ModbusController/.venv/bin/python /home/cristiantr/GitHub/ModbusController/examples/scheduled_inverter_control.py
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Notas importantes**:
- Cambia `User=cristiantr` por tu usuario
- Ajusta las rutas según tu instalación
- `Restart=always` asegura que el servicio se reinicie si falla
- `RestartSec=30` espera 30 segundos antes de reiniciar

#### Paso 3: Habilitar e iniciar el servicio

```bash
# Recargar configuración de systemd
sudo systemctl daemon-reload

# Habilitar el servicio para que inicie con el sistema
sudo systemctl enable inverter-control.service

# Iniciar el servicio ahora
sudo systemctl start inverter-control.service

# Verificar estado
sudo systemctl status inverter-control.service
```

#### Paso 4: Ver logs del servicio

```bash
# Ver logs en tiempo real
sudo journalctl -u inverter-control.service -f

# Ver últimas 100 líneas
sudo journalctl -u inverter-control.service -n 100

# Ver logs desde hoy
sudo journalctl -u inverter-control.service --since today
```

#### Comandos útiles del servicio

```bash
# Detener el servicio
sudo systemctl stop inverter-control.service

# Reiniciar el servicio
sudo systemctl restart inverter-control.service

# Deshabilitar inicio automático
sudo systemctl disable inverter-control.service
```

## Control de Múltiples Inversores

Para controlar varios inversores, modifica la función `main()`:

```python
async def main():
    """Controlar múltiples inversores"""

    # Configuración de múltiples inversores
    INVERSORES = [
        {
            "nombre": "Inversor 136",
            "config": str(PROJECT_DIR / "configs" / "medidor_potencia.json"),
        },
        {
            "nombre": "Inversor 135",
            "config": str(PROJECT_DIR / "configs" / "medidor_potencia_135.json"),
        }
    ]

    # Crear tareas para cada inversor
    tasks = []
    for inv in INVERSORES:
        task = asyncio.create_task(
            iniciar_control_automatico(inv['config'], inv['nombre'])
        )
        tasks.append(task)

    # Ejecutar todos en paralelo
    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        logger.info("Deteniendo todos los inversores...")
```

Esto ejecutará el control de todos los inversores simultáneamente con schedulers independientes.

## Ejemplo de Logs

```
======================================================================
CONTROL AUTOMÁTICO DE INVERSORES SOLARES - INICIO
======================================================================
Configuración: /home/cristiantr/GitHub/ModbusController/configs/medidor_potencia.json
Inversor: Inversor
Timezone: Atlantic/Canary
Horario laboral: 7:00 - 15:59 (Lun-Vie)
Verificación periódica: cada 5 minutos
======================================================================

Scheduler iniciado correctamente

Ejecutando verificación inicial...
============================================================
[Inversor] Verificación: 2025-11-05 14:30:00 WET
[Inversor] Estado deseado: ENABLE
[Inversor] Aplicando ENABLE (producción completa)...
[Inversor] ✓ ENABLE aplicado correctamente (Enable=0, producción completa)
[Inversor] ✓ Estado aplicado correctamente
============================================================

Próximas ejecuciones programadas:
  - Verificación periódica de estado: 2025-11-05 14:35:00 WET
  - Inicio jornada laboral (07:00): 2025-11-06 07:00:00 WET
  - Fin jornada laboral (16:00): 2025-11-05 16:00:00 WET
  - Inicio fin de semana (Sábado 00:00): 2025-11-09 00:00:00 WET
```

## Verificación y Depuración

### Verificar estado actual del inversor

Usa el script de lectura de estado:

```bash
cd scripts/
make status
```

O manualmente:

```bash
python scripts/read_status.py
```

Salida esperada:

```
Potencia actual: 1250.50 W
Limitación: 0% WMax
Estado: DESHABILITADO          <- ENABLE (producción completa)
Timeout: PERSISTENTE
```

O durante horario no laboral:

```
Potencia actual: 0.00 W
Limitación: 0% WMax
Estado: HABILITADO             <- DISABLE (sin producción)
Timeout: PERSISTENTE
```

### Probar cambios manuales

```bash
cd scripts/

# Forzar ENABLE (producción completa)
make enable

# Forzar DISABLE (sin producción)
make disable

# Verificar resultado
make status
```

## Comportamiento ante Errores

El script está diseñado para ser extremadamente robusto:

1. **Errores de conexión**: Se registran pero el servicio continúa, reintentando en la próxima verificación
2. **Errores al escribir registros**: Se registran y se reintenta en 5 minutos (o en el próximo evento programado)
3. **Errores críticos**: El servicio completo se reinicia automáticamente después de 30 segundos
4. **Interrupciones de red**: El servicio espera y reintenta, sin detenerse

El scheduler de APScheduler garantiza que:
- Las tareas programadas se ejecutan incluso si hay errores en ejecuciones anteriores
- Cada verificación es independiente
- Los eventos críticos (07:00, 16:00) siempre se ejecutan aunque haya fallado la verificación periódica

## Cronograma de Ejecución

El script ejecuta verificaciones en estos momentos:

| Evento | Horario | Frecuencia | Acción |
|--------|---------|------------|--------|
| Verificación periódica | Cada 5 minutos | Continuo | Verifica y corrige estado si es necesario |
| Inicio jornada laboral | 07:00 (Lun-Vie) | Diario laboral | Aplica ENABLE (producción completa) |
| Fin jornada laboral | 16:00 (Lun-Vie) | Diario laboral | Aplica DISABLE (sin producción) |
| Inicio fin de semana | 00:00 (Sábado) | Semanal | Aplica DISABLE (sin producción) |

Las verificaciones periódicas garantizan que el estado se mantenga correcto incluso si:
- El inversor se reinicia
- Hay cambios manuales
- Ocurren errores de comunicación temporales

## Solución de Problemas

### El script no cambia el estado del inversor

1. Verifica que el archivo de configuración JSON sea correcto
2. Comprueba la conectividad de red con el inversor: `ping 10.142.230.136`
3. Verifica los logs para identificar errores específicos
4. Prueba los scripts manuales en `scripts/` para descartar problemas de comunicación Modbus

### El servicio systemd no inicia

1. Verifica permisos del script: `chmod +x examples/scheduled_inverter_control.py`
2. Comprueba que el virtual environment exista: `ls -la .venv/`
3. Verifica los logs: `sudo journalctl -u inverter-control.service -n 50`
4. Prueba ejecutar el script manualmente primero para detectar errores

### El horario no es correcto

1. Verifica la zona horaria del sistema: `timedatectl`
2. Comprueba que `TIMEZONE` en el script sea correcto: `Atlantic/Canary`
3. Verifica que la hora del sistema sea correcta: `date`

### Logs no aparecen en journalctl

Asegúrate de que el servicio systemd tenga configurado:
```ini
StandardOutput=journal
StandardError=journal
```

## Seguridad

- El script NO expone puertos de red
- Solo realiza conexiones salientes a los inversores configurados
- No requiere permisos de root para ejecutarse
- Los logs NO contienen información sensible (no se registran credenciales)

## Licencia

Este script es parte del proyecto ModbusController. Ver LICENSE en el directorio raíz.
