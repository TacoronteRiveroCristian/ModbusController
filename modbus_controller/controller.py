"""
Clase principal ModbusController para gestión de lecturas y escrituras Modbus
"""
import asyncio
import logging
from typing import Dict, List, Optional, Callable, Any, Union
from datetime import datetime, timedelta
from pathlib import Path

from pymodbus.client import AsyncModbusTcpClient, AsyncModbusSerialClient
from pymodbus.exceptions import ModbusException

from .config_loader import ModbusConfig, RegisterConfig
from .data_converter import ModbusDataConverter
from .exceptions import (
    ModbusControllerError,
    ConnectionError as ModbusConnectionError,
    ReadError,
    WriteError,
    ConfigurationError
)

logger = logging.getLogger(__name__)


class ModbusController:
    """
    Controlador Modbus asíncrono con gestión inteligente de conexiones,
    monitorización automática y conversión de tipos de datos.
    """

    def __init__(self, config: Union[str, Path, ModbusConfig]):
        """
        Inicializa el controlador Modbus.

        Args:
            config: Ruta al archivo JSON de configuración o instancia de ModbusConfig
        """
        if isinstance(config, (str, Path)):
            from .config_loader import ConfigLoader
            self.config = ConfigLoader.load_from_file(config)
        elif isinstance(config, ModbusConfig):
            self.config = config
        else:
            raise ConfigurationError(f"Tipo de configuración no válido: {type(config)}")

        self.client: Optional[Union[AsyncModbusTcpClient, AsyncModbusSerialClient]] = None
        self.converter = ModbusDataConverter()
        self._monitoring_task: Optional[asyncio.Task] = None
        self._monitoring_active = False
        self._last_values: Dict[str, Any] = {}
        self._last_read_time: Dict[str, datetime] = {}
        self._connection_lock = asyncio.Lock()
        self._rate_limiter = asyncio.Semaphore(1)
        self._min_request_interval = self.config.limits.min_request_interval

        logger.info(f"ModbusController inicializado con {len(self.config.registers)} registros")

    async def __aenter__(self):
        """Context manager entry - conecta al servidor Modbus"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cierra la conexión"""
        await self.disconnect()

    async def connect(self) -> None:
        """Establece conexión con el dispositivo Modbus"""
        async with self._connection_lock:
            if self.client and self.client.connected:
                logger.warning("Ya existe una conexión activa")
                return

            try:
                conn = self.config.connection

                if conn.type == "tcp":
                    self.client = AsyncModbusTcpClient(
                        host=conn.host,
                        port=conn.port,
                        timeout=conn.timeout
                    )
                elif conn.type == "rtu":
                    if not conn.port_name:
                        raise ConfigurationError("port_name requerido para conexión RTU")

                    self.client = AsyncModbusSerialClient(
                        port=conn.port_name,
                        baudrate=conn.baudrate,
                        bytesize=conn.bytesize,
                        parity=conn.parity,
                        stopbits=conn.stopbits,
                        timeout=conn.timeout
                    )
                else:
                    raise ConfigurationError(f"Tipo de conexión no soportado: {conn.type}")

                await self.client.connect()

                if not self.client.connected:
                    raise ModbusConnectionError("No se pudo establecer la conexión")

                logger.info(f"Conectado exitosamente via {conn.type.upper()}")

            except Exception as e:
                logger.error(f"Error al conectar: {e}")
                raise ModbusConnectionError(f"Error de conexión: {e}")

    async def disconnect(self) -> None:
        """Cierra la conexión Modbus y detiene monitorización"""
        await self.stop_monitoring()

        async with self._connection_lock:
            if self.client:
                self.client.close()
                self.client = None
                logger.info("Conexión Modbus cerrada")

    async def _ensure_connected(self) -> None:
        """Verifica y reestablece la conexión si es necesario"""
        if not self.client or not self.client.connected:
            logger.warning("Conexión perdida, intentando reconectar...")
            await self.connect()

    def _get_registers_by_name(self, name: str) -> RegisterConfig:
        """Obtiene configuración de registro por nombre"""
        for reg in self.config.registers:
            if reg.name == name:
                return reg
        raise ConfigurationError(f"Registro '{name}' no encontrado en la configuración")

    def _group_consecutive_registers(self, registers: List[RegisterConfig]) -> List[List[RegisterConfig]]:
        """
        Agrupa registros consecutivos para optimizar lecturas,
        respetando el límite máximo de registros por lectura.
        """
        if not registers:
            return []

        # Ordenar por dirección
        sorted_regs = sorted(registers, key=lambda r: r.address)
        groups = []
        current_group = [sorted_regs[0]]

        max_regs = self.config.limits.max_registers_per_read

        for reg in sorted_regs[1:]:
            last_reg = current_group[-1]
            last_end = last_reg.address + self.converter.get_register_count(last_reg.type, last_reg.length)

            # Calcular tamaño total si añadimos este registro
            total_size = reg.address - current_group[0].address + self.converter.get_register_count(reg.type, reg.length)

            # ¿Es consecutivo y no excede el límite?
            if reg.address == last_end and total_size <= max_regs:
                current_group.append(reg)
            else:
                groups.append(current_group)
                current_group = [reg]

        groups.append(current_group)
        return groups

    async def _read_register_group(self, group: List[RegisterConfig], slave: int = 1) -> Dict[str, Any]:
        """Lee un grupo de registros consecutivos"""
        if not group:
            return {}

        first_reg = group[0]
        last_reg = group[-1]

        # Calcular dirección de inicio y cantidad
        start_address = first_reg.address
        end_address = last_reg.address + self.converter.get_register_count(last_reg.type, last_reg.length)
        count = end_address - start_address

        # Rate limiting
        async with self._rate_limiter:
            await self._ensure_connected()

            try:
                # Leer según el function code (3 = holding, 4 = input)
                if first_reg.function_code == 3:
                    response = await self.client.read_holding_registers(
                        address=start_address,
                        count=count,
                        device_id=slave
                    )
                elif first_reg.function_code == 4:
                    response = await self.client.read_input_registers(
                        address=start_address,
                        count=count,
                        device_id=slave
                    )
                else:
                    raise ReadError(f"Function code {first_reg.function_code} no soportado")

                if response.isError():
                    raise ReadError(f"Error Modbus: {response}")

                # Parsear valores individuales
                results = {}
                for reg in group:
                    offset = reg.address - start_address
                    reg_count = self.converter.get_register_count(reg.type, reg.length)
                    raw_registers = response.registers[offset:offset + reg_count]

                    value = self.converter.registers_to_value(
                        registers=raw_registers,
                        data_type=reg.type,
                        length=reg.length
                    )

                    # Apply scale factor and offset if configured
                    if reg.scale_factor is not None:
                        value = value * reg.scale_factor
                    if reg.offset is not None:
                        value = value + reg.offset

                    results[reg.name] = {
                        'value': value,
                        'unit': reg.unit,
                        'timestamp': datetime.now(),
                        'address': reg.address,
                        'type': reg.type
                    }

                    self._last_values[reg.name] = value
                    self._last_read_time[reg.name] = datetime.now()

                # Respetar intervalo mínimo entre peticiones
                await asyncio.sleep(self._min_request_interval)

                return results

            except ModbusException as e:
                raise ReadError(f"Error al leer registros {start_address}-{end_address}: {e}")

    async def read_all(self, slave: int = 1) -> Dict[str, Any]:
        """
        Lee todos los registros configurados.

        Args:
            slave: ID del dispositivo esclavo (por defecto 1)

        Returns:
            Diccionario con todos los valores leídos
        """
        groups = self._group_consecutive_registers(self.config.registers)
        all_results = {}

        logger.info(f"Leyendo {len(self.config.registers)} registros en {len(groups)} grupos")

        for group in groups:
            results = await self._read_register_group(group, slave)
            all_results.update(results)

        return all_results

    async def read_register(self, name: str, slave: int = 1) -> Any:
        """
        Lee un registro específico por nombre.

        Args:
            name: Nombre del registro configurado
            slave: ID del dispositivo esclavo

        Returns:
            Valor del registro
        """
        reg = self._get_registers_by_name(name)
        result = await self._read_register_group([reg], slave)
        return result[name]['value']

    async def write_register(self, name: str, value: Any, slave: int = 1) -> None:
        """
        Escribe un valor en un registro.

        Args:
            name: Nombre del registro
            value: Valor a escribir
            slave: ID del dispositivo esclavo
        """
        reg = self._get_registers_by_name(name)

        # Apply inverse scaling if configured (user value -> raw hardware value)
        write_value = value
        if reg.offset is not None:
            write_value = write_value - reg.offset
        if reg.scale_factor is not None:
            if reg.scale_factor == 0:
                raise WriteError(f"Scale factor cannot be zero for register '{name}'")
            write_value = write_value / reg.scale_factor

        # Convertir valor a registros
        registers = self.converter.value_to_registers(
            value=write_value,
            data_type=reg.type,
            length=reg.length
        )

        async with self._rate_limiter:
            await self._ensure_connected()

            try:
                if len(registers) == 1:
                    # Escribir registro único
                    response = await self.client.write_register(
                        address=reg.address,
                        value=registers[0],
                        device_id=slave
                    )
                else:
                    # Escribir múltiples registros
                    response = await self.client.write_registers(
                        address=reg.address,
                        values=registers,
                        device_id=slave
                    )

                if response.isError():
                    raise WriteError(f"Error al escribir: {response}")

                # Log with scale info if applicable
                if reg.scale_factor is not None or reg.offset is not None:
                    logger.info(f"Escrito '{name}' = {value} (raw: {write_value}) en dirección {reg.address}")
                else:
                    logger.info(f"Escrito '{name}' = {value} en dirección {reg.address}")

                # Actualizar caché
                self._last_values[name] = value

                await asyncio.sleep(self._min_request_interval)

            except ModbusException as e:
                raise WriteError(f"Error al escribir registro '{name}': {e}")

    async def start_monitoring(
        self,
        callback: Optional[Callable[[str, Any, Any], None]] = None,
        slave: int = 1
    ) -> None:
        """
        Inicia monitorización automática de registros según sus intervalos configurados.

        Args:
            callback: Función llamada cuando cambia un valor: callback(name, old_value, new_value)
            slave: ID del dispositivo esclavo
        """
        if self._monitoring_active:
            logger.warning("La monitorización ya está activa")
            return

        self._monitoring_active = True
        self._monitoring_task = asyncio.create_task(
            self._monitoring_loop(callback, slave)
        )
        logger.info("Monitorización iniciada")

    async def stop_monitoring(self) -> None:
        """Detiene la monitorización automática"""
        if not self._monitoring_active:
            return

        self._monitoring_active = False

        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
            self._monitoring_task = None

        logger.info("Monitorización detenida")

    async def _monitoring_loop(self, callback: Optional[Callable], slave: int) -> None:
        """Bucle de monitorización que lee registros según sus intervalos"""
        while self._monitoring_active:
            try:
                now = datetime.now()

                # Determinar qué registros necesitan ser leídos
                to_read = []
                for reg in self.config.registers:
                    if reg.poll_interval is None:
                        continue

                    last_read = self._last_read_time.get(reg.name)
                    if last_read is None or (now - last_read).total_seconds() >= reg.poll_interval:
                        to_read.append(reg)

                if to_read:
                    # Agrupar y leer
                    groups = self._group_consecutive_registers(to_read)
                    for group in groups:
                        results = await self._read_register_group(group, slave)

                        # Llamar callback si hay cambios
                        if callback:
                            for name, data in results.items():
                                old_value = self._last_values.get(name)
                                new_value = data['value']

                                if old_value != new_value:
                                    try:
                                        callback(name, old_value, new_value)
                                    except Exception as e:
                                        logger.error(f"Error en callback: {e}")

                # Esperar un poco antes de la siguiente iteración
                await asyncio.sleep(0.1)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error en monitorización: {e}")
                await asyncio.sleep(1)

    def get_last_value(self, name: str) -> Optional[Any]:
        """Obtiene el último valor leído de un registro (desde caché)"""
        return self._last_values.get(name)

    def get_all_last_values(self) -> Dict[str, Any]:
        """Obtiene todos los últimos valores leídos"""
        return self._last_values.copy()
