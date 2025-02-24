#!/usr/bin/env python3

import argparse
import json
import logging
import os
import sys
from typing import List, Dict, Any

from .parsers.vhdl_parser import VHDLParser
from .parsers.boolean_parser import BooleanParser
from .core.circuit_generator import CircuitGenerator, Circuit
from .writers.verilog_writer import VerilogWriter

def setup_logging(log_level: str = "INFO") -> None:
    """Set up logging configuration.
    
    Args:
        log_level: Desired logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def load_config(config_file: str) -> Dict[str, Any]:
    """Load configuration from JSON file.
    
    Args:
        config_file: Path to configuration file
        
    Returns:
        Dictionary containing configuration parameters
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        json.JSONDecodeError: If config file is invalid JSON
    """
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        logging.error(f"Configuration file not found: {config_file}")
        raise
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in configuration file: {str(e)}")
        raise
    
    return config

def generate_documentation(circuits: List[Circuit], config: Dict[str, Any], output_dir: str) -> None:
    """Generate documentation for the generated circuits.
    
    Args:
        circuits: List of generated circuits
        config: Configuration parameters
        output_dir: Directory to save documentation
    """
    if not config.get('documentation', {}).get('include_metrics', True):
        return
        
    doc_path = os.path.join(output_dir, "README.md")
    
    with open(doc_path, 'w') as f:
        f.write("# MTNCL Circuit Generation Results\n\n")
        
        # Circuit summary
        f.write("## Overview\n\n")
        f.write(f"Generated {len(circuits)} circuit implementations for the boolean equation:\n")
        f.write(f"```\n{config['input']['boolean_equation']}\n```\n\n")
        
        # Limitations and Supported Operations
        f.write("## Limitations and Supported Operations\n\n")
        f.write("### Supported Operations\n")
        f.write("- AND operations using TH22/TH33 gates\n")
        f.write("- OR operations using TH12/TH13 gates\n")
        f.write("- XOR operations using THXOR gates\n")
        f.write("- 2-of-3 threshold operations using TH23 gates\n\n")
        
        f.write("### Limitations\n")
        f.write("- Negation (NOT) operations are not supported\n")
        f.write("- All operations must be implemented using threshold gates\n")
        f.write("- Maximum circuit depth is limited by configuration\n")
        f.write("- Maximum fanout is limited by configuration\n\n")
        
        # Configuration summary
        f.write("## Configuration\n\n")
        f.write("```json\n")
        f.write(json.dumps(config, indent=4))
        f.write("\n```\n\n")
        
        # Circuit metrics
        f.write("## Generated Circuits\n\n")
        for i, circuit in enumerate(circuits):
            f.write(f"### Circuit {i}\n\n")
            f.write(f"- Gate count: {circuit.gate_count}\n")
            f.write(f"- Circuit depth: {circuit.depth}\n")
            f.write(f"- Input ports: {', '.join(sorted(circuit.inputs))}\n")
            f.write(f"- Output ports: {', '.join(sorted(circuit.outputs))}\n")
            f.write(f"- Internal wires: {len(circuit.wires) - len(circuit.inputs) - len(circuit.outputs)}\n")
            
            # Gate breakdown
            gate_types = {}
            for gate in circuit.gates:
                gate_types[gate.gate_type] = gate_types.get(gate.gate_type, 0) + 1
            f.write("\nGate breakdown:\n")
            for gate_type, count in sorted(gate_types.items()):
                f.write(f"- {gate_type}: {count}\n")
            f.write("\n")
            
        # File listing
        f.write("## Generated Files\n\n")
        f.write("```\n")
        f.write("output/\n")
        for i in range(len(circuits)):
            f.write(f"├── circuit_{i}.v          # Circuit implementation {i}\n")
            if config.get('output', {}).get('generate_testbench', False):
                f.write(f"├── circuit_{i}_tb.v       # Testbench for circuit {i}\n")
        f.write("└── README.md            # This documentation\n")
        f.write("```\n")

def generate_mtncl_circuits(
    vhdl_files: List[str],
    boolean_equation: str,
    num_circuits: int,
    config: Dict[str, Any]
) -> List[str]:
    """Generate MTNCL circuit implementations from a boolean equation.
    
    Args:
        vhdl_files: List of VHDL files containing gate definitions
        boolean_equation: Boolean equation to implement
        num_circuits: Number of different implementations to generate
        config: Configuration parameters
        
    Returns:
        List of Verilog netlist strings
        
    Raises:
        ValueError: If inputs are invalid
    """
    logger = logging.getLogger(__name__)
    
    # Parse VHDL files
    logger.info("Parsing VHDL files...")
    vhdl_parser = VHDLParser(vhdl_files)
    available_gates = vhdl_parser.parse_gates()
    
    # Parse boolean equation
    logger.info("Parsing boolean equation...")
    boolean_parser = BooleanParser(boolean_equation)
    ast = boolean_parser.parse()
    
    # Generate circuits
    logger.info("Generating circuits...")
    circuit_generator = CircuitGenerator(available_gates, ast, config)
    circuits = circuit_generator.generate_circuits(num_circuits)
    
    if not circuits:
        logger.warning("No valid circuits generated!")
        return []
    
    # Create output directory
    output_dir = config.get('output_dir', './output')
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate documentation
    logger.info("Generating documentation...")
    generate_documentation(circuits, config, output_dir)
    
    # Generate Verilog netlists
    logger.info("Generating Verilog netlists...")
    netlists = []
    for i, circuit in enumerate(circuits):
        writer = VerilogWriter(circuit, f"mtncl_circuit_{i}")
        netlist = writer.generate_netlist()
        netlists.append(netlist)
        
        # Save netlist
        netlist_path = os.path.join(output_dir, f"circuit_{i}.v")
        with open(netlist_path, 'w') as f:
            f.write(netlist)
        logger.info(f"Saved netlist to {netlist_path}")
        
        # Generate testbench if requested
        if config.get('generate_testbench', False):
            testbench = writer.generate_testbench()
            testbench_path = os.path.join(output_dir, f"circuit_{i}_tb.v")
            with open(testbench_path, 'w') as f:
                f.write(testbench)
            logger.info(f"Saved testbench to {testbench_path}")
    
    return netlists

def save_netlists(netlists: List[str], output_dir: str) -> None:
    """Save Verilog netlists to files.
    
    Args:
        netlists: List of Verilog netlist strings
        output_dir: Directory to save files in
    """
    logger = logging.getLogger(__name__)
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Save each netlist
    for i, netlist in enumerate(netlists):
        filename = os.path.join(output_dir, f"circuit_{i}.v")
        try:
            with open(filename, 'w') as f:
                f.write(netlist)
            logger.info(f"Saved netlist to {filename}")
        except IOError as e:
            logger.error(f"Failed to save netlist to {filename}: {str(e)}")
            raise

def main():
    """Main entry point for the MTNCL circuit generator."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Generate MTNCL circuits from boolean equations"
    )
    parser.add_argument(
        'vhdl_files',
        nargs='*',
        help="VHDL files containing gate definitions (optional if specified in config)"
    )
    parser.add_argument(
        'equation',
        nargs='?',
        help="Boolean equation to implement (optional if specified in config)"
    )
    parser.add_argument(
        '-n', '--num-circuits',
        type=int,
        help="Number of different implementations to generate (optional if specified in config)"
    )
    parser.add_argument(
        '-c', '--config',
        default='config.json',
        help="Configuration file path"
    )
    parser.add_argument(
        '-o', '--output-dir',
        help="Output directory for generated files (optional if specified in config)"
    )
    parser.add_argument(
        '-l', '--log-level',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help="Set logging level"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    try:
        # Load configuration
        config = load_config(args.config)
        
        # Ensure required sections exist
        if 'input' not in config:
            config['input'] = {}
        if 'output' not in config:
            config['output'] = {}
        if 'constraints' not in config:
            config['constraints'] = {}
        if 'optimization' not in config:
            config['optimization'] = {}
        if 'gates' not in config:
            config['gates'] = {}
        
        # Override config with command line arguments if provided
        if args.vhdl_files:
            config['input']['gates_dir'] = args.vhdl_files[0]
        if args.equation:
            config['input']['boolean_equation'] = args.equation
        if args.num_circuits:
            config['input']['num_circuits'] = args.num_circuits
        if args.output_dir:
            config['output']['directory'] = args.output_dir
            
        # Validate required parameters
        if 'gates_dir' not in config['input']:
            raise ValueError("No VHDL files specified in config or command line")
        if 'boolean_equation' not in config['input']:
            raise ValueError("No boolean equation specified in config or command line")
            
        # Convert config structure to old format for backward compatibility
        compat_config = {
            'min_gates': config['constraints'].get('min_gates', 1),
            'max_gates': config['constraints'].get('max_gates', None),
            'optimization_target': config['optimization'].get('target', 'area'),
            'output_dir': config['output'].get('directory', './output'),
            'generate_testbench': config['output'].get('generate_testbench', True),
            'gate_constraints': {
                'max_fanout': config['constraints'].get('max_fanout', 4),
                'max_depth': config['constraints'].get('max_depth', 10),
                'preferred_gates': config['gates'].get('preferred', []),
                'avoid_gates': config['gates'].get('avoid', [])
            },
            'optimization_weights': config['optimization'].get('weights', {
                'area': 1.0,
                'delay': 0.5,
                'power': 0.3
            }),
            'documentation': config.get('documentation', {
                'include_metrics': True,
                'include_diagrams': False,
                'format': 'markdown'
            })
        }
        
        # Generate circuits
        netlists = generate_mtncl_circuits(
            [config['input']['gates_dir']],
            config['input']['boolean_equation'],
            config['input'].get('num_circuits', 1),
            compat_config
        )
        
        # Save netlists
        if netlists:
            save_netlists(netlists, config['output']['directory'])
            logger.info("Circuit generation completed successfully")
        else:
            logger.error("No circuits were generated")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Circuit generation failed: {str(e)}")
        if logger.getEffectiveLevel() <= logging.DEBUG:
            logger.exception("Detailed error information:")
        sys.exit(1)

if __name__ == "__main__":
    main() 