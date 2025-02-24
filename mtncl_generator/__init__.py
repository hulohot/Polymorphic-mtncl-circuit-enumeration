"""MTNCL Circuit Generator Package.

This package provides tools for generating MTNCL (Multi-Threshold Null Convention Logic)
circuits from boolean equations. It includes parsers for VHDL and boolean equations,
a circuit generator, and Verilog netlist writer.
"""

from .parsers.vhdl_parser import VHDLParser
from .parsers.boolean_parser import BooleanParser
from .core.circuit_generator import CircuitGenerator
from .writers.verilog_writer import VerilogWriter
from .main import generate_mtncl_circuits

__version__ = '0.1.0'
__author__ = 'Your Name'
__email__ = 'your.email@example.com'

__all__ = [
    'VHDLParser',
    'BooleanParser',
    'CircuitGenerator',
    'VerilogWriter',
    'generate_mtncl_circuits',
] 