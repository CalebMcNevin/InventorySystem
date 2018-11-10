import numpy as np
import functools
import networkx as nx
import pandas as pd

DEMAND = [23,86,40,12,None]
STARTING_INV = 0
ENDING_INV = 100
SETUP_COST = 300
HOLDING_COST = 3

def make_aggregation_plan(demand, setup_cost, holding_cost,
                          starting_inv = 0, ending_inv = 0,
                          max_lead = 10):
    if demand[-1] is not None: demand += [None]
    demand[0] -= starting_inv
    demand[-2] += ending_inv
    G = nx.DiGraph()
    for i in range(0, len(demand)):
        for j in range(i+1, min(len(demand), i + max_lead)):
            q = [0 if x is None else x for x in demand[i:j+1]]
            cost = setup_cost if sum(q[:-1])>0 else 0
            for k in list(range(j-i)):
                cost += q[k]*k*holding_cost
            if j == len(demand)-1:
                cost += holding_cost*ending_inv
            G.add_edge(i, j,
                    Q=sum(q[:-1]),
                    cost=cost)
    for i in range(0, len(demand)):
        G.nodes[i]['D'] = demand[i]
    result = dynamic_aggregate(G, 0)
    result['route'] = result['route'][:-1]
    result['demand'] = demand
    return result

@functools.lru_cache()
def dynamic_aggregate(G, stage):
    if stage == max(G.nodes):
        # base case
        return {'route': [[stage, 0]], 'cost': 0}
    else:
        stages = {x:G[stage][x] for x in list(G.successors(stage))[::-1]}
        next_stage = min(stages, key=lambda x:stages[x]['cost']
                    + dynamic_aggregate(G, x)['cost'])
        route = [[stage, G[stage][next_stage]['Q']]] \
                + dynamic_aggregate(G, next_stage)['route']
        return {'route': route, 'cost': graph_cost(G, np.array(route)[:,0])}

def graph_cost(G, route):
    segments = [route[i:i+2] for i in range(len(route)-1)]
    cost = 0
    for seg in segments:
        cost += G[seg[0]][seg[1]]['cost']
    return cost

if __name__=='__main__':
    print(make_aggregation_plan(DEMAND, SETUP_COST, HOLDING_COST,
                               starting_inv=STARTING_INV, ending_inv=ENDING_INV))