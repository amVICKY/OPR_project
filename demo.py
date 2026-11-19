"""
LIVE DEMO - AI query routing across GPU data centers (pygame + Gurobi)

Every time you change something, the model is solved again with Gurobi
and the new optimal routing is shown immediately.

Controls
    1 / 2 / 3     Part 1: LP (all ON) / Part 2: IP (choose ON/OFF) / average-demand plan
    Mouse click   on a data center: break it (outage) or repair it
    UP / DOWN     demand +10% / -10%   (e.g. viral launch day)
    SPACE         pause / play
    LEFT / RIGHT  previous / next time block
    R             reset everything
    ESC           quit

Run:  python demo.py
"""
import math
import time

import pygame

import data
from model import RoutingModel

# ---------------- window and colors ----------------
W, H = 1200, 700
MAP_W = 820                 # left part = map, right part = info panel
BLOCK_SECONDS = 4           # how long each 4-hour block is shown

BG = (20, 22, 26)
PANEL = (30, 33, 39)
GRID = (38, 42, 48)
TEXT = (235, 235, 230)
MUTED = (150, 150, 145)
RED = (235, 95, 95)
GREEN = (90, 200, 130)

REGION_COLOR = {
    "India": (57, 135, 229),
    "Southeast Asia": (217, 89, 38),
    "Middle East": (25, 158, 112),
    "Europe": (201, 133, 0),
    "USA": (213, 81, 129),
}

# Positions on a simple flat world map (longitude, latitude)
POSITION = {
    "Virginia": (-77, 34), "Frankfurt": (0, 44), "Mumbai": (64, 12), "Singapore": (100, -6),
    "USA": (-102, 44), "Europe": (22, 57), "Middle East": (42, 28),
    "India": (84, 27), "Southeast Asia": (118, 12),
}

MODE_NAME = {
    1: "Part 1: Transportation LP (all ON)",
    2: "Part 2: Integer Program (choose ON/OFF)",
    3: "Plan made from AVERAGE demand",
}


def to_screen(name):
    """Convert (longitude, latitude) to a pixel position on the map."""
    lon, lat = POSITION[name]
    x = 50 + (lon + 125) / 255 * (MAP_W - 100)
    y = 140 + (65 - lat) / 85 * (H - 240)
    return int(x), int(y)


def curve_point(p0, p1, s):
    """Point at fraction s (0..1) along a curved path from p0 to p1."""
    mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
    lift = 0.2 * math.dist(p0, p1)
    cx, cy = mx, my - lift                       # control point above the middle
    x = (1 - s) ** 2 * p0[0] + 2 * (1 - s) * s * cx + s ** 2 * p1[0]
    y = (1 - s) ** 2 * p0[1] + 2 * (1 - s) * s * cy + s ** 2 * p1[1]
    return int(x), int(y)


