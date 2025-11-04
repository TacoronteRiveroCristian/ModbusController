# Makefile para operaciones Modbus
# Uso: make <comando> [CONFIG=path/to/config.json] [LIMIT=<0-100>]
#
# IMPORTANTE: Asegúrate de tener el venv activado antes de usar estos comandos:
#   source ../.venv/bin/activate

.PHONY: help read status set-limit enable disable limit reset check-deps auto install-cron uninstall-cron logs

# Configuración por defecto
CONFIG ?= configs/medidor_potencia.json

# Usar el python que esté activo (debe tener venv activado)
PYTHON := python

check-deps:
	@if ! $(PYTHON) -c "import pymodbus" 2>/dev/null; then \
		echo ""; \
		echo "Error: pymodbus no está instalado o el venv no está activado."; \
		echo ""; \
		echo "Por favor ejecuta:"; \
		echo "  cd .. && source .venv/bin/activate && cd scripts"; \
		echo "  O desde el directorio raíz:"; \
		echo "  source .venv/bin/activate"; \
		echo ""; \
		exit 1; \
	fi

help:
	@echo "=== Operaciones Modbus ==="
	@echo ""
	@echo "IMPORTANTE: Activa el venv primero:"
	@echo "  source ../.venv/bin/activate"
	@echo ""
	@echo "Lectura:"
	@echo "  make read [CONFIG=path]       - Leer todos los registros"
	@echo "  make status                   - Ver estado de limitación"
	@echo ""
	@echo "Escritura de limitación de potencia:"
	@echo "  make limit LIMIT=<0-100>      - Establecer limitación y habilitar"
	@echo "  make set-limit LIMIT=<0-100>  - Solo cambiar límite (sin habilitar)"
	@echo "  make enable                   - Habilitar limitación"
	@echo "  make disable                  - Deshabilitar limitación"
	@echo "  make reset                    - Poner todo a 0 (límite=0, enable=0)"
	@echo ""
	@echo "Control automático (ambos inversores .135 y .136):"
	@echo "  make auto                     - Ejecutar control automático ahora"
	@echo "  make install-cron             - Instalar en cron (cada 15 min)"
	@echo "  make uninstall-cron           - Desinstalar de cron"
	@echo "  make logs                     - Ver logs del control automático"
	@echo ""
	@echo "Ejemplos:"
	@echo "  make status                           # Ver estado actual"
	@echo "  make limit LIMIT=50                   # Limitar a 50% y habilitar"
	@echo "  make set-limit LIMIT=75               # Solo cambiar límite a 75%"
	@echo "  make disable                          # Deshabilitar limitación"
	@echo "  make reset                            # Reset todo a 0"
	@echo "  make auto                             # Control automático manual"
	@echo "  make install-cron                     # Activar automatización"
	@echo "  make read CONFIG=configs/otro.json    # Leer con config específico"
	@echo ""
	@echo "Config por defecto: $(CONFIG)"

read: check-deps
	@cd .. && $(PYTHON) scripts/read_all.py

status: check-deps
	@cd .. && $(PYTHON) scripts/read_status.py $(CONFIG)

set-limit: check-deps
	@if [ -z "$(LIMIT)" ]; then \
		echo "Error: Debes especificar LIMIT=<0-100>"; \
		echo "Ejemplo: make set-limit LIMIT=50"; \
		exit 1; \
	fi
	@cd .. && $(PYTHON) scripts/set_limit_only.py $(LIMIT) $(CONFIG)

enable: check-deps
	@cd .. && $(PYTHON) scripts/toggle_enable.py enable $(CONFIG)

disable: check-deps
	@cd .. && $(PYTHON) scripts/toggle_enable.py disable $(CONFIG)

limit: check-deps
	@if [ -z "$(LIMIT)" ]; then \
		echo "Error: Debes especificar LIMIT=<0-100>"; \
		echo "Ejemplo: make limit LIMIT=50"; \
		exit 1; \
	fi
	@cd .. && $(PYTHON) scripts/set_limit_and_enable.py $(LIMIT) $(CONFIG)

reset: check-deps
	@echo ""
	@echo "=== RESET: Estableciendo límite=0 y enable=0 ==="
	@echo ""
	@cd .. && $(PYTHON) scripts/set_limit_only.py 0 $(CONFIG)
	@sleep 1
	@cd .. && $(PYTHON) scripts/toggle_enable.py disable $(CONFIG)

# Alias comunes
off: disable
on: enable

# Control automático
auto:
	@./run_control_automatico.sh

install-cron:
	@echo ""
	@echo "=== INSTALANDO CONTROL AUTOMÁTICO EN CRON ==="
	@echo ""
	@mkdir -p ../logs
	@(crontab -l 2>/dev/null | grep -v "control_automatico"; echo "*/15 * * * * $(PWD)/run_control_automatico.sh >> $(PWD)/../logs/control_auto.log 2>&1") | crontab -
	@echo "✓ Cron instalado: se ejecutará cada 15 minutos"
	@echo ""
	@echo "Verificar con: crontab -l | grep control_automatico"
	@echo "Ver logs con:  make logs"
	@echo ""

uninstall-cron:
	@echo ""
	@echo "=== DESINSTALANDO CONTROL AUTOMÁTICO DE CRON ==="
	@echo ""
	@crontab -l 2>/dev/null | grep -v "control_automatico" | crontab -
	@echo "✓ Cron desinstalado"
	@echo ""

logs:
	@if [ -f ../logs/control_auto.log ]; then \
		tail -100 ../logs/control_auto.log; \
	else \
		echo "No hay logs todavía. El archivo se creará cuando el cron se ejecute."; \
	fi
