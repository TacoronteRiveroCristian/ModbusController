# ⏰ Horarios Configurados - Control de Inversores

## 📊 Tabla de Horarios

### Días Laborables (Lunes a Viernes)

| Hora | Estado | Producción | Descripción |
|------|--------|------------|-------------|
| 00:00 - 06:59 | ⛔ **LIMIT 0%** | 0W | Horario nocturno sin demanda |
| 07:00 - 15:59 | ✅ **DISABLE** | ~8000W total | Producción normal (horario laboral) |
| 16:00 - 23:59 | ⛔ **LIMIT 0%** | 0W | Tarde/noche sin demanda |

### Fines de Semana (Sábado y Domingo)

| Hora | Estado | Producción | Descripción |
|------|--------|------------|-------------|
| 00:00 - 23:59 | ✅ **DISABLE** | ~8000W total | Producción normal todo el día |

## 📈 Distribución Semanal

```
LUNES A VIERNES (5 días):
├─ 00:00 ─────── 06:59   →  LIMIT 0%  (7 horas × 5 días = 35 horas)
├─ 07:00 ─────── 15:59   →  DISABLE   (9 horas × 5 días = 45 horas)
└─ 16:00 ─────── 23:59   →  LIMIT 0%  (8 horas × 5 días = 40 horas)

FINES DE SEMANA (2 días):
└─ 00:00 ─────── 23:59   →  DISABLE   (24 horas × 2 días = 48 horas)
```

## 📊 Resumen Estadístico

- **Total horas semanales**: 168 horas (7 días × 24h)
- **Horas con LIMIT 0%** (sin producción): 75 horas (44.6%)
- **Horas con DISABLE** (producción normal): 93 horas (55.4%)

### Desglose por Día de la Semana

| Día | LIMIT 0% | DISABLE | Total |
|-----|----------|---------|-------|
| Lunes | 15h | 9h | 24h |
| Martes | 15h | 9h | 24h |
| Miércoles | 15h | 9h | 24h |
| Jueves | 15h | 9h | 24h |
| Viernes | 15h | 9h | 24h |
| **Sábado** | 0h | **24h** | 24h |
| **Domingo** | 0h | **24h** | 24h |
| **TOTAL** | **75h** | **93h** | **168h** |

## 🔄 Transiciones de Estado

El sistema cambia automáticamente cada 15 minutos (si está instalado el cron):

```
Horarios críticos de cambio:

06:45-07:15  →  Transición: LIMIT 0% → DISABLE (empiezan las operaciones)
15:45-16:15  →  Transición: DISABLE → LIMIT 0% (terminan las operaciones)

Viernes 23:45 → Sábado 00:15  →  LIMIT 0% → DISABLE (empieza fin de semana)
Domingo 23:45 → Lunes 00:15   →  DISABLE → LIMIT 0% (termina fin de semana)
```

## 📝 Notas Importantes

### Estado LIMIT 0%
- **Enable**: 1 (control activo)
- **Límite**: 0%
- **Timeout**: 0 (persistente)
- **Producción**: 0W
- **Cuándo**: 16:00-06:59 laborables

### Estado DISABLE
- **Enable**: 0 (control desactivado)
- **Límite**: (valor guardado, no usado)
- **Producción**: ~4000W por inversor
- **Cuándo**: 07:00-15:59 laborables y todo el fin de semana

## 🧪 Probar Lógica de Horarios

```bash
cd scripts/
source ../.venv/bin/activate
python test_horarios.py
```

Este script muestra una tabla completa de todos los horarios sin conectar a los inversores.

## ✏️ Modificar Horarios

Para cambiar los horarios, edita `scripts/control_automatico_inversores.py` línea ~103:

```python
# Horario actual (16:00 a 06:59)
elif hora >= 16 or hora <= 6:

# Ejemplos de modificaciones:

# Solo tardes (16:00 a 20:59)
elif 16 <= hora <= 20:

# Solo noches (00:00 a 07:59)
elif hora <= 7:

# Tarde extendida (14:00 a 22:59)
elif 14 <= hora <= 22:

# Noche completa (18:00 a 08:59)
elif hora >= 18 or hora <= 8:
```

Después de modificar, prueba con:
```bash
make auto
```

## 📞 Verificación del Estado Actual

```bash
# Ver qué acción se aplicaría AHORA
make auto

# Ver estado específico de cada inversor
make status  # Inversor .136
python read_status.py configs/medidor_potencia_135.json  # Inversor .135
```

---

**Última actualización**: Configuración para LIMIT 0% de 16:00 a 06:59 en días laborables
