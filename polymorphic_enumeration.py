# This file will be used to implement the boolean function to netlist converter
# First, let's gather requirements through questions

"""
Questions about the requirements:

1. Input Format:
- What format should the boolean function input be in? 
  - Sum of products (like in sbox_matching.py)?
  - Truth table?
  - Other format?
Answer: I think the best format is sum of products using standard operators (+ AND, | OR , ~ NOT)

2. Polymorphic Gates:
- What are the available MTNCL gates to use?
- Do they have different modes of operation?
- Are there constraints on which gates can be used together?
Answer: See @polymorphic_gates.py

3. Circuit Enumeration:
- What criteria should be used to determine if two circuits are "different"?
- Should the enumeration prioritize:
  a) Minimal gate count
  b) Minimal transistor count 
  c) Both as Pareto optimal solutions
  d) Other metrics?
Answer: They are different if they have a unique gate graph (The graph of gates that make up the solution are not the same), c) Both as Pareto optimal solutions

4. Netlist Output:
- What specific Verilog format is needed?
- Should the output include:
  a) Just gate instantiations
  b) Full module definition
  c) Multiple files/modules
  d) Testbench generation
Answer: Just regular Verilog, a) Just gate instantiations

5. Comparison Metrics:
- Besides gate count and transistor count, are there other metrics to track?
- How should the comparison be formatted/displayed?
Answer: Table using tabulate

6. Size Constraints:
- Is there a maximum size boolean function to handle?
- Maximum number of inputs/outputs?
- Maximum number of terms?
Answer: No, we can handle any size boolean function

Please provide any clarification on these points to help guide the implementation.
"""

# Implementation will begin after requirements are clarified

import re
import os
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict, Set, Union, Any, Optional, Tuple
import networkx as nx
from tabulate import tabulate
import getpass
from polymorphic_gates import POLYMORPHIC_MTNCL_GATES, POLYMORPHIC_GATES
from mtncl_types import Gate, DualRail
import itertools

@dataclass
class Circuit:
    """Represents a circuit implementation"""
    gates: List[Gate]
    inputs: Set[DualRail]
    outputs: Set[DualRail]
    graph: nx.DiGraph
    voltage_level: str = "HVDD"  # Default to HVDD
    
    def total_transistors(self) -> int:
        return sum(gate.transistor_count for gate in self.gates)

class Node:
    def __init__(self, type: str, value: str = None, children: List['Node'] = None):
        self.type = type  # VAR, AND, OR
        self.value = value  # Variable name for VAR nodes
        self.children = children if children else []

    def __str__(self):
        if self.type == 'VAR':
            return f"VAR: {self.value}"
        else:
            return f"{self.type}: ({', '.join(str(c) for c in self.children)})"

