import pytest
from mtncl_generator.writers.verilog_writer import VerilogWriter
from mtncl_generator.core.circuit_generator import Circuit, GateInstance, Wire

@pytest.fixture
def simple_circuit():
    """Fixture providing a simple circuit with one OR gate."""
    circuit = Circuit(
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
    return circuit

@pytest.fixture
def complex_circuit():
    """Fixture providing a more complex circuit."""
    circuit = Circuit(
        inputs={"A", "B", "C", "D"},
        outputs={"Z"},
        gates=[
            GateInstance(
                gate_type="TH12",
                instance_name="th12_0",
                inputs={"A": "A", "B": "B"},
                outputs={"Z": "w0"}
            ),
            GateInstance(
                gate_type="TH12",
                instance_name="th12_1",
                inputs={"A": "C", "B": "D"},
                outputs={"Z": "w1"}
            ),
            GateInstance(
                gate_type="TH22",
                instance_name="th22_0",
                inputs={"A": "w0", "B": "w1"},
                outputs={"Z": "Z"}
            )
        ],
        wires={
            "A": Wire(name="A", destinations={"th12_0"}),
            "B": Wire(name="B", destinations={"th12_0"}),
            "C": Wire(name="C", destinations={"th12_1"}),
            "D": Wire(name="D", destinations={"th12_1"}),
            "w0": Wire(name="w0", source="th12_0", destinations={"th22_0"}),
            "w1": Wire(name="w1", source="th12_1", destinations={"th22_0"}),
            "Z": Wire(name="Z", source="th22_0")
        },
        depth=2,
        gate_count=3
    )
    return circuit

def test_simple_netlist(simple_circuit):
    """Test generation of a simple Verilog netlist."""
    writer = VerilogWriter(simple_circuit)
    netlist = writer.generate_netlist()
    
    # Check module declaration
    assert "module mtncl_circuit" in netlist
    
    # Check port declarations
    assert "input wire A" in netlist
    assert "input wire B" in netlist
    assert "output wire Z" in netlist
    
    # Check gate instantiation
    assert "TH12 th12_0" in netlist
    assert ".A(A)" in netlist
    assert ".B(B)" in netlist
    assert ".Z(Z)" in netlist
    
    # Check module end
    assert "endmodule" in netlist

def test_complex_netlist(complex_circuit):
    """Test generation of a more complex Verilog netlist."""
    writer = VerilogWriter(complex_circuit)
    netlist = writer.generate_netlist()
    
    # Check module declaration
    assert "module mtncl_circuit" in netlist
    
    # Check port declarations
    for port in ["A", "B", "C", "D"]:
        assert f"input wire {port}" in netlist
    assert "output wire Z" in netlist
    
    # Check wire declarations
    assert "wire w0" in netlist
    assert "wire w1" in netlist
    
    # Check gate instantiations
    assert "TH12 th12_0" in netlist
    assert "TH12 th12_1" in netlist
    assert "TH22 th22_0" in netlist

def test_testbench_generation(simple_circuit):
    """Test generation of a Verilog testbench."""
    writer = VerilogWriter(simple_circuit)
    testbench = writer.generate_testbench()
    
    # Check testbench structure
    assert "`timescale" in testbench
    assert "module mtncl_circuit_tb" in testbench
    
    # Check signal declarations
    assert "reg A" in testbench
    assert "reg B" in testbench
    assert "wire Z" in testbench
    
    # Check DUT instantiation
    assert "mtncl_circuit uut" in testbench
    
    # Check test stimulus
    assert "initial begin" in testbench
    assert "$monitor" in testbench
    assert "endmodule" in testbench

def test_custom_module_name(simple_circuit):
    """Test using a custom module name."""
    writer = VerilogWriter(simple_circuit, module_name="custom_circuit")
    netlist = writer.generate_netlist()
    
    assert "module custom_circuit" in netlist
    assert "endmodule" in netlist
    
    testbench = writer.generate_testbench()
    assert "module custom_circuit_tb" in testbench
    assert "custom_circuit uut" in testbench

def test_wire_declarations(complex_circuit):
    """Test proper wire declarations in the netlist."""
    writer = VerilogWriter(complex_circuit)
    netlist = writer.generate_netlist()
    
    # Internal wires should be declared
    assert "wire w0" in netlist
    assert "wire w1" in netlist
    
    # Input/output ports should not be declared as wires
    assert "wire A" not in netlist.split("input wire A")[1]
    assert "wire B" not in netlist.split("input wire B")[1]
    assert "wire Z" not in netlist.split("output wire Z")[1]

def test_gate_connections(complex_circuit):
    """Test proper gate connections in the netlist."""
    writer = VerilogWriter(complex_circuit)
    netlist = writer.generate_netlist()
    
    # First OR gate
    assert ".A(A)" in netlist
    assert ".B(B)" in netlist
    assert ".Z(w0)" in netlist
    
    # Second OR gate
    assert ".A(C)" in netlist
    assert ".B(D)" in netlist
    assert ".Z(w1)" in netlist
    
    # AND gate
    assert ".A(w0)" in netlist
    assert ".B(w1)" in netlist
    assert ".Z(Z)" in netlist

def test_testbench_monitoring(complex_circuit):
    """Test signal monitoring in the testbench."""
    writer = VerilogWriter(complex_circuit)
    testbench = writer.generate_testbench()
    
    # Check that all signals are monitored
    monitor_line = testbench.split("$monitor")[1].split(";")[0]
    for signal in ["A", "B", "C", "D", "Z"]:
        assert signal in monitor_line 