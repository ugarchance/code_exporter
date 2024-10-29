from setuptools import setup, find_packages

setup(
    name="code_exporter",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        'PyQt6>=6.4.0',
        'chardet>=4.0.0',
        'python-dateutil>=2.8.2',
    ],
)