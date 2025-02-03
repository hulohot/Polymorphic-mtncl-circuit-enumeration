from dataclasses import dataclass
from typing import List, Set, Optional

@dataclass(frozen=True)
class DualRail:
    name: str
    rail0: str = None
    rail1: str = None
    
    def __post_init__(self):
        # Use object.__setattr__ since the class is frozen
        if self.rail0 is None:
            object.__setattr__(self, 'rail0', f"{self.name}_rail0")
        if self.rail1 is None:
            object.__setattr__(self, 'rail1', f"{self.name}_rail1")
            
    def __hash__(self):
        return hash((self.name, self.rail0, self.rail1))
        
    def __eq__(self, other):
        if not isinstance(other, DualRail):
            return False
        return (self.name == other.name and 
                self.rail0 == other.rail0 and 
                self.rail1 == other.rail1)
                
    def __lt__(self, other):
        if not isinstance(other, DualRail):
            return NotImplemented
        return self.name < other.name
        
    def __str__(self):
        return self.name

@dataclass
class Gate:
    """Represents a polymorphic MTNCL gate"""
    name: str
    inputs: List[DualRail]  
    output: DualRail
    transistor_count: int
    voltage_level: str  # "HVDD", "LVDD", or "POLY"
    function: str  # The function being implemented (format: "hvdd_func__lvdd_func")
    num_inputs: int  # Number of inputs the gate supports

@dataclass
class PolymorphicGate:
    """Represents a polymorphic MTNCL gate"""
    name: str
    inputs: List[DualRail]
    output: DualRail
    transistor_count: int
    hvdd_function: str
    lvdd_function: str