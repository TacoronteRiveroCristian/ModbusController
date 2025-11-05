# ModbusController

Librería Python asíncrona para gestión de comunicaciones Modbus TCP/IP y RTU con soporte para scale factors, monitorización automática y conversión inteligente de tipos de datos.

## 🚀 Características Principales

- ✅ **Soporte dual**: Modbus TCP/IP y RTU
- ✅ **Asíncrono**: Operaciones no bloqueantes con asyncio
- ✅ **Scale Factor**: Conversión automática de valores (ej: 0-100% ↔ 0-10000)
- ✅ **Gestión inteligente**: Agrupación automática de registros consecutivos
- ✅ **Rate limiting**: Control de frecuencia para no saturar dispositivos
- ✅ **Conversión de tipos**: uint16, int16, uint32, int32, float32, string
- ✅ **Monitorización**: Lectura automática con intervalos configurables
- ✅ **Reconexión automática**: Manejo robusto de pérdidas de conexión
- ✅ **Caché de valores**: Acceso rápido a últimas lecturas
- ✅ **Validación con Pydantic**: Configuración JSON validada automáticamente

## 📦 Instalación

```bash
# Clonar el repositorio
git clone <url-del-repo>
cd ModbusController

# Instalar dependencias
pip install -r requirements.txt

# Instalar en modo desarrollo (editable)
pip install -e .
```

## 🔧 Configuración

### Estructura Básica

Crea un archivo JSON con la configuración de tus registros Modbus. Consulta [`configs/README.md`](configs/README.md) para documentación completa.

```json
{
  "connection": {
    "type": "tcp",
    "host": "192.168.1.100",
    "port": 502,
    "timeout": 3
  },
  "registers": [
    {
      "name": "Temperature",
      "address": 40100,
      "type": "float32",
      "unit": "°C",
      "function_code": 3,
      "poll_interval": 5.0,
      "description": "Temperature sensor reading"
    },
    {
      "name": "Power_Limit",
      "address": 40242,
      "type": "uint16",
      "unit": "%",
      "function_code": 3,
      "writable": true,
      "scale_factor": 100,
      "description": "Power limit: user writes 50, hardware receives 5000"
    }
  ],
  "limits": {
    "max_registers_per_read": 125,
    "min_request_interval": 0.1
  }
}
```

### Plantilla de Configuración

Usa la plantilla como punto de partida:

```bash
cp configs/config.template.json configs/mi_dispositivo.json
```

Consulta [`configs/README.md`](configs/README.md) para:
- Tipos de datos soportados
- Configuración de scale factors
- Ejemplos de TCP/IP y RTU
- Mejores prácticas

## 📖 Uso Básico

### Lectura de Registros

```python
import asyncio
from modbus_controller import ModbusController

async def main():
    # Context manager maneja conexión automáticamente
    async with ModbusController("configs/mi_dispositivo.json") as controller:
        # Leer todos los registros
        valores = await controller.read_all()

        for nombre, datos in valores.items():
            print(f"{nombre}: {datos['value']} {datos['unit']}")

        # Leer registro individual
        temperatura = await controller.read_register("Temperature")
        print(f"Temperatura: {temperatura:.1f} °C")

asyncio.run(main())
```

### Escritura de Registros

```python
async with ModbusController("config.json") as controller:
    # Escribir valor (con scale_factor automático si está configurado)
    await controller.write_register("Power_Limit", 50)  # Usuario: 50%, Hardware: 5000

    # Verificar
    limit = await controller.read_register("Power_Limit")
    print(f"Límite configurado: {limit:.1f}%")  # Muestra: 50.0%
```

### Scale Factor Automático

El scale factor permite trabajar con valores amigables:

