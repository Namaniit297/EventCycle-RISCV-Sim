from collections import deque, defaultdict

# Logic values for 2/3-value logic
LOGIC_ZERO = '0'
LOGIC_ONE = '1'
LOGIC_U = 'U'   # Unknown
LOGIC_X = 'X'   # Conflict/hazard (treated similarly to unknown)

def logic_and(inputs, values, logic_model='2val'):
    """Logic AND: 1 if all inputs are 1, 0 if any input is 0, U if any input is U (in 3-val mode)."""
    res = LOGIC_ONE
    for i in inputs:
        val = values[i]
        if val == LOGIC_ZERO:
            return LOGIC_ZERO
        if logic_model == '3val' and val == LOGIC_U:
            return LOGIC_U
    return res

def logic_or(inputs, values, logic_model='2val'):
    """Logic OR: 0 if all inputs are 0, 1 if any input is 1, U if any input is U (3-val mode)."""
    res = LOGIC_ZERO
    for i in inputs:
        val = values[i]
        if val == LOGIC_ONE:
            return LOGIC_ONE
        if logic_model == '3val' and val == LOGIC_U:
            return LOGIC_U
    return res

def logic_not(input_idx, values, logic_model='2val'):
    """Logic NOT (inverter)."""
    val = values[input_idx]
    if logic_model == '3val' and val == LOGIC_U:
        return LOGIC_U
    if val == LOGIC_ZERO:
        return LOGIC_ONE
    if val == LOGIC_ONE:
        return LOGIC_ZERO
    return LOGIC_X

def logic_not_single(val, logic_model='2val'):
    """Helper for NOT when given a value directly."""
    if logic_model == '3val' and val == LOGIC_U:
        return LOGIC_U
    if val == LOGIC_ZERO:
        return LOGIC_ONE
    if val == LOGIC_ONE:
        return LOGIC_ZERO
    return LOGIC_X

def logic_nand(inputs, values, logic_model='2val'):
    """Logic NAND: invert of AND."""
    andv = logic_and(inputs, values, logic_model)
    if andv == LOGIC_U:
        return LOGIC_U
    return logic_not_single(andv, logic_model)

def logic_nor(inputs, values, logic_model='2val'):
    """Logic NOR: invert of OR."""
    orv = logic_or(inputs, values, logic_model)
    if orv == LOGIC_U:
        return LOGIC_U
    return logic_not_single(orv, logic_model)

def logic_xor(inputs, values, logic_model='2val'):
    """Logic XOR (parity): 1 if odd number of 1s, 0 if even, U if any input is U."""
    ones = 0
    for i in inputs:
        val = values[i]
        if val == LOGIC_U:
            return LOGIC_U
        if val == LOGIC_ONE:
            ones += 1
    return LOGIC_ONE if (ones % 2 == 1) else LOGIC_ZERO

def logic_xnor(inputs, values, logic_model='2val'):
    """Logic XNOR: invert of XOR."""
    xorv = logic_xor(inputs, values, logic_model)
    if xorv == LOGIC_U:
        return LOGIC_U
    return logic_not_single(xorv, logic_model)

# Mapping gate types to logic functions
GATE_FUNCS = {
    'AND': logic_and,
    'OR': logic_or,
    'NOT': logic_not,   # NOT expects a single input
    'NAND': logic_nand,
    'NOR': logic_nor,
    'XOR': logic_xor,
    'XNOR': logic_xnor
}

class Gate:
    """Represents a logic gate."""
    def __init__(self, gate_id, gate_type, inputs, output):
        self.id = gate_id
        self.type = gate_type.upper()
        self.inputs = inputs
        self.output = output
        if self.type not in GATE_FUNCS:
            raise ValueError(f"Unsupported gate type: {self.type}")
    def simulate(self, net_values, logic_model='2val'):
        """Simulate gate output given current net values."""
        if self.type == 'NOT':
            return logic_not(self.inputs[0], net_values, logic_model)
        func = GATE_FUNCS[self.type]
        return func(self.inputs, net_values, logic_model)

