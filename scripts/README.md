# Scripts de Operaciones Modbus

Scripts para operaciones rápidas de lectura/escritura de registros Modbus.

## Requisitos

Activar el entorno virtual antes de usar:
```bash
source ../.venv/bin/activate
```

## Comandos Disponibles

### Lectura

```bash
# Ver estado actual de limitación de potencia
make status

# Leer todos los registros
make read

# Leer con configuración específica
make read CONFIG=configs/otro.json
```

### Control de Limitación de Potencia

```bash
# Establecer límite y habilitar en un solo paso
make limit LIMIT=50        # Limita al 50% y habilita

# Solo cambiar el límite (sin habilitar)
make set-limit LIMIT=75    # Cambia límite al 75%

# Habilitar/Deshabilitar limitación
make enable                # Habilita la limitación
make disable               # Deshabilita la limitación
make on                    # Alias de enable
make off                   # Alias de disable

# Reset completo
make reset                 # Pone límite=0 y enable=0
```

### Ver ayuda

```bash
make help
```

## Scripts Python

Alternativamente, puedes usar los scripts directamente:

```bash
# Ver estado
python read_status.py [config_path]

# Establecer límite solo
python set_limit_only.py <porcentaje> [config_path]

# Establecer límite y habilitar
python set_limit_and_enable.py <porcentaje> [config_path]

# Toggle enable/disable
python toggle_enable.py [enable|disable] [config_path]

# Leer todos los registros
python read_all.py
```

## Ejemplos Completos

```bash
# Activar venv
source ../.venv/bin/activate

# Ver estado actual
make status

# Limitar potencia al 60% y activar
make limit LIMIT=60

# Verificar cambio
make status

# Solo cambiar límite al 80% sin activar
make set-limit LIMIT=80

# Activar la limitación
make enable

# Desactivar todo
make reset
```

## Nota sobre el Enable

En algunos dispositivos Modbus, el registro de `Enable_limitacion` puede no mantenerse en 1 después de escribirlo. Esto es normal si el dispositivo requiere condiciones especiales para habilitar la limitación (por ejemplo, ciertos estados de funcionamiento o confirmaciones adicionales).
