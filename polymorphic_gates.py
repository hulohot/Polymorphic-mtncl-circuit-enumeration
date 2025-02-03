from mtncl_types import Gate, DualRail

# The following are the available standard MTNCL gates
# Key is the gate name, value is the boolean function

STANDARD_MTNCL_GATES = {
    "TH12": "A | B",
    "TH22": "A & B",
    "TH13": "A | B | C",
    "TH23": "(A & B) | (A & C) | (B & C)",
    "TH33": "A & B & C",
    "TH23w2": "A | (B & C)",
    "TH33w2": "(A & B) | (A & C)",
    "TH14": "A | B | C | D",
    "TH24": "(A & B) | (A & C) | (A & D) | (B & C) | (B & D) | (C & D)",
    "TH34": "(A & B & C) | (A & B & D) | (A & C & D) | (B & C & D)",
    "TH44": "A & B & C & D",
    "TH24w2": "A | (B & C) | (B & D) | (C & D)",
    "TH34w2": "(A & B) | (A & C) | (A & D) | (B & C & D)",
    "TH44w2": "(A & B & C) | (A & B & D) | (A & C & D)",
    "TH34w3": "A | (B & C & D)",
    "TH44w3": "(A & B) | (A & C) | (A & D)",
    "TH24w22": "A | B | (C & D)",
    "TH34w22": "(A & B) | (A & C) | (A & D) | (B & C) | (B & D)",
    "TH44w22": "(A & B & C) | (A & B & D) | (A & C & D) | (B & C)",
    "TH54w22": "A & B & C | A & B & D",
    "TH34w32": "A | B | (C & D)",
    "TH54w32": "A & B | A & C & D | B & C & D",
    "TH44w322": "A & B | A & C | A & D | B & C",
    "TH54w322": "A & B & C | A & B & D | C & D",
    "THxor0": "A & B | C & D",
    "THand0": "A & B | B & C | A & D",
    "TH24comp": "A & C | B & C | A & D | B & D"
}

# The following are the available polymorphic gates
POLYMORPHIC_MTNCL_GATES = {
    'th12m_th22m': {
        'hvdd': 'a | b',           # OR at HVDD
        'lvdd': 'a & b',           # AND at LVDD
        'inputs': ['a', 'b'],
        'transistors': 14
    },
    'th13m_th23m': {
        'hvdd': 'a | b | c',       # OR at HVDD
        'lvdd': '(a & b) | (b & c) | (c & a)',  # 2-of-3 at LVDD
        'inputs': ['a', 'b', 'c'],
        'transistors': 16
    },
    'th13m_th33m': {
        'hvdd': 'a | b | c',       # OR at HVDD
        'lvdd': 'a & b & c',       # AND at LVDD
        'inputs': ['a', 'b', 'c'],
        'transistors': 16
    },
    'th33w2m_th33m': {
        'hvdd': '(a & b) | (a & c)',  # Weighted threshold at HVDD
        'lvdd': 'a & b & c',          # AND at LVDD
        'inputs': ['a', 'b', 'c'],
        'transistors': 16
    },
    'th23m_th33m': {
        'hvdd': '(a & b) | (b & c) | (c & a)',  # 2-of-3 at HVDD
        'lvdd': 'a & b & c',                     # AND at LVDD
        'inputs': ['a', 'b', 'c'],
        'transistors': 16
    },
    'th34m_th44m': {
        'hvdd': '(a & b & c) | (a & c & d) | (a & b & d) | (b & c & d)',  # 3-of-4 at HVDD
        'lvdd': 'a & b & c & d',                                           # AND at LVDD
        'inputs': ['a', 'b', 'c', 'd'],
        'transistors': 18
    },
    'th24w22m_th24w2m': {
        'hvdd': 'a | b | (c & d)',                                         # Weighted threshold at HVDD
        'lvdd': 'a | (b & c) | (b & d) | (c & d)',                        # Weighted threshold at LVDD
        'inputs': ['a', 'b', 'c', 'd'],
        'transistors': 18
    }
}

# Convert the above dictionary into Gate objects
POLYMORPHIC_GATES = []
for name, info in POLYMORPHIC_MTNCL_GATES.items():
    POLYMORPHIC_GATES.append(
        Gate(
            name=name,
            inputs=info['inputs'],
            output=DualRail('z'),  # All gates have output named 'z'
            transistor_count=info['transistors'],
            voltage_level="POLY",
            function=f"{info['hvdd']}__{info['lvdd']}",
            num_inputs=len(info['inputs'])
        )
    )