class Circuit:
    """Represents the logic circuit (netlist)."""
    def __init__(self):
        self.net_id_map = {}
        self.net_names = []
        self.next_net_id = 0
        self.gates = []
        self.primary_inputs = []
        self.primary_outputs = []
        self.fanout = defaultdict(list)  # net_id -> list of gates
    
    def add_net(self, name):
        """Add net by name if not existing, return its ID."""
        if name not in self.net_id_map:
            self.net_id_map[name] = self.next_net_id
            self.net_names.append(name)
            self.next_net_id += 1
        return self.net_id_map[name]
    
    def add_gate(self, gate_type, input_names, output_name):
        """Add a gate and its nets to the circuit."""
        input_ids = [self.add_net(n) for n in input_names]
        out_id = self.add_net(output_name)
        gate = Gate(len(self.gates), gate_type, input_ids, out_id)
        self.gates.append(gate)
        for net in input_ids:
            self.fanout[net].append(gate)
        return gate
    
    def set_primary_inputs(self, input_names):
        """Define primary input nets."""
        self.primary_inputs = [self.add_net(n) for n in input_names]
    
    def set_primary_outputs(self, output_names):
        """Define primary output nets."""
        self.primary_outputs = [self.add_net(n) for n in output_names]
    
    def get_net_name(self, net_id):
        """Get the name of a net by its ID."""
        return self.net_names[net_id]
    
    def get_gate_by_output(self, net_id):
        """Return gate(s) driving a given net (usually one)."""
        return [g for g in self.gates if g.output == net_id]

class TwoListSimulator:
    """
    Two-List Event-Driven Simulation.
    - Separate event queue and gate queue.
    - Unit-delay timing.
    - Hazard detection (static/dynamic).
    - Optional 3-state logic (U) initialization or net marking.
    """
    def __init__(self, circuit, logic_model='2val'):
        self.circuit = circuit
        self.logic_model = logic_model
        self.num_nets = circuit.next_net_id
        # Initialize net values (0 or U) and net marking flags
        self.net_values = [LOGIC_U if logic_model=='3val' else LOGIC_ZERO 
                           for _ in range(self.num_nets)]
        self.net_mark = [True]*self.num_nets if logic_model=='2val' else [False]*self.num_nets
        self.gate_sim_count = 0
        self.output_log = []
        self.intermediate_log = []
    def simulate_vector(self, input_vector):
        event_queue = deque()
        gate_queue = deque()
        old_values = self.net_values.copy()
        change_count = [0]*self.num_nets
        # Queue events for changed or marked inputs
        for net in self.circuit.primary_inputs:
            val = input_vector.get(net, self.net_values[net])
            if self.logic_model == '2val':
                if val != self.net_values[net] or self.net_mark[net]:
                    event_queue.append({'net': net, 'value': val})
                    self.net_mark[net] = False
            else:  # 3-value logic
                if val != self.net_values[net]:
                    event_queue.append({'net': net, 'value': val})
        time_unit = 0
        # Event-driven simulation loop
        while event_queue:
            # Process all events: update net values, schedule fanout gates
            while event_queue:
                ev = event_queue.popleft()
                net_id = ev['net']; new_val = ev['value']
                if new_val != self.net_values[net_id]:
                    self.net_values[net_id] = new_val
                    change_count[net_id] += 1
                for g in self.circuit.fanout[net_id]:
                    if g not in gate_queue:
                        gate_queue.append(g)
            # If gates to process, output intermediate state then simulate gates
            if gate_queue:
                self.intermediate_log.append((time_unit, 
                    {nid: self.net_values[nid] for nid in self.circuit.primary_outputs}))
                while gate_queue:
                    g = gate_queue.popleft()
                    out_net = g.output
                    new_val = g.simulate(self.net_values, self.logic_model)
                    self.gate_sim_count += 1
                    if new_val != self.net_values[out_net]:
                        event_queue.append({'net': out_net, 'value': new_val})
                time_unit += 1
        # Record final outputs
        self.output_log.append({nid: self.net_values[nid] for nid in self.circuit.primary_outputs})
        # Hazard detection
        hazards = []
        for net in range(self.num_nets):
            if change_count[net] > 1:
                if old_values[net] == self.net_values[net]:
                    hazards.append((net, 'static'))
                else:
                    hazards.append((net, 'dynamic'))
        return hazards

