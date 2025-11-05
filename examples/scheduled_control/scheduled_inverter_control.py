#!/usr/bin/env python3
"""
Control Automático de Inversores Solares por Horario Laboral

Este script controla inversores solares basándose en el horario laboral:
- ENABLE (producción completa): Lunes-Viernes 07:00-15:59
- DISABLE (sin producción): Lunes-Viernes 16:00-06:59 + Fines de semana

IMPORTANTE - Terminología Modbus:
- ENABLE (producción completa) = Enable_limitacion = 0 (desactiva la limitación)
- DISABLE (sin producción) = Enable_limitacion = 1 + Limitacion_potencia = 0%

El script se ejecuta como servicio Linux con APScheduler en horario canario.
"""

import sys
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

# Configurar importación del módulo principal
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = (
    SCRIPT_DIR.parent.parent
)  # Subir dos niveles: scheduled_control -> examples -> raíz
sys.path.insert(0, str(PROJECT_DIR))

from modbus_controller import ModbusController

# Configurar APScheduler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

# ========================== CONFIGURACIÓN ==========================

# Timezone de Canarias
TIMEZONE = pytz.timezone("Atlantic/Canary")

# Ruta a la configuración del inversor (modificar según necesidad)
DEFAULT_CONFIG = str(PROJECT_DIR / "configs" / "medidor_potencia.json")

# Horario laboral (hora en formato 24h)
HORA_INICIO_LABORAL = 7  # 07:00
HORA_FIN_LABORAL = 15  # 15:59 (hasta las 16:00)

# Intervalo de verificación periódica (minutos)
INTERVALO_VERIFICACION = 5

# ========================== LOGGING ==========================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ========================== FUNCIONES DE CONTROL ==========================


async def aplicar_enable_produccion(
    controller, nombre: str = "Inversor"
) -> bool:
    """
    ENABLE: Habilita producción completa (desactiva limitación)

    Configuración Modbus:
    - Enable_limitacion = 0 (DESACTIVAR limitación = producción normal)

    Returns:
        bool: True si se aplicó correctamente, False en caso de error
    """
    try:
        logger.info(f"[{nombre}] Aplicando ENABLE (producción completa)...")

        # Desactivar la limitación para permitir producción completa
        await controller.write_register("Enable_limitacion", 0)
        await asyncio.sleep(0.3)

        # Verificar que se aplicó correctamente
        enable = await controller.read_register("Enable_limitacion")

        if int(enable) == 0:
            logger.info(
                f"[{nombre}] ✓ ENABLE aplicado correctamente (Enable=0, producción completa)"
            )
            return True
        else:
            logger.error(
                f"[{nombre}] ✗ Error al aplicar ENABLE: Enable={int(enable)} (esperado: 0)"
            )
            return False

    except Exception as e:
        logger.error(f"[{nombre}] ✗ Excepción al aplicar ENABLE: {e}")
        return False


async def aplicar_disable_produccion(
    controller, nombre: str = "Inversor"
) -> bool:
    """
    DISABLE: Deshabilita producción (limitación al 0%)

    Configuración Modbus:
    - Timeout_limitacion = 0 (persistente, no auto-reset)
    - Limitacion_potencia = 0 (0% de potencia máxima)
    - Enable_limitacion = 1 (ACTIVAR limitación al 0%)

    Returns:
        bool: True si se aplicó correctamente, False en caso de error
    """
    try:
        logger.info(f"[{nombre}] Aplicando DISABLE (sin producción)...")

        # Paso 1: Configurar timeout a 0 (persistente)
        await controller.write_register("Timeout_limitacion", 0)
        await asyncio.sleep(0.2)

        # Paso 2: Configurar límite a 0%
        await controller.write_register("Limitacion_potencia", 0)
        await asyncio.sleep(0.2)

        # Paso 3: Habilitar la limitación
        await controller.write_register("Enable_limitacion", 1)
        await asyncio.sleep(0.3)

        # Verificar que se aplicó correctamente
        enable = await controller.read_register("Enable_limitacion")
        limit = await controller.read_register("Limitacion_potencia")
        timeout = await controller.read_register("Timeout_limitacion")

        if int(enable) == 1 and abs(limit) < 0.1 and int(timeout) == 0:
            logger.info(
                f"[{nombre}] ✓ DISABLE aplicado correctamente (Enable=1, Limit=0%, Timeout=0)"
            )
            return True
        else:
            logger.error(
                f"[{nombre}] ✗ Error al aplicar DISABLE: "
                f"Enable={int(enable)} (esperado: 1), "
                f"Limit={limit:.1f}% (esperado: 0), "
                f"Timeout={int(timeout)} (esperado: 0)"
            )
            return False

    except Exception as e:
        logger.error(f"[{nombre}] ✗ Excepción al aplicar DISABLE: {e}")
        return False


