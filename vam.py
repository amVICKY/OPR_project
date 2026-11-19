"""
Vogel's Approximation Method (VAM) - the hand method from class.
Gives a good STARTING solution for a transportation problem (not always optimal).
"""

BIG_M = 1000   # cost used for prohibited routes, so VAM never picks them


def vogel(cost, supply, demand):
    """
    cost   : {(source, destination): cost}  (missing pair = prohibited route)
    supply : {source: amount}
    demand : {destination: amount}
    Returns (allocation, total_cost)
    """
    supply = dict(supply)
    demand = dict(demand)

    # Balance the problem: extra supply goes to a Dummy column with cost 0
    extra = sum(supply.values()) - sum(demand.values())
    if extra > 0:
        demand["Dummy"] = extra

    def c(s, d):
        if d == "Dummy":
            return 0
        return cost.get((s, d), BIG_M)

    def penalty(costs):
        """Difference between the two smallest costs."""
        costs = sorted(costs)
        return costs[1] - costs[0] if len(costs) > 1 else costs[0]

    rows = list(supply)
    cols = list(demand)
    allocation = {}

    while rows and cols:
        # find the row or column with the largest penalty
        best = None   # (penalty, source, destination)
        for s in rows:
            p = penalty([c(s, d) for d in cols])
            d = min(cols, key=lambda d: c(s, d))
            if best is None or p > best[0]:
                best = (p, s, d)
        for d in cols:
            p = penalty([c(s, d) for s in rows])
            s = min(rows, key=lambda s: c(s, d))
            if p > best[0]:
                best = (p, s, d)

        # allocate as much as possible to the cheapest cell in it
        _, s, d = best
        amount = min(supply[s], demand[d])
        allocation[s, d] = amount
        supply[s] -= amount
        demand[d] -= amount
        if supply[s] == 0:
            rows.remove(s)
        if demand[d] == 0:
            cols.remove(d)

    total_cost = sum(amount * c(s, d) for (s, d), amount in allocation.items())
    return allocation, total_cost
