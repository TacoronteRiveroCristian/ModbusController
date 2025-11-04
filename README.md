# ModbusController

Sistema completo de gestión de lecturas y escrituras Modbus con control de frecuencia, gestión inteligente de conexiones y soporte para múltiples formatos de datos.

## 🚀 Características principales

- ✅ **Soporte dual**: Modbus TCP/IP y RTU
- ✅ **Asíncrono**: Operaciones no bloqueantes con asyncio
- ✅ **Gestión inteligente**: Agrupación automática de registros consecutivos
- ✅ **Rate limiting**: Control de frecuencia para no saturar el PLC
- ✅ **Conversión de tipos**: uint16, int16, uint32, int32, float32, string
- ✅ **Monitorización**: Lectura automática con intervalos configurables
- ✅ **Reconexión automática**: Manejo robusto de pérdidas de conexión
- ✅ **Caché de valores**: Acceso rápido a últimas lecturas
- ✅ **Validación con Pydantic**: Configuración JSON validada

## 📦 Instalación

```bash
# Clonar el repositorio
git clone <url-del-repo>
cd ModbusController

# Instalar dependencias
pip install -r requirements.txt
```

## 🔧 Configuración

Crea un archivo JSON con la configuración de tus registros Modbus:

```json
{
  "connection": {
    "type": "tcp",
    "host": "192.168.1.100",
    "port": 502,
    "timeout": 3,
    "retry_on_empty": true,
    "retries": 3
  },
  "registers": [
    {
      "name": "temperatura_ambiente",
      "address": 100,
      "type": "float32",
      "unit": "°C",
      "function_code": 3,
      "poll_interval": 5.0,
      "description": "Temperatura ambiente"
    },
    {
      "name": "setpoint_temperatura",
      "address": 300,
      "type": "float32",
      "unit": "°C",
      "function_code": 3,
      "poll_interval": 10.0
    }
  ],
  "limits": {
    "max_registers_per_read": 125,
    "min_request_interval": 0.1
  }
}
```

### Tipos de datos soportados

| Tipo | Registros | Descripción |
|------|-----------|-------------|
| `uint16` | 1 | Entero sin signo 16-bit |
| `int16` | 1 | Entero con signo 16-bit |
| `uint32` | 2 | Entero sin signo 32-bit |
| `int32` | 2 | Entero con signo 32-bit |
| `float32` | 2 | Punto flotante IEEE 754 |
| `string` | N | Cadena de texto (N registros) |

### Tipos de conexión

#### TCP/IP
```json
{
  "connection": {
    "type": "tcp",
    "host": "192.168.1.100",
    "port": 502,
    "timeout": 3
  }
}
```

#### RTU (Serial)
```json
{
  "connection": {
    "type": "rtu",
    "port_name": "/dev/ttyUSB0",
    "baudrate": 9600,
    "bytesize": 8,
    "parity": "N",
    "stopbits": 1,
    "timeout": 3
  }
}
```

## 📖 Uso

### Ejemplo básico: Leer todos los registros

```python
import asyncio
from modbus_controller import ModbusController

async def main():
    async with ModbusController("configs/example_config.json") as controller:
        # Leer todos los registros
        valores = await controller.read_all()

        for nombre, datos in valores.items():
            print(f"{nombre}: {datos['value']} {datos['unit']}")

asyncio.run(main())
```

### Lectura de registro individual

```python
async with ModbusController("config.json") as controller:
    temperatura = await controller.read_register("temperatura_ambiente")
    print(f"Temperatura: {temperatura} °C")
```

### Escritura de registros

```python
async with ModbusController("config.json") as controller:
    # Escribir nuevo setpoint
    await controller.write_register("setpoint_temperatura", 22.5)

    # Verificar
    valor = await controller.read_register("setpoint_temperatura")
    print(f"Nuevo setpoint: {valor} °C")
```

### Monitorización continua

```python
def on_value_change(nombre, valor_anterior, valor_nuevo):
    print(f"[CAMBIO] {nombre}: {valor_anterior} → {valor_nuevo}")

async with ModbusController("config.json") as controller:
    # Iniciar monitorización con callback
    await controller.start_monitoring(callback=on_value_change)

    # Mantener monitorización activa
    await asyncio.sleep(60)

    # Se detiene automáticamente al salir del context manager
```

### Control automático basado en lecturas

```python
async with ModbusController("config.json") as controller:
    while True:
        # Leer temperatura
        temp_actual = await controller.read_register("temperatura_ambiente")
        setpoint = await controller.read_register("setpoint_temperatura")

        # Lógica de control
        if temp_actual < setpoint - 1.0:
            await controller.write_register("control_calefaccion", 1)
            print("Calefacción ON")
        elif temp_actual > setpoint + 1.0:
            await controller.write_register("control_calefaccion", 0)
            print("Calefacción OFF")

        await asyncio.sleep(5)
```

