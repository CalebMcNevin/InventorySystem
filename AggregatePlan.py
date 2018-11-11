import numpy as np
import functools
import pandas as pd
import networkx as nx


class AggregatePlan:
    def __init__(self,
                 demand,
                 setup_cost,
                 holding_cost,
                 inv_start=0,
                 inv_end=0):
        self.demand = demand
        self.setup_cost = setup_cost
        self.holding_cost = holding_cost
        self.inv_end = inv_end
        self.inv_start = inv_start
        self.G = self.create_graph()
        self.plan = self.make_plan_dynamic(0)
        print(self.make_plan_dynamic.cache_info())
        self.make_plan_dynamic.cache_clear()

    @functools.lru_cache()
    def make_plan_dynamic(self, stage):
        if stage == max(self.G.nodes):
            # base case
            return {'route': [[stage, 0]], 'cost': 0}
        else:
            stages = {
                x: self.G[stage][x]
                for x in list(self.G.successors(stage))[::-1]
            }
            next_stage = min(
                stages,
                key=
                lambda x: stages[x]['cost'] + self.make_plan_dynamic(x)['cost']
            )
            route = [[stage, self.G[stage][next_stage]['Q']]
                     ] + self.make_plan_dynamic(next_stage)['route']
            return {'route': route, 'cost': self.route_cost(route)}

    def create_graph(self, max_lead=10):
        net_demand = self.demand
        if net_demand[-1] is not None: net_demand += [None]
        net_demand[0] -= self.inv_start
        net_demand[-2] += self.inv_end
        G = nx.DiGraph()
        for i in range(len(net_demand)):
            for j in range(i + 1, min(len(net_demand), i + max_lead)):
                q = [0 if x is None else x for x in net_demand[i:j + 1]]
                cost = self.setup_cost if sum(q[:-1]) > 0 else 0
                for k in list(range(j - i)):
                    cost += q[k] * k * self.holding_cost
                if j == len(net_demand) - 1:
                    cost += self.holding_cost * self.inv_end
                G.add_edge(i, j, Q=sum(q[:-1]), cost=cost)
            G.nodes[i]['demand'] = net_demand[i]
        return G

    def route_cost(self, route):
        route = np.array(route)[:, 0]
        segments = [route[i:i + 2] for i in range(len(route) - 1)]
        cost = 0
        for seg in segments:
            cost += self.G[seg[0]][seg[1]]['cost']
        return cost