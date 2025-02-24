import pytest
from mtncl_generator.parsers.boolean_parser import BooleanParser
from mtncl_generator.parsers.vhdl_parser import VHDLParser, GateInfo, Port
from mtncl_generator.core.circuit_generator import CircuitGenerator, Circuit

@pytest.fixture
def basic_gates():
    """Fixture providing basic MTNCL gates."""
    gates = {
        "TH12": GateInfo(
            name="TH12",
            ports=[
                Port(name="A", direction="in", port_type="STD_LOGIC"),
                Port(name="B", direction="in", port_type="STD_LOGIC"),
                Port(name="Z", direction="out", port_type="STD_LOGIC")
            ],
            delays={"rise": 0.1, "fall": 0.1}
        ),
        "TH12m": GateInfo(  # Modified timing variant
            name="TH12m",
            ports=[
                Port(name="A", direction="in", port_type="STD_LOGIC"),
                Port(name="B", direction="in", port_type="STD_LOGIC"),
                Port(name="Z", direction="out", port_type="STD_LOGIC")
            ],
            delays={"rise": 0.15, "fall": 0.15}
        ),
        "TH13": GateInfo(
            name="TH13",
            ports=[
                Port(name="A", direction="in", port_type="STD_LOGIC"),
                Port(name="B", direction="in", port_type="STD_LOGIC"),
                Port(name="C", direction="in", port_type="STD_LOGIC"),
                Port(name="Z", direction="out", port_type="STD_LOGIC")
            ],
            delays={"rise": 0.2, "fall": 0.2}
        ),
        "TH22": GateInfo(
            name="TH22",
            ports=[
                Port(name="A", direction="in", port_type="STD_LOGIC"),
                Port(name="B", direction="in", port_type="STD_LOGIC"),
                Port(name="Z", direction="out", port_type="STD_LOGIC")
            ],
            delays={"rise": 0.15, "fall": 0.15}
        ),
        "TH22m": GateInfo(  # Modified timing variant
            name="TH22m",
            ports=[
                Port(name="A", direction="in", port_type="STD_LOGIC"),
                Port(name="B", direction="in", port_type="STD_LOGIC"),
                Port(name="Z", direction="out", port_type="STD_LOGIC")
            ],
            delays={"rise": 0.2, "fall": 0.2}
        ),
        "TH33": GateInfo(
            name="TH33",
            ports=[
                Port(name="A", direction="in", port_type="STD_LOGIC"),
                Port(name="B", direction="in", port_type="STD_LOGIC"),
                Port(name="C", direction="in", port_type="STD_LOGIC"),
                Port(name="Z", direction="out", port_type="STD_LOGIC")
            ],
            delays={"rise": 0.25, "fall": 0.25}
        ),
        "THXOR": GateInfo(
            name="THXOR",
            ports=[
                Port(name="A", direction="in", port_type="STD_LOGIC"),
                Port(name="B", direction="in", port_type="STD_LOGIC"),
                Port(name="Z", direction="out", port_type="STD_LOGIC")
            ],
            delays={"rise": 0.2, "fall": 0.2}
        )
    }
    return gates

@pytest.fixture
def basic_config():
    """Fixture providing basic configuration."""
    return {
        'min_gates': 1,
        'max_gates': None,
        'optimization_target': 'area',
        'gate_constraints': {
            'max_fanout': 4,
            'max_depth': 10
        }
    }

def test_simple_or_circuit(basic_gates, basic_config):
    """Test generation of a simple OR circuit."""
    parser = BooleanParser("A + B")
    ast = parser.parse()
    
    generator = CircuitGenerator(basic_gates, ast, basic_config)
    circuits = generator.generate_circuits(1)
    
    assert len(circuits) == 1
    circuit = circuits[0]
    
    # Check circuit structure
    assert len(circuit.inputs) == 2
    assert "A" in circuit.inputs
    assert "B" in circuit.inputs
    assert len(circuit.outputs) == 1
    assert len(circuit.gates) == 1
    assert circuit.gates[0].gate_type == "TH12"

