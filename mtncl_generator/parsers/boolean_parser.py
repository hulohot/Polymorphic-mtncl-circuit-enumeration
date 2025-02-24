from typing import List, Optional, Set
from dataclasses import dataclass
from enum import Enum, auto
import re

class TokenType(Enum):
    VARIABLE = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    XOR = auto()
    LPAREN = auto()
    RPAREN = auto()

@dataclass
class Token:
    type: TokenType
    value: str
    position: int

@dataclass
class ASTNode:
    type: TokenType
    value: Optional[str] = None
    left: Optional['ASTNode'] = None
    right: Optional['ASTNode'] = None

class BooleanParser:
    """Parser for boolean equations that creates an Abstract Syntax Tree."""
    
    def __init__(self, equation: str):
        """Initialize the boolean equation parser.
        
        Args:
            equation: String containing the boolean equation
        """
        self.equation = equation.strip()
        self.position = 0
        self.tokens: List[Token] = []

    def parse(self) -> ASTNode:
        """Parse the boolean equation and return its AST representation.
        
        Returns:
            Root node of the Abstract Syntax Tree
            
        Raises:
            ValueError: If the equation syntax is invalid
        """
        self._tokenize()
        return self._parse_expression()

    def get_variables(self) -> Set[str]:
        """Get all variable names used in the equation.
        
        Returns:
            Set of variable names
        """
        return {token.value for token in self.tokens if token.type == TokenType.VARIABLE}

    def _tokenize(self) -> None:
        """Convert the equation string into a list of tokens."""
        self.tokens = []
        self.position = 0
        
        while self.position < len(self.equation):
            char = self.equation[self.position]
            
            if char.isspace():
                self.position += 1
                continue
                
            if char.isalpha():
                self._tokenize_variable()
            elif char == '&' or char == '*':
                self.tokens.append(Token(TokenType.AND, '&', self.position))
                self.position += 1
            elif char == '|' or char == '+':
                self.tokens.append(Token(TokenType.OR, '|', self.position))
                self.position += 1
            elif char == '!':
                self.tokens.append(Token(TokenType.NOT, '!', self.position))
                self.position += 1
            elif char == '^':
                self.tokens.append(Token(TokenType.XOR, '^', self.position))
                self.position += 1
            elif char == '(':
                self.tokens.append(Token(TokenType.LPAREN, '(', self.position))
                self.position += 1
            elif char == ')':
                self.tokens.append(Token(TokenType.RPAREN, ')', self.position))
                self.position += 1
            else:
                raise ValueError(f"Invalid character '{char}' at position {self.position}")

    def _tokenize_variable(self) -> None:
        """Parse a variable name from the current position."""
        start = self.position
        while self.position < len(self.equation) and (
            self.equation[self.position].isalnum() or 
            self.equation[self.position] == '_'
        ):
            self.position += 1
        
        var_name = self.equation[start:self.position]
        self.tokens.append(Token(TokenType.VARIABLE, var_name, start))

    def _parse_expression(self, precedence: int = 0) -> ASTNode:
        """Parse an expression with operator precedence.
        
        Args:
            precedence: Current operator precedence level
            
        Returns:
            Root node of the parsed expression
        """
        if precedence == 0:
            return self._parse_or()
        elif precedence == 1:
            return self._parse_and()
        elif precedence == 2:
            return self._parse_xor()
        else:
            return self._parse_factor()

    def _parse_or(self) -> ASTNode:
        """Parse OR expressions."""
        left = self._parse_expression(1)
        
        while self.tokens and self.tokens[0].type == TokenType.OR:
            op_token = self.tokens.pop(0)
            right = self._parse_expression(1)
            left = ASTNode(type=op_token.type, left=left, right=right)
        
        return left

    def _parse_and(self) -> ASTNode:
        """Parse AND expressions."""
        left = self._parse_expression(2)
        
        while self.tokens and self.tokens[0].type == TokenType.AND:
            op_token = self.tokens.pop(0)
            right = self._parse_expression(2)
            left = ASTNode(type=op_token.type, left=left, right=right)
        
        return left

    def _parse_xor(self) -> ASTNode:
        """Parse XOR expressions."""
        left = self._parse_factor()
        
        while self.tokens and self.tokens[0].type == TokenType.XOR:
            op_token = self.tokens.pop(0)
            right = self._parse_factor()
            left = ASTNode(type=op_token.type, left=left, right=right)
        
        return left

    def _parse_factor(self) -> ASTNode:
        """Parse basic factors (variables, NOT expressions, parenthesized expressions)."""
        if not self.tokens:
            raise ValueError("Unexpected end of expression")
            
        token = self.tokens.pop(0)
        
        if token.type == TokenType.VARIABLE:
            return ASTNode(type=TokenType.VARIABLE, value=token.value)
        elif token.type == TokenType.NOT:
            factor = self._parse_factor()
            return ASTNode(type=TokenType.NOT, left=factor)
        elif token.type == TokenType.LPAREN:
            expr = self._parse_expression(0)
            if not self.tokens or self.tokens[0].type != TokenType.RPAREN:
                raise ValueError("Missing closing parenthesis")
            self.tokens.pop(0)  # Remove RPAREN
            return expr
        else:
            raise ValueError(f"Unexpected token {token.value} at position {token.position}")

    def validate(self) -> bool:
        """Validate the boolean equation syntax.
        
        Returns:
            True if the equation is valid, raises ValueError otherwise
        
        Raises:
            ValueError: If the equation syntax is invalid
        """
        try:
            self._tokenize()
            self._parse_expression()
            if self.tokens:  # Check if there are any remaining tokens
                raise ValueError("Unexpected tokens at end of expression")
            return True
        except Exception as e:
            raise ValueError(f"Invalid boolean equation: {str(e)}") 