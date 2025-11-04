# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ModbusController is a Python library for managing Modbus TCP/IP and RTU communications with features like:
- Asynchronous operations using asyncio
- Intelligent register grouping and rate limiting
- Automatic monitoring and reconnection
- Support for multiple data types (uint16, int16, uint32, int32, float32, string)
- Configuration validation using Pydantic

## Development Commands

### Testing
```bash
# Run all tests
make test

# Run tests manually (requires venv)
.venv/bin/pytest tests/test_controller.py -v

# Run integration tests (requires Modbus server)
.venv/bin/pytest tests/test_controller.py -v -m integration
```

### Modbus Operations (scripts/)
Quick commands for reading/writing Modbus registers. **Important**: Activate venv first with `source .venv/bin/activate`

```bash
cd scripts/

# Read operations
make status                    # Check current limitation status
make read                      # Read all registers (default: configs/medidor_potencia.json)
make read CONFIG=configs/other_config.json

# Power limitation control
make limit LIMIT=50            # Set power limit to 50% and enable
make set-limit LIMIT=75        # Set limit to 75% without enabling
make enable                    # Enable power limitation
make disable                   # Disable power limitation
make reset                     # Reset both limit and enable to 0

# Aliases
make on    # Same as enable
make off   # Same as disable
```

**Available scripts**:
- `read_all.py` - Read all registers
- `read_status.py` - Check power limitation status
- `set_limit_only.py` - Set limit without enabling
- `set_limit_and_enable.py` - Set limit and enable in one step
- `toggle_enable.py` - Toggle enable/disable

### Installation
```bash
# Install dependencies in editable mode
pip install -r requirements.txt
pip install -e .
```

### Virtual Environment
The project uses `.venv/` for virtual environment. The Makefile automatically creates and activates it.

## Architecture

### Core Components

**ModbusController** (`modbus_controller/controller.py`):
- Main class that manages connections, reads, and writes
- Implements context manager for automatic connection handling
- Uses asyncio locks for thread-safe operations
- Rate limiting via semaphore to prevent PLC saturation
- Maintains cache of last read values and timestamps

**ConfigLoader** (`modbus_controller/config_loader.py`):
- Loads and validates JSON configuration using Pydantic models
- Three main models: `ConnectionConfig`, `RegisterConfig`, `ModbusConfig`
- Validates connection types (tcp/rtu), register types, function codes
- Enforces required parameters based on connection type

**ModbusDataConverter** (`modbus_controller/data_converter.py`):
- Converts between Modbus registers (16-bit) and Python types
- Handles byte order (big/little endian) for 32-bit types
- Bidirectional conversion: registers to values and values to registers

**Custom Exceptions** (`modbus_controller/exceptions.py`):
- Hierarchy: `ModbusControllerError` (base) → specific errors
- Types: `ConnectionError`, `ReadError`, `WriteError`, `ConfigurationError`, `DataConversionError`, `RegisterNotFoundError`

### Key Architectural Patterns

1. **Async Context Manager Pattern**: Use `async with ModbusController(config) as controller:` for automatic connection lifecycle management

2. **Register Grouping**: Controller automatically groups consecutive registers to minimize Modbus requests

3. **Rate Limiting**: `min_request_interval` in config enforces minimum time between requests

4. **Monitoring System**: Background task polls registers at individual `poll_interval` rates defined per register

5. **Cache Layer**: Last read values stored in `_last_values` dict with timestamps in `_last_read_time`

## Configuration

Configuration is JSON-based with validation. Key sections:

- **connection**: Type (tcp/rtu), host, port, timeout, retry settings, device_id
- **registers**: List of register definitions with name, address, type, function_code, poll_interval
- **limits**: `max_registers_per_read`, `min_request_interval`

Example configs in `configs/` directory:
- `example_config.json` - TCP example
- `example_config_rtu.json` - RTU serial example
- `power_control_config.json` - Real-world power control example
- `medidor_potencia.json` - Power meter example

## Important Implementation Notes

1. **Connection Types**:
   - TCP requires `host` and `port`
   - RTU requires `port_name`, `baudrate`, `parity`, `stopbits`, `bytesize`

2. **Function Codes**:
   - FC 3: Read Holding Registers (read/write)
   - FC 4: Read Input Registers (read-only)
   - FC 6: Write Single Register
   - FC 16: Write Multiple Registers

3. **Data Type Sizes**:
   - uint16/int16: 1 register
   - uint32/int32/float32: 2 registers
   - string: N registers (specify with `length` parameter)

4. **Slave ID**: Default is 1, can be overridden in connection config or per-request

5. **Register Grouping Limit**: Many Modbus servers limit to 125 registers per request - controller handles this automatically

## Testing Approach

Tests use pytest with pytest-asyncio. Mock Modbus clients are used for unit tests. Integration tests (marked with `@pytest.mark.integration`) require an actual Modbus server.

## Dependencies

- `pymodbus>=3.7.0` - Modbus protocol implementation
- `pydantic>=2.0.0` - Configuration validation
- `asyncio-mqtt>=0.16.1` - MQTT support (optional feature)
