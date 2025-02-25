#!/usr/bin/env python3

import argparse
import json
import logging
import os
from typing import Dict, List, Optional

from .parsers.vhdl_parser import parse_vhdl_gates
from .parsers.boolean_parser import parse_boolean_equation
from .core.circuit_generator import CircuitGenerator
from .core.polymorphic_generator import PolymorphicCircuitGenerator
from .writers.verilog_writer import write_verilog_netlist

def load_config(config_path: str) -> Dict:
    """Load configuration from JSON file."""
    with open(config_path, 'r') as f:
        return json.load(f)

def setup_logging(level: str = 'INFO') -> None:
    """Configure logging."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Generate MTNCL circuits from boolean equations')
    parser.add_argument('vhdl_files', nargs='*', help='VHDL files with gate definitions')
    parser.add_argument('-e', '--equation', help='Boolean equation for regular MTNCL circuit')
    parser.add_argument('--hvdd-equation', help='Boolean equation for HVDD operation')
    parser.add_argument('--lvdd-equation', help='Boolean equation for LVDD operation')
    parser.add_argument('-n', '--num-circuits', type=int, help='Number of circuits to generate')
    parser.add_argument('-c', '--config', default='config.json', help='Configuration file')
    parser.add_argument('-p', '--polymorphic-config', default='polymorphic_config.json', 
                        help='Polymorphic configuration file')
    parser.add_argument('-o', '--output-dir', help='Output directory')
    parser.add_argument('-l', '--log-level', default='INFO', help='Logging level')
    parser.add_argument('--polymorphic', action='store_true', help='Generate polymorphic circuits')
    return parser.parse_args()

def generate_regular_documentation(output_dir: str, circuits: List, config: Dict) -> None:
    """Generate documentation for regular MTNCL circuit generation results."""
    doc_path = os.path.join(output_dir, 'README.md')
    with open(doc_path, 'w') as f:
        f.write('# MTNCL Circuit Generation Results\n\n')
        
        # Configuration summary
        f.write('## Configuration\n\n')
        f.write(f"Boolean Equation: {config['input']['equation']}\n\n")
        
        # Circuit implementations
        f.write('## Generated Circuits\n\n')
        for i, circuit in enumerate(circuits):
            f.write(f'### Circuit {i}\n\n')
            f.write(f"Gate Count: {circuit.gate_count}\n")
            f.write(f"Circuit Depth: {circuit.depth}\n")
            f.write('\nGates Used:\n')
            gate_types = {}
            for gate in circuit.gates:
                gate_type = gate.gate_type
                gate_types[gate_type] = gate_types.get(gate_type, 0) + 1
            
            for gate_type, count in gate_types.items():
                f.write(f"- {gate_type}: {count}\n")
            f.write('\n')

def generate_polymorphic_documentation(output_dir: str, circuits: List, config: Dict) -> None:
    """Generate documentation for polymorphic circuit generation results."""
    doc_path = os.path.join(output_dir, 'README.md')
    with open(doc_path, 'w') as f:
        f.write('# Polymorphic MTNCL Circuit Generation Results\n\n')
        
        # Configuration summary
        f.write('## Configuration\n\n')
        f.write(f"HVDD Function: {config['input']['hvdd_equation']}\n")
        f.write(f"LVDD Function: {config['input']['lvdd_equation']}\n\n")
        
        # Circuit implementations
        f.write('## Generated Circuits\n\n')
        for i, circuit in enumerate(circuits):
            f.write(f'### Circuit {i}\n\n')
            
            # Handle both object and dictionary formats
            if isinstance(circuit, dict):
                # Dictionary format
                f.write(f"Gate Count: {len(circuit['gates'])}\n")
                f.write(f"Inputs: {', '.join(circuit['inputs'])}\n")
                f.write(f"Outputs: {', '.join(circuit['outputs'])}\n")
                f.write(f"HVDD Function: {circuit.get('hvdd_function', '')}\n")
                f.write(f"LVDD Function: {circuit.get('lvdd_function', '')}\n")
                
                f.write('\nPolymorphic Gates Used:\n')
                gate_types = {}
                for gate in circuit['gates']:
                    gate_type = gate['type']
                    gate_types[gate_type] = gate_types.get(gate_type, 0) + 1
                
                for gate_type, count in gate_types.items():
                    f.write(f"- {gate_type}: {count}\n")
            else:
                # Object format
                if hasattr(circuit, 'hvdd_circuit') and hasattr(circuit, 'lvdd_circuit'):
                    f.write(f"HVDD Gate Count: {circuit.hvdd_circuit.gate_count}\n")
                    f.write(f"LVDD Gate Count: {circuit.lvdd_circuit.gate_count}\n")
                    f.write(f"HVDD Circuit Depth: {circuit.hvdd_circuit.depth}\n")
                    f.write(f"LVDD Circuit Depth: {circuit.lvdd_circuit.depth}\n")
                else:
                    f.write(f"Gate Count: {circuit.gate_count}\n")
                    f.write(f"Circuit Depth: {circuit.depth}\n")
                
                f.write('\nPolymorphic Gates Used:\n')
                gate_types = {}
                for gate in circuit.gates:
                    gate_type = gate.gate_type
                    gate_types[gate_type] = gate_types.get(gate_type, 0) + 1
                
                for gate_type, count in gate_types.items():
                    f.write(f"- {gate_type}: {count}\n")
            
            f.write('\n')

def generate_mtncl_circuits(
    equation: Optional[str] = None,
    hvdd_equation: Optional[str] = None,
    lvdd_equation: Optional[str] = None,
    gate_files: Optional[List[str]] = None,
    output_dir: str = 'output',
    num_circuits: int = 1,
    is_polymorphic: bool = False,
    generate_docs: bool = True,
    generate_testbench: bool = False
) -> List[Dict]:
    """Generate MTNCL circuits from boolean equations.
    
    Args:
        equation: Boolean equation for regular MTNCL circuit
        hvdd_equation: Boolean equation for HVDD operation
        lvdd_equation: Boolean equation for LVDD operation
        gate_files: List of VHDL files with gate definitions
        output_dir: Directory to store generated files
        num_circuits: Number of circuits to generate
        is_polymorphic: Whether to generate polymorphic circuits
        generate_docs: Whether to generate documentation
        generate_testbench: Whether to generate testbenches
        
    Returns:
        List of generated circuit dictionaries
        
    Raises:
        ValueError: If required parameters are missing or invalid
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Parse gate definitions
    gates_dict = {}
    if gate_files:
        for gate_file in gate_files:
            gates_dict.update(parse_vhdl_gates(gate_file))
    
    # Generate circuits based on mode
    is_polymorphic = is_polymorphic or (hvdd_equation and lvdd_equation)
    
    if is_polymorphic:
        # Validate required equations
        if not hvdd_equation or not lvdd_equation:
            raise ValueError("Both HVDD and LVDD equations are required for polymorphic generation")
            
        # Generate polymorphic circuits
        generator = PolymorphicCircuitGenerator(
            gates_dict,
            hvdd_equation,
            lvdd_equation
        )
        circuits = generator.generate_circuits()
        
        if not circuits:
            raise ValueError("No valid polymorphic implementations found")
            
        # Generate documentation
        if generate_docs:
            config = {
                'input': {
                    'hvdd_equation': hvdd_equation,
                    'lvdd_equation': lvdd_equation
                }
            }
            generate_polymorphic_documentation(output_dir, circuits, config)
    else:
        # Validate required equation
        if not equation:
            raise ValueError("Boolean equation is required for regular circuit generation")
            
        # Generate regular MTNCL circuits
        generator = CircuitGenerator(
            gates_dict,
            equation
        )
        circuits = generator.generate_circuits()
        
        if not circuits:
            raise ValueError("No valid circuits generated")
            
        # Generate documentation
        if generate_docs:
            config = {
                'input': {
                    'equation': equation
                }
            }
            generate_regular_documentation(output_dir, circuits, config)
    
    # Generate output files
    for i, circuit in enumerate(circuits):
        output_file = os.path.join(output_dir, f'circuit_{i}.v')
        write_verilog_netlist(circuit, output_file)
        
        if generate_testbench:
            tb_file = os.path.join(output_dir, f'circuit_{i}_tb.v')
            write_verilog_netlist(circuit, tb_file, is_testbench=True)
    
    return circuits