# ========================== LÓGICA DE HORARIOS ==========================


def determinar_estado_segun_horario() -> str:
    """
    Determina el estado que debe tener el inversor según el horario actual

    Returns:
        str: "ENABLE" para producción completa, "DISABLE" para sin producción
    """
    ahora = datetime.now(TIMEZONE)
    dia_semana = ahora.weekday()  # 0=Lunes, 6=Domingo
    hora = ahora.hour

    # Fines de semana (Sábado=5, Domingo=6): DISABLE
    if dia_semana >= 5:
        logger.debug(f"Fin de semana detectado (día {dia_semana}): DISABLE")
        return "DISABLE"

    # Horario no laboral (16:00-06:59): DISABLE
    if hora >= 16 or hora < HORA_INICIO_LABORAL:
        logger.debug(f"Fuera de horario laboral (hora {hora}): DISABLE")
        return "DISABLE"

    # Horario laboral (07:00-15:59): ENABLE
    if HORA_INICIO_LABORAL <= hora <= HORA_FIN_LABORAL:
        logger.debug(f"Horario laboral (hora {hora}): ENABLE")
        return "ENABLE"

    # Caso por defecto (no debería llegar aquí)
    logger.warning(
        f"Horario no clasificado (día {dia_semana}, hora {hora}): DISABLE por seguridad"
    )
    return "DISABLE"


async def leer_estado_actual(
    controller, nombre: str = "Inversor"
) -> Optional[dict]:
    """
    Lee el estado actual del inversor

    Returns:
        dict: Diccionario con los valores actuales o None si hay error
    """
    try:
        enable = await controller.read_register("Enable_limitacion")
        limit = await controller.read_register("Limitacion_potencia")
        timeout = await controller.read_register("Timeout_limitacion")

        estado = {
            "enable": int(enable),
            "limit": float(limit),
            "timeout": int(timeout),
        }

        logger.debug(
            f"[{nombre}] Estado actual: Enable={estado['enable']}, Limit={estado['limit']:.1f}%, Timeout={estado['timeout']}"
        )
        return estado

    except Exception as e:
        logger.error(f"[{nombre}] Error al leer estado actual: {e}")
        return None


