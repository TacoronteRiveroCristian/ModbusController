# Configuración de ModbusController

Esta carpeta contiene los archivos de configuración JSON para conectar y leer/escribir registros Modbus.

## Estructura del Archivo de Configuración

### Plantilla Base

Usa `config.template.json` como punto de partida para crear tu propia configuración.

```bash
cp config.template.json mi_dispositivo.json
```

## Secciones de Configuración

### 1. Connection (Conexión)

Define cómo conectar al dispositivo Modbus.

#### Modbus TCP/IP
```json
{
    "connection": {
        "type": "tcp",
        "host": "192.168.1.100",
        "port": 502,
        "timeout": 3,
        "retry_on_empty": true,
        "retry_delay": 1
    }
}
```

**Parámetros:**
- `type`: `"tcp"` para Modbus TCP/IP
- `host`: Dirección IP del dispositivo
- `port`: Puerto Modbus (por defecto 502)
- `timeout`: Timeout en segundos
- `retry_on_empty`: Reintentar si la respuesta está vacía
- `retry_delay`: Segundos entre reintentos

#### Modbus RTU (Serial)
```json
{
    "connection": {
        "type": "rtu",
        "port_name": "/dev/ttyUSB0",
        "baudrate": 9600,
        "parity": "N",
        "stopbits": 1,
        "bytesize": 8,
        "timeout": 3
    }
}
```

**Parámetros:**
- `type`: `"rtu"` para Modbus RTU
- `port_name`: Puerto serie (ej: `/dev/ttyUSB0`, `COM3`)
- `baudrate`: Velocidad de comunicación (9600, 19200, 38400, etc.)
- `parity`: Paridad - `"N"` (None), `"E"` (Even), `"O"` (Odd)
- `stopbits`: Bits de parada (1 o 2)
- `bytesize`: Tamaño del byte (7 u 8)

### 2. Registers (Registros)

Define los registros Modbus a leer/escribir.

```json
{
    "registers": [
        {
            "name": "Power_Limit",
            "address": 40242,
            "type": "uint16",
            "unit": "%",
            "function_code": 3,
            "poll_interval": 10.0,
            "writable": true,
            "scale_factor": 100,
            "offset": 0,
            "description": "Power limitation percentage"
        }
    ]
}
```

**Parámetros obligatorios:**
- `name`: Nombre único del registro (usado en el código)
- `address`: Dirección del registro Modbus
- `type`: Tipo de dato (ver tabla abajo)
- `function_code`: Código de función Modbus (3 o 4)

**Parámetros opcionales:**
- `unit`: Unidad de medida (para documentación)
- `poll_interval`: Intervalo de lectura en segundos (para monitoreo automático)
- `writable`: `true` si el registro es escribible
- `scale_factor`: Factor de escala para conversión automática
- `offset`: Offset para conversión automática
- `description`: Descripción del registro

#### Tipos de Datos Soportados

| Tipo | Registros | Rango | Descripción |
|------|-----------|-------|-------------|
| `uint16` | 1 | 0 a 65535 | Entero sin signo de 16 bits |
| `int16` | 1 | -32768 a 32767 | Entero con signo de 16 bits |
| `uint32` | 2 | 0 a 4294967295 | Entero sin signo de 32 bits |
| `int32` | 2 | -2147483648 a 2147483647 | Entero con signo de 32 bits |
| `float32` | 2 | IEEE 754 | Número de punto flotante |
| `string` | N | - | Cadena de texto ASCII |

#### Function Codes

| Código | Nombre | Tipo | Descripción |
|--------|--------|------|-------------|
| 3 | Read Holding Registers | Lectura/Escritura | Registros de lectura/escritura |
| 4 | Read Input Registers | Solo lectura | Registros de solo lectura |

**Para escritura:**
- FC 6: Write Single Register (automático para 1 registro)
- FC 16: Write Multiple Registers (automático para múltiples registros)

### 3. Scale Factor y Offset

El scale factor permite trabajar con valores amigables mientras la librería convierte automáticamente a valores hardware.