### Uso de caché

```python
async with ModbusController("config.json") as controller:
    # Leer desde dispositivo
    await controller.read_all()

    # Acceder a valores desde caché (sin acceso al dispositivo)
    temp_cached = controller.get_last_value("temperatura_ambiente")
    print(f"Temperatura (caché): {temp_cached} °C")

    # Obtener todos los valores cacheados
    all_values = controller.get_all_last_values()
```

### Múltiples dispositivos

```python
# Dispositivo 1 (TCP)
async with ModbusController("config_plc1.json") as plc1:
    valores1 = await plc1.read_all()

# Dispositivo 2 (RTU)
async with ModbusController("config_plc2.json") as plc2:
    valores2 = await plc2.read_all()
```

## 🎯 Características avanzadas

### Agrupación automática de registros

El controlador agrupa automáticamente registros consecutivos para optimizar las lecturas:

```python
# Si tienes registros en direcciones 100, 101, 102, 103
# Se leerán todos en una sola petición en lugar de 4 peticiones
```

### Rate limiting

Evita saturar el PLC con peticiones demasiado frecuentes:

```json
{
  "limits": {
    "max_registers_per_read": 125,
    "min_request_interval": 0.1
  }
}
```

### Intervalos de monitorización por registro

Cada registro puede tener su propia frecuencia de lectura:

```json
{
  "registers": [
    {
      "name": "alarma_critica",
      "poll_interval": 0.5  // Leer cada 0.5 segundos
    },
    {
      "name": "temperatura",
      "poll_interval": 5.0  // Leer cada 5 segundos
    },
    {
      "name": "modelo_equipo",
      "poll_interval": 60.0  // Leer cada minuto
    }
  ]
}
```

### Reconexión automática

Si se pierde la conexión, el controlador intenta reconectar automáticamente.

## 🧪 Tests

## 🛠️ Uso del Makefile

El proyecto incluye un Makefile para facilitar tareas comunes:

```bash
make help      # Muestra ayuda de comandos disponibles
make test      # Ejecuta los tests unitarios
```

## 🧪 Tests

Para ejecutar los tests manualmente:

```bash
# Instalar pytest
pip install pytest pytest-asyncio

# Ejecutar tests
pytest tests/test_controller.py -v

# Tests de integración (requieren servidor Modbus)
pytest tests/test_controller.py -v -m integration
```

## 📁 Estructura del proyecto

```
ModbusController/
├── requirements.txt
├── README.md
├── modbus_controller/
│   ├── __init__.py
│   ├── controller.py          # Clase principal
│   ├── config_loader.py       # Cargador JSON + validación
│   ├── data_converter.py      # Conversión de tipos
│   └── exceptions.py          # Excepciones personalizadas
├── configs/
│   ├── example_config.json    # Ejemplo TCP
│   └── example_config_rtu.json # Ejemplo RTU
├── examples/
│   └── usage_example.py       # Ejemplos de uso
└── tests/
    └── test_controller.py     # Tests unitarios
```

## 🔍 Logging

El controlador usa logging de Python:

```python
import logging

# Configurar nivel de logging
logging.basicConfig(level=logging.INFO)

# O más detallado para debugging
logging.basicConfig(level=logging.DEBUG)
```

## ⚠️ Consideraciones importantes

1. **Límite de registros**: Algunos servidores Modbus solo permiten leer 125 registros por petición. El controlador maneja esto automáticamente.

2. **Strings**: Para leer strings (modelos, nombres), usa `type: "string"` y especifica `length` (número de registros).

3. **Function codes**:
   - FC 3: Read Holding Registers (lectura/escritura)
   - FC 4: Read Input Registers (solo lectura)

4. **Slave ID**: Por defecto es 1, pero puedes especificarlo:
   ```python
   await controller.read_all(slave=2)
   ```

## 🐛 Manejo de errores

```python
from modbus_controller.exceptions import (
    ConnectionError,
    ReadError,
    WriteError,
    ConfigurationError
)

try:
    async with ModbusController("config.json") as controller:
        await controller.read_all()
except ConnectionError as e:
    print(f"Error de conexión: {e}")
except ReadError as e:
    print(f"Error de lectura: {e}")
except ConfigurationError as e:
    print(f"Error de configuración: {e}")
```

## 📝 Licencia

MIT License

## 👥 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork del repositorio
2. Crea una rama para tu feature
3. Commit de tus cambios
4. Push a la rama
5. Crea un Pull Request

## 📞 Soporte

Para reportar bugs o solicitar features, abre un issue en el repositorio.
