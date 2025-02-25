# MTNCL Circuit Generator

This tool generates MTNCL (Multi-Threshold Null Convention Logic) circuits from boolean equations. It supports both regular MTNCL circuits and polymorphic MTNCL circuits that implement different functions depending on the supply voltage (HVDD or LVDD).

## Features

- Converts boolean equations to MTNCL circuit implementations
- Generates multiple alternative implementations using different gate combinations
- Supports various MTNCL gates (TH12, TH22, TH13, TH33, TH23, THXOR)
- Produces Verilog netlists and testbenches
- Validates circuit constraints (depth, fanout, etc.)
- Optimizes for area, delay, or power based on configuration
- Supports polymorphic MTNCL gates for dual-function circuits

## Limitations

- Does NOT support negation operations (NOT/INV gates)
- All operations must be implemented using threshold gates
- Boolean equations must use only AND (&), OR (+), and XOR (^) operations

## Installation

1. Clone this repository
2. Create a virtual environment: `python -m venv .venv`
3. Activate the virtual environment: `source .venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`

## Gate Definitions

The tool includes several VHDL files with gate definitions:

- `gates/basic_gates.vhdl`: Basic MTNCL gate definitions without timing details
- `gates/MTNCL_Polymorphic_Gates.vhd`: Detailed polymorphic gate definitions with timing information
- `gates/MTNCL_Polymorphic_Gates_Basic.vhd`: Simplified polymorphic gate definitions without detailed timing

## Configuration Files

The tool uses separate configuration files for regular and polymorphic circuit generation:

- `config.json`: Configuration for regular MTNCL circuits
- `polymorphic_config.json`: Configuration for polymorphic MTNCL circuits

### Regular MTNCL Configuration (`config.json`)

```json
{
    "input": {
        "gates_dir": ["gates/basic_gates.vhdl"],
        "equation": "(A + B) & (C + D)",
        "num_circuits": 2
    },
    "mode": "regular",
    "output": {
        "directory": "./output/regular",
        "generate_testbench": true
    },
    "constraints": {
        "min_gates": 1,
        "max_gates": null,
        "max_fanout": 4,
        "max_depth": 10
    },
    "optimization": {
        "target": "area",
        "weights": {
            "area": 1.0,
            "delay": 0.5,
            "power": 0.3
        }
    },
    "documentation": {
        "include_metrics": true,
        "include_diagrams": false,
        "format": "markdown"
    },
    "gates": {
        "preferred": [],
        "avoid": []
    }
}
```

### Polymorphic MTNCL Configuration (`polymorphic_config.json`)

```json
{
    "input": {
        "gates_dir": ["gates/basic_gates.vhdl", "gates/MTNCL_Polymorphic_Gates.vhd"],
        "hvdd_equation": "A + B",
        "lvdd_equation": "A & B",
        "num_circuits": 2
    },
    "mode": "polymorphic",
    "output": {
        "directory": "./output/polymorphic",
        "generate_testbench": true
    },
    "constraints": {
        "min_gates": 1,
        "max_gates": null,
        "max_fanout": 4,
        "max_depth": 10
    },
    "optimization": {
        "target": "area",
        "weights": {
            "area": 1.0,
            "delay": 0.5,
            "power": 0.3
        }
    },
    "documentation": {
        "include_metrics": true,
        "include_diagrams": false,
        "format": "markdown"
    },
    "gates": {
        "preferred": ["TH12m_TH22m", "TH13m_TH33m"],
        "avoid": []
    },
    "polymorphic": {
        "use_direct_mapping": true,
        "use_alternative_mapping": true,
        "required_gates": ["TH12m_TH22m"],
        "alternative_gates": ["TH13m_TH33m"]
    }
}
```

## Usage

### Generate Regular MTNCL Circuits

```bash
python -m mtncl_generator.main -c config.json
```

### Generate Polymorphic MTNCL Circuits

```bash
python -m mtncl_generator.main --polymorphic -p polymorphic_config.json
```

### Command Line Options

- `-c, --config`: Path to regular configuration file (default: `config.json`)
- `-p, --polymorphic-config`: Path to polymorphic configuration file (default: `polymorphic_config.json`)
- `--polymorphic`: Use polymorphic mode
- `-e, --equation`: Boolean equation for regular MTNCL circuit
- `--hvdd-equation`: Boolean equation for HVDD operation
- `--lvdd-equation`: Boolean equation for LVDD operation
- `-n, --num-circuits`: Number of circuits to generate
- `-o, --output-dir`: Output directory
- `-l, --log-level`: Logging level

## Examples

### Generate a Regular MTNCL Circuit

```bash
python -m mtncl_generator.main -e "A & B | C"
```

### Generate a Polymorphic MTNCL Circuit

```bash
python -m mtncl_generator.main --polymorphic --hvdd-equation "A + B" --lvdd-equation "A & B"
```

### Use Custom Configuration Files

```bash
python -m mtncl_generator.main -c my_config.json
python -m mtncl_generator.main --polymorphic -p my_polymorphic_config.json
```

## Output

The generated circuits are saved in the output directory specified in the configuration file. For each circuit, the following files are generated:

- `circuit_X.v`: Verilog netlist for the circuit
- `circuit_X_tb.v`: Testbench for the circuit (if enabled)
- `README.md`: Documentation of the generated circuits

## Testing

Run the tests to verify the functionality:

```bash
python -m pytest tests/
```

## Supported Gates

The following MTNCL gates are supported:

| Gate  | Function | Description |
|-------|----------|-------------|
| TH12  | OR       | 2-input OR gate |
| TH22  | AND      | 2-input AND gate |
| TH13  | OR3      | 3-input OR gate |
| TH33  | AND3     | 3-input AND gate |
| TH23  | 2of3     | 2-of-3 threshold gate |
| THXOR | XOR      | 2-input XOR gate |

## Development

### Running Tests

```bash
python3 -m pytest tests/ -v
```

### Project Structure

```
.
├── mtncl_generator/          # Main package directory
│   ├── __init__.py          # Package initialization
│   ├── main.py              # Main entry point
│   ├── parsers/             # Input parsing modules
│   │   ├── boolean_parser.py  # Boolean equation parser
│   │   └── vhdl_parser.py     # VHDL gate definition parser
│   ├── core/                # Core functionality
│   │   └── circuit_generator.py  # Circuit generation logic
│   └── writers/             # Output generation modules
│       └── verilog_writer.py    # Verilog netlist writer
├── gates/                   # VHDL gate definitions
│   └── basic_gates.vhdl     # Basic MTNCL gate definitions
├── tests/                   # Test suite
│   ├── test_parsers.py      # Parser tests
│   ├── test_circuit_generator.py  # Generator tests
│   └── test_verilog_writer.py    # Writer tests
├── output/                  # Generated circuit output
├── config.json             # Default configuration
├── requirements.txt        # Python dependencies
├── setup.py               # Package installation setup
└── README.md              # Project documentation
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- MTNCL gate definitions based on standard threshold logic implementations
- Circuit optimization strategies derived from established EDA practices