class BooleanParser:
    """Parser for boolean expressions with support for dual functionality (HVDD and LVDD)"""
    def __init__(self):
        self.variables = set()
        
    def parse(self, hvdd_expr: str, lvdd_expr: str) -> Tuple[Node, Node]:
        """Parse both HVDD and LVDD expressions into operation trees"""
        print(f"\nParsing HVDD expression: {hvdd_expr}")
        hvdd_tree = self._parse_expr(hvdd_expr)
        print(f"Parsing LVDD expression: {lvdd_expr}")
        lvdd_tree = self._parse_expr(lvdd_expr)
        return hvdd_tree, lvdd_tree
        
    def _parse_expr(self, expr: str, depth: int = 0) -> Node:
        """Parse a boolean expression into a Node tree"""
        # Check recursion depth
        if depth > 100:  # Reasonable limit for our expressions
            raise RecursionError("Expression too complex or malformed")
        
        # Remove spaces
        expr = expr.replace(" ", "")
        
        # Handle empty expression
        if not expr:
            raise ValueError("Empty expression")
        
        # Handle parentheses
        if expr.startswith('(') and expr.endswith(')'):
            # Remove outer parentheses and parse inner expression
            inner = expr[1:-1].strip()
            if not inner:
                raise ValueError("Empty parentheses")
            return self._parse_expr(inner, depth + 1)
        
        # Split on OR first (lowest precedence)
        if "|" in expr:
            # Find top-level OR operators (not inside parentheses)
            terms = []
            current_term = ""
            paren_count = 0
            for c in expr:
                if c == '(':
                    paren_count += 1
                elif c == ')':
                    paren_count -= 1
                elif c == '|' and paren_count == 0:
                    if current_term:
                        terms.append(current_term)
                    current_term = ""
                    continue
                current_term += c
            if current_term:
                terms.append(current_term)
            
            if not terms:  # No valid terms found
                return self.Node("VAR", value=expr)
            
            children = [self._parse_expr(term.strip(), depth + 1) for term in terms if term.strip()]
            if not children:
                raise ValueError("No valid terms in OR expression")
            return self.Node("OR", children=children)
        
        # Then split on AND (higher precedence)
        if "&" in expr:
            # Find top-level AND operators (not inside parentheses)
            factors = []
            current_factor = ""
            paren_count = 0
            for c in expr:
                if c == '(':
                    paren_count += 1
                elif c == ')':
                    paren_count -= 1
                elif c == '&' and paren_count == 0:
                    if current_factor:
                        factors.append(current_factor)
                    current_factor = ""
                    continue
                current_factor += c
            if current_factor:
                factors.append(current_factor)
            
            if not factors:  # No valid factors found
                return self.Node("VAR", value=expr)
            
            children = [self._parse_expr(factor.strip(), depth + 1) for factor in factors if factor.strip()]
            if not children:
                raise ValueError("No valid factors in AND expression")
            return self.Node("AND", children=children)
        
        # Must be a variable
        if not expr.isalnum():  # Basic validation for variable names
            raise ValueError(f"Invalid variable name: {expr}")
        return self.Node("VAR", value=expr)

    def debug_print_tree(self, tree: Node, prefix: str = ""):
        """Print the operation tree for debugging"""
        if tree is None:
            return
            
        if isinstance(tree, tuple):
            print(f"{prefix}HVDD Tree:")
            self.debug_print_tree(tree[0], prefix + "  ")
            print(f"{prefix}LVDD Tree:")
            self.debug_print_tree(tree[1], prefix + "  ")
            return
            
        print(f"{prefix}{tree.type}", end="")
        if tree.type == 'VAR':
            print(f": {tree.value}")
        else:
            print()
            for child in tree.children:
                self.debug_print_tree(child, prefix + "  ")

    def _tree_to_expr(self, tree: Node) -> str:
        """Convert a Node tree back to a string expression"""
        if tree is None:
            return ""
        
        if tree.type == "VAR":
            return tree.value
        
        if len(tree.children) == 0:
            return ""
        
        if tree.type == "AND":
            return "&".join(self._tree_to_expr(child) for child in tree.children)
        elif tree.type == "OR":
            return "|".join(self._tree_to_expr(child) for child in tree.children)
        
        return ""

    def _get_variables(self, tree: Node) -> List[str]:
        """Get all variables used in a tree"""
        if tree.type == "VAR":
            return [tree.value]
        
        variables = []
        for child in tree.children:
            variables.extend(self._get_variables(child))
        return list(set(variables))

@dataclass
class PolymorphicGate:
    """Represents a polymorphic MTNCL gate with its modes and characteristics"""
    name: str
    num_inputs: int
    transistor_count: int
    modes: List[str]
    
    def can_implement(self, operation: str) -> bool:
        """Check if this gate can implement the given operation in any of its modes"""
        return operation in self.modes