**Fórmula:**
```
Lectura:   valor_usuario = (valor_hardware × scale_factor) + offset
Escritura: valor_hardware = (valor_usuario - offset) ÷ scale_factor
```

**Ejemplo: SunSpec Power Limit**
- Hardware espera: 0-10000 (donde 10000 = 100%)
- Usuario quiere: 0-100 (porcentajes directos)
- Solución: `scale_factor: 100`

```json
{
    "name": "Power_Limit",
    "address": 40242,
    "type": "uint16",
    "scale_factor": 100,
    "description": "Usuario escribe 50, hardware recibe 5000"
}
```

**Ejemplo: Temperatura con offset**
```json
{
    "name": "Temperature",
    "address": 40100,
    "type": "int16",
    "scale_factor": 0.1,
    "offset": -40,
    "unit": "°C",
    "description": "Hardware: -400 a 850 → Usuario: -40.0°C a 85.0°C"
}
```

### 4. Limits (Límites)

Configuración de límites de comunicación.

```json
{
    "limits": {
        "max_registers_per_read": 125,
        "min_request_interval": 0.1
    }
}
```

**Parámetros:**
- `max_registers_per_read`: Máximo de registros por petición (por defecto 125)
- `min_request_interval`: Intervalo mínimo entre peticiones en segundos (rate limiting)

## Ejemplos Incluidos

### `medidor_potencia.json`
Configuración para inversor solar con control de potencia SunSpec.
- **Dispositivo:** Inversor 136 (10.142.230.136)
- **Registros:** Potencia, Limitación, Timeout, Enable
- **Uso:** Control automático de producción solar

### `medidor_potencia_135.json`
Configuración para segundo inversor solar.
- **Dispositivo:** Inversor 135 (10.142.230.135)
- **Registros:** Idénticos al inversor 136

## Validación de Configuración

La librería valida automáticamente la configuración usando Pydantic:

```python
from modbus_controller import ModbusController

try:
    controller = ModbusController("configs/mi_config.json")
except Exception as e:
    print(f"Error en configuración: {e}")
```

**Errores comunes:**
- ❌ Tipo de dato incorrecto
- ❌ Function code no válido (debe ser 3 o 4)
- ❌ Falta `host` para TCP o `port_name` para RTU
- ❌ Scale factor igual a 0 (causa división por cero)

## Mejores Prácticas

1. **Nomenclatura:**
   - Usa nombres descriptivos: `Power_Limit`, `Temperature_Sensor`
   - Evita espacios: usa guiones bajos `_`

2. **Organización:**
   - Agrupa registros consecutivos para optimizar lecturas
   - Ordena por dirección de menor a mayor

3. **Documentación:**
   - Siempre incluye `description` explicando qué hace el registro
   - Especifica `unit` para valores medibles

4. **Writable:**
   - Solo marca `writable: true` en registros que realmente se pueden escribir
   - Documenta qué valores son válidos

5. **Poll Interval:**
   - Usa intervalos cortos (1-5s) para datos críticos
   - Usa intervalos largos (30-60s) para datos estáticos
   - Omite `poll_interval` si no usarás monitoreo automático

6. **Scale Factor:**
   - Siempre documenta el rango hardware vs usuario
   - Prueba con valores mínimos y máximos
   - Nunca uses `scale_factor: 0`

## Referencia Rápida

### Crear nueva configuración
```bash
cd configs/
cp config.template.json mi_dispositivo.json
# Editar con tu editor favorito
nano mi_dispositivo.json
```

### Verificar configuración
```python
from modbus_controller import ModbusController

controller = ModbusController("configs/mi_dispositivo.json")
print(f"Registros configurados: {len(controller.config.registers)}")
```

### Leer todos los registros
```python
import asyncio

async def test():
    async with ModbusController("configs/mi_dispositivo.json") as controller:
        datos = await controller.read_all()
        for nombre, info in datos.items():
            print(f"{nombre}: {info['value']} {info['unit']}")

asyncio.run(test())
```

## Soporte

Para más información consulta:
- [Documentación principal](../README.md)
- [Especificación Modbus](https://modbus.org/)
- [SunSpec Alliance](https://sunspec.org/) (para inversores solares)
