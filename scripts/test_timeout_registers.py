"""
Probar si modificar registros 40241 o 40244 ayuda a mantener el Enable activo
"""
import asyncio
from pymodbus.client import AsyncModbusTcpClient

async def test_with_register_change(client, test_reg, test_value, description):
    """Prueba habilitar WMaxLim después de cambiar otro registro"""
    addr_limit = 40242
    addr_enable = 40246

    print(f"\n{'='*70}")
    print(f"TEST: {description}")
    print(f"{'='*70}\n")

    # Leer valor original del registro de prueba
    response = await client.read_holding_registers(address=test_reg, count=1, device_id=1)
    original_value = response.registers[0] if not response.isError() else None
    print(f"1. Registro {test_reg} valor original: {original_value}")

    # Escribir nuevo valor en el registro de prueba
    print(f"2. Escribiendo {test_value} en registro {test_reg}...")
    response = await client.write_register(address=test_reg, value=test_value, device_id=1)

    if response.isError():
        print(f"   ✗ Error al escribir: {response}")
        return
    print(f"   ✓ Escrito correctamente")

    await asyncio.sleep(0.2)

    # Configurar límite
    print(f"3. Configurando límite a 50%...")
    await client.write_register(address=addr_limit, value=50, device_id=1)
    await asyncio.sleep(0.2)

    # Habilitar
    print(f"4. Habilitando control (Enable=1)...")
    await client.write_register(address=addr_enable, value=1, device_id=1)

    # Monitorear Enable durante varios segundos
    print(f"\n5. Monitoreando Enable durante 5 segundos:")
    for i in range(10):
        await asyncio.sleep(0.5)
        response = await client.read_holding_registers(address=addr_enable, count=1, device_id=1)

        if not response.isError():
            enable_value = response.registers[0]
            elapsed = (i + 1) * 0.5
            status = "✓" if enable_value == 1 else "✗"
            print(f"   {status} t={elapsed:3.1f}s: Enable={enable_value}")

            if enable_value == 0 and i > 0:
                print(f"      (se desactivó después de ~{elapsed}s)")
                break

    # Restaurar valor original
    if original_value is not None:
        print(f"\n6. Restaurando registro {test_reg} a {original_value}...")
        await client.write_register(address=test_reg, value=original_value, device_id=1)

async def main():
    client = AsyncModbusTcpClient(host="10.142.230.136", port=502, timeout=3)
    await client.connect()

    if not client.connected:
        print("No se pudo conectar")
        return

    print("Conectado exitosamente")

    # Test 1: Sin cambiar nada (baseline)
    await test_with_register_change(client, 40241, 1, "BASELINE - Sin cambios")

    # Test 2: Cambiar 40241 a 0
    await test_with_register_change(client, 40241, 0, "Cambiar reg 40241 a 0")

    # Test 3: Cambiar 40244 a 0
    await test_with_register_change(client, 40244, 0, "Cambiar reg 40244 a 0")

    # Test 4: Cambiar ambos a 0
    print(f"\n{'='*70}")
    print("TEST FINAL: Cambiar AMBOS registros 40241=0 y 40244=0")
    print(f"{'='*70}\n")

    await client.write_register(address=40241, value=0, device_id=1)
    await client.write_register(address=40244, value=0, device_id=1)
    await asyncio.sleep(0.2)

    await client.write_register(address=40242, value=50, device_id=1)
    await asyncio.sleep(0.2)

    await client.write_register(address=40246, value=1, device_id=1)

    print("Monitoreando Enable:")
    for i in range(10):
        await asyncio.sleep(0.5)
        response = await client.read_holding_registers(address=40246, count=1, device_id=1)

        if not response.isError():
            enable_value = response.registers[0]
            elapsed = (i + 1) * 0.5
            status = "✓" if enable_value == 1 else "✗"
            print(f"   {status} t={elapsed:3.1f}s: Enable={enable_value}")

    # Restaurar
    print("\nRestaurando valores...")
    await client.write_register(address=40241, value=1, device_id=1)
    await client.write_register(address=40244, value=1, device_id=1)

if __name__ == "__main__":
    asyncio.run(main())