class SingleListEventSimulator:
    """
    Single-List (Event) Simulation:
    - Only an event queue is used (with time-marker events).
    - Gates are simulated immediately when processing events.
    - Implements simple event cancellation to prevent duplicates.
    """
    def __init__(self, circuit, logic_model='2val'):
        self.circuit = circuit
        self.logic_model = logic_model
        self.num_nets = circuit.next_net_id
        self.net_values = [LOGIC_U if logic_model=='3val' else LOGIC_ZERO 
                           for _ in range(self.num_nets)]
        self.net_mark = [True]*self.num_nets if logic_model=='2val' else [False]*self.num_nets
        self.gate_sim_count = 0
        self.output_log = []
        self.intermediate_log = []
    def simulate_vector(self, input_vector):
        event_queue = deque()
        MARKER = {'marker': True}
        old_values = self.net_values.copy()
        change_count = [0]*self.num_nets
        # Queue events for changed/marked inputs
        for net in self.circuit.primary_inputs:
            val = input_vector.get(net, self.net_values[net])
            if self.logic_model == '2val':
                if val != self.net_values[net] or self.net_mark[net]:
                    event_queue.append({'net': net, 'value': val})
                    self.net_mark[net] = False
            else:
                if val != self.net_values[net]:
                    event_queue.append({'net': net, 'value': val})
        # Place first time-marker
        event_queue.append(MARKER)
        time_unit = 0
        hazards = []
        # Process events (including markers)
        while event_queue:
            ev = event_queue.popleft()
            if 'marker' in ev:
                self.intermediate_log.append((time_unit, 
                    {nid: self.net_values[nid] for nid in self.circuit.primary_outputs}))
                time_unit += 1
                if event_queue:
                    event_queue.append(MARKER)
                continue
            net_id, new_val = ev['net'], ev['value']
            if new_val != self.net_values[net_id]:
                self.net_values[net_id] = new_val
                change_count[net_id] += 1
            # Simulate fanout gates immediately
            for g in self.circuit.fanout[net_id]:
                out_net = g.output
                new_out = g.simulate(self.net_values, self.logic_model)
                self.gate_sim_count += 1
                if new_out != self.net_values[out_net]:
                    # Prevent duplicate event scheduling
                    exists = any((e.get('net')==out_net and e.get('value')==new_out) 
                                 for e in event_queue if 'net' in e)
                    if not exists:
                        event_queue.append({'net': out_net, 'value': new_out})
        # Final outputs and hazard detection
        self.output_log.append({nid: self.net_values[nid] for nid in self.circuit.primary_outputs})
        for net in range(self.num_nets):
            if change_count[net] > 1:
                if old_values[net] == self.net_values[net]:
                    hazards.append((net, 'static'))
                else:
                    hazards.append((net, 'dynamic'))
        return hazards

