from typing import List, Dict, Set, Union, Any
from ..core.circuit_generator import Circuit, GateInstance, Wire

class VerilogWriter:
    """Writer for generating Verilog netlists from circuit descriptions."""
    
    def __init__(self, circuit: Union[Circuit, Dict[str, Any]], module_name: str = "mtncl_circuit"):
        """Initialize the Verilog writer.
        
        Args:
            circuit: Circuit object or dictionary to convert to Verilog
            module_name: Name of the Verilog module to generate
        """
        self.circuit = circuit
        self.module_name = module_name
        self.testbench_name = f"{module_name}_tb"
        self._is_dict = isinstance(circuit, dict)
        
        # Extract circuit properties based on type
        if self._is_dict:
            self.inputs = set(circuit.get('inputs', []))
            self.outputs = set(circuit.get('outputs', []))
            self.gates = circuit.get('gates', [])
            # Collect all wires from gate connections
            self.wires = set()
            for gate in self.gates:
                for wire in gate.get('inputs', {}).values():
                    self.wires.add(wire)
                for wire in gate.get('outputs', {}).values():
                    self.wires.add(wire)
        else:
            self.inputs = circuit.inputs
            self.outputs = circuit.outputs
            self.gates = circuit.gates
            self.wires = circuit.wires
    
    def generate_netlist(self) -> str:
        """Generate a complete Verilog netlist for the circuit.
        
        Returns:
            String containing the Verilog netlist
        """
        verilog_lines = []
        
        # Add module header
        verilog_lines.extend(self._generate_module_header())
        
        # Add wire declarations
        verilog_lines.extend(self._generate_wire_declarations())
        
        # Add gate instantiations
        verilog_lines.extend(self._generate_gate_instantiations())
        
        # Add module footer
        verilog_lines.append("endmodule")
        
        return "\n".join(verilog_lines)
    
    def _generate_module_header(self) -> List[str]:
        """Generate the Verilog module header.
        
        Returns:
            List of lines for the module header
        """
        lines = []
        
        # Add timescale directive for MTNCL timing
        lines.append("`timescale 1ns/1ps")
        lines.append("")
        
        # Module declaration
        lines.append(f"module {self.module_name} (")
        
        # Global control signals first
        lines.append("    // Control signals")
        lines.append("    input wire sleep,")
        lines.append("    input wire rst,")
        lines.append("")
        
        # Input ports
        input_ports = sorted(p for p in self.inputs if p not in {"sleep", "rst"})
        if input_ports:
            lines.append("    // Input ports")
            for port in input_ports:
                lines.append(f"    input wire {port},")
            lines.append("")
        
        # Output ports
        output_ports = sorted(self.outputs)
        lines.append("    // Output ports")
        for port in output_ports[:-1]:
            lines.append(f"    output wire {port},")
        lines.append(f"    output wire {output_ports[-1]}")
        
        lines.append(");")
        lines.append("")
        
        return lines
    
    def _generate_wire_declarations(self) -> List[str]:
        """Generate wire declarations for internal connections.
        
        Returns:
            List of lines declaring internal wires
        """
        lines = []
        internal_wires = set()
        
        # Find all internal wires (not inputs or outputs)
        for wire_name in self.wires:
            if (wire_name not in self.inputs and 
                wire_name not in self.outputs):
                internal_wires.add(wire_name)
        
        if internal_wires:
            lines.append("    // Internal wires")
            for wire in sorted(internal_wires):
                lines.append(f"    wire {wire};")
            lines.append("")
        
        return lines
    
    def _generate_gate_instantiations(self) -> List[str]:
        """Generate gate instantiations for all gates in the circuit.
        
        Returns:
            List of lines instantiating gates
        """
        lines = []
        lines.append("    // Gate instantiations")
        
        for i, gate in enumerate(self.gates):
            if self._is_dict:
                # Dictionary format
                gate_type = gate.get('type', '').upper()
                instance_name = f"{gate_type.lower()}_inst_{i}"
                inputs = gate.get('inputs', {})
                outputs = gate.get('outputs', {})
                
                lines.append(f"    {gate_type} {instance_name} (")
                
                # Connect inputs
                input_connections = []
                for port_name, wire_name in sorted(inputs.items()):
                    input_connections.append(f".{port_name}({wire_name})")
                
                # Connect outputs
                output_connections = []
                for port_name, wire_name in sorted(outputs.items()):
                    output_connections.append(f".{port_name}({wire_name})")
                
                # Add sleep and reset connections
                input_connections.append(".S(sleep)")
                input_connections.append(".vdd_sel(1'b1)")  # Default to high voltage mode
                
                # Combine all connections
                all_connections = input_connections + output_connections
                for conn in all_connections[:-1]:
                    lines.append(f"        {conn},")
                lines.append(f"        {all_connections[-1]}")
                
                lines.append("    );")
                lines.append("")
            else:
                # Circuit object format
                lines.extend(self._generate_single_gate(gate))
        
        return lines
    
    def _generate_single_gate(self, gate: GateInstance) -> List[str]:
        """Generate Verilog code for a single gate instance.
        
        Args:
            gate: Gate instance to generate code for
            
        Returns:
            List of lines for the gate instantiation
        """
        lines = []
        
        # Gate instantiation
        lines.append(f"    {gate.gate_type} {gate.instance_name} (")
        
        # Connect inputs
        input_connections = []
        for port_name, wire_name in sorted(gate.inputs.items()):
            input_connections.append(f".{port_name}({wire_name})")
        
        # Connect outputs
        output_connections = []
        for port_name, wire_name in sorted(gate.outputs.items()):
            output_connections.append(f".{port_name}({wire_name})")
        
        # Combine all connections
        all_connections = input_connections + output_connections
        for conn in all_connections[:-1]:
            lines.append(f"        {conn},")
        lines.append(f"        {all_connections[-1]}")
        
        lines.append("    );")
        lines.append("")
        
        return lines
    
    def generate_testbench(self) -> str:
        """Generate a basic testbench for the circuit.
        
        Returns:
            String containing the Verilog testbench
        """
        lines = []
        
        # Testbench module
        lines.append("`timescale 1ns/1ps")
        lines.append(f"module {self.testbench_name} (");
        
        # Declare registers and wires
        lines.append("    // Control signals")
        lines.append("    reg sleep;")
        lines.append("    reg rst;")
        lines.append("")
        
        input_ports = sorted(p for p in self.inputs if p not in {"sleep", "rst"})
        if input_ports:
            lines.append("    // Input signals")
            for input_port in input_ports:
                lines.append(f"    reg {input_port};")
            lines.append("")
        
        lines.append("    // Output signals")
        for output_port in sorted(self.outputs):
            lines.append(f"    wire {output_port};")
        lines.append("")
        
        # Instantiate circuit under test
        lines.append(f"    // Instantiate the Unit Under Test (UUT)")
        lines.append(f"    {self.module_name} uut (")
        
        # Connect ports
        connections = []
        connections.append("        .sleep(sleep)")
        connections.append("        .rst(rst)")
        for port in input_ports:
            connections.append(f"        .{port}({port})")
        for port in sorted(self.outputs):
            connections.append(f"        .{port}({port})")
        
        lines.append(",\n".join(connections))
        lines.append("    );")
        lines.append("")
        
        # Add initial block with test vectors
        lines.append("    initial begin")
        lines.append("        // Initialize control signals")
        lines.append("        sleep = 1;")
        lines.append("        rst = 1;")
        lines.append("")
        
        if input_ports:
            lines.append("        // Initialize inputs")
            for input_port in input_ports:
                lines.append(f"        {input_port} = 0;")
            lines.append("")
        
        lines.append("        // Wait 100ns for global reset")
        lines.append("        #100;")
        lines.append("        rst = 0;")
        lines.append("        sleep = 0;")
        lines.append("")
        
        lines.append("        // Add test vectors")
        if input_ports:
            lines.append("        #50;")
            for input_port in input_ports:
                lines.append(f"        {input_port} = 1;")
            lines.append("        #50;")
            for input_port in input_ports:
                lines.append(f"        {input_port} = 0;")
        
        lines.append("        // Test sleep mode")
        lines.append("        #50;")
        lines.append("        sleep = 1;")
        lines.append("        #50;")
        lines.append("        sleep = 0;")
        lines.append("")
        
        lines.append("        // End simulation")
        lines.append("        #100;")
        lines.append("        $finish;")
        lines.append("    end")
        lines.append("")
        
        # Add monitoring
        lines.append("    // Monitor changes")
        lines.append("    initial begin")
        lines.append("        $monitor($time, \" sleep=%b rst=%b ")
        
        # Create monitor format string
        monitor_ports = []
        for port in input_ports:
            monitor_ports.append(f"{port}=%b")
        for port in sorted(self.outputs):
            monitor_ports.append(f"{port}=%b")
        
        lines.append(" ".join(monitor_ports) + "\",")
        
        # Add monitored signals
        monitor_signals = ["sleep", "rst"]
        monitor_signals.extend(input_ports)
        monitor_signals.extend(sorted(self.outputs))
        
        lines.append("            " + ", ".join(monitor_signals))
        lines.append("        );")
        lines.append("    end")
        lines.append("")
        
        lines.append("endmodule")
        
        return "\n".join(lines)

def write_verilog_netlist(circuit: Dict, output_file: str, is_testbench: bool = False) -> None:
    """Write a Verilog netlist to a file.
    
    Args:
        circuit: Circuit dictionary containing the netlist information
        output_file: Path to the output file
        is_testbench: Whether to generate a testbench instead of a netlist
        
    Raises:
        ValueError: If the circuit dictionary is invalid
    """
    writer = VerilogWriter(circuit)
    
    with open(output_file, 'w') as f:
        if is_testbench:
            f.write(writer.generate_testbench())
        else:
            f.write(writer.generate_netlist()) 