class CircuitEnumerator:
    """Enumerates possible circuit implementations"""
    def __init__(self):
        self.gates = POLYMORPHIC_MTNCL_GATES
        self._truth_table_cache = {}  # Cache for truth tables
        self._gate_truth_table_cache = {}  # Cache for gate truth tables

    class Node:
        def __init__(self, type: str, value: str = None, children: List['CircuitEnumerator.Node'] = None):
            self.type = type  # VAR, AND, OR
            self.value = value  # Variable name for VAR nodes
            self.children = children if children else []

        def __str__(self):
            if self.type == 'VAR':
                return f"VAR: {self.value}"
            else:
                return f"{self.type}: ({', '.join(str(c) for c in self.children)})"

    def _parse_expr(self, expr: str) -> Node:
        """Parse a boolean expression into a Node tree"""
        # Remove spaces
        expr = expr.replace(" ", "")
        
        # Handle parentheses
        if expr.startswith('(') and expr.endswith(')'):
            # Remove outer parentheses and parse inner expression
            return self._parse_expr(expr[1:-1])
        
        # Split on OR
        if "|" in expr:
            # Find top-level OR operators (not inside parentheses)
            terms = []
            current_term = ""
            paren_count = 0
            for c in expr:
                if c == '(':
                    paren_count += 1
                elif c == ')':
                    paren_count -= 1
                elif c == '|' and paren_count == 0:
                    if current_term:
                        terms.append(current_term)
                    current_term = ""
                    continue
                current_term += c
            if current_term:
                terms.append(current_term)
            
            if not terms:  # No valid terms found
                return self.Node("VAR", value=expr)
            
            children = [self._parse_expr(term) for term in terms]
            return self.Node("OR", children=children)
        
        # Split on AND
        if "&" in expr:
            # Find top-level AND operators (not inside parentheses)
            factors = []
            current_factor = ""
            paren_count = 0
            for c in expr:
                if c == '(':
                    paren_count += 1
                elif c == ')':
                    paren_count -= 1
                elif c == '&' and paren_count == 0:
                    if current_factor:
                        factors.append(current_factor)
                    current_factor = ""
                    continue
                current_factor += c
            if current_factor:
                factors.append(current_factor)
            
            if not factors:  # No valid factors found
                return self.Node("VAR", value=expr)
            
            children = [self._parse_expr(factor) for factor in factors]
            return self.Node("AND", children=children)
        
        # Must be a variable
        return self.Node("VAR", value=expr)

    def _get_variables(self, tree: Node) -> List[str]:
        """Get all variables used in a tree"""
        if tree.type == "VAR":
            return [tree.value]
        
        variables = []
        for child in tree.children:
            variables.extend(self._get_variables(child))
        return list(set(variables))

    def _tree_to_expr(self, tree: Node) -> str:
        """Convert a Node tree back to a string expression"""
        if tree is None:
            return ""
        
        if tree.type == "VAR":
            return tree.value
        
        if len(tree.children) == 0:
            return ""
        
        if tree.type == "AND":
            return "&".join(self._tree_to_expr(child) for child in tree.children)
        elif tree.type == "OR":
            return "|".join(self._tree_to_expr(child) for child in tree.children)
        
        return ""

    def _evaluate_tree(self, node: Node, assignments: Dict[str, int]) -> bool:
        """Evaluate a boolean expression tree with given variable assignments"""
        if node.type == "VAR":
            return assignments[node.value]
        elif node.type == "AND":
            return all(self._evaluate_tree(child, assignments) for child in node.children)
        elif node.type == "OR":
            return any(self._evaluate_tree(child, assignments) for child in node.children)
        else:
            raise ValueError(f"Unknown node type: {node.type}")

    def _get_truth_table(self, tree: Node, all_vars: List[str]) -> List[int]:
        """Get truth table for a boolean expression tree with given variables"""
        # Create cache key
        cache_key = (self._tree_to_expr(tree), tuple(all_vars))
        if cache_key in self._truth_table_cache:
            return self._truth_table_cache[cache_key]

        n = len(all_vars)
        table = []
        for i in range(2**n):
            # Create variable assignments
            assignments = {}
            for j, var in enumerate(all_vars):
                assignments[var] = (i >> (n-1-j)) & 1
            
            # Evaluate tree with these assignments
            result = self._evaluate_tree(tree, assignments)
            table.append(1 if result else 0)
        
        self._truth_table_cache[cache_key] = table
        return table

    def _get_gate_truth_table(self, gate_func: str, input_map: List[str], all_vars: List[str]) -> List[int]:
        """Get truth table for a gate with given input mappings"""
        # Create cache key
        cache_key = (gate_func, tuple(input_map), tuple(all_vars))
        if cache_key in self._gate_truth_table_cache:
            return self._gate_truth_table_cache[cache_key]

        n = len(all_vars)
        table = []
        for i in range(2**n):
            # Create variable assignments
            assignments = {}
            for j, var in enumerate(all_vars):
                assignments[var] = (i >> (n-1-j)) & 1
            
            # Map inputs to gate
            gate_inputs = [assignments[var] for var in input_map]
            
            # Evaluate gate function
            result = self._evaluate_gate_function(gate_func, gate_inputs)
            table.append(1 if result else 0)
        
        self._gate_truth_table_cache[cache_key] = table
        return table

    def _evaluate_gate_function(self, gate_func: str, inputs: List[int]) -> bool:
        """Evaluate a gate function with given inputs"""
        # Replace input variables with their values
        expr = gate_func
        for i, val in enumerate(inputs):
            var = chr(ord('a') + i)
            expr = expr.replace(var, str(val))
        
        # Replace operators
        expr = expr.replace('&', ' and ').replace('|', ' or ')
        
        # Evaluate the expression
        try:
            return bool(eval(expr))
        except:
            return False

    def enumerate_all(self, hvdd_expr: str, lvdd_expr: str, max_results: int = 10) -> List[Dict]:
        """Enumerate all possible polymorphic circuits implementing the given functions"""
        print("DEBUG: Starting circuit enumeration")
        
        # Parse expressions into trees
        hvdd_tree = self._parse_expr(hvdd_expr)
        lvdd_tree = self._parse_expr(lvdd_expr)
        
        # Get all input variables from both trees
        hvdd_vars = self._get_variables(hvdd_tree)
        lvdd_vars = self._get_variables(lvdd_tree)
        all_vars = sorted(list(set(hvdd_vars + lvdd_vars)))
        print(f"Input variables: {all_vars}")
        
        # Get target truth tables
        hvdd_table = self._get_truth_table(hvdd_tree, all_vars)
        lvdd_table = self._get_truth_table(lvdd_tree, all_vars)
        print("Target truth tables:")
        print(f"HVDD: {hvdd_table}")
        print(f"LVDD: {lvdd_table}")
        
        # Count total work to be done
        total_gates = len(self.gates)
        print(f"\nEnumerating {total_gates} gates...")
        
        results = []
        gate_count = 0
        mappings_tested = 0
        
        # Sort gates by number of inputs (try simpler gates first)
        sorted_gates = sorted(self.gates.items(), key=lambda x: len(x[1]['inputs']))
        
        for gate, gate_info in sorted_gates:
            gate_count += 1
            hvdd_func = gate_info['hvdd']
            lvdd_func = gate_info['lvdd']
            num_inputs = len(gate_info['inputs'])
            
            # Skip gates that require more inputs than we have variables
            if num_inputs < len(all_vars):
                print(f"\rProgress: {gate_count}/{total_gates} gates ({gate}) - Skipped (insufficient inputs)", end="")
                continue
            
            # Skip gates that require too many inputs (more than 2x the variables)
            if num_inputs > 2 * len(all_vars):
                print(f"\rProgress: {gate_count}/{total_gates} gates ({gate}) - Skipped (too many inputs)", end="")
                continue
            
            # For each required variable, ensure it appears at least once in the mapping
            required_positions = {var: False for var in all_vars}
            base_mapping = []
            
            # First, place each required variable in a position
            for var in all_vars:
                base_mapping.append(var)
                required_positions[var] = True
            
            # Fill remaining positions with variables that appear in the target functions
            remaining_vars = hvdd_vars if len(hvdd_vars) > len(lvdd_vars) else lvdd_vars
            while len(base_mapping) < num_inputs:
                base_mapping.append(remaining_vars[0])
            
            num_mappings = len(list(itertools.permutations(base_mapping)))
            print(f"\rTrying gate {gate} ({gate_count}/{total_gates}) with {num_mappings} possible mappings...")
            
            # Generate and test permutations one at a time
            seen_mappings = set()  # To avoid duplicate mappings
            for mapping in itertools.permutations(base_mapping):
                mappings_tested += 1
                
                mapping_key = tuple(mapping)
                if mapping_key not in seen_mappings:
                    seen_mappings.add(mapping_key)
                    
                    # Show progress (update every 1000 mappings)
                    if mappings_tested % 1000 == 0:
                        print(f"\rProgress: Gate {gate} ({gate_count}/{total_gates}) - Mappings tested: {mappings_tested}/{num_mappings}", end="")
                    
                    # Get truth tables for this gate and mapping
                    hvdd_gate_table = self._get_gate_truth_table(hvdd_func, list(mapping), all_vars)
                    lvdd_gate_table = self._get_gate_truth_table(lvdd_func, list(mapping), all_vars)
                    
                    # Check if tables match
                    if hvdd_gate_table == hvdd_table and lvdd_gate_table == lvdd_table:
                        print(f"\nFound matching circuit with gate {gate}!")
                        print(f"Input mapping: {list(mapping)}")
                        print(f"HVDD function: {hvdd_func}")
                        print(f"LVDD function: {lvdd_func}")
                        results.append({
                            'gate': gate,
                            'input_map': list(mapping)
                        })
                        if len(results) >= max_results:
                            print("\nReached maximum number of results.")
                            return results
        
        print("\nEnumeration complete.")
        return results

    def _create_circuit(self, gate_name: str, input_mapping: List[str]) -> Circuit:
        """Create a Circuit object from a gate and its input mapping"""
        # Create input signals
        input_signals = set()
        for var in input_mapping:
            signal = DualRail(var.lower())
            input_signals.add(signal)
        
        # Create output signal
        output_signal = DualRail("z")
        
        # Create the gate
        gate = Gate(
            name=gate_name,
            inputs=[DualRail(var.lower()) for var in input_mapping],
            output=output_signal,
            transistor_count=self.gates[gate_name]['transistors'],
            voltage_level="POLY",
            function=f"{self.gates[gate_name]['hvdd']}__{self.gates[gate_name]['lvdd']}",
            num_inputs=len(input_mapping)
        )
        
        # Create circuit graph
        graph = nx.DiGraph()
        
        # Add input nodes
        for signal in input_signals:
            graph.add_node(signal.name, type='input')
        
        # Add gate node
        gate_node = f"{gate_name}_{output_signal.name}"
        graph.add_node(gate_node, type='gate', gate_type=gate_name)
        
        # Add connections
        for signal in input_signals:
            graph.add_edge(signal.name, gate_node)
        graph.add_edge(gate_node, output_signal.name)
        
        return Circuit(
            gates=[gate],
            inputs=input_signals,
            outputs={output_signal},
            graph=graph,
            voltage_level="POLY"
        )