def main() -> None:
    """Main entry point."""
    args = parse_args()
    
    # Determine which config file to use based on mode
    config_file = args.polymorphic_config if args.polymorphic else args.config
    config = load_config(config_file)
    setup_logging(args.log_level)
    
    # Override config with command line arguments
    if args.vhdl_files:
        config['input']['gates_dir'] = args.vhdl_files
    if args.equation and not args.polymorphic:
        config['input']['equation'] = args.equation
    if args.hvdd_equation:
        config['input']['hvdd_equation'] = args.hvdd_equation
    if args.lvdd_equation:
        config['input']['lvdd_equation'] = args.lvdd_equation
    if args.num_circuits:
        config['input']['num_circuits'] = args.num_circuits
    if args.output_dir:
        config['output']['directory'] = args.output_dir
    if args.polymorphic:
        config['mode'] = 'polymorphic'
        
    # Ensure output directory exists
    os.makedirs(config['output']['directory'], exist_ok=True)
    
    # Parse gate definitions
    gates_dict = {}
    gate_files = config['input']['gates_dir']
    if isinstance(gate_files, str):
        gate_files = [gate_files]
    for gate_file in gate_files:
        gates_dict.update(parse_vhdl_gates(gate_file))
    
    # Generate circuits based on mode
    is_polymorphic = config.get('mode') == 'polymorphic' or (args.hvdd_equation and args.lvdd_equation)
    
    if is_polymorphic:
        # Validate required equations
        if not config['input'].get('hvdd_equation') or not config['input'].get('lvdd_equation'):
            logging.error("Both HVDD and LVDD equations are required for polymorphic generation")
            return
            
        # Generate polymorphic circuits
        polymorphic_config = {
            'use_direct_mapping': config.get('polymorphic', {}).get('use_direct_mapping', True),
            'use_alternative_mapping': config.get('polymorphic', {}).get('use_alternative_mapping', True),
            'gate_constraints': config.get('constraints', {}),
            'min_gates': config.get('constraints', {}).get('min_gates'),
            'max_gates': config.get('constraints', {}).get('max_gates'),
            'gates': config.get('gates', {})
        }
        
        generator = PolymorphicCircuitGenerator(
            gates_dict,
            config['input']['hvdd_equation'],
            config['input']['lvdd_equation'],
            polymorphic_config
        )
        circuits = generator.generate_circuits(config['input'].get('num_circuits', 1))
        
        if not circuits:
            logging.error("No valid polymorphic implementations found")
            return
            
        # Generate documentation
        if config.get('documentation', {}).get('format') == 'markdown':
            generate_polymorphic_documentation(config['output']['directory'], circuits, config)
    else:
        # Validate required equation
        if not config['input'].get('equation'):
            logging.error("Boolean equation is required for regular circuit generation")
            return
            
        # Generate regular MTNCL circuits
        circuit_config = {
            'gate_constraints': config.get('constraints', {}),
            'min_gates': config.get('constraints', {}).get('min_gates'),
            'max_gates': config.get('constraints', {}).get('max_gates'),
            'gates': config.get('gates', {})
        }
        
        ast = parse_boolean_equation(config['input']['equation'])
        generator = CircuitGenerator(
            gates_dict,
            ast,
            circuit_config
        )
        circuits = generator.generate_circuits(config['input'].get('num_circuits', 1))
        
        if not circuits:
            logging.error("No valid circuits generated")
            return
            
        # Generate documentation
        if config.get('documentation', {}).get('format') == 'markdown':
            generate_regular_documentation(config['output']['directory'], circuits, config)
    
    # Generate output files
    for i, circuit in enumerate(circuits):
        output_file = os.path.join(config['output']['directory'], f'circuit_{i}.v')
        write_verilog_netlist(circuit, output_file)
        
        if config['output'].get('generate_testbench', False):
            tb_file = os.path.join(config['output']['directory'], f'circuit_{i}_tb.v')
            write_verilog_netlist(circuit, tb_file, is_testbench=True)
    
    logging.info(f"Generated {len(circuits)} circuits in {config['output']['directory']}")

if __name__ == "__main__":
    main() 