async def verificar_y_aplicar_estado(
    config_path: str = DEFAULT_CONFIG, nombre: str = "Inversor"
):
    """
    Verifica el horario actual y aplica el estado correspondiente al inversor

    Esta función:
    1. Determina el estado según el horario (ENABLE o DISABLE)
    2. Lee el estado actual del inversor
    3. Si es necesario, aplica el cambio correspondiente

    Args:
        config_path: Ruta al archivo de configuración JSON
        nombre: Nombre descriptivo del inversor (para logs)
    """
    try:
        estado_deseado = determinar_estado_segun_horario()
        ahora = datetime.now(TIMEZONE)

        logger.info(f"{'='*60}")
        logger.info(
            f"[{nombre}] Verificación: {ahora.strftime('%Y-%m-%d %H:%M:%S %Z')}"
        )
        logger.info(f"[{nombre}] Estado deseado: {estado_deseado}")

        async with ModbusController(config_path) as controller:
            # Leer estado actual
            estado_actual = await leer_estado_actual(controller, nombre)

            if estado_actual is None:
                logger.error(
                    f"[{nombre}] No se pudo leer el estado actual, reintentando en próxima verificación"
                )
                return

            # Determinar si el estado actual coincide con el deseado
            if estado_deseado == "ENABLE":
                # ENABLE = Enable_limitacion debe ser 0
                necesita_cambio = estado_actual["enable"] != 0
            else:  # DISABLE
                # DISABLE = Enable_limitacion debe ser 1 y Limit debe ser 0 (usar tolerancia para floats)
                necesita_cambio = (
                    estado_actual["enable"] != 1
                    or abs(estado_actual["limit"]) >= 0.1
                )

            if necesita_cambio:
                logger.info(
                    f"[{nombre}] Estado actual no coincide con deseado, aplicando cambio..."
                )

                if estado_deseado == "ENABLE":
                    exito = await aplicar_enable_produccion(controller, nombre)
                else:  # DISABLE
                    exito = await aplicar_disable_produccion(controller, nombre)

                if exito:
                    logger.info(f"[{nombre}] ✓ Estado aplicado correctamente")
                else:
                    logger.error(
                        f"[{nombre}] ✗ Error al aplicar estado, se reintentará en próxima verificación"
                    )
            else:
                logger.info(
                    f"[{nombre}] ✓ Estado actual ya es el correcto, no se requiere acción"
                )

        logger.info(f"{'='*60}\n")

    except Exception as e:
        logger.error(f"[{nombre}] ✗ Error en verificación: {e}")
        logger.info(f"{'='*60}\n")


# ========================== SCHEDULER ==========================


async def iniciar_control_automatico(
    config_path: str = DEFAULT_CONFIG, nombre: str = "Inversor"
):
    """
    Inicia el sistema de control automático con APScheduler

    Configura:
    - Verificación periódica cada INTERVALO_VERIFICACION minutos
    - Jobs específicos a las 07:00 y 16:00 (cambios de turno)
    - Verificación inicial al arrancar

    Args:
        config_path: Ruta al archivo de configuración JSON
        nombre: Nombre descriptivo del inversor (para logs)
    """
    logger.info("=" * 70)
    logger.info("CONTROL AUTOMÁTICO DE INVERSORES SOLARES - INICIO")
    logger.info("=" * 70)
    logger.info(f"Configuración: {config_path}")
    logger.info(f"Inversor: {nombre}")
    logger.info(f"Timezone: {TIMEZONE}")
    logger.info(
        f"Horario laboral: {HORA_INICIO_LABORAL}:00 - {HORA_FIN_LABORAL}:59 (Lun-Vie)"
    )
    logger.info(
        f"Verificación periódica: cada {INTERVALO_VERIFICACION} minutos"
    )
    logger.info("=" * 70 + "\n")

    # Crear scheduler
    scheduler = AsyncIOScheduler(timezone=TIMEZONE)

    # Job 1: Verificación periódica cada N minutos
    scheduler.add_job(
        verificar_y_aplicar_estado,
        trigger="interval",
        minutes=INTERVALO_VERIFICACION,
        args=[config_path, nombre],
        id="verificacion_periodica",
        name="Verificación periódica de estado",
    )

    # Job 2: Cambio a ENABLE a las 07:00 (lunes a viernes)
    scheduler.add_job(
        verificar_y_aplicar_estado,
        trigger=CronTrigger(
            hour=HORA_INICIO_LABORAL,
            minute=0,
            day_of_week="mon-fri",
            timezone=TIMEZONE,
        ),
        args=[config_path, nombre],
        id="inicio_laboral",
        name="Inicio jornada laboral (07:00)",
    )

    # Job 3: Cambio a DISABLE a las 16:00 (lunes a viernes)
    scheduler.add_job(
        verificar_y_aplicar_estado,
        trigger=CronTrigger(
            hour=16, minute=0, day_of_week="mon-fri", timezone=TIMEZONE
        ),
        args=[config_path, nombre],
        id="fin_laboral",
        name="Fin jornada laboral (16:00)",
    )

    # Job 4: Cambio a DISABLE los sábados a las 00:00
    scheduler.add_job(
        verificar_y_aplicar_estado,
        trigger=CronTrigger(
            hour=0, minute=0, day_of_week="sat", timezone=TIMEZONE
        ),
        args=[config_path, nombre],
        id="inicio_fin_semana",
        name="Inicio fin de semana (Sábado 00:00)",
    )

    # Iniciar scheduler
    scheduler.start()
    logger.info("Scheduler iniciado correctamente\n")

    # Ejecutar verificación inicial inmediatamente
    logger.info("Ejecutando verificación inicial...")
    await verificar_y_aplicar_estado(config_path, nombre)

    # Mostrar próximas ejecuciones programadas
    logger.info("\nPróximas ejecuciones programadas:")
    for job in scheduler.get_jobs():
        next_run = job.next_run_time
        logger.info(
            f"  - {job.name}: {next_run.strftime('%Y-%m-%d %H:%M:%S %Z') if next_run else 'N/A'}"
        )
    logger.info("\n")

    # Mantener el scheduler ejecutándose indefinidamente
    try:
        while True:
            await asyncio.sleep(
                3600
            )  # Dormir 1 hora entre checks del loop principal
    except KeyboardInterrupt:
        logger.info("\nInterrupción recibida, deteniendo scheduler...")
        scheduler.shutdown()
        logger.info("Scheduler detenido correctamente")


