import pytest
from mtncl_generator.core.polymorphic_generator import PolymorphicCircuitGenerator
from mtncl_generator.parsers.vhdl_parser import GateInfo, Port
from mtncl_generator.core.circuit_generator import Circuit, GateInstance, Wire

@pytest.fixture
def polymorphic_gates():
    """Fixture providing both basic and polymorphic MTNCL gates."""
    gates = {
        # Basic gates
        "TH12": GateInfo(
            name="TH12",
            ports=[
                Port(name="A", direction="in", port_type="STD_LOGIC"),
                Port(name="B", direction="in", port_type="STD_LOGIC"),
                Port(name="Z", direction="out", port_type="STD_LOGIC")
            ],
            delays=[]
        ),
        "TH22": GateInfo(
            name="TH22",
            ports=[
                Port(name="A", direction="in", port_type="STD_LOGIC"),
                Port(name="B", direction="in", port_type="STD_LOGIC"),
                Port(name="Z", direction="out", port_type="STD_LOGIC")
            ],
            delays=[]
        ),
        "TH13": GateInfo(
            name="TH13",
            ports=[
                Port(name="A", direction="in", port_type="STD_LOGIC"),
                Port(name="B", direction="in", port_type="STD_LOGIC"),
                Port(name="C", direction="in", port_type="STD_LOGIC"),
                Port(name="Z", direction="out", port_type="STD_LOGIC")
            ],
            delays=[]
        ),
        "TH33": GateInfo(
            name="TH33",
            ports=[
                Port(name="A", direction="in", port_type="STD_LOGIC"),
                Port(name="B", direction="in", port_type="STD_LOGIC"),
                Port(name="C", direction="in", port_type="STD_LOGIC"),
                Port(name="Z", direction="out", port_type="STD_LOGIC")
            ],
            delays=[]
        ),
        # Polymorphic gates
        "TH12m_TH22m": GateInfo(
            name="TH12m_TH22m",
            ports=[
                Port(name="vdd_sel", direction="in", port_type="STD_LOGIC"),
                Port(name="A", direction="in", port_type="STD_LOGIC"),
                Port(name="B", direction="in", port_type="STD_LOGIC"),
                Port(name="s", direction="in", port_type="STD_LOGIC"),
                Port(name="Z", direction="out", port_type="STD_LOGIC")
            ],
            delays=[]
        ),
        "TH13m_TH33m": GateInfo(
            name="TH13m_TH33m",
            ports=[
                Port(name="vdd_sel", direction="in", port_type="STD_LOGIC"),
                Port(name="A", direction="in", port_type="STD_LOGIC"),
                Port(name="B", direction="in", port_type="STD_LOGIC"),
                Port(name="C", direction="in", port_type="STD_LOGIC"),
                Port(name="s", direction="in", port_type="STD_LOGIC"),
                Port(name="Z", direction="out", port_type="STD_LOGIC")
            ],
            delays=[]
        )
    }
    return gates

def test_simple_polymorphic_circuit(polymorphic_gates):
    """Test generation of a simple polymorphic circuit (OR/AND)."""
    generator = PolymorphicCircuitGenerator(
        polymorphic_gates,
        hvdd_equation="A + B",  # OR operation
        lvdd_equation="A & B"   # AND operation
    )
    
    circuits = generator.generate_circuits()
    assert len(circuits) > 0
    
    # Check first implementation
    circuit = circuits[0]
    assert len(circuit['gates']) == 1
    assert circuit['gates'][0]['type'] == 'th12m_th22m'
    assert circuit['hvdd_function'] == "A + B"
    assert circuit['lvdd_function'] == "A & B"

def test_complex_polymorphic_circuit(polymorphic_gates):
    """Test generation of a more complex polymorphic circuit."""
    generator = PolymorphicCircuitGenerator(
        polymorphic_gates,
        hvdd_equation="(A + B) + C",  # 3-input OR
        lvdd_equation="(A & B) & C"   # 3-input AND
    )
    
    circuits = generator.generate_circuits()
    assert len(circuits) > 0
    
    # Check implementation uses TH13m_TH33m
    circuit = circuits[0]
    assert len(circuit['gates']) == 1
    assert circuit['gates'][0]['type'] == 'th13m_th33m'

