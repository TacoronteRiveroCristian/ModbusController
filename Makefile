# Makefile principal para ModbusController
# Uso: make <comando>

.PHONY: help test


# Función para activar entorno virtual y crearlo si no existe
VENV_ACTIVATE = if [ ! -d .venv ]; then python3 -m venv .venv; fi; . .venv/bin/activate;
VENV_PYTHON = .venv/bin/python
VENV_PIP = .venv/bin/pip
VENV_PYTEST = .venv/bin/pytest

help:
	@$(VENV_ACTIVATE) \
	echo "ModbusController - Makefile" && \
	echo "Comandos disponibles:" && \
	echo "  help        Muestra esta ayuda" && \
	echo "  test        Ejecuta los tests (importado desde makefiles/test)"

# Importar sección de test desde makefiles/test
include makefiles/test

test:
	@$(VENV_ACTIVATE) \
	$(VENV_PIP) install --upgrade pip > /dev/null 2>&1; \
	$(VENV_PIP) install -r requirements.txt > /dev/null 2>&1; \
	$(VENV_PIP) install -e . > /dev/null 2>&1; \
	if ! [ -x $(VENV_PYTEST) ]; then $(VENV_PIP) install pytest pytest-asyncio > /dev/null 2>&1; fi; \
	make test-run
