from typing import List, Dict, Set
from ..core.circuit_generator import Circuit, GateInstance, Wire

class VerilogWriter:
    """Writer for generating Verilog netlists from circuit descriptions."""
    
    def __init__(self, circuit: Circuit, module_name: str = "mtncl_circuit"):
        """Initialize the Verilog writer.
        
        Args:
            circuit: Circuit object to convert to Verilog
            module_name: Name of the Verilog module to generate
        """
        self.circuit = circuit
        self.module_name = module_name
        self.testbench_name = f"{module_name}_tb"
    
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
        input_ports = sorted(p for p in self.circuit.inputs if p not in {"sleep", "rst"})
        if input_ports:
            lines.append("    // Input ports")
            for port in input_ports:
                lines.append(f"    input wire {port},")
            lines.append("")
        
        # Output ports
        output_ports = sorted(self.circuit.outputs)
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
        for wire_name in self.circuit.wires:
            if (wire_name not in self.circuit.inputs and 
                wire_name not in self.circuit.outputs):
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
        
        for gate in self.circuit.gates:
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
        
        input_ports = sorted(p for p in self.circuit.inputs if p not in {"sleep", "rst"})
        if input_ports:
            lines.append("    // Input signals")
            for input_port in input_ports:
                lines.append(f"    reg {input_port};")
            lines.append("")
        
        lines.append("    // Output signals")
        for output_port in sorted(self.circuit.outputs):
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
        for port in sorted(self.circuit.outputs):
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
        for port in sorted(self.circuit.outputs):
            monitor_ports.append(f"{port}=%b")
        
        lines.append(" ".join(monitor_ports) + "\",")
        
        # Add monitored signals
        monitor_signals = ["sleep", "rst"]
        monitor_signals.extend(input_ports)
        monitor_signals.extend(sorted(self.circuit.outputs))
        
        lines.append("            " + ", ".join(monitor_signals))
        lines.append("        );")
        lines.append("    end")
        lines.append("")
        
        lines.append("endmodule")
        
        return "\n".join(lines) 