def test_incompatible_functions(polymorphic_gates):
    """Test handling of functions that can't be implemented with same structure."""
    generator = PolymorphicCircuitGenerator(
        polymorphic_gates,
        hvdd_equation="A + B",      # Single gate
        lvdd_equation="A & B & C"   # Different structure
    )
    
    circuits = generator.generate_circuits()
    assert len(circuits) == 0  # Should not find any valid implementations

def test_missing_polymorphic_gates(polymorphic_gates):
    """Test handling of missing required polymorphic gates."""
    # Remove the TH12m_TH22m gate
    gates_subset = {k: v for k, v in polymorphic_gates.items() if k != 'TH12m_TH22m'}
    
    generator = PolymorphicCircuitGenerator(
        gates_subset,
        hvdd_equation="A + B",
        lvdd_equation="A & B"
    )
    
    circuits = generator.generate_circuits()
    assert len(circuits) == 0  # Should not find any valid implementations

def test_multiple_implementations(polymorphic_gates):
    """Test generation of multiple polymorphic implementations."""
    # Add alternative gates that could implement OR/AND
    gates_extended = polymorphic_gates.copy()
    gates_extended['TH13m_TH23m'] = GateInfo(
        name="TH13m_TH23m",
        ports=[
            Port(name="vdd_sel", direction="in", port_type="STD_LOGIC"),
            Port(name="A", direction="in", port_type="STD_LOGIC"),
            Port(name="B", direction="in", port_type="STD_LOGIC"),
            Port(name="C", direction="in", port_type="STD_LOGIC"),
            Port(name="s", direction="in", port_type="STD_LOGIC"),
            Port(name="Z", direction="out", port_type="STD_LOGIC")
        ],
        delays=[]
    )
    
    generator = PolymorphicCircuitGenerator(
        gates_extended,
        hvdd_equation="A + B",
        lvdd_equation="A & B"
    )
    
    circuits = generator.generate_circuits()
    assert len(circuits) >= 2  # Should find multiple implementations
    
    # Check that implementations are different
    gate_types = {circuit['gates'][0]['type'] for circuit in circuits}
    assert len(gate_types) >= 2

def test_circuit_compatibility(polymorphic_gates):
    """Test the circuit compatibility checking."""
    generator = PolymorphicCircuitGenerator(
        polymorphic_gates,
        hvdd_equation="A + B",
        lvdd_equation="A & B"
    )
    
    # Test compatible circuits
    hvdd_circuit = Circuit(
        inputs={"A", "B"},
        outputs={"Z"},
        gates=[
            GateInstance(
                gate_type="TH12",
                instance_name="th12_0",
                inputs={"A": "A", "B": "B"},
                outputs={"Z": "Z"}
            )
        ],
        wires={
            "A": Wire(name="A", destinations={"th12_0"}),
            "B": Wire(name="B", destinations={"th12_0"}),
            "Z": Wire(name="Z", source="th12_0")
        },
        depth=1,
        gate_count=1
    )
    
    lvdd_circuit = Circuit(
        inputs={"A", "B"},
        outputs={"Z"},
        gates=[
            GateInstance(
                gate_type="TH22",
                instance_name="th22_0",
                inputs={"A": "A", "B": "B"},
                outputs={"Z": "Z"}
            )
        ],
        wires={
            "A": Wire(name="A", destinations={"th22_0"}),
            "B": Wire(name="B", destinations={"th22_0"}),
            "Z": Wire(name="Z", source="th22_0")
        },
        depth=1,
        gate_count=1
    )
    
    assert generator._are_circuits_compatible(hvdd_circuit, lvdd_circuit, use_direct_mapping=True)
    
    # Test incompatible circuits (different structure)
    lvdd_circuit_diff = Circuit(
        inputs={"A", "B", "C"},
        outputs={"Z"},
        gates=[
            GateInstance(
                gate_type="TH22",
                instance_name="th22_0",
                inputs={"A": "A", "B": "B"},
                outputs={"Z": "w1"}
            ),
            GateInstance(
                gate_type="TH22",
                instance_name="th22_1",
                inputs={"A": "w1", "B": "C"},
                outputs={"Z": "Z"}
            )
        ],
        wires={
            "A": Wire(name="A", destinations={"th22_0"}),
            "B": Wire(name="B", destinations={"th22_0"}),
            "C": Wire(name="C", destinations={"th22_1"}),
            "w1": Wire(name="w1", source="th22_0", destinations={"th22_1"}),
            "Z": Wire(name="Z", source="th22_1")
        },
        depth=2,
        gate_count=2
    )
    
    assert not generator._are_circuits_compatible(hvdd_circuit, lvdd_circuit_diff)

