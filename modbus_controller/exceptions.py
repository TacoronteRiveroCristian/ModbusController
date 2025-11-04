"""
Excepciones personalizadas para ModbusController
"""


class ModbusControllerError(Exception):
    """Excepción base para errores del controlador Modbus"""
    pass


class ConnectionError(ModbusControllerError):
    """Error al conectar con el dispositivo Modbus"""
    pass


class ConfigurationError(ModbusControllerError):
    """Error en la configuración del controlador"""
    pass


class ReadError(ModbusControllerError):
    """Error al leer registros Modbus"""
    pass


class WriteError(ModbusControllerError):
    """Error al escribir registros Modbus"""
    pass


class DataConversionError(ModbusControllerError):
    """Error al convertir datos entre formatos"""
    pass


class RegisterNotFoundError(ModbusControllerError):
    """Registro no encontrado en la configuración"""
    pass
