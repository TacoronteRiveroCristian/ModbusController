"""
Setup para ModbusController
"""
from setuptools import setup, find_packages
from pathlib import Path

# Leer el contenido del README
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# Leer requirements
requirements = (this_directory / "requirements.txt").read_text(encoding='utf-8').splitlines()

setup(
    name="modbus_controller",
    version="1.0.0",
    author="Carlos Tacoronte",
    description="Sistema de gestión de lecturas y escrituras Modbus con control de frecuencia",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=requirements,
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