def generate_verilog_netlist(circuit, circuit_num, output_dir, hvdd_expr, lvdd_expr):
    """Generate a Verilog netlist for the given circuit."""
    netlist = []
    
    # Add header comments
    netlist.append(f"// Original boolean function: {hvdd_expr}__{lvdd_expr}")
    netlist.append(f"// Circuit implementation using {len(circuit.gates)} gates")
    netlist.append(f"// Total transistors: {circuit.total_transistors()}")
    netlist.append("")
    
    # Module declaration
    netlist.append(f"module circuit_{circuit_num}(")
    
    # Port list - include vdd_sel and sleep
    netlist.append("    vdd_sel,")
    netlist.append("    sleep,")
    inputs = sorted(list(circuit.inputs))  # Sort inputs for consistent ordering
    for i, input_signal in enumerate(inputs):
        netlist.append(f"    {input_signal.name}" + ("," if i < len(inputs)-1 or circuit.outputs else ""))
    if circuit.outputs:
        netlist.append("    z")  # Use z instead of out to match MTNCL gates
    netlist.append(");")
    netlist.append("")
    
    # Port declarations
    netlist.append("    input vdd_sel;  // 1 for HVDD function, 0 for LVDD function")
    netlist.append("    input sleep;    // Sleep signal for NCL operation")
    for input_signal in inputs:
        netlist.append(f"    input {input_signal.name};")
    if circuit.outputs:
        netlist.append("    output z;")  # Use z instead of out
    netlist.append("")
    
    # Internal wire declarations
    if len(circuit.gates) > 1:
        netlist.append("    // Internal wires")
        for i in range(len(circuit.gates)-1):  # -1 because last gate connects directly to z
            netlist.append(f"    wire w{i};")
        netlist.append("")
    
    # Gate instances
    netlist.append("    // Gate instances")
    for i, gate in enumerate(circuit.gates):
        netlist.append(f"    // {gate.name} implementing {gate.function}")
        netlist.append(f"    {gate.name} g{i} (")
        netlist.append("        .vdd_sel(vdd_sel),")
        netlist.append("        .s(sleep),")
        
        # Connect inputs in standard alphabetical order
        for j, input_signal in enumerate(gate.inputs):
            port_name = chr(ord('a') + j)  # a, b, c, d...
            if i == 0:
                # First gate connects to primary inputs
                netlist.append(f"        .{port_name}({input_signal.name})" + ("," if j < len(gate.inputs)-1 else ""))
            else:
                # Other gates connect to previous gate's output
                netlist.append(f"        .{port_name}(w{i-1})" + ("," if j < len(gate.inputs)-1 else ""))
        
        # Connect output
        if i == len(circuit.gates)-1:
            # Last gate connects to primary output
            netlist.append("        .z(z)")  # Use z for output
        else:
            # Other gates connect to internal wires
            netlist.append(f"        .z(w{i})")
        netlist.append("    );")
        netlist.append("")
    
    netlist.append("endmodule")
    
    # Write netlist to file
    output_file = os.path.join(output_dir, f"circuit_{circuit_num}.v")
    with open(output_file, "w") as f:
        f.write("\n".join(netlist))

