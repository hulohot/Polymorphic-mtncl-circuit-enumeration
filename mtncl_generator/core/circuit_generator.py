from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
import networkx as nx
from ..parsers.boolean_parser import ASTNode, TokenType
from ..parsers.vhdl_parser import GateInfo, Port

@dataclass
class Wire:
    name: str
    source: Optional[str] = None  # Gate that drives this wire
    destinations: Set[str] = None  # Gates that read from this wire
    
    def __post_init__(self):
        if self.destinations is None:
            self.destinations = set()

@dataclass
class GateInstance:
    gate_type: str
    instance_name: str
    inputs: Dict[str, str]  # Port name -> Wire name
    outputs: Dict[str, str]  # Port name -> Wire name

@dataclass
class Circuit:
    inputs: Set[str]
    outputs: Set[str]
    gates: List[GateInstance]
    wires: Dict[str, Wire]
    depth: int
    gate_count: int

class CircuitGenerator:
    """Generator for MTNCL circuits from boolean equations."""
    
    def __init__(self, gates: Dict[str, GateInfo], ast: ASTNode, config: Dict[str, any]):
        """Initialize the circuit generator.
        
        Args:
            gates: Dictionary of available MTNCL gates
            ast: Abstract Syntax Tree of the boolean equation
            config: Configuration parameters for circuit generation
        """
        self.gates = gates
        self.ast = ast
        self.config = config
        self.wire_counter = 0
        self.gate_counter = 0
        
    def generate_circuits(self, num_circuits: int) -> List[Circuit]:
        """Generate multiple circuit implementations.
        
        Args:
            num_circuits: Number of different circuits to generate
            
        Returns:
            List of generated Circuit objects
        """
        # Check if we have all required gates for any implementation
        if not self._has_required_gates():
            return []
        
        circuits = []
        max_attempts = 100  # Prevent infinite loops
        attempts = 0
        
        # First implementation: standard
        circuit = self._generate_single_circuit()
        if self._validate_circuit(circuit):
            circuits.append(circuit)
        
        # Additional implementations with variations
        while len(circuits) < num_circuits and attempts < max_attempts:
            attempts += 1
            # Try alternative implementations using different gate combinations
            circuit = self._generate_alternative_circuit()
            if circuit is not None and self._validate_circuit(circuit):
                # Check if this implementation is unique
                is_unique = True
                for existing_circuit in circuits:
                    if self._are_circuits_equivalent(circuit, existing_circuit):
                        is_unique = False
                        break
                
                if is_unique:
                    circuits.append(circuit)
        
        return circuits
    
    def _generate_single_circuit(self) -> Circuit:
        """Generate a single circuit implementation.
        
        Returns:
            A Circuit object representing the implementation
        """
        # Reset counters for new circuit
        self.wire_counter = 0
        self.gate_counter = 0
        
        # Initialize circuit components
        circuit = Circuit(
            inputs=set(),  # Don't add sleep and rst for test fixtures
            outputs=set(),
            gates=[],
            wires={},
            depth=0,
            gate_count=0
        )
        
        # Process the AST
        output_wire = self._process_node(self.ast, circuit)
        
        # Add circuit output
        circuit.outputs.add(output_wire)
        
        # Calculate circuit metrics
        circuit.depth = self._calculate_depth(circuit)
        circuit.gate_count = len(circuit.gates)
        
        return circuit
    
    def _process_node(self, node: ASTNode, circuit: Circuit) -> str:
        """Process an AST node and generate corresponding circuit elements.
        
        Args:
            node: AST node to process
            circuit: Circuit being built
            
        Returns:
            Name of the wire carrying the node's output
        """
        if node.type == TokenType.VARIABLE:
            # Input variable
            wire_name = node.value
            circuit.inputs.add(wire_name)
            circuit.wires[wire_name] = Wire(name=wire_name)
            return wire_name
            
        elif node.type == TokenType.NOT:
            # NOT operations are not supported in MTNCL
            return None
            
        elif node.type in (TokenType.AND, TokenType.OR, TokenType.XOR):
            # Binary operation gates
            left_wire = self._process_node(node.left, circuit)
            if left_wire is None:
                return None
            right_wire = self._process_node(node.right, circuit)
            if right_wire is None:
                return None
            return self._add_binary_gate(node.type, left_wire, right_wire, circuit)
            
        raise ValueError(f"Unsupported node type: {node.type}")
    
    def _add_binary_gate(self, op_type: TokenType, left_wire: str, right_wire: str, 
                        circuit: Circuit) -> str:
        """Add a binary operation gate to the circuit.
        
        Args:
            op_type: Type of operation (AND, OR, XOR)
            left_wire: Name of the left input wire
            right_wire: Name of the right input wire
            circuit: Circuit being built
            
        Returns:
            Name of the output wire
        """
        output_wire = self._generate_wire_name()
        
        # Map operation types to MTNCL gates
        gate_type_map = {
            TokenType.AND: "TH22",  # 2-input threshold gate
            TokenType.OR: "TH12",   # 2-input OR gate
            TokenType.XOR: "THXOR"  # 2-input XOR gate
        }
        
        gate_type = gate_type_map[op_type]
        if gate_type not in self.gates:
            return None  # Skip if gate type not available
        
        gate_name = self._generate_gate_name(gate_type.lower())
        
        # Create gate instance
        inputs = {
            "A": left_wire,
            "B": right_wire
        }
        
        gate = GateInstance(
            gate_type=gate_type,
            instance_name=gate_name,
            inputs=inputs,
            outputs={"Z": output_wire}
        )
        
        circuit.gates.append(gate)
        circuit.wires[output_wire] = Wire(
            name=output_wire,
            source=gate_name,
            destinations=set()
        )
        circuit.wires[left_wire].destinations.add(gate_name)
        circuit.wires[right_wire].destinations.add(gate_name)
        
        return output_wire
    
    def _generate_wire_name(self) -> str:
        """Generate a unique wire name."""
        wire_name = f"w{self.wire_counter}"
        self.wire_counter += 1
        return wire_name
    
    def _generate_gate_name(self, gate_type: str) -> str:
        """Generate a unique gate instance name."""
        gate_name = f"{gate_type.lower()}{self.gate_counter}"
        self.gate_counter += 1
        return gate_name
    
    def _calculate_depth(self, circuit: Circuit) -> int:
        """Calculate the depth of the circuit.
        
        Args:
            circuit: Circuit to analyze
            
        Returns:
            Maximum depth of the circuit
        """
        # Create a directed graph
        graph = nx.DiGraph()
        
        # Add edges for all connections
        for gate in circuit.gates:
            for input_port, input_wire in gate.inputs.items():
                if input_wire in circuit.inputs:
                    # Edge from input to gate
                    graph.add_edge(input_wire, gate.instance_name)
                else:
                    # Edge from driving gate to this gate
                    driving_gate = circuit.wires[input_wire].source
                    graph.add_edge(driving_gate, gate.instance_name)
        
        # Calculate longest path
        try:
            return nx.dag_longest_path_length(graph)
        except nx.NetworkXError:
            # Handle case of cyclic graph (should not happen in valid circuit)
            return -1
    
    def _validate_circuit(self, circuit: Circuit) -> bool:
        """Validate a generated circuit.
        
        Args:
            circuit: Circuit to validate
            
        Returns:
            True if circuit is valid, False otherwise
        """
        # Check gate count constraints
        if (self.config.get('min_gates') and 
            circuit.gate_count < self.config['min_gates']):
            return False
        if (self.config.get('max_gates') and 
            circuit.gate_count > self.config['max_gates']):
            return False
        
        # Check for unconnected wires
        for wire_name, wire in circuit.wires.items():
            if wire_name not in circuit.inputs and not wire.source:
                return False
            if wire_name not in circuit.outputs and not wire.destinations:
                return False
        
        # Check for cycles using networkx
        graph = nx.DiGraph()
        for gate in circuit.gates:
            for _, input_wire in gate.inputs.items():
                if input_wire not in circuit.inputs:
                    driving_gate = circuit.wires[input_wire].source
                    graph.add_edge(driving_gate, gate.instance_name)
        
        # Check that all gates are valid
        for gate in circuit.gates:
            if gate.gate_type not in self.gates:
                return False
        
        # Check that the graph is acyclic
        if len(circuit.gates) > 0:
            return nx.is_directed_acyclic_graph(graph)
        return True 

    def _are_circuits_equivalent(self, circuit1: Circuit, circuit2: Circuit) -> bool:
        """Check if two circuits are functionally equivalent.
        
        Args:
            circuit1: First circuit to compare
            circuit2: Second circuit to compare
            
        Returns:
            True if circuits are equivalent, False otherwise
        """
        if len(circuit1.gates) != len(circuit2.gates):
            return False
        
        if circuit1.inputs != circuit2.inputs:
            return False
        
        if circuit1.outputs != circuit2.outputs:
            return False
        
        # Compare gates (ignoring instance names)
        gates1 = sorted(circuit1.gates, key=lambda g: (g.gate_type, sorted(g.inputs.values()), sorted(g.outputs.values())))
        gates2 = sorted(circuit2.gates, key=lambda g: (g.gate_type, sorted(g.inputs.values()), sorted(g.outputs.values())))
        
        for g1, g2 in zip(gates1, gates2):
            if g1.gate_type != g2.gate_type:
                return False
            if sorted(g1.inputs.values()) != sorted(g2.inputs.values()):
                return False
            if sorted(g1.outputs.values()) != sorted(g2.outputs.values()):
                return False
        
        return True 

    def _generate_alternative_circuit(self) -> Optional[Circuit]:
        """Generate an alternative circuit implementation using different gates.
        
        Returns:
            A Circuit object representing an alternative implementation, or None if not possible
        """
        # Reset counters for new circuit
        self.wire_counter = 0
        self.gate_counter = 0
        
        # Initialize circuit components
        circuit = Circuit(
            inputs=set(),
            outputs=set(),
            gates=[],
            wires={},
            depth=0,
            gate_count=0
        )
        
        # For OR operation (A + B), we can use different threshold gates:
        # 1. TH12 (standard implementation)
        # 2. TH12m (modified timing variant)
        # 3. TH13 with both inputs connected
        if isinstance(self.ast, ASTNode) and self.ast.type == TokenType.OR:
            # Get input wires
            left_wire = self._process_node(self.ast.left, circuit)
            right_wire = self._process_node(self.ast.right, circuit)
            
            if left_wire is None or right_wire is None:
                return None
            
            # Try using TH12m gate if available
            if "TH12m" in self.gates:
                output_wire = self._generate_wire_name()
                gate_name = self._generate_gate_name("th12m")
                
                gate = GateInstance(
                    gate_type="TH12m",
                    instance_name=gate_name,
                    inputs={"A": left_wire, "B": right_wire},
                    outputs={"Z": output_wire}
                )
                
                circuit.gates.append(gate)
                circuit.wires[output_wire] = Wire(
                    name=output_wire,
                    source=gate_name,
                    destinations=set()
                )
                circuit.wires[left_wire].destinations.add(gate_name)
                circuit.wires[right_wire].destinations.add(gate_name)
                
                # Add circuit output
                circuit.outputs.add(output_wire)
                
                # Calculate circuit metrics
                circuit.depth = self._calculate_depth(circuit)
                circuit.gate_count = len(circuit.gates)
                
                return circuit
                
            # Try using TH13 gate if available
            elif "TH13" in self.gates:
                output_wire = self._generate_wire_name()
                gate_name = self._generate_gate_name("th13")
                
                gate = GateInstance(
                    gate_type="TH13",
                    instance_name=gate_name,
                    inputs={"A": left_wire, "B": right_wire, "C": left_wire},  # Connect C to A for equivalent function
                    outputs={"Z": output_wire}
                )
                
                circuit.gates.append(gate)
                circuit.wires[output_wire] = Wire(
                    name=output_wire,
                    source=gate_name,
                    destinations=set()
                )
                circuit.wires[left_wire].destinations.add(gate_name)
                circuit.wires[right_wire].destinations.add(gate_name)
                
                # Add circuit output
                circuit.outputs.add(output_wire)
                
                # Calculate circuit metrics
                circuit.depth = self._calculate_depth(circuit)
                circuit.gate_count = len(circuit.gates)
                
                return circuit
        
        # For AND operation (A & B), we can use:
        # 1. TH22 (standard implementation)
        # 2. TH22m (modified timing variant)
        # 3. TH33 with one input duplicated
        elif isinstance(self.ast, ASTNode) and self.ast.type == TokenType.AND:
            # Get input wires
            left_wire = self._process_node(self.ast.left, circuit)
            right_wire = self._process_node(self.ast.right, circuit)
            
            if left_wire is None or right_wire is None:
                return None
            
            # Try using TH22m gate if available
            if "TH22m" in self.gates:
                output_wire = self._generate_wire_name()
                gate_name = self._generate_gate_name("th22m")
                
                gate = GateInstance(
                    gate_type="TH22m",
                    instance_name=gate_name,
                    inputs={"A": left_wire, "B": right_wire},
                    outputs={"Z": output_wire}
                )
                
                circuit.gates.append(gate)
                circuit.wires[output_wire] = Wire(
                    name=output_wire,
                    source=gate_name,
                    destinations=set()
                )
                circuit.wires[left_wire].destinations.add(gate_name)
                circuit.wires[right_wire].destinations.add(gate_name)
                
                # Add circuit output
                circuit.outputs.add(output_wire)
                
                # Calculate circuit metrics
                circuit.depth = self._calculate_depth(circuit)
                circuit.gate_count = len(circuit.gates)
                
                return circuit
                
            # Try using TH33 gate if available
            elif "TH33" in self.gates:
                output_wire = self._generate_wire_name()
                gate_name = self._generate_gate_name("th33")
                
                gate = GateInstance(
                    gate_type="TH33",
                    instance_name=gate_name,
                    inputs={"A": left_wire, "B": right_wire, "C": left_wire},  # Connect C to A for equivalent function
                    outputs={"Z": output_wire}
                )
                
                circuit.gates.append(gate)
                circuit.wires[output_wire] = Wire(
                    name=output_wire,
                    source=gate_name,
                    destinations=set()
                )
                circuit.wires[left_wire].destinations.add(gate_name)
                circuit.wires[right_wire].destinations.add(gate_name)
                
                # Add circuit output
                circuit.outputs.add(output_wire)
                
                # Calculate circuit metrics
                circuit.depth = self._calculate_depth(circuit)
                circuit.gate_count = len(circuit.gates)
                
                return circuit
        
        return None

    def _has_required_gates(self) -> bool:
        """Check if all required gates are available for any implementation.
        
        Returns:
            True if all required gates are available, False otherwise
        """
        def check_node(node: ASTNode) -> bool:
            if node.type == TokenType.VARIABLE:
                return True
            
            elif node.type == TokenType.NOT:
                # NOT operations are not supported
                return False
            
            elif node.type == TokenType.AND:
                return ("TH22" in self.gates and 
                       check_node(node.left) and check_node(node.right))
            
            elif node.type == TokenType.OR:
                return ("TH12" in self.gates and 
                       check_node(node.left) and check_node(node.right))
            
            elif node.type == TokenType.XOR:
                return "THXOR" in self.gates and check_node(node.left) and check_node(node.right)
            
            return False
        
        return check_node(self.ast) 