```python
# Con scale_factor: 100 en la configuración
async with ModbusController("config.json") as controller:
    # Usuario escribe porcentaje (0-100)
    await controller.write_register("Power_Limit", 75)

    # Librería convierte automáticamente: 75 → 7500 (hardware)
    # Log: "Escrito 'Power_Limit' = 75 (raw: 7500.0)"

    # Usuario lee porcentaje (0-100)
    value = await controller.read_register("Power_Limit")
    # Librería convierte automáticamente: 7500 → 75.0 (usuario)
    print(f"Límite: {value:.1f}%")  # Output: 75.0%
```

Consulta [`SCALE_FACTOR_IMPLEMENTATION.md`](SCALE_FACTOR_IMPLEMENTATION.md) para detalles técnicos.

### Monitorización Continua

```python
def on_change(nombre, valor_anterior, valor_nuevo):
    print(f"[CAMBIO] {nombre}: {valor_anterior} → {valor_nuevo}")

async with ModbusController("config.json") as controller:
    # Iniciar monitorización con callback
    await controller.start_monitoring(callback=on_change)

    # Mantener activo
    await asyncio.sleep(3600)  # 1 hora

    # Se detiene automáticamente al salir del context manager
```

### Uso de Caché

```python
async with ModbusController("config.json") as controller:
    # Leer desde dispositivo
    await controller.read_all()

    # Acceso rápido desde caché (sin comunicación Modbus)
    temp = controller.get_last_value("Temperature")

    # Todos los valores cacheados
    all_values = controller.get_all_last_values()
```

## 🎯 Características Avanzadas

### Agrupación Automática de Registros

El controlador optimiza las lecturas agrupando registros consecutivos:

```python
# Registros en direcciones 100, 101, 102, 103
# → Se leen en 1 petición en lugar de 4
```

### Rate Limiting

Evita saturar dispositivos con peticiones frecuentes:

```json
{
  "limits": {
    "max_registers_per_read": 125,
    "min_request_interval": 0.1
  }
}
```

### Intervalos de Monitorización Personalizados

```json
{
  "registers": [
    {
      "name": "Critical_Alarm",
      "poll_interval": 0.5
    },
    {
      "name": "Temperature",
      "poll_interval": 5.0
    },
    {
      "name": "Device_Model",
      "poll_interval": 60.0
    }
  ]
}
```

### Múltiples Dispositivos

```python
# Controlar múltiples dispositivos simultáneamente
async with ModbusController("config_device1.json") as dev1, \
           ModbusController("config_device2.json") as dev2:

    values1 = await dev1.read_all()
    values2 = await dev2.read_all()
```

## 📊 Ejemplo Completo: Control Automático

Consulta [`examples/scheduled_control/`](examples/scheduled_control/) para un ejemplo completo de control automático de inversores solares basado en horarios:

- Control automático con APScheduler
- Timezone configurable (Canarias)
- Control de múltiples dispositivos en paralelo
- Manejo robusto de errores con reintentos
- Logging detallado

```bash
cd examples/scheduled_control/
pip install -r requirements.txt
python scheduled_inverter_control.py
```

## 🔍 Logging

Configura el nivel de logging según necesites:

```python
import logging

# Información general
logging.basicConfig(level=logging.INFO)

# Debug detallado (incluye lecturas/escrituras)
logging.basicConfig(level=logging.DEBUG)
```

Ejemplo de logs con scale_factor:
```
INFO: Escrito 'Power_Limit' = 50 (raw: 5000.0) en dirección 40242
INFO: Conectado exitosamente via TCP
```

## 🛠️ Desarrollo

### Tests

```bash
# Instalar dependencias de test
pip install pytest pytest-asyncio

# Ejecutar tests unitarios
make test

# O manualmente
pytest tests/test_controller.py -v

# Tests de integración (requieren servidor Modbus real)
pytest tests/test_controller.py -v -m integration
```

### Estructura del Proyecto

