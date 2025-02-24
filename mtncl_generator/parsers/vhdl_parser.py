from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import re
import logging

@dataclass
class Port:
    name: str
    direction: str  # 'in' or 'out'
    port_type: str  # e.g., 'STD_LOGIC'

@dataclass
class Delay:
    condition: str
    time: float  # in nanoseconds

@dataclass
class GateInfo:
    name: str
    ports: List[Port]
    delays: List[Delay]
    has_sleep: bool = False
    has_reset: bool = False
    description: Optional[str] = None

class VHDLParser:
    """Parser for VHDL files containing MTNCL gate definitions."""
    
    def __init__(self, vhdl_files: List[str]):
        """Initialize the VHDL parser.
        
        Args:
            vhdl_files: List of paths to VHDL files containing gate definitions
        """
        self.vhdl_files = vhdl_files
        self.gates: Dict[str, GateInfo] = {}
        self.logger = logging.getLogger(__name__)

    def parse_gates(self) -> Dict[str, GateInfo]:
        """Parse all VHDL files and extract gate information.
        
        Returns:
            Dictionary mapping gate names to their GateInfo objects
        
        Raises:
            FileNotFoundError: If a VHDL file cannot be found
            ValueError: If VHDL syntax is invalid
        """
        for file_path in self.vhdl_files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                self._parse_file_content(content)
            except FileNotFoundError:
                self.logger.error(f"VHDL file not found: {file_path}")
                raise
            except Exception as e:
                self.logger.error(f"Error parsing VHDL file {file_path}: {str(e)}")
                raise ValueError(f"Invalid VHDL syntax in {file_path}")
        
        return self.gates

    def _parse_file_content(self, content: str) -> None:
        """Parse the content of a single VHDL file.
        
        Args:
            content: String containing VHDL file content
        
        Raises:
            ValueError: If VHDL syntax is invalid
        """
        # Find all entity declarations and their architectures
        entity_pattern = r"entity\s+(\w+)\s+is\s+Port\s*\((.*?)\)\s*;\s*end\s+\1\s*;"
        arch_pattern = r"architecture\s+\w+\s+of\s+(\w+)\s+is\s+begin(.*?)end\s+\w+\s*;"
        
        entity_matches = list(re.finditer(entity_pattern, content, re.DOTALL | re.IGNORECASE))
        if not entity_matches:
            raise ValueError("No valid entity declarations found")
        
        arch_matches = re.finditer(arch_pattern, content, re.DOTALL | re.IGNORECASE)
        
        # Create a map of architectures by entity name
        arch_map = {match.group(1): match.group(2) for match in arch_matches}
        
        for match in entity_matches:
            gate_name = match.group(1)
            ports_str = match.group(2)
            
            # Parse ports
            ports = self._parse_ports(ports_str)
            if not ports:
                raise ValueError(f"No valid ports found in entity {gate_name}")
            
            # Check for sleep and reset signals
            has_sleep = any(p.name.lower() == 's' for p in ports)
            has_reset = any(p.name.lower() == 'rst' for p in ports)
            
            # Parse delays from architecture if available
            delays = []
            if gate_name in arch_map:
                delays = self._parse_delays(arch_map[gate_name])
            
            # Create GateInfo object
            gate_info = GateInfo(
                name=gate_name,
                ports=ports,
                delays=delays,
                has_sleep=has_sleep,
                has_reset=has_reset
            )
            
            self.gates[gate_name] = gate_info

    def _parse_ports(self, ports_str: str) -> List[Port]:
        """Parse port declarations from a VHDL entity.
        
        Args:
            ports_str: String containing port declarations
        
        Returns:
            List of Port objects
        """
        ports = []
        port_pattern = r"(\w+)\s*:\s*(in|out)\s+(\w+(?:_VECTOR)?(?:\s*\(\s*\d+\s+\w+\s+\d+\s*\))?)"
        
        for line in ports_str.split(';'):
            match = re.search(port_pattern, line, re.IGNORECASE)
            if match:
                port_type = match.group(3).strip().upper()
                # Extract base type without range for vector types
                if '(' in port_type:
                    port_type = port_type.split('(')[0].strip()
                port = Port(
                    name=match.group(1),
                    direction=match.group(2).lower(),
                    port_type=port_type
                )
                ports.append(port)
        
        return ports

    def _parse_delays(self, arch_str: str) -> List[Delay]:
        """Parse timing delays from architecture body.
        
        Args:
            arch_str: String containing architecture implementation
            
        Returns:
            List of Delay objects
        """
        delays = []
        delay_pattern = r"<=\s*'[01]'\s*after\s*(\d+)\s*ns"
        condition_pattern = r"if\s+(.*?)\s+then"
        
        # Find all delay assignments
        for line in arch_str.split('\n'):
            delay_match = re.search(delay_pattern, line)
            if delay_match:
                time = float(delay_match.group(1))
                
                # Try to find associated condition
                condition = "default"
                cond_match = re.search(condition_pattern, line)
                if cond_match:
                    condition = cond_match.group(1).strip()
                
                delays.append(Delay(condition=condition, time=time))
        
        return delays

    def get_gate_info(self, gate_name: str) -> Optional[GateInfo]:
        """Get information about a specific gate.
        
        Args:
            gate_name: Name of the gate to look up
        
        Returns:
            GateInfo object if gate exists, None otherwise
        """
        return self.gates.get(gate_name) 