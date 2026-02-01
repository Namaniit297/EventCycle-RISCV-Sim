from circuit import Circuit
from simulators.zero_delay import ZeroDelaySimulator

c = Circuit()
c.set_primary_inputs(['A','B'])
c.set_primary_outputs(['Y'])

c.add_gate('AND',['A','B'],'Y')

sim = ZeroDelaySimulator(c)

tests = [
    {'A':'0','B':'0'},
    {'A':'0','B':'1'},
    {'A':'1','B':'0'},
    {'A':'1','B':'1'}
]

for t in tests:
    out = sim.simulate_vector(t)
    print(t, "->", out)