def simplify_node_expr(expr):
    """Clean up node expressions by removing Node class references and cleaning up variable references."""
    # Remove Node class references and restructure expression format
    expr = re.sub(r"Node\(type='([^']+)', value='([^']+)', children=\[([^\]]+)\]\)", r'\2 \1 \3', expr)
    
    # Clean up variable references
    expr = re.sub(r"'VAR', [^)]*'([A-Z])'", r'\1', expr)
    expr = re.sub(r"VAR None", "", expr)
    expr = re.sub(r"children=\[\]", "", expr)
    expr = re.sub(r"value=", "", expr)
    
    # Replace operation symbols with logical symbols
    expr = expr.replace('AND', '∧')
    expr = expr.replace('NOT', '¬')
    
    # Convert underscores to arrows for signal flow
    expr = expr.replace('_', '→')
    
    # Clean up extra spaces and quotes
    expr = re.sub(r'\s+', ' ', expr)
    expr = expr.replace("'", "")
    
    return expr.strip()

def generate_documentation(circuits: List[Circuit], hvdd_expr: str, lvdd_expr: str) -> str:
    """Generate documentation for the circuits."""
    doc = "# Circuit Documentation\n\n"
    
    # Boolean Functions section
    doc += "## Boolean Functions\n"
    doc += f"- HVDD: {hvdd_expr}\n"
    doc += f"- LVDD: {lvdd_expr}\n\n"
    
    # Circuit Implementations section
    doc += "## Circuit Implementations\n\n"
    
    if not circuits:
        doc += "*No valid circuits found.*\n\n"
        return doc
    
    # Table headers
    headers = ["Circuit", "Transistors", "Gates", "Functions", "Inputs", "Output"]
    rows = []
    
    # Collect data for each circuit
    for i, circuit in enumerate(circuits, 1):
        total_transistors = sum(gate.transistor_count for gate in circuit.gates)
        gates = ", ".join(f"{gate.name}" for gate in circuit.gates)
        functions = ", ".join(f"{gate.function}" for gate in circuit.gates)
        inputs = ", ".join(str(s) for s in sorted(circuit.inputs))
        
        # Simplify the output expression
        outputs = list(circuit.outputs)  # Convert set to list
        output_str = ""
        if outputs:
            output = outputs[0]  # Get first output
            output_str = simplify_node_expr(output.name)
        
        rows.append([
            f"Circuit {i}",
            total_transistors,
            gates,
            functions,
            inputs,
            output_str
        ])
    
    # Generate table using tabulate
    doc += tabulate(rows, headers=headers, tablefmt="pipe") + "\n\n"
    
    # Circuit Details section
    doc += "## Circuit Details\n\n"
    for i, circuit in enumerate(circuits, 1):
        doc += f"### Circuit {i}\n\n"
        doc += "#### Gate Connections\n"
        for j, gate in enumerate(circuit.gates):
            doc += f"- Gate {j} ({gate.name}):\n"
            doc += f"  - Type: {gate.function}\n"
            doc += f"  - Transistors: {gate.transistor_count}\n"
        doc += "\n"
    
    return doc

