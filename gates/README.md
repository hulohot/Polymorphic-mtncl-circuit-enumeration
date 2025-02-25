# MTNCL Gate Definitions

This directory contains VHDL files with gate definitions for MTNCL (Multi-Threshold Null Convention Logic) circuits.

## Available Gate Files

### basic_gates.vhdl

This file contains simplified definitions of basic MTNCL gates without detailed timing information. These gates are used for regular (non-polymorphic) MTNCL circuit generation. The gates are defined with a simple behavioral architecture that implements the threshold logic function.

Gates included:
- TH12 (OR gate)
- TH22 (AND gate)
- TH13 (3-input OR gate)
- TH23 (2-of-3 threshold gate)
- TH33 (3-input AND gate)
- TH44 (4-input AND gate)
- TH24 (2-of-4 threshold gate)
- THXOR (XOR gate)
- Various weighted threshold gates (e.g., TH24w2, TH34w2)

### MTNCL_Polymorphic_Gates.vhd

This file contains detailed definitions of polymorphic MTNCL gates with precise timing information. These gates implement different functions depending on the supply voltage (HVDD or LVDD). The gates are defined with detailed timing specifications in picoseconds.

Gates included:
- TH54w322m_TH44w22m
- TH13m_TH23m
- TH13m_TH23w2m
- TH13m_TH33m
- TH33w2m_TH33m
- TH12m_TH22m
- TH23m_TH33m
- TH34m_TH44m
- THXOR0m_TH34w3m
- TH24w22m_TH24w2m

### MTNCL_Polymorphic_Gates_Basic.vhd

This file contains simplified definitions of polymorphic MTNCL gates without detailed timing information. These gates are functionally equivalent to those in MTNCL_Polymorphic_Gates.vhd but use a simpler behavioral architecture without specific timing delays.

## Gate Naming Convention

- **TH**: Threshold gate
- **Number**: Threshold value
- **Number after TH**: Number of inputs
- **w**: Weighted input (followed by input position and weight)
- **m**: Reset (sleep) capability
- **Polymorphic gates**: Named as HVDD_gate_LVDD_gate (e.g., TH12m_TH22m implements OR in HVDD mode and AND in LVDD mode)

## Usage

In the configuration files (config.json and polymorphic_config.json), specify which gate files to use:

```json
"gates_dir": [
    "gates/basic_gates.vhdl",
    "gates/MTNCL_Polymorphic_Gates_Basic.vhd"
]
```

For detailed timing information, use MTNCL_Polymorphic_Gates.vhd instead of MTNCL_Polymorphic_Gates_Basic.vhd. 