def test_polymorphic_gate_mapping(polymorphic_gates):
    """Test mapping of basic gates to polymorphic equivalents."""
    generator = PolymorphicCircuitGenerator(
        polymorphic_gates,
        hvdd_equation="A + B",
        lvdd_equation="A & B"
    )
    
    # Test direct mapping
    poly_gate = generator._find_polymorphic_gate('TH12', 'TH22')
    assert poly_gate == 'th12m_th22m'
    
    # Test reverse mapping
    poly_gate = generator._find_polymorphic_gate('TH22', 'TH12')
    assert poly_gate == 'th12m_th22m'
    
    # Test with timing variants
    poly_gate = generator._find_polymorphic_gate('TH12m', 'TH22m')
    assert poly_gate == 'th12m_th22m'
    
    # Test non-existent mapping
    poly_gate = generator._find_polymorphic_gate('TH12', 'TH12')
    assert poly_gate is None

def test_equivalent_implementations(polymorphic_gates):
    """Test detection of equivalent circuit implementations."""
    generator = PolymorphicCircuitGenerator(
        polymorphic_gates,
        hvdd_equation="A + B",
        lvdd_equation="A & B"
    )
    
    # Create two identical circuit implementations
    circuit1 = {
        'gates': [{'type': 'th12m_th22m', 'inputs': {'A': 'A', 'B': 'B'}, 'outputs': {'Z': 'Z'}}],
        'inputs': ['A', 'B'],
        'outputs': ['Z'],
        'hvdd_function': 'A + B',
        'lvdd_function': 'A & B'
    }
    
    circuit2 = {
        'gates': [{'type': 'th12m_th22m', 'inputs': {'A': 'A', 'B': 'B'}, 'outputs': {'Z': 'Z'}}],
        'inputs': ['A', 'B'],
        'outputs': ['Z'],
        'hvdd_function': 'A + B',
        'lvdd_function': 'A & B'
    }
    
    assert generator._are_implementations_equivalent(circuit1, circuit2)
    
    # Create a different implementation
    circuit3 = {
        'gates': [{'type': 'th13m_th33m', 'inputs': {'A': 'A', 'B': 'B', 'C': 'B'}, 'outputs': {'Z': 'Z'}}],
        'inputs': ['A', 'B'],
        'outputs': ['Z'],
        'hvdd_function': 'A + B',
        'lvdd_function': 'A & B'
    }
    
    assert not generator._are_implementations_equivalent(circuit1, circuit3)

def test_num_circuits_parameter(polymorphic_gates):
    """Test generating multiple circuits with num_circuits parameter."""
    generator = PolymorphicCircuitGenerator(
        polymorphic_gates,
        hvdd_equation="A + B",
        lvdd_equation="A & B"
    )
    
    # Test requesting 1 circuit
    circuits1 = generator.generate_circuits(1)
    assert len(circuits1) == 1
    
    # Test requesting 2 circuits
    circuits2 = generator.generate_circuits(2)
    assert len(circuits2) <= 2  # May be less if not enough unique implementations
    
    # Test requesting 0 circuits
    circuits0 = generator.generate_circuits(0)
    assert len(circuits0) == 0