# ========================== MAIN ==========================


async def main():
    """
    Función principal con manejo de errores y reinicio automático

    El servicio NUNCA se detiene, continúa ejecutándose incluso si hay errores.
    """
    # Configuración para UN SOLO inversor:
    # config_path = DEFAULT_CONFIG
    # nombre_inversor = "Inversor"

    # Configuración para MÚLTIPLES inversores (controla ambos en paralelo):
    INVERSORES = [
        {
            "nombre": "Inversor 136",
            "config": str(
                PROJECT_DIR
                / "examples"
                / "scheduled_control"
                / "medidor_potencia_136.json"
            ),
        },
        {
            "nombre": "Inversor 135",
            "config": str(
                PROJECT_DIR
                / "examples"
                / "scheduled_control"
                / "medidor_potencia_135.json"
            ),
        },
    ]

    intentos = 0
    while True:
        try:
            intentos += 1
            logger.info(f"\n{'#'*70}")
            logger.info(f"# INTENTO DE INICIO #{intentos}")
            logger.info(f"{'#'*70}\n")

            # Control de múltiples inversores en paralelo
            if INVERSORES:
                logger.info(
                    f"Iniciando control de {len(INVERSORES)} inversores en paralelo...\n"
                )
                tasks = []
                for inv in INVERSORES:
                    task = asyncio.create_task(
                        iniciar_control_automatico(inv["config"], inv["nombre"])
                    )
                    tasks.append(task)

                # Ejecutar todos en paralelo
                await asyncio.gather(*tasks)
            else:
                # Control de un solo inversor (fallback)
                await iniciar_control_automatico(DEFAULT_CONFIG, "Inversor")

        except KeyboardInterrupt:
            logger.info("\n\nInterrupción manual recibida (Ctrl+C)")
            logger.info("Deteniendo servicio de control automático...")
            break

        except Exception as e:
            logger.error(f"\n\n{'!'*70}")
            logger.error(f"! ERROR CRÍTICO EN EL SERVICIO")
            logger.error(f"! {type(e).__name__}: {e}")
            logger.error(f"{'!'*70}")
            logger.info("\nEl servicio se reiniciará en 30 segundos...")
            await asyncio.sleep(30)
            logger.info("Reiniciando servicio...\n")

    logger.info("\nServicio finalizado correctamente")
    logger.info("=" * 70 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nPrograma finalizado por el usuario")
