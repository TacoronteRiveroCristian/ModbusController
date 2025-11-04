"""
Control automático de limitación de potencia con horarios
- Lunes a Viernes: Limitación a 0 de 16:00 a 06:59
- Sábados y Domingos: Limitación a 0 todo el día
"""
import asyncio
import logging
from datetime import datetime, time
from pathlib import Path
from modbus_controller import ModbusController

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PowerLimitController:
    """Controlador de limitación de potencia con horarios"""

    # Horarios de limitación (lunes a viernes)
    LIMIT_START_TIME = time(16, 0)   # 16:00 (4:00 PM)
    LIMIT_END_TIME = time(6, 59)     # 06:59 (6:59 AM)

    # Días de la semana (0=Lunes, 6=Domingo)
    WEEKEND_DAYS = [5, 6]  # Sábado y Domingo

    def __init__(self, config_path: str):
        """
        Inicializa el controlador.

        Args:
            config_path: Ruta al archivo JSON de configuración con los registros:
                - potencia_actual: Lectura de potencia
                - limitacion_potencia: Setpoint de limitación
                - enable_limitacion: Habilitación de limitación (0=OFF, 1=ON)
        """
        self.config_path = config_path
        self.controller = None
        self.running = False
        self.last_state = None

    def should_limit_power(self) -> bool:
        """
        Determina si se debe limitar la potencia según el horario actual.

        Returns:
            True si se debe limitar, False en caso contrario
        """
        now = datetime.now()
        current_time = now.time()
        current_weekday = now.weekday()  # 0=Lunes, 6=Domingo

        # Fin de semana: siempre limitado
        if current_weekday in self.WEEKEND_DAYS:
            return True

        # Entre semana: limitado de 16:00 a 06:59
        # Como cruza medianoche, verificamos si está FUERA del horario permitido (07:00-15:59)
        if current_time >= self.LIMIT_START_TIME or current_time <= self.LIMIT_END_TIME:
            return True

        return False

    async def apply_power_limit(self, limit: bool) -> None:
        """
        Aplica o quita la limitación de potencia.

        Args:
            limit: True para aplicar limitación, False para quitar
        """
        try:
            if limit:
                # Aplicar limitación a 0
                logger.info("Aplicando limitación de potencia a 0 kW")
                await self.controller.write_register("limitacion_potencia", 0.0)
                await asyncio.sleep(0.2)  # Pequeña pausa entre escrituras
                await self.controller.write_register("enable_limitacion", 1)
                logger.info("Limitación activada: 0 kW")
            else:
                # Quitar limitación
                logger.info("Quitando limitación de potencia")
                await self.controller.write_register("enable_limitacion", 0)
                logger.info("Limitación desactivada")

        except Exception as e:
            logger.error(f"Error al aplicar limitación: {e}")
            raise

    def get_schedule_info(self) -> str:
        """Retorna información del estado del horario actual"""
        now = datetime.now()
        current_time = now.time()
        current_weekday = now.weekday()

        day_names = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        day_name = day_names[current_weekday]

        if current_weekday in self.WEEKEND_DAYS:
            return f"{day_name} {current_time.strftime('%H:%M')} - FIN DE SEMANA (limitación activa todo el día)"
        else:
            should_limit = self.should_limit_power()
            status = "LIMITADO" if should_limit else "PERMITIDO"
            next_change = "16:00" if not should_limit else "07:00"
            return f"{day_name} {current_time.strftime('%H:%M')} - {status} (próximo cambio: {next_change})"

    async def monitor_and_control(self, interval: float = 60.0) -> None:
        """
        Bucle principal de monitorización y control.

        Args:
            interval: Intervalo de verificación en segundos (por defecto 60s)
        """
        logger.info("=" * 70)
        logger.info("Sistema de Control de Limitación de Potencia")
        logger.info("=" * 70)
        logger.info("Horario de limitación:")
        logger.info("   - Lunes a Viernes: 16:00 - 06:59")
        logger.info("   - Fines de semana: Todo el día")
        logger.info(f"Intervalo de verificación: {interval}s")
        logger.info("=" * 70)

        async with ModbusController(self.config_path) as controller:
            self.controller = controller
            self.running = True
            iteration = 0

            while self.running:
                try:
                    iteration += 1

                    # Leer potencia actual
                    potencia_actual = await controller.read_register("potencia_actual")

                    # Leer estado actual de limitación
                    limitacion_actual = await controller.read_register("limitacion_potencia")
                    enable_actual = await controller.read_register("enable_limitacion")

                    # Determinar si se debe limitar
                    should_limit = self.should_limit_power()

                    # Información de estado
                    logger.info("")
                    logger.info(f"{'=' * 70}")
                    logger.info(f"Iteración #{iteration} - {self.get_schedule_info()}")
                    logger.info(f"{'=' * 70}")
                    logger.info(f"Potencia actual: {potencia_actual:.2f} kW")
                    logger.info(f"Limitación configurada: {limitacion_actual:.2f} kW")
                    logger.info(f"Enable limitación: {'ON' if enable_actual else 'OFF'}")
                    logger.info(f"Acción requerida: {'LIMITAR' if should_limit else 'PERMITIR'}")

                    # Verificar si el estado cambió
                    current_state = (should_limit, enable_actual == 1)

                    if self.last_state is None or self.last_state[0] != current_state[0]:
                        # Cambio de horario o primera ejecución
                        if should_limit:
                            if enable_actual != 1 or limitacion_actual != 0.0:
                                logger.info("Aplicando cambio de estado...")
                                await self.apply_power_limit(True)
                            else:
                                logger.info("Limitación ya está correctamente aplicada")
                        else:
                            if enable_actual != 0:
                                logger.info("Aplicando cambio de estado...")
                                await self.apply_power_limit(False)
                            else:
                                logger.info("Limitación ya está correctamente desactivada")
                    else:
                        # Verificar consistencia (por si alguien cambió manualmente)
                        if should_limit:
                            if enable_actual != 1 or limitacion_actual != 0.0:
                                logger.warning("Inconsistencia detectada, reaplicando limitación...")
                                await self.apply_power_limit(True)
                        else:
                            if enable_actual != 0:
                                logger.warning("Inconsistencia detectada, desactivando limitación...")
                                await self.apply_power_limit(False)

                    self.last_state = (should_limit, enable_actual == 1)

                    # Esperar hasta la próxima iteración
                    logger.info(f"Próxima verificación en {interval}s...")
                    await asyncio.sleep(interval)

                except KeyboardInterrupt:
                    logger.info("\nInterrupción recibida, deteniendo...")
                    break
                except Exception as e:
                    logger.error(f"Error en bucle de control: {e}", exc_info=True)
                    logger.info(f"Reintentando en {interval}s...")
                    await asyncio.sleep(interval)

    def stop(self):
        """Detiene el controlador"""
        self.running = False