class SingleListGateSimulator:
    """
    Single-List (Gate) Simulation:
    - Uses only a gate queue with a time-marker to separate simulation steps.
    - Gate outputs are stored in temporary storage and committed at marker.
    - Prevents re-queuing a gate for the same time step with flags.
    """
    def __init__(self, circuit, logic_model='2val'):
        self.circuit = circuit
        self.logic_model = logic_model
        self.num_nets = circuit.next_net_id
        self.net_values = [LOGIC_U if logic_model=='3val' else LOGIC_ZERO 
                           for _ in range(self.num_nets)]
        self.gate_sim_count = 0
        self.output_log = []
        self.intermediate_log = []
    def simulate_vector(self, input_vector):
        gate_queue = deque()
        MARKER = {'marker': True}
        old_values = self.net_values.copy()
        change_count = [0]*self.num_nets
        # Initialize gate queue with gates driven by changed inputs
        changed_inputs = []
        for net in self.circuit.primary_inputs:
            val = input_vector.get(net, self.net_values[net])
            if val != self.net_values[net]:
                self.net_values[net] = val
                changed_inputs.append(net)
        for net in changed_inputs:
            for g in self.circuit.fanout[net]:
                gate_queue.append(g)
        gate_queue.append(MARKER)
        temp_net_values = {}
        flagged_next = set()
        time_unit = 0
        hazards = []
        # Process gate queue
        while gate_queue:
            elem = gate_queue.popleft()
            if 'marker' in elem:
                # Commit all new net values at time boundary
                for net, val in temp_net_values.items():
                    if val != self.net_values[net]:
                        self.net_values[net] = val
                        change_count[net] += 1
                temp_net_values.clear()
                self.intermediate_log.append((time_unit, 
                    {nid: self.net_values[nid] for nid in self.circuit.primary_outputs}))
                time_unit += 1
                if gate_queue:
                    gate_queue.append(MARKER)
                    flagged_next.clear()
                continue
            g = elem
            out_net = g.output
            new_val = g.simulate(self.net_values, self.logic_model)
            self.gate_sim_count += 1
            if new_val != self.net_values[out_net]:
                temp_net_values[out_net] = new_val
                for h in self.circuit.fanout[out_net]:
                    if h not in flagged_next:
                        gate_queue.append(h)
                        flagged_next.add(h)
        # Final outputs and hazards
        self.output_log.append({nid: self.net_values[nid] for nid in self.circuit.primary_outputs})
        for net in range(self.num_nets):
            if change_count[net] > 1:
                if old_values[net] == self.net_values[net]:
                    hazards.append((net, 'static'))
                else:
                    hazards.append((net, 'dynamic'))
        return hazards

class ZeroDelaySimulator:
    """
    Zero-Delay Event-Driven Simulation:
    - Levelizes the circuit; gates are simulated once per level order.
    - Iterative passes handle feedback loops (force-levelized).
    - No intermediate time events (zero delay).
    """
    def __init__(self, circuit, logic_model='2val'):
        self.circuit = circuit
        self.logic_model = logic_model
        self.net_values = [LOGIC_ZERO]*circuit.next_net_id
        self.num_nets = circuit.next_net_id
        self.output_log = []
        self.gate_sim_count = 0
        self.intermediate_log = []  # none for pure zero-delay
        # Compute gate levels (topological sort)
        indeg = {g: 0 for g in self.circuit.gates}
        for g in self.circuit.gates:
            for net in g.inputs:
                for d in self.circuit.get_gate_by_output(net):
                    indeg[g] += 1
        queue = deque()
        self.levels = {}
        self.max_level = 0
        for g in self.circuit.gates:
            if indeg[g] == 0:
                self.levels[g.id] = 0
                queue.append(g)
        while queue:
            g = queue.popleft()
            lvl = self.levels[g.id]
            self.max_level = max(self.max_level, lvl)
            out_net = g.output
            for h in self.circuit.fanout[out_net]:
                indeg[h] -= 1
                if indeg[h] == 0:
                    self.levels[h.id] = lvl + 1
                    queue.append(h)
    def simulate_vector(self, input_vector):
        hazards = []
        old_values = self.net_values.copy()
        # Queues per level
        level_queues = {lvl: [] for lvl in range(self.max_level+1)}
        # Schedule gates for changed primary inputs
        for net in self.circuit.primary_inputs:
            new_val = input_vector.get(net, self.net_values[net])
            if new_val != self.net_values[net]:
                self.net_values[net] = new_val
                for g in self.circuit.fanout[net]:
                    lvl = self.levels.get(g.id, 0)
                    if g not in level_queues[lvl]:
                        level_queues[lvl].append(g)
        iteration = True
        pass_num = 0
        # Process levels in ascending order; iterate if feedback
        while iteration and pass_num < 2:
            iteration = False
            for lvl in range(self.max_level+1):
                while level_queues[lvl]:
                    g = level_queues[lvl].pop(0)
                    new_val = g.simulate(self.net_values, self.logic_model)
                    self.gate_sim_count += 1
                    if new_val != self.net_values[g.output]:
                        self.net_values[g.output] = new_val
                        for h in self.circuit.fanout[g.output]:
                            h_lvl = self.levels.get(h.id, 0)
                            if h_lvl < lvl:
                                iteration = True
                            if h not in level_queues[h_lvl]:
                                level_queues[h_lvl].append(h)
            pass_num += 1
        self.output_log.append({nid: self.net_values[nid] for nid in self.circuit.primary_outputs})
        # Zero-delay does not detect hazards by design
        return hazards