class Demo:

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Live AI Query Routing - Gurobi")
        self.screen = pygame.display.set_mode((W, H))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("segoeui", 16)
        self.small = pygame.font.SysFont("segoeui", 13)
        self.big = pygame.font.SysFont("segoeui", 22, bold=True)
        self.reset()

    # ---------------- state ----------------
    def reset(self):
        self.mode = 2
        self.broken = set()          # data centers with an outage
        self.scale = 1.0             # demand multiplier
        self.block = 0
        self.time_in_block = 0.0
        self.paused = False
        self.anim = 0.0
        self.solve()

    def demand(self):
        return {r: [v * self.scale for v in data.DEMAND[r]] for r in data.REGIONS}

    def solve(self):
        """Solve the model for the whole day with the current settings."""
        start = time.perf_counter()
        demand = self.demand()
        forced = {dc: False for dc in self.broken}
        hours = data.HOURS_PER_BLOCK

        if self.mode == 1:
            model = RoutingModel(demand, data.BLOCKS, hours,
                                 force_on_off=forced, allow_unserved=True)
        elif self.mode == 2:
            model = RoutingModel(demand, data.BLOCKS, hours, use_on_off=True,
                                 force_on_off=forced, allow_unserved=True)
        else:
            # decide ON/OFF using only the daily average, then test it on real demand
            average = {r: [sum(v) / len(v)] for r, v in demand.items()}
            static = RoutingModel(average, ["avg"], 24, use_on_off=True,
                                  force_on_off=forced, allow_unserved=True).solve()
            model = RoutingModel(demand, data.BLOCKS, hours,
                                 force_on_off=static.is_on, allow_unserved=True)

        self.plan = model.solve()
        self.solve_ms = (time.perf_counter() - start) * 1000

    # ---------------- drawing helpers ----------------
    def text(self, s, x, y, color=TEXT, font=None, center=False):
        img = (font or self.font).render(s, True, color)
        rect = img.get_rect(center=(x, y)) if center else img.get_rect(topleft=(x, y))
        self.screen.blit(img, rect)

    def draw_map(self):
        block = data.BLOCKS[self.block]

        # light grid lines
        for lon in range(-120, 131, 30):
            x = 50 + (lon + 125) / 255 * (MAP_W - 100)
            pygame.draw.line(self.screen, GRID, (x, 120), (x, H - 80))
        for lat in range(-15, 66, 20):
            y = 140 + (65 - lat) / 85 * (H - 240)
            pygame.draw.line(self.screen, GRID, (30, y), (MAP_W - 30, y))

        # flows: curved line + moving dots
        for (dc, r, b), q in self.plan.flow.items():
            if b != block:
                continue
            p0, p1 = to_screen(dc), to_screen(r)
            color = REGION_COLOR[r]
            dim = tuple(c // 3 for c in color)
            points = [curve_point(p0, p1, k / 30) for k in range(31)]
            pygame.draw.lines(self.screen, dim, False, points, max(2, int(q / 12)))
            n_dots = max(2, int(q / 10))
            for k in range(n_dots):
                s = (self.anim * 0.35 + k / n_dots) % 1
                pygame.draw.circle(self.screen, color, curve_point(p0, p1, s), 3)

        # regions (circles, size = demand)
        k = self.block
        for r in data.REGIONS:
            x, y = to_screen(r)
            d = data.DEMAND[r][k] * self.scale
            radius = int(8 + 2.2 * math.sqrt(d))
            pygame.draw.circle(self.screen, tuple(c // 2 for c in REGION_COLOR[r]), (x, y), radius)
            pygame.draw.circle(self.screen, REGION_COLOR[r], (x, y), radius, 3)
            self.text(r, x, y - radius - 22, TEXT, self.font, center=True)
            self.text(f"{d:.0f}k/h", x, y - radius - 6, MUTED, self.small, center=True)
            lost = self.plan.unserved.get((r, block), 0)
            if lost > 0:
                pygame.draw.circle(self.screen, RED, (x, y), radius + 5, 2)
                self.text(f"{lost:.0f}k/h NOT served", x, y + radius + 12, RED, self.small,
                          center=True)

        # data centers (squares)
        for dc in data.DATA_CENTERS:
            x, y = to_screen(dc)
            rect = pygame.Rect(x - 13, y - 13, 26, 26)
            if dc in self.broken:
                pygame.draw.rect(self.screen, (60, 30, 30), rect)
                pygame.draw.line(self.screen, RED, rect.topleft, rect.bottomright, 3)
                pygame.draw.line(self.screen, RED, rect.topright, rect.bottomleft, 3)
                status, color = "OUTAGE", RED
            elif self.plan.is_on[dc]:
                pygame.draw.rect(self.screen, TEXT, rect, border_radius=4)
                status, color = "ON", GREEN
            else:
                pygame.draw.rect(self.screen, (70, 70, 70), rect, 2, border_radius=4)
                status, color = "OFF", MUTED
            self.text(dc, x, y + 26, TEXT, self.font, center=True)
            self.text(status, x, y + 44, color, self.small, center=True)

    def draw_timeline(self):
        """Clock + the 6 blocks of the day at the top of the map."""
        hour = self.block * 4 + 4 * self.time_in_block / BLOCK_SECONDS
        self.text("Live AI Query Routing", 30, 18, TEXT, self.big)
        self.text(f"{int(hour):02d}:{int(hour % 1 * 60):02d} IST", 30, 52, TEXT, self.big)
        self.text("PAUSED" if self.paused else "", 160, 58, RED)

        totals = [sum(data.DEMAND[r][k] for r in data.REGIONS) * self.scale
                  for k in range(len(data.BLOCKS))]
        x0, w = 280, 85
        for k, b in enumerate(data.BLOCKS):
            x = x0 + k * w
            h = int(totals[k] / 9)
            active = (k == self.block)
            pygame.draw.rect(self.screen, (57, 135, 229) if active else GRID,
                             (x, 85 - h, w - 8, h), border_radius=3)
            self.text(b, x + (w - 8) // 2, 96, TEXT if active else MUTED, self.small, center=True)
        self.text("total demand per block", x0, 104, MUTED, self.small)

    def draw_panel(self):
        x = MAP_W + 20
        pygame.draw.rect(self.screen, PANEL, (MAP_W, 0, W - MAP_W, H))
        block = data.BLOCKS[self.block]

        self.text("MODE", x, 20, MUTED, self.small)
        self.text(MODE_NAME[self.mode], x, 38, TEXT)
        self.text(f"Demand x{self.scale:.1f}     solved in {self.solve_ms:.0f} ms by Gurobi",
                  x, 62, MUTED, self.small)

        # data center status + capacity used in this block
        self.text(f"DATA CENTERS  (capacity used, {block})", x, 100, MUTED, self.small)
        y = 122
        for dc in data.DATA_CENTERS:
            load = self.plan.load(dc, block)
            cap = data.CAPACITY[dc]
            on = self.plan.is_on[dc]
            self.text(dc, x, y, TEXT if on else MUTED)
            pygame.draw.rect(self.screen, GRID, (x + 110, y + 4, 180, 14), border_radius=3)
            if on:
                pygame.draw.rect(self.screen, (57, 135, 229),
                                 (x + 110, y + 4, int(180 * load / cap), 14), border_radius=3)
                self.text(f"{100 * load / cap:.0f}%", x + 300, y, TEXT, self.small)
            else:
                self.text("OUTAGE" if dc in self.broken else "OFF", x + 300, y,
                          RED if dc in self.broken else MUTED, self.small)
            y += 30

        # cost for the whole day
        y += 15
        self.text("COST FOR THE DAY", x, y, MUTED, self.small)
        self.text(f"Routing cost   ${self.plan.routing_cost:>10,.0f}", x, y + 20)
        self.text(f"Fixed cost     ${self.plan.fixed_cost:>10,.0f}", x, y + 42)
        self.text(f"TOTAL  ${self.plan.total_cost:,.0f}", x, y + 68, TEXT, self.big)

        # unserved queries
        y += 115
        lost_now = sum(v for (r, b), v in self.plan.unserved.items() if b == block)
        lost_day = self.plan.total_unserved
        color = RED if lost_day > 0 else GREEN
        self.text("UNSERVED QUERIES", x, y, MUTED, self.small)
        self.text(f"This block: {lost_now:,.0f}k / hour", x, y + 20, color)
        self.text(f"Whole day:  {lost_day:,.0f}k queries", x, y + 42, color)

        # controls
        y = H - 150
        self.text("CONTROLS", x, y, MUTED, self.small)
        help_lines = [
            "1 / 2 / 3   LP  /  IP  /  average plan",
            "Click data center   outage / repair",
            "UP / DOWN   demand +10% / -10%",
            "SPACE pause    LEFT/RIGHT change block",
            "R reset     ESC quit",
        ]
        for i, s in enumerate(help_lines):
            self.text(s, x, y + 20 + i * 22, TEXT, self.small)

    # ---------------- main loop ----------------
    def handle(self, event):
        if event.type == pygame.KEYDOWN:
            k = event.key
            if k == pygame.K_ESCAPE:
                return False
            if k in (pygame.K_1, pygame.K_2, pygame.K_3):
                self.mode = int(event.unicode)
                self.solve()
            elif k == pygame.K_UP:
                self.scale = round(self.scale + 0.1, 1)
                self.solve()
            elif k == pygame.K_DOWN:
                self.scale = max(0.1, round(self.scale - 0.1, 1))
                self.solve()
            elif k == pygame.K_SPACE:
                self.paused = not self.paused
            elif k == pygame.K_RIGHT:
                self.block, self.time_in_block = (self.block + 1) % len(data.BLOCKS), 0
            elif k == pygame.K_LEFT:
                self.block, self.time_in_block = (self.block - 1) % len(data.BLOCKS), 0
            elif k == pygame.K_r:
                self.reset()

        if event.type == pygame.MOUSEBUTTONDOWN:
            for dc in data.DATA_CENTERS:
                if math.dist(event.pos, to_screen(dc)) < 22:
                    self.broken ^= {dc}          # toggle outage
                    self.solve()
        return True

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(60) / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    running = self.handle(event) and running

            self.anim += dt
            if not self.paused:
                self.time_in_block += dt
                if self.time_in_block >= BLOCK_SECONDS:
                    self.time_in_block = 0
                    self.block = (self.block + 1) % len(data.BLOCKS)

            self.screen.fill(BG)
            self.draw_timeline()
            self.draw_map()
            self.draw_panel()
            pygame.display.flip()
        pygame.quit()


if __name__ == "__main__":
    Demo().run()
