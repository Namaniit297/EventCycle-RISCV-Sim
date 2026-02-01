EventCycle-RISCV-Sim  
A Unified Event-Driven Logic and Timing Simulation Framework for Digital Systems

────────────────────────────────────────────────────────────────────────────

§ Overview

EventCycle-RISCV-Sim is an academic, research-oriented event-driven digital logic
simulation framework developed to study, implement, and compare classical and
modern logic simulation techniques used in VLSI CAD and verification workflows.

The simulator supports multiple timing and execution paradigms including
unit-delay event-driven simulation, zero-delay levelized execution, and
threaded-code style simulation. These paradigms are widely discussed in standard
VLSI CAD literature and form the foundation of industrial logic simulators.

The framework is designed for coursework, research experimentation, and
architecture-level modeling, with particular suitability for RISC-V datapath and
control logic analysis.

────────────────────────────────────────────────────────────────────────────

§ Key Features

• Multiple event-driven logic simulation engines  
• Unit-delay and zero-delay timing semantics  
• Automatic static and dynamic hazard detection  
• Support for 2-valued and 3-valued logic models  
• Modular netlist, gate, and circuit abstractions  
• Intermediate state and time-step logging  
• Extensible architecture for future research extensions  

────────────────────────────────────────────────────────────────────────────

§ Simulation Engines Implemented

▸ Two-List Event-Driven Simulator

• Separate event queue and gate queue  
• Classical unit-delay simulation model  
• Accurate modeling of glitches and hazards  
• Intermediate time-step visibility  

▸ Single-List Event-Driven Simulator

• Unified event queue with explicit time markers  
• Immediate gate evaluation upon net updates  
• Event cancellation to reduce redundant scheduling  
• Balanced accuracy and performance  

▸ Single-List Gate-Driven Simulator

• Only gates are scheduled for execution  
• Net updates committed at discrete time boundaries  
• Duplicate gate execution prevented using flags  
• Reflects optimized industrial simulation strategies  

▸ Zero-Delay Levelized Simulator

• Pure functional simulation without timing delays  
• Gates evaluated using topological levelization  
• Iterative resolution of feedback paths  
• High performance for large combinational circuits  

▸ Threaded-Code Event-Driven Simulator

• Events represented as callable execution units  
• Stack-based execution without explicit queues  
• Mimics compiled-code logic simulation engines  
• Reduced scheduling overhead and improved locality  

────────────────────────────────────────────────────────────────────────────

§ Circuit Modeling

The simulator uses a structured and modular netlist representation:

• Nets represent wires with unique identifiers  
• Gates include AND, OR, NOT, NAND, NOR, XOR, XNOR  
• Fanout relationships automatically maintained  
• Primary inputs and outputs explicitly declared  

Example:

```python
circ = Circuit()
circ.set_primary_inputs(['A', 'B', 'C'])
circ.set_primary_outputs(['Y'])
circ.add_gate('AND', ['A', 'B'], 'X')
circ.add_gate('OR', ['X', 'C'], 'Y')
```

────────────────────────────────────────────────────────────────────────────

§ Logic Models Supported

2-valued logic  
Values: '0', '1'

3-valued logic  
Values: '0', '1', 'U' (unknown)

Three-valued logic enables conservative propagation, safe initialization
behavior, and improved hazard analysis.

────────────────────────────────────────────────────────────────────────────

§ Hazard Detection

The simulator automatically detects:

• Static hazards, where a signal temporarily toggles and returns to its original value  
• Dynamic hazards, where multiple transitions occur before final stabilization  

Hazards are reported for each simulation vector.

────────────────────────────────────────────────────────────────────────────

§ Outputs and Logging

Each simulation engine records:

• Final primary output values  
• Intermediate output states per time unit where applicable  
• Gate evaluation counts for performance analysis  
• Hazard detection reports  

These logs enable waveform reconstruction, debugging, and simulator comparison.

────────────────────────────────────────────────────────────────────────────

§ Project Structure

```
EventCycle-RISCV-Sim/
│
├── logic.py
├── gate.py
├── circuit.py
├── simulators/
│   ├── two_list.py
│   ├── single_list_event.py
│   ├── single_list_gate.py
│   ├── zero_delay.py
│   └── threaded.py
│
├── examples/
│   └── simple_circuit.py
│
├── README.md
└── LICENSE
```

The implementation may remain monolithic for clarity and instructional value.

────────────────────────────────────────────────────────────────────────────

§ Example Usage

```python
sim = TwoListSimulator(circ)
hazards = sim.simulate_vector({'A': '1', 'B': '1', 'C': '0'})
print(sim.output_log[-1], hazards)
```

────────────────────────────────────────────────────────────────────────────

§ Applications

• Logic simulation and verification  
• VLSI CAD education and laboratory experimentation  
• RISC-V datapath and control logic modeling  
• Event scheduling algorithm research  
• Microarchitecture exploration  

────────────────────────────────────────────────────────────────────────────

§ Future Extensions

• Sequential elements such as latches and flip-flops  
• Multi-delay gate timing models  
• VCD waveform generation  
• Switching activity and power estimation  
• Integration with RISC-V pipeline simulators  
• High-performance C or C++ backend  

────────────────────────────────────────────────────────────────────────────

§ Academic Attribution

This project was done in fulfillment of the course:

CS526L  
Testing and Verification of VLSI Systems  
Indian Institute of Technology Tirupati  

Under the guidance and supervision of:  
Prof. Jaynarayan Tudu  

Developed by:  
Naman Kalra  
EE23B032  

This work is intended strictly for academic and research purposes and implements
logic simulation techniques described in standard VLSI CAD literature.

────────────────────────────────────────────────────────────────────────────

§ License

Released for academic use. Refer to the LICENSE file for details.

────────────────────────────────────────────────────────────────────────────
