"""
Clase para controlar un inversor solar individual
"""
import asyncio
import logging
from datetime import datetime
from typing import Optional
from .controller import ModbusController


logger = logging.getLogger(__name__)


class InversorController:
    """
    Controlador de alto nivel para un inversor solar individual.

    Permite habilitar/deshabilitar la producción de forma sencilla,
    manejando automáticamente el timeout y la configuración correcta.
    """

    def __init__(self, config_path: str, nombre: str = "Inversor"):
        """
        Inicializa el controlador del inversor.

        Args:
            config_path: Ruta al archivo de configuración JSON
            nombre: Nombre descriptivo del inversor (para logs)
        """
        self.config_path = config_path
        self.nombre = nombre
        self._ultimo_estado = None
        self._ultima_accion = None

    async def deshabilitar_produccion(self) -> bool:
        """
        Deshabilita completamente la producción (DISABLE).

        El inversor producirá normalmente sin control.

        Returns:
            True si la operación fue exitosa, False en caso contrario
        """
        try:
            async with ModbusController(self.config_path) as controller:
                # Simplemente deshabilitar el control
                await controller.write_register("Enable_limitacion", 0)
                await asyncio.sleep(0.3)

                # Verificar
                enable = await controller.read_register("Enable_limitacion")

                if int(enable) == 0:
                    logger.info(f"[{self.nombre}] ✓ Producción HABILITADA (DISABLE aplicado)")
                    self._ultimo_estado = "DISABLE"
                    return True
                else:
                    logger.error(f"[{self.nombre}] ✗ Error al deshabilitar: Enable={int(enable)}")
                    return False

        except Exception as e:
            logger.error(f"[{self.nombre}] ✗ Error en deshabilitar_produccion: {e}")
            return False

    async def limitar_a_cero(self) -> bool:
        """
        Limita la producción a 0% (LIMIT 0%).

        El inversor no producirá nada (0W).

        Returns:
            True si la operación fue exitosa, False en caso contrario
        """
        try:
            async with ModbusController(self.config_path) as controller:
                # 1. Configurar timeout a 0 (persistente)
                await controller.write_register("Timeout_limitacion", 0)
                await asyncio.sleep(0.2)

                # 2. Configurar límite a 0%
                await controller.write_register("Limitacion_potencia", 0)
                await asyncio.sleep(0.2)

                # 3. Habilitar limitación
                await controller.write_register("Enable_limitacion", 1)
                await asyncio.sleep(0.3)

                # Verificar
                enable = await controller.read_register("Enable_limitacion")
                limit = await controller.read_register("Limitacion_potencia")

                if int(enable) == 1 and int(limit) == 0:
                    logger.info(f"[{self.nombre}] ✓ Producción DESHABILITADA (LIMIT 0% aplicado)")
                    self._ultimo_estado = "LIMIT_0"
                    return True
                else:
                    logger.error(f"[{self.nombre}] ✗ Error al limitar: Enable={int(enable)}, Limit={int(limit)}")
                    return False

        except Exception as e:
            logger.error(f"[{self.nombre}] ✗ Error en limitar_a_cero: {e}")
            return False

    async def leer_estado(self) -> dict:
        """
        Lee el estado actual del inversor.

        Returns:
            Diccionario con: potencia, enable, limite, timeout
        """
        try:
            async with ModbusController(self.config_path) as controller:
                potencia = await controller.read_register("Potencia")
                enable = await controller.read_register("Enable_limitacion")
                limite = await controller.read_register("Limitacion_potencia")
                timeout = await controller.read_register("Timeout_limitacion")

                return {
                    'potencia': float(potencia),
                    'enable': int(enable),
                    'limite': int(limite),
                    'timeout': int(timeout),
                    'timestamp': datetime.now()
                }

        except Exception as e:
            logger.error(f"[{self.nombre}] ✗ Error al leer estado: {e}")
            return None

    def debe_limitar(self, dia_semana: int, hora: int) -> bool:
        """
        Determina si el inversor debe estar limitado según el horario.

        Args:
            dia_semana: 0=lunes, 6=domingo
            hora: Hora del día (0-23)

        Returns:
            True si debe aplicar LIMIT 0%, False si debe aplicar DISABLE
        """
        # Fines de semana: siempre DISABLE (producción normal)
        if dia_semana >= 5:
            return False

        # Días laborables: LIMIT 0% desde 16:00 hasta 06:59
        if hora >= 16 or hora <= 6:
            return True

        # Resto del tiempo: DISABLE (producción normal)
        return False

    async def aplicar_control_horario(self) -> bool:
        """
        Aplica el control según el horario actual.

        Returns:
            True si la operación fue exitosa, False en caso contrario
        """
        now = datetime.now()
        dia_semana = now.weekday()
        hora = now.hour

        debe_limitar = self.debe_limitar(dia_semana, hora)

        # Evitar aplicar la misma acción repetidamente
        accion_actual = "LIMIT_0" if debe_limitar else "DISABLE"

        if accion_actual == self._ultima_accion:
            logger.debug(f"[{self.nombre}] Estado ya es {accion_actual}, no se requiere acción")
            return True

        # Aplicar la acción correspondiente
        if debe_limitar:
            logger.info(f"[{self.nombre}] Horario {hora}:00 → Aplicando LIMIT 0%")
            exito = await self.limitar_a_cero()
        else:
            logger.info(f"[{self.nombre}] Horario {hora}:00 → Aplicando DISABLE")
            exito = await self.deshabilitar_produccion()

        if exito:
            self._ultima_accion = accion_actual

        return exito

    def obtener_estado_descripcion(self) -> str:
        """
        Retorna una descripción textual del último estado conocido.

        Returns:
            String descriptivo del estado
        """
        if self._ultimo_estado == "DISABLE":
            return "Producción normal (DISABLE)"
        elif self._ultimo_estado == "LIMIT_0":
            return "Sin producción (LIMIT 0%)"
        else:
            return "Desconocido"
