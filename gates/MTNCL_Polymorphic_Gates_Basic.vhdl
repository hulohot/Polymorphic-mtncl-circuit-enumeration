library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

-- Basic MTNCL Polymorphic Gates

-- TH54w322m_TH44w22m (Polymorphic threshold gate)
entity TH54w322m_TH44w22m is
    Port ( vdd_sel : in  STD_LOGIC;
           A : in  STD_LOGIC;
           B : in  STD_LOGIC;
           C : in  STD_LOGIC;
           D : in  STD_LOGIC;
           S : in  STD_LOGIC;
           Z : out  STD_LOGIC);
end TH54w322m_TH44w22m;

architecture Behavioral of TH54w322m_TH44w22m is
begin
    process(vdd_sel, A, B, C, D, S)
    begin
        if S = '1' then
            Z <= '0';
        elsif vdd_sel = '1' then
            -- TH54w322m (high voltage mode)
            Z <= '1' when (A = '1' and B = '1') or (A = '1' and C = '1') or (B = '1' and C = '1' and D = '1') else '0';
        else
            -- TH44w22m (low voltage mode)
            Z <= '1' when ((A = '1' and B = '1') or (A = '1' and C = '1' and D = '1') or (B = '1' and C = '1' and D = '1')) else '0';
        end if;
    end process;
end Behavioral;

-- TH13m_TH23m (Polymorphic threshold gate)
entity TH13m_TH23m is
    Port ( vdd_sel : in  STD_LOGIC;
           A : in  STD_LOGIC;
           B : in  STD_LOGIC;
           C : in  STD_LOGIC;
           S : in  STD_LOGIC;
           Z : out  STD_LOGIC);
end TH13m_TH23m;

architecture Behavioral of TH13m_TH23m is
begin
    process(vdd_sel, A, B, C, S)
    begin
        if S = '1' then
            Z <= '0';
        elsif vdd_sel = '1' then
            -- TH13m (high voltage mode)
            Z <= '1' when A = '1' or B = '1' or C = '1' else '0';
        else
            -- TH23m (low voltage mode)
            Z <= '1' when (A = '1' and B = '1') or (B = '1' and C = '1') or (C = '1' and A = '1') else '0';
        end if;
    end process;
end Behavioral;

-- TH13m_TH23w2m (Polymorphic threshold gate)
entity TH13m_TH23w2m is
    Port ( vdd_sel : in  STD_LOGIC;
           A : in  STD_LOGIC;
           B : in  STD_LOGIC;
           C : in  STD_LOGIC;
           S : in  STD_LOGIC;
           Z : out  STD_LOGIC);
end TH13m_TH23w2m;

architecture Behavioral of TH13m_TH23w2m is
begin
    process(vdd_sel, A, B, C, S)
    begin
        if S = '1' then
            Z <= '0';
        elsif vdd_sel = '1' then
            -- TH13m (high voltage mode)
            Z <= '1' when A = '1' or B = '1' or C = '1' else '0';
        else
            -- TH23w2m (low voltage mode)
            Z <= '1' when (A = '1') or (B = '1' and C = '1') else '0';
        end if;
    end process;
end Behavioral;

-- TH13m_TH33m (Polymorphic threshold gate)
entity TH13m_TH33m is
    Port ( vdd_sel : in  STD_LOGIC;
           A : in  STD_LOGIC;
           B : in  STD_LOGIC;
           C : in  STD_LOGIC;
           S : in  STD_LOGIC;
           Z : out  STD_LOGIC);
end TH13m_TH33m;

architecture Behavioral of TH13m_TH33m is
begin
    process(vdd_sel, A, B, C, S)
    begin
        if S = '1' then
            Z <= '0';
        elsif vdd_sel = '1' then
            -- TH13m (high voltage mode)
            Z <= '1' when A = '1' or B = '1' or C = '1' else '0';
        else
            -- TH33m (low voltage mode)
            Z <= '1' when (A = '1' and B = '1' and C = '1') else '0';
        end if;
    end process;
end Behavioral;

-- TH33w2m_TH33m (Polymorphic threshold gate)
entity TH33w2m_TH33m is
    Port ( vdd_sel : in  STD_LOGIC;
           A : in  STD_LOGIC;
           B : in  STD_LOGIC;
           C : in  STD_LOGIC;
           S : in  STD_LOGIC;
           Z : out  STD_LOGIC);
end TH33w2m_TH33m;

architecture Behavioral of TH33w2m_TH33m is
begin
    process(vdd_sel, A, B, C, S)
    begin
        if S = '1' then
            Z <= '0';
        elsif vdd_sel = '1' then
            -- TH33w2m (high voltage mode)
            Z <= '1' when (A = '1' and B = '1') or (A = '1' and C = '1') else '0';
        else
            -- TH33m (low voltage mode)
            Z <= '1' when (A = '1' and B = '1' and C = '1') else '0';
        end if;
    end process;
