library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

-- Basic MTNCL Gates

-- TH12 (2-input OR gate)
entity TH12 is
    Port ( A : in  STD_LOGIC;
           B : in  STD_LOGIC;
           Z : out STD_LOGIC);
end TH12;

architecture Behavioral of TH12 is
begin
    Z <= A or B;
end Behavioral;

-- TH22 (2-input AND gate)
entity TH22 is
    Port ( A : in  STD_LOGIC;
           B : in  STD_LOGIC;
           Z : out STD_LOGIC);
end TH22;

architecture Behavioral of TH22 is
begin
    Z <= A and B;
end Behavioral;

-- THXOR (2-input XOR gate)
entity THXOR is
    Port ( A : in  STD_LOGIC;
           B : in  STD_LOGIC;
           Z : out STD_LOGIC);
end THXOR;

architecture Behavioral of THXOR is
begin
    Z <= A xor B;
end Behavioral;

-- TH13 (3-input OR gate)
entity TH13 is
    Port ( A : in  STD_LOGIC;
           B : in  STD_LOGIC;
           C : in  STD_LOGIC;
           Z : out STD_LOGIC);
end TH13;

architecture Behavioral of TH13 is
begin
    Z <= A or B or C;
end Behavioral;

-- TH33 (3-input AND gate)
entity TH33 is
    Port ( A : in  STD_LOGIC;
           B : in  STD_LOGIC;
           C : in  STD_LOGIC;
           Z : out STD_LOGIC);
end TH33;

architecture Behavioral of TH33 is
begin
    Z <= A and B and C;
end Behavioral;

-- TH23 (2-of-3 threshold gate)
entity TH23 is
    Port ( A : in  STD_LOGIC;
           B : in  STD_LOGIC;
           C : in  STD_LOGIC;
           Z : out STD_LOGIC);
end TH23;

architecture Behavioral of TH23 is
begin
    Z <= (A and B) or (B and C) or (A and C);
end Behavioral; 