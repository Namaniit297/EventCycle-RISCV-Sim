from circuit import Circuit
from simulators.zero_delay import ZeroDelaySimulator

c = Circuit()
c.set_primary_inputs(['A','B','C','D'])
c.set_primary_outputs(['Y'])

c.add_gate('AND',['A','B'],'X1')
c.add_gate('OR',['C','D'],'X2')
c.add_gate('XOR',['X1','X2'],'Y')

sim = ZeroDelaySimulator(c)

print(sim.simulate_vector({'A':'1','B':'1','C':'0','D':'1'}))
