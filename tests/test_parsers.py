import pytest
from mtncl_generator.parsers.boolean_parser import BooleanParser, TokenType, ASTNode
from mtncl_generator.parsers.vhdl_parser import VHDLParser, GateInfo, Port

def test_boolean_parser_simple():
    """Test parsing of simple boolean expressions."""
    parser = BooleanParser("A + B")
    ast = parser.parse()
    
    assert ast.type == TokenType.OR
    assert ast.left.type == TokenType.VARIABLE
    assert ast.left.value == "A"
    assert ast.right.type == TokenType.VARIABLE
    assert ast.right.value == "B"

def test_boolean_parser_complex():
    """Test parsing of complex boolean expressions."""
    parser = BooleanParser("(A + B) & !(C + D)")
    ast = parser.parse()
    
    assert ast.type == TokenType.AND
    assert ast.left.type == TokenType.OR
    assert ast.right.type == TokenType.NOT

def test_boolean_parser_invalid():
    """Test parsing of invalid boolean expressions."""
    with pytest.raises(ValueError):
        parser = BooleanParser("A + + B")
        parser.parse()
    
    with pytest.raises(ValueError):
        parser = BooleanParser("(A + B")
        parser.parse()

def test_boolean_parser_variables():
    """Test extraction of variable names."""
    parser = BooleanParser("(A + B) & (C + D)")
    parser._tokenize()  # Call tokenize directly to populate tokens
    variables = parser.get_variables()
    assert variables == {"A", "B", "C", "D"}

def test_vhdl_parser_basic():
    """Test parsing of basic VHDL gate definitions."""
    vhdl_content = """
    entity TH12 is
        Port ( A : in  STD_LOGIC;
               B : in  STD_LOGIC;
               Z : out STD_LOGIC);
    end TH12;
    """
    
    with open("test_gate.vhdl", "w") as f:
        f.write(vhdl_content)
    
    parser = VHDLParser(["test_gate.vhdl"])
    gates = parser.parse_gates()
    
    assert "TH12" in gates
    assert len(gates["TH12"].ports) == 3
    
    # Clean up
    import os
    os.remove("test_gate.vhdl")

def test_vhdl_parser_multiple_gates():
    """Test parsing of multiple gates from a single file."""
    vhdl_content = """
    entity TH12 is
        Port ( A : in  STD_LOGIC;
               B : in  STD_LOGIC;
               Z : out STD_LOGIC);
    end TH12;
    
    entity TH22 is
        Port ( A : in  STD_LOGIC;
               B : in  STD_LOGIC;
               Z : out STD_LOGIC);
    end TH22;
    """
    
    with open("test_gates.vhdl", "w") as f:
        f.write(vhdl_content)
    
    parser = VHDLParser(["test_gates.vhdl"])
    gates = parser.parse_gates()
    
    assert "TH12" in gates
    assert "TH22" in gates
    assert len(gates) == 2
    
    # Clean up
    import os
    os.remove("test_gates.vhdl")

def test_vhdl_parser_invalid():
    """Test parsing of invalid VHDL files."""
    vhdl_content = """
    entity TH12 is
        Port ( A : in  STD_LOGIC;
               B : in  STD_LOGIC;
               Z : out STD_LOGIC);
    -- Missing end statement
    """
    
    with open("invalid_gate.vhdl", "w") as f:
        f.write(vhdl_content)
    
    parser = VHDLParser(["invalid_gate.vhdl"])
    with pytest.raises(ValueError):
        parser.parse_gates()
    
    # Clean up
    import os
    os.remove("invalid_gate.vhdl")

def test_vhdl_parser_port_types():
    """Test parsing of different port types."""
    vhdl_content = """
    entity THComplex is
        Port ( A : in  STD_LOGIC;
               B : in  STD_LOGIC_VECTOR(3 downto 0);
               Z : out STD_LOGIC);
    end THComplex;
    """
    
    with open("complex_gate.vhdl", "w") as f:
        f.write(vhdl_content)
    
    parser = VHDLParser(["complex_gate.vhdl"])
    gates = parser.parse_gates()
    
    assert "THComplex" in gates
    ports = gates["THComplex"].ports
    assert any(p.port_type == "STD_LOGIC_VECTOR" for p in ports)
    
    # Clean up
    import os
    os.remove("complex_gate.vhdl") 