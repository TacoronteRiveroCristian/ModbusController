import asyncio
from modbus_controller import ModbusController

async def main():
    async with ModbusController("configs/medidor_potencia.json") as controller:
        valores = await controller.read_all()

        print("\n=== LECTURA DE MEDIDOR DE POTENCIA ===\n")
        for nombre, datos in valores.items():
            print(f"{nombre}: {datos['value']:.2f} {datos['unit']}")

asyncio.run(main())