def test_complex_gate_mapping(polymorphic_gates):
    """Test mapping of complex gate combinations."""
    # Add more complex gates to the test set
    gates_extended = polymorphic_gates.copy()
    gates_extended.update({
        "TH34": GateInfo(
            name="TH34",
            ports=[
                Port(name="A", direction="in", port_type="STD_LOGIC"),
                Port(name="B", direction="in", port_type="STD_LOGIC"),
                Port(name="C", direction="in", port_type="STD_LOGIC"),
                Port(name="D", direction="in", port_type="STD_LOGIC"),
                Port(name="Z", direction="out", port_type="STD_LOGIC")
            ],
            delays=[]
        ),
        "TH44": GateInfo(
            name="TH44",
            ports=[
                Port(name="A", direction="in", port_type="STD_LOGIC"),
                Port(name="B", direction="in", port_type="STD_LOGIC"),
                Port(name="C", direction="in", port_type="STD_LOGIC"),
                Port(name="D", direction="in", port_type="STD_LOGIC"),
                Port(name="Z", direction="out", port_type="STD_LOGIC")
            ],
            delays=[]
        ),
        "TH34m_TH44m": GateInfo(
            name="TH34m_TH44m",
            ports=[
                Port(name="vdd_sel", direction="in", port_type="STD_LOGIC"),
                Port(name="A", direction="in", port_type="STD_LOGIC"),
                Port(name="B", direction="in", port_type="STD_LOGIC"),
                Port(name="C", direction="in", port_type="STD_LOGIC"),
                Port(name="D", direction="in", port_type="STD_LOGIC"),
                Port(name="s", direction="in", port_type="STD_LOGIC"),
                Port(name="Z", direction="out", port_type="STD_LOGIC")
            ],
            delays=[]
        )
    })
    
    generator = PolymorphicCircuitGenerator(
        gates_extended,
        hvdd_equation="A + B + C + D",
        lvdd_equation="A & B & C & D"
    )
    
    # Test mapping of 4-input gates
    poly_gate = generator._find_polymorphic_gate('TH34', 'TH44')
    assert poly_gate == 'th34m_th44m'
    
    # Test reverse mapping
    poly_gate = generator._find_polymorphic_gate('TH44', 'TH34')
    assert poly_gate == 'th34m_th44m'

def test_invalid_equations(polymorphic_gates):
    """Test handling of invalid boolean equations."""
    # Test with invalid HVDD equation
    with pytest.raises(ValueError):
        PolymorphicCircuitGenerator(
            polymorphic_gates,
            hvdd_equation="A ++ B",  # Invalid syntax
            lvdd_equation="A & B"
        )
    
    # Test with invalid LVDD equation
    with pytest.raises(ValueError):
        PolymorphicCircuitGenerator(
            polymorphic_gates,
            hvdd_equation="A + B",
            lvdd_equation="A && B"  # Invalid syntax
        )
    
    # Test with empty equations
    with pytest.raises(ValueError):
        PolymorphicCircuitGenerator(
            polymorphic_gates,
            hvdd_equation="",
            lvdd_equation="A & B"
        )

def test_wire_consistency(polymorphic_gates):
    """Test wire naming and connections in polymorphic circuits."""
    generator = PolymorphicCircuitGenerator(
        polymorphic_gates,
        hvdd_equation="(A + B) + (C + D)",
        lvdd_equation="(A & B) & (C & D)"
    )
    
    circuits = generator.generate_circuits()
    assert len(circuits) > 0
    
    circuit = circuits[0]
    
    # Check that all referenced wires are in inputs or outputs
    all_wires = set()
    for gate in circuit['gates']:
        all_wires.update(gate['inputs'].values())
        all_wires.update(gate['outputs'].values())
    
    # All wires should be either inputs, outputs, or internal wires
    assert all(wire in circuit['inputs'] or wire in circuit['outputs'] or wire.startswith('w')
              for wire in all_wires)

def test_optimization_constraints(polymorphic_gates):
    """Test circuit generation with optimization constraints."""
    # Create generator with strict depth constraint
    generator = PolymorphicCircuitGenerator(
        polymorphic_gates,
        hvdd_equation="(A + B) + (C + D)",
        lvdd_equation="(A & B) & (C & D)"
    )
    generator.config['gate_constraints']['max_depth'] = 1  # Force single level
    
    circuits = generator.generate_circuits()
    assert len(circuits) == 0  # Should not find valid implementation with depth 1
    
    # Test with relaxed constraints
    generator.config['gate_constraints']['max_depth'] = 2
    circuits = generator.generate_circuits()
    assert len(circuits) > 0  # Should find valid implementations 