class ThreadedSimulator:
    """
    Threaded Code Style Simulation:
    - Uses stacks of callable tasks (net events and gate simulations).
    - No explicit queues; mimic event-driven behavior via LIFO stacks.
    """
    def __init__(self, circuit, logic_model='2val'):
        self.circuit = circuit
        self.logic_model = logic_model
        self.num_nets = circuit.next_net_id
        self.net_values = [LOGIC_U if logic_model=='3val' else LOGIC_ZERO 
                           for _ in range(self.num_nets)]
        self.event_stack = []
        self.gate_stack = []
        self.gate_sim_count = 0
        self.output_log = []
    def simulate_vector(self, input_vector):
        hazards = []
        old_values = self.net_values.copy()
        change_count = [0]*self.num_nets
        # Define event and gate tasks as inner classes to capture 'self'
        class NetEventTask:
            def __init__(self, sim, net_id, value):
                self.sim = sim; self.net_id = net_id; self.value = value
            def __call__(self):
                if self.value != self.sim.net_values[self.net_id]:
                    self.sim.net_values[self.net_id] = self.value
                    change_count[self.net_id] += 1
                for g in self.sim.circuit.fanout[self.net_id]:
                    self.sim.gate_stack.append(GateTask(self.sim, g))
        class GateTask:
            def __init__(self, sim, gate):
                self.sim = sim; self.gate = gate
            def __call__(self):
                out_net = self.gate.output
                new_val = self.gate.simulate(self.sim.net_values, self.sim.logic_model)
                self.sim.gate_sim_count += 1
                if new_val != self.sim.net_values[out_net]:
                    self.sim.event_stack.append(NetEventTask(self.sim, out_net, new_val))
        # Schedule initial net events for changed inputs
        for net in self.circuit.primary_inputs:
            new_val = input_vector.get(net, self.net_values[net])
            if new_val != self.net_values[net]:
                self.event_stack.append(NetEventTask(self, net, new_val))
        # Process tasks until both stacks empty
        while self.event_stack or self.gate_stack:
            if self.event_stack:
                task = self.event_stack.pop()
            else:
                task = self.gate_stack.pop()
            task()
        self.output_log.append({nid: self.net_values[nid] for nid in self.circuit.primary_outputs})
        for net in range(self.num_nets):
            if change_count[net] > 1:
                if old_values[net] == self.net_values[net]:
                    hazards.append((net, 'static'))
                else:
                    hazards.append((net, 'dynamic'))
        return hazards

# ================= Example Usage =================
if __name__ == "__main__":
    # Define a small test circuit: (A AND B) -> X, (X OR C) -> Y
    circ = Circuit()
    circ.set_primary_inputs(['A','B','C'])
    circ.set_primary_outputs(['Y'])
    circ.add_gate('AND', ['A','B'], 'X')
    circ.add_gate('OR',  ['X','C'], 'Y')
    # Define a sequence of input vectors
    vectors = [
        {'A':'0','B':'0','C':'0'},
        {'A':'1','B':'0','C':'0'},
        {'A':'1','B':'1','C':'0'},
        {'A':'1','B':'1','C':'1'},
    ]
    # Initialize each simulator
    sims = {
        "Two-List": TwoListSimulator(circ, logic_model='2val'),
        "Single-List (Event)": SingleListEventSimulator(circ, logic_model='2val'),
        "Single-List (Gate)": SingleListGateSimulator(circ, logic_model='2val'),
        "Zero-Delay": ZeroDelaySimulator(circ, logic_model='2val'),
        "Threaded": ThreadedSimulator(circ, logic_model='2val'),
    }
    # Run simulations and print results
    for name, sim in sims.items():
        print(f"{name} Simulator:")
        for vec in vectors:
            hazards = sim.simulate_vector(vec)
            output = {circ.get_net_name(n): val for n,val in sim.output_log[-1].items()}
            print(f"  Input {vec} -> Output {output}, Hazards: {hazards}")
        print(f"  Intermediate outputs: {getattr(sim, 'intermediate_log', None)}")
        print()
