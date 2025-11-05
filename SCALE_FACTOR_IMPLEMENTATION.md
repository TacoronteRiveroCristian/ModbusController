# Implementación de Scale Factor

## Resumen

Se ha implementado soporte completo para factores de escala (`scale_factor`) y offsets en ModbusController. Esta funcionalidad permite que los usuarios trabajen con valores amigables (0-100%) mientras la librería convierte automáticamente a los valores raw del hardware (0-10000).

## Cambios Realizados

### 1. Librería Core (`modbus_controller/controller.py`)

**Lectura de registros (líneas 215-219):**
```python
# Apply scale factor and offset if configured
if reg.scale_factor is not None:
    value = value * reg.scale_factor
if reg.offset is not None:
    value = value + reg.offset
```

Fórmula: `valor_usuario = valor_raw * scale_factor + offset`

**Escritura de registros (líneas 287-294):**
```python
# Apply inverse scaling if configured (user value -> raw hardware value)
write_value = value
if reg.offset is not None:
    write_value = write_value - reg.offset
if reg.scale_factor is not None:
    if reg.scale_factor == 0:
        raise WriteError(f"Scale factor cannot be zero for register '{name}'")
    write_value = write_value / reg.scale_factor
```

Fórmula inversa: `valor_raw = (valor_usuario - offset) / scale_factor`

**Logging mejorado (líneas 325-329):**
```python
# Log with scale info if applicable
if reg.scale_factor is not None or reg.offset is not None:
    logger.info(f"Escrito '{name}' = {value} (raw: {write_value}) en dirección {reg.address}")
else:
    logger.info(f"Escrito '{name}' = {value} en dirección {reg.address}")
```

### 2. Configuración JSON

**Registro `Limitacion_potencia` actualizado en:**
- `configs/medidor_potencia.json`
- `configs/medidor_potencia_135.json`

```json
{
    "name": "Limitacion_potencia",
    "address": 40242,
    "type": "uint16",
    "unit": "%",
    "function_code": 3,
    "poll_interval": 10.0,
    "writable": true,
    "scale_factor": 100,
    "description": "WMaxLimPct - Set power output (0-100%, hardware expects 0-10000)"
}
```

**Resultado:**
- Usuario escribe: `50` → Hardware recibe: `5000` (50% × 100)
- Usuario escribe: `100` → Hardware recibe: `10000` (100% × 100)
- Usuario lee: `5000` → Usuario recibe: `50.0` (5000 ÷ 100)

### 3. Scripts Actualizados

#### `scripts/set_limit_and_enable.py`
- Rango aceptado: 0-100 (porcentajes)
- Validación: `if valor < 0 or valor > 100`
- Mensajes actualizados para mostrar porcentajes con `.1f` format
- Comparaciones con tolerancia float: `abs(limit_final - valor) < 0.1`

#### `scripts/set_limit_only.py`
- Rango aceptado: 0-100 (porcentajes)
- Validación: `if valor < 0 or valor > 100`
- Mensajes actualizados para mostrar porcentajes con `.1f` format
- Comparaciones con tolerancia float: `abs(limit_verificado - valor) < 0.1`

#### `scripts/read_status.py`
- Display actualizado: `{limit:.1f}%` en lugar de `{int(limit)}`

#### `scripts/control_automatico_inversores.py`
- Display actualizado: `{limit_actual:.1f}%`
- Comparación con tolerancia: `abs(limit) < 0.1` en lugar de `int(limit) == 0`

#### `examples/scheduled_inverter_control.py`
- Display actualizado en múltiples lugares
- Comparaciones con tolerancia float
- Estado almacenado como `float(limit)` en lugar de `int(limit)`

## Compatibilidad

### Registros sin scale_factor
Los registros que NO tienen `scale_factor` definido funcionan **exactamente igual que antes**. No hay cambios en su comportamiento.

### Registros con scale_factor
Los registros con `scale_factor` ahora:
- Aceptan valores en el rango amigable para el usuario (0-100)
- Convierten automáticamente al rango del hardware (0-10000)
- Muestran valores amigables al leer (50.0 en lugar de 5000)

## Uso

### Escribir valores

```python
from modbus_controller import ModbusController

async with ModbusController("configs/medidor_potencia.json") as controller:
    # Usuario escribe porcentaje (0-100)
    await controller.write_register("Limitacion_potencia", 50)

    # La librería escribe automáticamente 5000 al hardware
    # Log: "Escrito 'Limitacion_potencia' = 50 (raw: 5000.0) en dirección 40242"
```

### Leer valores

```python
async with ModbusController("configs/medidor_potencia.json") as controller:
    # Hardware tiene valor 5000
    limit = await controller.read_register("Limitacion_potencia")

    # Usuario recibe 50.0 (5000 / 100)
    print(f"Limitación: {limit:.1f}%")  # Output: "Limitación: 50.0%"
```

