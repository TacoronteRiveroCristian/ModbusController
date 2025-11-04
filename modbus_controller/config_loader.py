"""
Cargador de configuración desde JSON con validación usando Pydantic
"""
import json
from typing import List, Optional, Dict, Any
from pathlib import Path
from pydantic import BaseModel, Field, field_validator, model_validator
from .exceptions import ConfigurationError


class ConnectionConfig(BaseModel):
    """Configuración de conexión Modbus"""
    type: str = Field(..., description="Tipo de conexión: 'tcp' o 'rtu'")
    host: Optional[str] = Field(None, description="Host para conexión TCP")
    port: Optional[int] = Field(502, description="Puerto para conexión TCP")
    timeout: float = Field(3.0, description="Timeout en segundos")
    retry_on_empty: bool = Field(True, description="Reintentar en respuestas vacías")
    retry_delay: float = Field(1.0, description="Retardo entre reintentos en segundos")
    device_id: int = Field(1, description="ID del dispositivo Modbus (slave ID)")

    # Parámetros específicos para RTU
    port_name: Optional[str] = Field(None, description="Puerto serial para conexión RTU (ej: /dev/ttyUSB0)")
    baudrate: Optional[int] = Field(9600, description="Baudrate para conexión serial")
    parity: Optional[str] = Field("N", description="Paridad: 'N', 'E', 'O'")
    stopbits: Optional[int] = Field(1, description="Bits de parada: 1 o 2")
    bytesize: Optional[int] = Field(8, description="Tamaño de byte: 7 u 8")

    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        if v not in ['tcp', 'rtu']:
            raise ValueError("El tipo debe ser 'tcp' o 'rtu'")
        return v

    @model_validator(mode='after')
    def validate_connection_params(self):
        if self.type == 'tcp' and not self.host:
            raise ValueError("Se requiere 'host' para conexión TCP")
        if self.type == 'rtu' and not self.port_name:
            raise ValueError("Se requiere 'port_name' (puerto serial) para conexión RTU")
        return self


class RegisterConfig(BaseModel):
    """Configuración de un registro Modbus"""
    name: str = Field(..., description="Nombre único del registro")
    address: int = Field(..., description="Dirección del registro")
    type: str = Field(..., description="Tipo de dato: uint16, int16, uint32, int32, float32, string")
    unit: Optional[str] = Field(None, description="Unidad de medida")
    function_code: int = Field(3, description="Código de función Modbus (3=holding, 4=input)")
    poll_interval: Optional[float] = Field(None, description="Intervalo de polling en segundos")
    description: Optional[str] = Field(None, description="Descripción del registro")
    length: Optional[int] = Field(None, description="Longitud en registros para strings")
    byte_order: str = Field("big", description="Orden de bytes: 'big' o 'little' para tipos de 32 bits")
    writable: bool = Field(False, description="Indica si el registro es escribible")
    scale_factor: Optional[float] = Field(None, description="Factor de escala para aplicar al valor leído")
    offset: Optional[float] = Field(None, description="Offset para aplicar al valor leído")

    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        valid_types = ['uint16', 'int16', 'uint32', 'int32', 'float32', 'string']
        if v not in valid_types:
            raise ValueError(f"El tipo debe ser uno de: {', '.join(valid_types)}")
        return v

    @field_validator('function_code')
    @classmethod
    def validate_function_code(cls, v):
        valid_codes = [1, 2, 3, 4, 5, 6, 15, 16]
        if v not in valid_codes:
            raise ValueError(f"Código de función inválido. Válidos: {valid_codes}")
        return v

    @field_validator('byte_order')
    @classmethod
    def validate_byte_order(cls, v):
        if v not in ['big', 'little']:
            raise ValueError("El orden de bytes debe ser 'big' o 'little'")
        return v

    @model_validator(mode='after')
    def validate_string_length(self):
        if self.type == 'string' and not self.length:
            raise ValueError("Se requiere 'length' para tipo 'string'")
        return self

    def get_register_count(self) -> int:
        """Retorna el número de registros necesarios para este tipo de dato"""
        if self.type in ['uint16', 'int16']:
            return 1
        elif self.type in ['uint32', 'int32', 'float32']:
            return 2
        elif self.type == 'string':
            return self.length
        return 1


class LimitsConfig(BaseModel):
    """Configuración de límites de comunicación"""
    max_registers_per_read: int = Field(125, description="Máximo de registros por lectura")
    min_request_interval: float = Field(0.1, description="Intervalo mínimo entre requests en segundos")
    max_retries: int = Field(3, description="Número máximo de reintentos")
    reconnect_delay: float = Field(5.0, description="Retardo antes de intentar reconexión en segundos")


class ModbusConfig(BaseModel):
    """Configuración completa del controlador Modbus"""
    connection: ConnectionConfig
    registers: List[RegisterConfig]
    limits: LimitsConfig = Field(default_factory=LimitsConfig)

    @model_validator(mode='after')
    def validate_unique_names(self):
        names = [reg.name for reg in self.registers]
        if len(names) != len(set(names)):
            raise ValueError("Los nombres de los registros deben ser únicos")
        return self


class ConfigLoader:
    """
    Clase para cargar y validar configuraciones desde archivos JSON
    """

    @staticmethod
    def load_from_file(file_path: str) -> ModbusConfig:
        """
        Carga y valida una configuración desde un archivo JSON

        Args:
            file_path: Ruta al archivo JSON de configuración

        Returns:
            Objeto ModbusConfig validado

        Raises:
            ConfigurationError: Si hay errores en la configuración
        """
        try:
            path = Path(file_path)
            if not path.exists():
                raise ConfigurationError(f"Archivo de configuración no encontrado: {file_path}")

            with open(path, 'r', encoding='utf-8') as f:
                config_dict = json.load(f)

            return ModbusConfig(**config_dict)

        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Error al parsear JSON: {e}")
        except ValueError as e:
            raise ConfigurationError(f"Error de validación: {e}")
        except Exception as e:
            raise ConfigurationError(f"Error al cargar configuración: {e}")

    @staticmethod
    def load_from_dict(config_dict: Dict[str, Any]) -> ModbusConfig:
        """
        Carga y valida una configuración desde un diccionario

        Args:
            config_dict: Diccionario con la configuración

        Returns:
            Objeto ModbusConfig validado

        Raises:
            ConfigurationError: Si hay errores en la configuración
        """
        try:
            return ModbusConfig(**config_dict)
        except ValueError as e:
            raise ConfigurationError(f"Error de validación: {e}")
        except Exception as e:
            raise ConfigurationError(f"Error al cargar configuración: {e}")

    @staticmethod
    def validate_file(file_path: str) -> bool:
        """
        Valida un archivo de configuración sin cargarlo

        Args:
            file_path: Ruta al archivo JSON

        Returns:
            True si la configuración es válida

        Raises:
            ConfigurationError: Si la configuración es inválida
        """
        try:
            ConfigLoader.load_from_file(file_path)
            return True
        except ConfigurationError:
            raise