end Behavioral;

-- TH12m_TH22m (Polymorphic threshold gate)
entity TH12m_TH22m is
    Port ( vdd_sel : in  STD_LOGIC;
           A : in  STD_LOGIC;
           B : in  STD_LOGIC;
           S : in  STD_LOGIC;
           Z : out  STD_LOGIC);
end TH12m_TH22m;

architecture Behavioral of TH12m_TH22m is
begin
    process(vdd_sel, A, B, S)
    begin
        if S = '1' then
            Z <= '0';
        elsif vdd_sel = '1' then
            -- TH12m (high voltage mode)
            Z <= '1' when A = '1' or B = '1' else '0';
        else
            -- TH22m (low voltage mode)
            Z <= '1' when (A = '1' and B = '1') else '0';
        end if;
    end process;
end Behavioral;

-- TH23m_TH33m (Polymorphic threshold gate)
entity TH23m_TH33m is
    Port ( vdd_sel : in  STD_LOGIC;
           A : in  STD_LOGIC;
           B : in  STD_LOGIC;
           C : in  STD_LOGIC;
           S : in  STD_LOGIC;
           Z : out  STD_LOGIC);
end TH23m_TH33m;

architecture Behavioral of TH23m_TH33m is
begin
    process(vdd_sel, A, B, C, S)
    begin
        if S = '1' then
            Z <= '0';
        elsif vdd_sel = '1' then
            -- TH23m (high voltage mode)
            Z <= '1' when (A = '1' and B = '1') or (B = '1' and C = '1') or (C = '1' and A = '1') else '0';
        else
            -- TH33m (low voltage mode)
            Z <= '1' when (A = '1' and B = '1' and C = '1') else '0';
        end if;
    end process;
end Behavioral;

-- TH34m_TH44m (Polymorphic threshold gate)
entity TH34m_TH44m is
    Port ( vdd_sel : in  STD_LOGIC;
           A : in  STD_LOGIC;
           B : in  STD_LOGIC;
           C : in  STD_LOGIC;
           D : in  STD_LOGIC;
           S : in  STD_LOGIC;
           Z : out  STD_LOGIC);
end TH34m_TH44m;

architecture Behavioral of TH34m_TH44m is
begin
    process(vdd_sel, A, B, C, D, S)
    begin
        if S = '1' then
            Z <= '0';
        elsif vdd_sel = '1' then
            -- TH34m (high voltage mode)
            Z <= '1' when ((A = '1' and B = '1' and C = '1') or 
                           (A = '1' and C = '1' and D = '1') or 
                           (A = '1' and B = '1' and D = '1') or 
                           (B = '1' and C = '1' and D = '1')) else '0';
        else
            -- TH44m (low voltage mode)
            Z <= '1' when (A = '1' and B = '1' and C = '1' and D = '1') else '0';
        end if;
    end process;
end Behavioral;

-- THXOR0m_TH34w3m (Polymorphic threshold gate)
entity THXOR0m_TH34w3m is
    Port ( vdd_sel : in  STD_LOGIC;
           A : in  STD_LOGIC;
           B : in  STD_LOGIC;
           C : in  STD_LOGIC;
           D : in  STD_LOGIC;
           S : in  STD_LOGIC;
           Z : out  STD_LOGIC);
end THXOR0m_TH34w3m;

architecture Behavioral of THXOR0m_TH34w3m is
begin
    process(vdd_sel, A, B, C, D, S)
    begin
        if S = '1' then
            Z <= '0';
        elsif vdd_sel = '1' then
            -- THXOR0m (high voltage mode)
            Z <= '1' when (A = '1' and B = '1') or (C = '1' and D = '1') else '0';
        else
            -- TH34w3m (low voltage mode)
            Z <= '1' when (A = '1' or (B = '1' and C = '1' and D = '1')) else '0';
        end if;
    end process;
end Behavioral;

-- TH24w22m_TH24w2m (Polymorphic threshold gate)
entity TH24w22m_TH24w2m is
    Port ( vdd_sel : in  STD_LOGIC;
           A : in  STD_LOGIC;
           B : in  STD_LOGIC;
           C : in  STD_LOGIC;
           D : in  STD_LOGIC;
           S : in  STD_LOGIC;
           Z : out  STD_LOGIC);
end TH24w22m_TH24w2m;

architecture Behavioral of TH24w22m_TH24w2m is
begin
    process(vdd_sel, A, B, C, D, S)
    begin
        if S = '1' then
            Z <= '0';
        elsif vdd_sel = '1' then
            -- TH24w22m (high voltage mode)
            Z <= '1' when (A = '1' or B = '1' or (C = '1' and D = '1')) else '0';
        else
            -- TH24w2m (low voltage mode)
            Z <= '1' when (A = '1' or (B = '1' and C = '1') or 
                          (B = '1' and D = '1') or (C = '1' and D = '1')) else '0';
        end if;
    end process;
end Behavioral; 