async def main():
    """Función principal"""
    # Ruta al archivo de configuración
    # Asegúrate de tener un JSON con los registros:
    # - potencia_actual
    # - limitacion_potencia
    # - enable_limitacion
    config_path = Path(__file__).parent.parent / "configs" / "power_control_config.json"

    if not config_path.exists():
        logger.error(f"Archivo de configuración no encontrado: {config_path}")
        logger.info("Crea un archivo JSON con la siguiente estructura:")
        logger.info("""
{
  "connection": {
    "type": "tcp",
    "host": "192.168.1.100",
    "port": 502,
    "timeout": 3
  },
  "registers": [
    {
      "name": "potencia_actual",
      "address": 1000,
      "type": "float32",
      "unit": "kW",
      "function_code": 3,
      "description": "Lectura de potencia actual"
    },
    {
      "name": "limitacion_potencia",
      "address": 2000,
      "type": "float32",
      "unit": "kW",
      "function_code": 3,
      "description": "Setpoint de limitación de potencia"
    },
    {
      "name": "enable_limitacion",
      "address": 2002,
      "type": "uint16",
      "unit": "",
      "function_code": 3,
      "description": "Enable limitación (0=OFF, 1=ON)"
    }
  ],
  "limits": {
    "max_registers_per_read": 125,
    "min_request_interval": 0.1
  }
}
        """)
        return

    # Crear controlador
    controller = PowerLimitController(str(config_path))

    try:
        # Iniciar monitorización y control
        # Verificación cada 60 segundos (ajustar según necesidad)
        await controller.monitor_and_control(interval=60.0)
    except KeyboardInterrupt:
        logger.info("\nPrograma terminado por el usuario")
    except Exception as e:
        logger.error(f"Error fatal: {e}", exc_info=True)
    finally:
        controller.stop()
        logger.info("Sistema detenido")


if __name__ == "__main__":
    asyncio.run(main())
