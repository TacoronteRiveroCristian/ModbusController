"""
ModbusController - Sistema de gestión de lecturas y escrituras Modbus
"""
from .controller import ModbusController
from .exceptions import (
    ModbusControllerError,
    ConnectionError,
    ReadError,
    WriteError,
    ConfigurationError,
    DataConversionError
)

__version__ = "1.0.0"
__all__ = [
    "ModbusController",
    "ModbusControllerError",
    "ConnectionError",
    "ReadError",
    "WriteError",
    "ConfigurationError",
    "DataConversionError"
]
