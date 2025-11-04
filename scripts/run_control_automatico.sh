#!/bin/bash
#
# Script wrapper para ejecutar el control automático de inversores
# Activa el entorno virtual y ejecuta el script de Python
#

# Directorio del proyecto
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Activar entorno virtual
source "$PROJECT_DIR/.venv/bin/activate"

# Ejecutar script de control
python "$SCRIPT_DIR/control_automatico_inversores.py"

# Guardar código de salida
EXIT_CODE=$?

# Desactivar entorno virtual
deactivate

# Retornar código de salida
exit $EXIT_CODE