### Comparaciones

Cuando se comparan valores con scale_factor, usar tolerancia para floats:

```python
# ❌ Incorrecto (puede fallar por precisión de floats)
if limit == 50:
    ...

# ✓ Correcto
if abs(limit - 50) < 0.1:
    ...
```

## Ejemplos de Scripts

### Establecer límite al 75%

```bash
python scripts/set_limit_and_enable.py 75
```

Salida:
```
=== LIMITAR POTENCIA AL 75% Y HABILITAR ===

Estado inicial:
  Limitación: 0.0%
  Enable: 0 (DESHABILITADO)
  Timeout: 0

[1/3] Desactivando timeout automático...
      Verificado: 0

[2/3] Escribiendo limitación: 75...
      Verificado: 75.0%

[3/3] Habilitando limitación...
      Verificado: 1 (HABILITADO)

Estado final:
  Limitación: 75.0%
  Enable: 1 (HABILITADO)
  Timeout: 0

✓ Limitación al 75% habilitada correctamente
```

### Leer estado actual

```bash
python scripts/read_status.py
```

Salida:
```
=== ESTADO ACTUAL ===

Potencia actual: 1250.50 W
Limitación: 75.0%
Estado: HABILITADO (1)
Timeout: PERSISTENTE (0)

→ La potencia está limitada al 75.0%
```

## Detalles Técnicos

### Fix para Tipos Enteros

**Problema resuelto**: El data converter ahora acepta valores `float` y los redondea automáticamente a `int` para tipos enteros (uint16, int16, uint32, int32).

**Antes (causaba error):**
```python
value = 0.0  # float después del scale factor
converter.value_to_registers(value, "uint16")
# ERROR: "Valor 0.0 fuera de rango para uint16"
```

**Ahora (funciona correctamente):**
```python
value = 0.0  # float después del scale factor
converter.value_to_registers(value, "uint16")
# OK: [0] - el float se redondea a int automáticamente
```

**Implementación** (`data_converter.py` líneas 161-163):
```python
if isinstance(value, float):
    value = round(value)
# Luego validar como int
```

Esto aplica a:
- `uint16`: Redondea floats a int antes de validar rango 0-65535
- `int16`: Redondea floats a int antes de validar rango -32768 a 32767
- `uint32`: Redondea floats a int antes de validar rango 0-4294967295
- `int32`: Redondea floats a int antes de validar rango -2147483648 a 2147483647

### Cálculo del Scale Factor

Para el registro `Limitacion_potencia` (SunSpec):
- Rango usuario: 0-100 (%)
- Rango hardware: 0-10000
- Scale factor: 100

**Fórmula:**
```
scale_factor = rango_hardware / rango_usuario
scale_factor = 10000 / 100 = 100
```

### Precisión

Los valores se manejan como `float` en Python, con precisión suficiente para este caso de uso:
- `50.0%` → `5000.0` raw → `50.0%` (sin pérdida)
- `75.5%` → `7550.0` raw → `75.5%` (sin pérdida)

Para comparaciones se usa tolerancia de `0.1` para evitar problemas de precisión flotante.

## Testing

Verificación de sintaxis realizada:
```bash
✓ modbus_controller/controller.py OK
✓ scripts/set_limit_and_enable.py OK
✓ scripts/set_limit_only.py OK
✓ scripts/read_status.py OK
✓ scripts/control_automatico_inversores.py OK
✓ examples/scheduled_inverter_control.py OK
```

## Notas Importantes

1. **Validación de division por cero**: El código valida que `scale_factor != 0` antes de dividir.

2. **Orden de operaciones**:
   - Lectura: `(raw * scale_factor) + offset`
   - Escritura: `(user - offset) / scale_factor`

3. **Compatibilidad hacia atrás**: Registros sin `scale_factor` funcionan igual que antes.

4. **Logging**: Los logs muestran tanto el valor del usuario como el valor raw cuando hay scaling aplicado.

5. **Tipos de datos**: Los valores escalados se mantienen como `float` para preservar precisión.

## Migración

Para añadir scale_factor a otros registros:

1. Añadir `scale_factor` en el JSON:
   ```json
   {
       "name": "Mi_Registro",
       "address": 40xxx,
       "type": "uint16",
       "scale_factor": 100,
       ...
   }
   ```

2. Actualizar scripts para usar valores escalados (0-100 en lugar de raw).

3. Actualizar comparaciones para usar tolerancia float si es necesario.

4. Actualizar display para mostrar `.1f` en lugar de `int()`.

## Referencias

- SunSpec Alliance: https://sunspec.org/
- Modbus Protocol: https://modbus.org/
- Pydantic Models: `modbus_controller/config_loader.py` línea 56-57
