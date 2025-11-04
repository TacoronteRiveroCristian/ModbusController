"""
Tests básicos para ModbusController
"""
import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from modbus_controller import ModbusController
from modbus_controller.exceptions import (
    ConfigurationError,
    ReadError,
    WriteError
)
from modbus_controller.config_loader import ConfigLoader
from modbus_controller.data_converter import ModbusDataConverter


class TestDataConverter:
    """Tests para el conversor de datos"""

    def test_uint16_conversion(self):
        converter = ModbusDataConverter()

        # Valor a registros
        registers = converter.value_to_registers(1234, "uint16")
        assert registers == [1234]

        # Registros a valor
        value = converter.registers_to_value([1234], "uint16")
        assert value == 1234

    def test_float32_conversion(self):
        converter = ModbusDataConverter()

        # Valor a registros
        registers = converter.value_to_registers(123.45, "float32")
        assert len(registers) == 2

        # Registros a valor (round-trip)
        value = converter.registers_to_value(registers, "float32")
        assert abs(value - 123.45) < 0.01

    def test_string_conversion(self):
        converter = ModbusDataConverter()

        # Valor a registros
        registers = converter.value_to_registers("TEST", "string", length=4)
        assert len(registers) == 4

        # Registros a valor
        value = converter.registers_to_value(registers, "string", length=4)
        assert "TEST" in value


class TestConfigLoader:
    """Tests para el cargador de configuración"""

    def test_load_valid_config(self):
        config_path = Path(__file__).parent.parent / "configs" / "example_config.json"

        if config_path.exists():
            config = ConfigLoader.load_from_file(config_path)

            assert config.connection.type == "tcp"
            assert config.connection.host == "192.168.1.100"
            assert len(config.registers) > 0
            assert config.limits.max_registers_per_read == 125

    def test_invalid_config_path(self):
        with pytest.raises(ConfigurationError):
            ConfigLoader.load_from_file("nonexistent.json")


class TestModbusController:
    """Tests para el controlador principal"""

    @pytest.mark.asyncio
    async def test_initialization(self):
        config_path = Path(__file__).parent.parent / "configs" / "example_config.json"

        if not config_path.exists():
            pytest.skip("Config file not found")

        controller = ModbusController(config_path)

        assert controller.config is not None
        assert len(controller.config.registers) > 0
        assert controller.converter is not None

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test que el context manager funciona correctamente"""
        config_path = Path(__file__).parent.parent / "configs" / "example_config.json"

        if not config_path.exists():
            pytest.skip("Config file not found")

        controller = ModbusController(config_path)

        # Mock del cliente para evitar conexión real
        with patch('modbus_controller.controller.AsyncModbusTcpClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.connected = True
            mock_client_class.return_value = mock_client

            async with controller:
                assert controller.client is not None

            # Verificar que se cerró la conexión
            mock_client.close.assert_called()

    @pytest.mark.asyncio
    async def test_get_register_by_name(self):
        config_path = Path(__file__).parent.parent / "configs" / "example_config.json"

        if not config_path.exists():
            pytest.skip("Config file not found")

        controller = ModbusController(config_path)

        # Obtener un registro válido
        reg = controller._get_registers_by_name("temperatura_ambiente")
        assert reg.name == "temperatura_ambiente"
        assert reg.address == 100

        # Intentar obtener registro inexistente
        with pytest.raises(ConfigurationError):
            controller._get_registers_by_name("registro_inexistente")

    def test_group_consecutive_registers(self):
        config_path = Path(__file__).parent.parent / "configs" / "example_config.json"

        if not config_path.exists():
            pytest.skip("Config file not found")

        controller = ModbusController(config_path)

        # Los registros consecutivos deberían agruparse
        registers = controller.config.registers[:3]
        groups = controller._group_consecutive_registers(registers)

        assert len(groups) > 0
        assert all(isinstance(group, list) for group in groups)


# Tests de integración (requieren servidor Modbus real o simulado)
@pytest.mark.integration
class TestModbusControllerIntegration:
    """Tests de integración con servidor Modbus real"""

    @pytest.mark.asyncio
    async def test_read_all_integration(self):
        """Test de lectura completa (requiere servidor Modbus)"""
        pytest.skip("Requiere servidor Modbus real")

        config_path = Path(__file__).parent.parent / "configs" / "example_config.json"

        async with ModbusController(config_path) as controller:
            values = await controller.read_all()
            assert len(values) > 0

    @pytest.mark.asyncio
    async def test_write_read_integration(self):
        """Test de escritura y lectura (requiere servidor Modbus)"""
        pytest.skip("Requiere servidor Modbus real")

        config_path = Path(__file__).parent.parent / "configs" / "example_config.json"

        async with ModbusController(config_path) as controller:
            # Escribir valor
            await controller.write_register("setpoint_temperatura", 25.0)

            # Leer y verificar
            value = await controller.read_register("setpoint_temperatura")
            assert abs(value - 25.0) < 0.1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
