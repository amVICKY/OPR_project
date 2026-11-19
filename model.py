"""
The optimisation model (solved with Gurobi).

Part 1 - Transportation problem (LP)       -> RoutingModel(use_on_off=False)
    All data centers are ON. Decide how many queries each data center
    sends to each region in each time block, at minimum cost.

Part 2 - Data center selection (IP)        -> RoutingModel(use_on_off=True)
    Same as Part 1, plus a YES/NO (binary) decision for every data center:
    keep it ON for the day (pay fixed cost) or switch it OFF (capacity = 0).

Variables:
    x[dc, region, block] >= 0    queries sent (thousand / hour)
    on[dc] in {0, 1}             1 = data center is ON   (Part 2 only)

Objective:
    minimise   hours * sum( cost * x )   +   sum( fixed cost * on )

Constraints:
    supply :  sum over regions of x[dc, region, block] <= capacity[dc] * on[dc]
    demand :  sum over dcs     of x[dc, region, block]  = demand[region][block]
"""
import gurobipy as gp
from gurobipy import GRB

import data

# One quiet Gurobi environment (hides the license banner and solver log)
ENV = gp.Env(empty=True)
ENV.setParam("OutputFlag", 0)
ENV.start()


class RoutingModel:

    def __init__(self, demand, blocks, hours, use_on_off=False,
                 force_on_off=None, allow_unserved=False):
        """
        demand         : {region: [demand in each block]}
        blocks         : list of block names
        hours          : hours in each block (used to turn per-hour cost into per-day)
        use_on_off     : False = Part 1 (LP), True = Part 2 (IP)
        force_on_off   : e.g. {"Frankfurt": False} to fix a decision (for testing a plan)
        allow_unserved : allow some demand to go unserved (only for testing a plan)
        """
        self.demand = demand
        self.blocks = blocks
        self.hours = hours
        self.use_on_off = use_on_off
        self.force_on_off = force_on_off or {}
        self.allow_unserved = allow_unserved

    def solve(self):
        m = gp.Model(env=ENV)

        dcs, regions, blocks = data.DATA_CENTERS, data.REGIONS, self.blocks

        # ---------- decision variables ----------
        x = {}
        for dc in dcs:
            for r in regions:
                if data.route_allowed(dc, r):        # prohibited routes get no variable
                    for b in blocks:
                        x[dc, r, b] = m.addVar(lb=0)

        on = {}
        for dc in dcs:
            if self.use_on_off or dc in self.force_on_off:
                on[dc] = m.addVar(vtype=GRB.BINARY)
                if dc in self.force_on_off:          # fix the decision
                    on[dc].LB = on[dc].UB = int(self.force_on_off[dc])
            else:
                on[dc] = 1                           # Part 1: always ON

        unserved = {}
        for r in regions:
            for b in blocks:
                unserved[r, b] = m.addVar(lb=0) if self.allow_unserved else 0

        # ---------- constraints ----------
        for dc in dcs:                               # supply (capacity)
            for b in blocks:
                sent = gp.quicksum(x[dc, r, b] for r in regions if (dc, r, b) in x)
                m.addConstr(sent <= data.CAPACITY[dc] * on[dc])

        for r in regions:                            # demand must be met
            for k, b in enumerate(blocks):
                received = gp.quicksum(x[dc, r, b] for dc in dcs if (dc, r, b) in x)
                m.addConstr(received + unserved[r, b] == self.demand[r][k])

        # ---------- objective ----------
        routing_cost = self.hours * gp.quicksum(
            data.cost(dc, r) * x[dc, r, b] for (dc, r, b) in x)
        fixed_cost = gp.quicksum(data.FIXED_COST[dc] * on[dc] for dc in dcs)
        penalty = 100 * self.hours * gp.quicksum(unserved.values())  # $100 per 1000 lost

        m.setObjective(routing_cost + fixed_cost + penalty, GRB.MINIMIZE)
        m.optimize()

        # ---------- read the results ----------
        self.optimal = (m.Status == GRB.OPTIMAL)
        if not self.optimal:
            return self

        def value(v):
            return v.X if hasattr(v, "X") else v     # works for variables and numbers

        self.routing_cost = routing_cost.getValue()
        self.fixed_cost = fixed_cost.getValue()
        self.total_cost = self.routing_cost + self.fixed_cost
        self.is_on = {dc: value(on[dc]) > 0.5 for dc in dcs}
        self.flow = {key: var.X for key, var in x.items() if var.X > 1e-6}
        self.unserved = {key: value(v) for key, v in unserved.items() if value(v) > 1e-6}
        self.total_unserved = self.hours * sum(self.unserved.values())   # thousand queries
        return self

    # ---------- small helpers for printing ----------
    def load(self, dc, block):
        """Queries handled by a data center in one block (thousand / hour)."""
        return sum(v for (d, r, b), v in self.flow.items() if d == dc and b == block)

    def on_list(self):
        return [dc for dc, is_on in self.is_on.items() if is_on]
