"""
Polymorphic circuit generator for MTNCL circuits.
Handles generation of dual-function circuits using polymorphic gates.
"""

from typing import Dict, List, Optional, Tuple
from .circuit_generator import CircuitGenerator

class PolymorphicCircuitGenerator:
    """Generates polymorphic MTNCL circuits that implement different functions for HVDD and LVDD."""
    
    def __init__(self, gates_dict: Dict, hvdd_equation: str, lvdd_equation: str):
        """
        Initialize the polymorphic circuit generator.
        
        Args:
            gates_dict: Dictionary of available gates (both basic and polymorphic)
            hvdd_equation: Boolean equation for HVDD operation
            lvdd_equation: Boolean equation for LVDD operation
        """
        self.gates_dict = gates_dict
        self.hvdd_equation = hvdd_equation
        self.lvdd_equation = lvdd_equation
        
        # Create separate generators for HVDD and LVDD
        self.hvdd_generator = CircuitGenerator(gates_dict, hvdd_equation)
        self.lvdd_generator = CircuitGenerator(gates_dict, lvdd_equation)
        
        # Map of basic gate combinations to polymorphic gates
        self.polymorphic_map = {
            ('th12', 'th22'): 'th12m_th22m',
            ('th13', 'th23'): 'th13m_th23m',
            ('th13', 'th33'): 'th13m_th33m',
            ('th23', 'th33'): 'th23m_th33m',
            ('th34', 'th44'): 'th34m_th44m',
            ('th33w2', 'th33'): 'th33w2m_th33m',
            ('thxor0', 'th34w3'): 'thxor0m_th34w3m',
            ('th24w22', 'th24w2'): 'th24w22m_th24w2m',
            ('th54w322', 'th44w22'): 'th54w322m_th44w22m'
        }

    def generate_circuits(self) -> List[Dict]:
        """
        Generate polymorphic circuits that implement both HVDD and LVDD functions.
        
        Returns:
            List of circuit implementations using polymorphic gates
        """
        # Generate individual circuits
        hvdd_circuits = self.hvdd_generator.generate_circuits()
        lvdd_circuits = self.lvdd_generator.generate_circuits()
        
        polymorphic_circuits = []
        
        # Try to match circuits that can be implemented with polymorphic gates
        for hvdd_circuit in hvdd_circuits:
            for lvdd_circuit in lvdd_circuits:
                if polymorphic_impl := self._find_polymorphic_implementation(hvdd_circuit, lvdd_circuit):
                    polymorphic_circuits.append(polymorphic_impl)
        
        return polymorphic_circuits

    def _find_polymorphic_implementation(self, hvdd_circuit: Dict, lvdd_circuit: Dict) -> Optional[Dict]:
        """
        Find a polymorphic implementation that can realize both circuits.
        
        Args:
            hvdd_circuit: Circuit implementation for HVDD
            lvdd_circuit: Circuit implementation for LVDD
            
        Returns:
            Dictionary describing the polymorphic implementation if found, None otherwise
        """
        # Check if circuits have compatible structure
        if not self._are_circuits_compatible(hvdd_circuit, lvdd_circuit):
            return None
            
        # Map gates to polymorphic equivalents
        polymorphic_gates = []
        for hvdd_gate, lvdd_gate in zip(hvdd_circuit['gates'], lvdd_circuit['gates']):
            poly_gate = self._find_polymorphic_gate(hvdd_gate['type'], lvdd_gate['type'])
            if not poly_gate:
                return None
            polymorphic_gates.append({
                'type': poly_gate,
                'inputs': hvdd_gate['inputs'],  # Input connections should be identical
                'output': hvdd_gate['output']
            })
            
        return {
            'gates': polymorphic_gates,
            'inputs': hvdd_circuit['inputs'],
            'outputs': hvdd_circuit['outputs'],
            'hvdd_function': self.hvdd_equation,
            'lvdd_function': self.lvdd_equation
        }

    def _are_circuits_compatible(self, hvdd_circuit: Dict, lvdd_circuit: Dict) -> bool:
        """Check if two circuits have compatible structure for polymorphic implementation."""
        # Must have same number of gates
        if len(hvdd_circuit['gates']) != len(lvdd_circuit['gates']):
            return False
            
        # Must have same inputs and outputs
        if (hvdd_circuit['inputs'] != lvdd_circuit['inputs'] or 
            hvdd_circuit['outputs'] != lvdd_circuit['outputs']):
            return False
            
        # Check that gate connections match
        for hvdd_gate, lvdd_gate in zip(hvdd_circuit['gates'], lvdd_circuit['gates']):
            if (hvdd_gate['inputs'] != lvdd_gate['inputs'] or 
                hvdd_gate['output'] != lvdd_gate['output']):
                return False
                
        return True

    def _find_polymorphic_gate(self, hvdd_type: str, lvdd_type: str) -> Optional[str]:
        """Find a polymorphic gate that implements both HVDD and LVDD functions."""
        # Remove timing variants (e.g., 'm' suffix) for matching
        hvdd_base = hvdd_type.lower().rstrip('m')
        lvdd_base = lvdd_type.lower().rstrip('m')
        
        # Check direct match
        if (hvdd_base, lvdd_base) in self.polymorphic_map:
            return self.polymorphic_map[(hvdd_base, lvdd_base)]
            
        # Check reverse match
        if (lvdd_base, hvdd_base) in self.polymorphic_map:
            return self.polymorphic_map[(lvdd_base, hvdd_base)]
            
        return None 