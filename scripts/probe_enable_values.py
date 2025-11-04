"""
Probar diferentes valores para el registro Enable
"""
import asyncio
from pymodbus.client import AsyncModbusTcpClient

async def test_write_value(client, address, value, description):
    """Intenta escribir un valor y reporta el resultado"""
    print(f"\nProbando {description} (valor={value})...")

    # Intentar escribir
    response = await client.write_register(address=address, value=value, device_id=1)

    if response.isError():
        print(f"  ✗ ERROR: {response}")
        return False
    else:
        print(f"  ✓ Escritura exitosa")

        # Verificar si se mantuvo
        await asyncio.sleep(0.1)
        read_response = await client.read_holding_registers(address=address, count=1, device_id=1)

        if not read_response.isError():
            read_value = read_response.registers[0]
            print(f"  Valor leído: {read_value}")

            if read_value == value:
                print(f"  ✓✓ VALOR SE MANTUVO!")
                return True
            else:
                print(f"  ~ Valor cambió a {read_value}")
                return False
        else:
            print(f"  Error al leer: {read_response}")
            return False

async def main():
    client = AsyncModbusTcpClient(host="10.142.230.136", port=502, timeout=3)
    await client.connect()

    if not client.connected:
        print("No se pudo conectar")
        return

    print("Conectado exitosamente")
    print("\n" + "="*60)
    print("PROBANDO VALORES PARA Enable_limitacion (addr 40246)")
    print("="*60)

    addr_enable = 40246
    addr_limit = 40242

    # Primero configurar un límite válido
    print("\n>>> Configurando límite de potencia a 50% primero...")
    await client.write_register(address=addr_limit, value=50, device_id=1)
    await asyncio.sleep(0.2)

    # Probar diferentes valores
    valores_a_probar = [
        (1, "Enable simple (1)"),
        (0, "Disable (0)"),
        (2, "Valor 2"),
        (3, "Valor 3"),
        (10, "Valor 10"),
        (100, "Valor 100"),
        (256, "Valor 256"),
        (1000, "Valor 1000"),
        (65535, "Valor máximo uint16 (65535)"),
        (0xFFFF, "0xFFFF"),
    ]

    for valor, descripcion in valores_a_probar:
        resultado = await test_write_value(client, addr_enable, valor, descripcion)
        if resultado:
            print(f"\n{'='*60}")
            print(f"ENCONTRADO: {descripcion} funciona!")
            print(f"{'='*60}")
            break
        await asyncio.sleep(0.3)

    # Probar también escribir múltiples registros
    print("\n\n>>> Probando write_registers (multiple) en lugar de write_register...")
    response = await client.write_registers(address=addr_enable, values=[1], device_id=1)
    print(f"Respuesta: {response}")

    await asyncio.sleep(0.1)
    read_response = await client.read_holding_registers(address=addr_enable, count=1, device_id=1)
    if not read_response.isError():
        print(f"Valor leído: {read_response.registers[0]}")

if __name__ == "__main__":
    asyncio.run(main())