```
ModbusController/
├── README.md                          # Este archivo
├── requirements.txt                   # Dependencias principales
├── setup.py                          # Configuración del paquete
├── modbus_controller/                # Librería principal
│   ├── __init__.py
│   ├── controller.py                 # Clase ModbusController
│   ├── config_loader.py              # Cargador y validador JSON
│   ├── data_converter.py             # Conversión de tipos + scale factor
│   └── exceptions.py                 # Excepciones personalizadas
├── configs/                          # Configuraciones de ejemplo
│   ├── README.md                     # Documentación de configuración
│   ├── config.template.json          # Plantilla
│   ├── medidor_potencia.json         # Ejemplo: inversor solar 136
│   └── medidor_potencia_135.json     # Ejemplo: inversor solar 135
├── examples/                         # Ejemplos de uso
│   └── scheduled_control/            # Control automático por horarios
│       ├── README.md
│       ├── requirements.txt
│       └── scheduled_inverter_control.py
└── tests/                            # Tests unitarios
    └── test_controller.py
```

## 🐛 Manejo de Errores

```python
from modbus_controller.exceptions import (
    ConnectionError,
    ReadError,
    WriteError,
    ConfigurationError,
    DataConversionError
)

try:
    async with ModbusController("config.json") as controller:
        value = await controller.read_register("Temperature")
except ConnectionError as e:
    print(f"Error de conexión: {e}")
except ReadError as e:
    print(f"Error de lectura: {e}")
except WriteError as e:
    print(f"Error de escritura: {e}")
except ConfigurationError as e:
    print(f"Error de configuración: {e}")
except DataConversionError as e:
    print(f"Error de conversión: {e}")
```

## ⚠️ Consideraciones Importantes

### Tipos de Datos

| Tipo | Registros | Rango | Uso |
|------|-----------|-------|-----|
| `uint16` | 1 | 0-65535 | Enteros positivos |
| `int16` | 1 | -32768 a 32767 | Enteros con signo |
| `uint32` | 2 | 0-4294967295 | Enteros grandes |
| `int32` | 2 | -2147483648 a 2147483647 | Enteros grandes con signo |
| `float32` | 2 | IEEE 754 | Decimales |
| `string` | N | - | Texto ASCII |

### Function Codes

- **FC 3**: Read Holding Registers (lectura/escritura)
- **FC 4**: Read Input Registers (solo lectura)
- **FC 6**: Write Single Register (automático)
- **FC 16**: Write Multiple Registers (automático)

### Scale Factor

**Siempre documenta el rango esperado:**

```json
{
  "name": "Power_Limit",
  "scale_factor": 100,
  "description": "User: 0-100%, Hardware: 0-10000"
}
```

**Nunca uses `scale_factor: 0`** (causará división por cero).

### Límite de Registros

Algunos dispositivos limitan a 125 registros por petición. El controlador maneja esto automáticamente mediante agrupación inteligente.

### Slave ID

Por defecto es 1, pero puedes especificarlo:

```python
await controller.read_all(slave=2)
await controller.write_register("name", value, slave=3)
```

## 📚 Documentación Adicional

- [`configs/README.md`](configs/README.md) - Guía completa de configuración
- [`examples/scheduled_control/README.md`](examples/scheduled_control/README.md) - Control automático por horarios
- [`SCALE_FACTOR_IMPLEMENTATION.md`](SCALE_FACTOR_IMPLEMENTATION.md) - Detalles técnicos de scale factor
- [`CLAUDE.md`](CLAUDE.md) - Instrucciones para Claude Code

## 📝 Licencia

MIT License

## 👥 Contribuciones

Las contribuciones son bienvenidas:

1. Fork del repositorio
2. Crea una rama para tu feature
3. Commit de tus cambios
4. Push a la rama
5. Crea un Pull Request

## 📞 Soporte

Para reportar bugs o solicitar features, abre un issue en el repositorio.

## 🙏 Agradecimientos

- [pymodbus](https://github.com/pymodbus-dev/pymodbus) - Implementación del protocolo Modbus
- [Pydantic](https://pydantic-docs.helpmanual.io/) - Validación de datos
- [SunSpec Alliance](https://sunspec.org/) - Estándares para inversores solares
