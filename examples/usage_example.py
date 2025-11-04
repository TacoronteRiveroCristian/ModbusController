"""
Ejemplos de uso de ModbusController
"""
import asyncio
import logging
from pathlib import Path
from modbus_controller import ModbusController

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def ejemplo_basico():
    """Ejemplo básico: leer todos los registros una vez"""
    print("\n=== EJEMPLO 1: Lectura básica ===\n")

    config_path = Path(__file__).parent.parent / "configs" / "example_config.json"

    async with ModbusController(config_path) as controller:
        # Leer todos los registros
        valores = await controller.read_all()

        print("Valores leídos:")
        for nombre, datos in valores.items():
            print(f"  {nombre}: {datos['value']} {datos['unit']}")


async def ejemplo_lectura_individual():
    """Ejemplo: leer registros individuales"""
    print("\n=== EJEMPLO 2: Lectura individual ===\n")

    config_path = Path(__file__).parent.parent / "configs" / "example_config.json"

    async with ModbusController(config_path) as controller:
        # Leer registro específico
        temperatura = await controller.read_register("temperatura_ambiente")
        print(f"Temperatura: {temperatura} °C")

        presion = await controller.read_register("presion_sistema")
        print(f"Presión: {presion} bar")

        modelo = await controller.read_register("modelo_equipo")
        print(f"Modelo: {modelo}")


async def ejemplo_escritura():
    """Ejemplo: escribir valores en registros"""
    print("\n=== EJEMPLO 3: Escritura de registros ===\n")

    config_path = Path(__file__).parent.parent / "configs" / "example_config.json"

    async with ModbusController(config_path) as controller:
        # Leer valor actual
        setpoint_actual = await controller.read_register("setpoint_temperatura")
        print(f"Setpoint actual: {setpoint_actual} °C")

        # Escribir nuevo valor
        nuevo_setpoint = 22.5
        await controller.write_register("setpoint_temperatura", nuevo_setpoint)
        print(f"Nuevo setpoint escrito: {nuevo_setpoint} °C")

        # Verificar escritura
        await asyncio.sleep(0.5)
        setpoint_verificado = await controller.read_register("setpoint_temperatura")
        print(f"Setpoint verificado: {setpoint_verificado} °C")


async def ejemplo_monitorizacion():
    """Ejemplo: monitorización continua con callback"""
    print("\n=== EJEMPLO 4: Monitorización continua ===\n")

    config_path = Path(__file__).parent.parent / "configs" / "example_config.json"

    # Callback para notificaciones de cambios
    def on_value_change(nombre, valor_anterior, valor_nuevo):
        print(f"[CAMBIO] {nombre}: {valor_anterior} → {valor_nuevo}")

    async with ModbusController(config_path) as controller:
        # Iniciar monitorización
        await controller.start_monitoring(callback=on_value_change)

        print("Monitorizando... (presiona Ctrl+C para detener)")
        print("La monitorización lee cada registro según su poll_interval configurado")

        try:
            # Monitorizar durante 30 segundos
            await asyncio.sleep(30)
        except KeyboardInterrupt:
            print("\nDeteniendo monitorización...")

        # La monitorización se detiene automáticamente al salir del context manager


async def ejemplo_control_automatico():
    """Ejemplo: control automático basado en lecturas"""
    print("\n=== EJEMPLO 5: Control automático ===\n")

    config_path = Path(__file__).parent.parent / "configs" / "example_config.json"

    async with ModbusController(config_path) as controller:
        print("Control de temperatura automático (simulación)")

        for i in range(10):
            # Leer temperatura actual
            temperatura = await controller.read_register("temperatura_ambiente")
            setpoint = await controller.read_register("setpoint_temperatura")

            print(f"\nIteración {i+1}:")
            print(f"  Temperatura actual: {temperatura} °C")
            print(f"  Setpoint: {setpoint} °C")

            # Lógica de control simple
            if temperatura < setpoint - 1.0:
                # Temperatura baja: encender calefacción
                print(f"  → Temperatura baja, ajustando control...")
                # Aquí escribirías en el registro de control
                # await controller.write_register("control_calefaccion", 1)
            elif temperatura > setpoint + 1.0:
                # Temperatura alta: apagar calefacción
                print(f"  → Temperatura alta, ajustando control...")
                # await controller.write_register("control_calefaccion", 0)
            else:
                print(f"  → Temperatura en rango OK")

            await asyncio.sleep(2)


async def ejemplo_cache():
    """Ejemplo: uso de caché para valores leídos"""
    print("\n=== EJEMPLO 6: Uso de caché ===\n")

    config_path = Path(__file__).parent.parent / "configs" / "example_config.json"

    async with ModbusController(config_path) as controller:
        # Primera lectura (desde dispositivo)
        print("Primera lectura desde dispositivo...")
        await controller.read_all()

        # Obtener valores desde caché (sin acceder al dispositivo)
        print("\nValores desde caché:")
        cached_values = controller.get_all_last_values()
        for nombre, valor in cached_values.items():
            print(f"  {nombre}: {valor}")

        # Obtener valor individual desde caché
        temp_cached = controller.get_last_value("temperatura_ambiente")
        print(f"\nTemperatura (caché): {temp_cached} °C")


async def ejemplo_multiples_configs():
    """Ejemplo: usar múltiples configuraciones (múltiples dispositivos)"""
    print("\n=== EJEMPLO 7: Múltiples dispositivos ===\n")

    config1_path = Path(__file__).parent.parent / "configs" / "example_config.json"
    config2_path = Path(__file__).parent.parent / "configs" / "example_config_rtu.json"

    # Controlador 1 (TCP)
    async with ModbusController(config1_path) as controller1:
        print("Leyendo dispositivo 1 (TCP)...")
        valores1 = await controller1.read_all()
        print(f"  Leídos {len(valores1)} registros")

    # Controlador 2 (RTU)
    # async with ModbusController(config2_path) as controller2:
    #     print("Leyendo dispositivo 2 (RTU)...")
    #     valores2 = await controller2.read_all()
    #     print(f"  Leídos {len(valores2)} registros")


async def main():
    """Ejecuta todos los ejemplos"""
    print("=" * 60)
    print("EJEMPLOS DE USO DE ModbusController")
    print("=" * 60)

    ejemplos = [
        ("Lectura básica", ejemplo_basico),
        ("Lectura individual", ejemplo_lectura_individual),
        ("Escritura", ejemplo_escritura),
        ("Monitorización", ejemplo_monitorizacion),
        ("Control automático", ejemplo_control_automatico),
        ("Uso de caché", ejemplo_cache),
        ("Múltiples dispositivos", ejemplo_multiples_configs),
    ]

    print("\nEjemplos disponibles:")
    for i, (nombre, _) in enumerate(ejemplos, 1):
        print(f"{i}. {nombre}")

    print("\nNOTA: Estos ejemplos requieren un servidor Modbus real o simulado.")
    print("Para pruebas, puedes usar pymodbus.simulator o un PLC/dispositivo real.")

    # Descomentar para ejecutar ejemplos específicos:
    # await ejemplo_basico()
    # await ejemplo_lectura_individual()
    # await ejemplo_escritura()
    # await ejemplo_monitorizacion()
    # await ejemplo_control_automatico()
    # await ejemplo_cache()
    # await ejemplo_multiples_configs()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nEjecución interrumpida por el usuario")
    except Exception as e:
        logger.error(f"Error en ejemplos: {e}", exc_info=True)