def save_netlists(hvdd_expr: str, lvdd_expr: str, circuits: List[Circuit]) -> str:
    """Save netlists and documentation for the circuits."""
    # Create output directory with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"netlists_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate documentation
    doc = generate_documentation(circuits, hvdd_expr, lvdd_expr)
    
    # Save documentation
    with open(os.path.join(output_dir, "README.md"), "w") as f:
        f.write(doc)
    
    # Generate and save netlists
    for i, circuit in enumerate(circuits, 1):
        generate_verilog_netlist(circuit, i, output_dir, hvdd_expr, lvdd_expr)
    
    return output_dir

def test():
    """Test the circuit enumeration with various cases that match our available gates:
    - th12m_th22m: 2-input OR vs 2-input AND
    - th13m_th23m: 3-input OR vs 2-of-3
    - th13m_th33m: 3-input OR vs 3-input AND
    - th33w2m_th33m: 3-input weighted threshold vs 3-input AND
    - th23m_th33m: 2-of-3 vs 3-input AND
    - th34m_th44m: 3-of-4 vs 4-input AND
    - th24w22m_th24w2m: 2-of-4 weighted vs 2-of-4 weighted
    """
    test_cases = [
        # Simple 2-input cases
        ("a|b", "a&b", "2-input OR vs AND (th12m_th22m)"),
        
        # 3-input cases
        ("a|b|c", "a&b&c", "3-input OR vs AND (th13m_th33m)"),
        ("(a&b)|(b&c)|(c&a)", "a&b&c", "2-of-3 vs AND (th23m_th33m)"),
        
        # 4-input cases
        ("(a&b&c)|(b&c&d)|(c&d&a)|(d&a&b)", "a&b&c&d", "3-of-4 vs AND (th34m_th44m)")
    ]
    
    for hvdd_expr, lvdd_expr, description in test_cases:
        print("\n" + "=" * 80)
        print(f"Testing {description}:")
        print(f"HVDD: {hvdd_expr}")
        print(f"LVDD: {lvdd_expr}")
        print("=" * 80 + "\n")
        
        enumerator = CircuitEnumerator()
        results = enumerator.enumerate_all(hvdd_expr, lvdd_expr)
        
        # Convert results to circuits
        circuits = []
        for result in results:
            circuit = enumerator._create_circuit(result['gate'], result['input_map'])
            circuits.append(circuit)
        
        print(f"\nFound {len(circuits)} polymorphic circuit implementations:")
        for i, circuit in enumerate(circuits, 1):
            print(f"\nCircuit {i} details:")
            print(f"Gate: {circuit.gates[0].name}")
            print(f"Input mapping: {[s.name for s in circuit.inputs]}")
            print(f"Transistor count: {circuit.total_transistors()}")
        
        # Save netlists and documentation
        if circuits:
            output_dir = save_netlists(hvdd_expr, lvdd_expr, circuits)
            print(f"\nNetlists and documentation saved to: {output_dir}")
        else:
            print("\nNo circuits found, skipping netlist generation.")
        
        input("Press Enter to continue to next test case...")

if __name__ == "__main__":
    test()