def test_complex_circuit(basic_gates, basic_config):
    """Test generation of a more complex circuit."""
    parser = BooleanParser("(A + B) & (C + D)")
    ast = parser.parse()
    
    generator = CircuitGenerator(basic_gates, ast, basic_config)
    circuits = generator.generate_circuits(1)
    
    assert len(circuits) == 1
    circuit = circuits[0]
    
    # Check circuit structure
    assert len(circuit.inputs) == 4
    assert all(x in circuit.inputs for x in ["A", "B", "C", "D"])
    assert len(circuit.outputs) == 1
    assert len(circuit.gates) >= 3  # At least two OR gates and one AND gate

def test_multiple_implementations(basic_gates, basic_config):
    """Test generation of multiple circuit implementations."""
    parser = BooleanParser("A + B")
    ast = parser.parse()
    
    generator = CircuitGenerator(basic_gates, ast, basic_config)
    circuits = generator.generate_circuits(3)  # Try to get all possible implementations
    
    # Should get at least 2 different implementations (TH12 and TH12m)
    assert len(circuits) >= 2
    
    # Verify we get different gate types
    gate_types = {circuit.gates[0].gate_type for circuit in circuits}
    assert len(gate_types) >= 2  # Should have at least 2 different gate types
    assert "TH12" in gate_types  # Should include standard implementation

def test_gate_constraints(basic_gates, basic_config):
    """Test enforcement of gate constraints."""
    # Set max gates to 2
    basic_config['max_gates'] = 2
    
    parser = BooleanParser("(A + B) & (C + D)")  # Would normally need 3 gates
    ast = parser.parse()
    
    generator = CircuitGenerator(basic_gates, ast, basic_config)
    circuits = generator.generate_circuits(1)
    
    assert len(circuits) == 0  # Should not generate any circuits

def test_circuit_depth(basic_gates, basic_config):
    """Test calculation of circuit depth."""
    parser = BooleanParser("(A + B) & (C + D)")
    ast = parser.parse()
    
    generator = CircuitGenerator(basic_gates, ast, basic_config)
    circuits = generator.generate_circuits(1)
    
    assert len(circuits) == 1
    circuit = circuits[0]
    
    assert circuit.depth >= 2  # Should have at least 2 levels

def test_wire_connections(basic_gates, basic_config):
    """Test proper wire connections in generated circuit."""
    parser = BooleanParser("A + B")
    ast = parser.parse()
    
    generator = CircuitGenerator(basic_gates, ast, basic_config)
    circuits = generator.generate_circuits(1)
    
    assert len(circuits) == 1
    circuit = circuits[0]
    
    # Check wire connections
    for gate in circuit.gates:
        # Check input connections
        for wire_name in gate.inputs.values():
            assert wire_name in circuit.wires
            if wire_name not in circuit.inputs:
                assert circuit.wires[wire_name].source is not None
        
        # Check output connections
        for wire_name in gate.outputs.values():
            assert wire_name in circuit.wires
            assert circuit.wires[wire_name].source == gate.instance_name

def test_invalid_equation(basic_gates, basic_config):
    """Test handling of invalid boolean equations."""
    with pytest.raises(ValueError):
        parser = BooleanParser("A + + B")  # Invalid equation
        ast = parser.parse()
        
        generator = CircuitGenerator(basic_gates, ast, basic_config)
        generator.generate_circuits(1)

def test_missing_gates(basic_gates, basic_config):
    """Test handling of missing required gates."""
    # Remove all gates needed for OR operation (both direct and alternative implementations)
    basic_gates.clear()  # Remove all gates
    
    parser = BooleanParser("A + B")  # Requires OR gate
    ast = parser.parse()
    
    generator = CircuitGenerator(basic_gates, ast, basic_config)
    circuits = generator.generate_circuits(1)
    
    assert len(circuits) == 0  # Should not generate any circuits

def test_unsupported_not(basic_gates, basic_config):
    """Test that NOT operations are not supported."""
    parser = BooleanParser("!A")  # Simple NOT operation
    ast = parser.parse()
    
    generator = CircuitGenerator(basic_gates, ast, basic_config)
    circuits = generator.generate_circuits(1)
    
    assert len(circuits) == 0  # Should not generate any circuits 