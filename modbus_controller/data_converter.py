"""
Conversor de datos Modbus para diferentes tipos de registros
"""
import struct
from typing import List, Union, Any
from .exceptions import DataConversionError


class ModbusDataConverter:
    """
    Clase para convertir datos entre registros Modbus (16-bit) y tipos de datos Python
    """

    @staticmethod
    def registers_to_uint16(registers: List[int]) -> int:
        """
        Convierte 1 registro a uint16

        Args:
            registers: Lista con 1 registro

        Returns:
            Valor uint16
        """
        if len(registers) != 1:
            raise DataConversionError(f"Se esperaba 1 registro para uint16, se recibieron {len(registers)}")
        return registers[0]

    @staticmethod
    def registers_to_int16(registers: List[int]) -> int:
        """
        Convierte 1 registro a int16 con signo

        Args:
            registers: Lista con 1 registro

        Returns:
            Valor int16
        """
        if len(registers) != 1:
            raise DataConversionError(f"Se esperaba 1 registro para int16, se recibieron {len(registers)}")

        value = registers[0]
        # Convertir a signed int16
        if value >= 0x8000:
            value = value - 0x10000
        return value

    @staticmethod
    def registers_to_uint32(registers: List[int], byte_order: str = "big") -> int:
        """
        Convierte 2 registros a uint32

        Args:
            registers: Lista con 2 registros
            byte_order: 'big' (high word first) o 'little' (low word first)

        Returns:
            Valor uint32
        """
        if len(registers) != 2:
            raise DataConversionError(f"Se esperaban 2 registros para uint32, se recibieron {len(registers)}")

        if byte_order == "big":
            return (registers[0] << 16) | registers[1]
        else:
            return (registers[1] << 16) | registers[0]

    @staticmethod
    def registers_to_int32(registers: List[int], byte_order: str = "big") -> int:
        """
        Convierte 2 registros a int32 con signo

        Args:
            registers: Lista con 2 registros
            byte_order: 'big' (high word first) o 'little' (low word first)

        Returns:
            Valor int32
        """
        if len(registers) != 2:
            raise DataConversionError(f"Se esperaban 2 registros para int32, se recibieron {len(registers)}")

        value = ModbusDataConverter.registers_to_uint32(registers, byte_order)
        # Convertir a signed int32
        if value >= 0x80000000:
            value = value - 0x100000000
        return value

    @staticmethod
    def registers_to_float32(registers: List[int], byte_order: str = "big") -> float:
        """
        Convierte 2 registros a float32 (IEEE 754)

        Args:
            registers: Lista con 2 registros
            byte_order: 'big' (high word first) o 'little' (low word first)

        Returns:
            Valor float32
        """
        if len(registers) != 2:
            raise DataConversionError(f"Se esperaban 2 registros para float32, se recibieron {len(registers)}")

        try:
            if byte_order == "big":
                # Big endian: high word first
                bytes_data = struct.pack('>HH', registers[0], registers[1])
            else:
                # Little endian: low word first
                bytes_data = struct.pack('>HH', registers[1], registers[0])

            return struct.unpack('>f', bytes_data)[0]
        except struct.error as e:
            raise DataConversionError(f"Error al convertir a float32: {e}")

    @staticmethod
    def registers_to_string(registers: List[int]) -> str:
        """
        Convierte N registros a string (2 caracteres ASCII por registro)

        Args:
            registers: Lista de registros

        Returns:
            String decodificado
        """
        if not registers:
            raise DataConversionError("Se requiere al menos 1 registro para string")

        try:
            # Cada registro contiene 2 bytes (2 caracteres ASCII)
            bytes_data = b''
            for reg in registers:
                # High byte primero, luego low byte
                high_byte = (reg >> 8) & 0xFF
                low_byte = reg & 0xFF
                bytes_data += bytes([high_byte, low_byte])

            # Decodificar y eliminar caracteres nulos y espacios finales
            return bytes_data.decode('ascii', errors='ignore').rstrip('\x00 ')
        except Exception as e:
            raise DataConversionError(f"Error al convertir a string: {e}")

    @staticmethod
    def value_to_registers(value: Any, data_type: str, byte_order: str = "big", length: int = None) -> List[int]:
        """
        Convierte un valor Python a registros Modbus según el tipo de dato

        Args:
            value: Valor a convertir
            data_type: Tipo de dato ('uint16', 'int16', 'uint32', 'int32', 'float32', 'string')
            byte_order: 'big' o 'little' para tipos de 32 bits
            length: Para strings, número de registros deseado (opcional)

        Returns:
            Lista de registros Modbus
        """
        try:
            if data_type == "uint16":
                if not isinstance(value, int) or value < 0 or value > 0xFFFF:
                    raise DataConversionError(f"Valor {value} fuera de rango para uint16 (0-65535)")
                return [value]

            elif data_type == "int16":
                if not isinstance(value, int) or value < -32768 or value > 32767:
                    raise DataConversionError(f"Valor {value} fuera de rango para int16 (-32768 a 32767)")
                # Convertir a unsigned para Modbus
                if value < 0:
                    value = value + 0x10000
                return [value]

            elif data_type == "uint32":
                if not isinstance(value, int) or value < 0 or value > 0xFFFFFFFF:
                    raise DataConversionError(f"Valor {value} fuera de rango para uint32 (0-4294967295)")
                if byte_order == "big":
                    return [(value >> 16) & 0xFFFF, value & 0xFFFF]
                else:
                    return [value & 0xFFFF, (value >> 16) & 0xFFFF]

            elif data_type == "int32":
                if not isinstance(value, int) or value < -2147483648 or value > 2147483647:
                    raise DataConversionError(f"Valor {value} fuera de rango para int32")
                # Convertir a unsigned
                if value < 0:
                    value = value + 0x100000000
                if byte_order == "big":
                    return [(value >> 16) & 0xFFFF, value & 0xFFFF]
                else:
                    return [value & 0xFFFF, (value >> 16) & 0xFFFF]

            elif data_type == "float32":
                if not isinstance(value, (int, float)):
                    raise DataConversionError(f"Valor {value} no es numérico para float32")

                bytes_data = struct.pack('>f', float(value))
                if byte_order == "big":
                    return [
                        struct.unpack('>H', bytes_data[0:2])[0],
                        struct.unpack('>H', bytes_data[2:4])[0]
                    ]
                else:
                    return [
                        struct.unpack('>H', bytes_data[2:4])[0],
                        struct.unpack('>H', bytes_data[0:2])[0]
                    ]

            elif data_type == "string":
                if not isinstance(value, str):
                    raise DataConversionError(f"Valor {value} no es string")

                # Convertir string a bytes
                bytes_data = value.encode('ascii', errors='ignore')

                # Si se especifica length, ajustar el tamaño
                if length is not None:
                    target_bytes = length * 2
                    if len(bytes_data) < target_bytes:
                        bytes_data = bytes_data.ljust(target_bytes, b' ')
                    elif len(bytes_data) > target_bytes:
                        bytes_data = bytes_data[:target_bytes]

                # Rellenar con espacios si es necesario para completar el último registro
                if len(bytes_data) % 2 != 0:
                    bytes_data += b' '

                # Convertir a registros
                registers = []
                for i in range(0, len(bytes_data), 2):
                    high_byte = bytes_data[i]
                    low_byte = bytes_data[i + 1] if i + 1 < len(bytes_data) else 0x20  # espacio
                    registers.append((high_byte << 8) | low_byte)

                return registers

            else:
                raise DataConversionError(f"Tipo de dato no soportado: {data_type}")

        except DataConversionError:
            raise
        except Exception as e:
            raise DataConversionError(f"Error al convertir valor a registros: {e}")

    @staticmethod
    def convert_from_registers(registers: List[int], data_type: str, byte_order: str = "big") -> Any:
        """
        Convierte registros Modbus a valor Python según el tipo de dato

        Args:
            registers: Lista de registros Modbus
            data_type: Tipo de dato ('uint16', 'int16', 'uint32', 'int32', 'float32', 'string')
            byte_order: 'big' o 'little' para tipos de 32 bits

        Returns:
            Valor convertido
        """
        if data_type == "uint16":
            return ModbusDataConverter.registers_to_uint16(registers)
        elif data_type == "int16":
            return ModbusDataConverter.registers_to_int16(registers)
        elif data_type == "uint32":
            return ModbusDataConverter.registers_to_uint32(registers, byte_order)
        elif data_type == "int32":
            return ModbusDataConverter.registers_to_int32(registers, byte_order)
        elif data_type == "float32":
            return ModbusDataConverter.registers_to_float32(registers, byte_order)
        elif data_type == "string":
            return ModbusDataConverter.registers_to_string(registers)
        else:
            raise DataConversionError(f"Tipo de dato no soportado: {data_type}")

    # Alias para compatibilidad
    @staticmethod
    def registers_to_value(registers: List[int], data_type: str, length: int = None, byte_order: str = "big") -> Any:
        """
        Alias de convert_from_registers para compatibilidad con tests y controller

        Args:
            registers: Lista de registros Modbus
            data_type: Tipo de dato
            length: Número de registros (ignorado, se calcula automáticamente)
            byte_order: 'big' o 'little'

        Returns:
            Valor convertido
        """
        return ModbusDataConverter.convert_from_registers(registers, data_type, byte_order)

    @staticmethod
    def get_register_count(data_type: str, length: int = None) -> int:
        """
        Obtiene el número de registros necesarios para un tipo de dato

        Args:
            data_type: Tipo de dato
            length: Para strings, número de registros

        Returns:
            Número de registros necesarios
        """
        if data_type in ("uint16", "int16"):
            return 1
        elif data_type in ("uint32", "int32", "float32"):
            return 2
        elif data_type == "string":
            if length is None:
                raise DataConversionError("Se requiere 'length' para tipo string")
            return length
        else:
            raise DataConversionError(f"Tipo de dato no soportado: {data_type}")
