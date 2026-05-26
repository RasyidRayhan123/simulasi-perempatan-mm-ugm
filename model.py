"""
model.py  –  IntersectionModel (Mesa 2.3)
Perempatan MM UGM: Jl. Kaliurang (Utara) × Jl. Agro (Timur)
                   Jl. Teknika Sel. (Barat) × Jl. Persatuan (Selatan)
"""

import mesa
import numpy as np
import random
from agents import VehicleAgent

# ── Konstanta ──────────────────────────────────────────────────────────
GRID_SIZE = 25

# Entry points (titik masuk)
ENTRY_POINTS = {
    "Utara":   [(13, 0)],
    "Barat":   [(0, 12)],
    "Selatan": [(11, 24)],
    "Timur":   [(24, 13)],
}

# Exit points (titik keluar) – sengaja berbeda dari entry
EXIT_COORDS = {
    "Utara":   (13, 24),   # keluar bawah
    "Barat":   (24, 12),   # keluar kanan
    "Selatan": (11,  0),   # keluar atas
    "Timur":   ( 0, 13),   # keluar kiri
}

CENTER    = (12, 12)
YELLOW_BOX = [(x, y) for x in range(9, 16) for y in range(9, 16)]


def build_route(origin: str, dest: str) -> list:
    """Rute (x,y) dari entry -> exit (Aturan Lajur Kiri Indonesia)."""
    gs  = GRID_SIZE
    ex, ey = ENTRY_POINTS[origin][0]
    
    # Lajur: Utara-Selatan (x=13), Selatan-Utara (x=11)
    # Lajur: Barat-Timur (y=12), Timur-Barat (y=13)

    if origin == "Utara": # Masuk x=13, y=0 (bergerak y+)
        approach = [(13, y) for y in range(ey, 10)]
        if dest == "Lurus":
            body   = [(13, y) for y in range(10, 15)]
            depart = [(13, y) for y in range(15, gs)]
        elif dest == "Kiri":   # Ke Timur (masuk lajur y=12, bergerak x+)
            body   = [(13, 10), (13, 11), (13, 12)] + [(x, 12) for x in range(14, gs)]
            depart = []
        else:                  # Ke Barat (masuk lajur y=13, bergerak x-)
            body   = [(13, 10), (13, 11), (13, 12), (13, 13)] + [(x, 13) for x in range(12, -1, -1)]
            depart = []
            
    elif origin == "Barat": # Masuk x=0, y=12 (bergerak x+)
        approach = [(x, 12) for x in range(ex, 10)]
        if dest == "Lurus":
            body   = [(x, 12) for x in range(10, 15)]
            depart = [(x, 12) for x in range(15, gs)]
        elif dest == "Kiri":   # Ke Utara (masuk lajur x=11, bergerak y-)
            body   = [(10, 12), (11, 12)] + [(11, y) for y in range(11, -1, -1)]
            depart = []
        else:                  # Ke Selatan (masuk lajur x=13, bergerak y+)
            body   = [(10, 12), (11, 12), (12, 12), (13, 12)] + [(13, y) for y in range(13, gs)]
            depart = []
            
    elif origin == "Selatan": # Masuk x=11, y=24 (bergerak y-)
        approach = [(11, y) for y in range(ey, 14, -1)]
        if dest == "Lurus":
            body   = [(11, y) for y in range(14, 9, -1)]
            depart = [(11, y) for y in range(9, -1, -1)]
        elif dest == "Kiri":   # Ke Barat (masuk lajur y=13, bergerak x-)
            body   = [(11, 14), (11, 13)] + [(x, 13) for x in range(10, -1, -1)]
            depart = []
        else:                  # Ke Timur (masuk lajur y=12, bergerak x+)
            body   = [(11, 14), (11, 13), (11, 12)] + [(x, 12) for x in range(12, gs)]
            depart = []
            
    else:  # origin == "Timur" # Masuk x=24, y=13 (bergerak x-)
        approach = [(x, 13) for x in range(ex, 14, -1)]
        if dest == "Lurus":
            body   = [(x, 13) for x in range(14, 9, -1)]
            depart = [(x, 13) for x in range(9, -1, -1)]
        elif dest == "Kiri":   # Ke Selatan (masuk lajur x=13, bergerak y+)
            body   = [(14, 13), (13, 13)] + [(13, y) for y in range(14, gs)]
            depart = []
        else:                  # Ke Utara (masuk lajur x=11, bergerak y-)
            body   = [(14, 13), (13, 13), (12, 13), (11, 13)] + [(11, y) for y in range(12, -1, -1)]
            depart = []

    # Filter koordinat yang ada di luar grid untuk mencegah error
    cleaned = []
    for pos in (approach + body + depart):
        x, y = pos
        if 0 <= x < gs and 0 <= y < gs:
            if not cleaned or cleaned[-1] != pos:
                cleaned.append(pos)
    return cleaned


# ── Model ──────────────────────────────────────────────────────────────

class IntersectionModel(mesa.Model):

    DIRECTIONS = ["Utara", "Barat", "Selatan", "Timur"]
    DEST_PROB  = {
        "Utara":   {"Lurus": 0.55, "Kiri": 0.30, "Kanan": 0.15},
        "Barat":   {"Lurus": 0.45, "Kiri": 0.35, "Kanan": 0.20},
        "Selatan": {"Lurus": 0.55, "Kiri": 0.25, "Kanan": 0.20},
        "Timur":   {"Lurus": 0.60, "Kiri": 0.20, "Kanan": 0.20},
    }

    def __init__(
        self,
        scenario:      str   = "A",
        arrival_north: float = 8,
        arrival_west:  float = 6,
        arrival_south: float = 6,
        arrival_east:  float = 4,
        green_duration: int  = 25,
        seed=None,
    ):
        super().__init__()
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

        self.scenario         = scenario
        self.grid_size        = GRID_SIZE
        self.center           = CENTER
        self.yellow_box_cells = YELLOW_BOX

        self.arrival_rates = {
            "Utara":   arrival_north,
            "Barat":   arrival_west,
            "Selatan": arrival_south,
            "Timur":   arrival_east,
        }
        self.green_duration = green_duration
        self.phase_index    = 0
        self.phase_timer    = 0

        # Statistik
        self.total_crossed    = 0
        self.gridlock_count   = 0
        self.tick             = 0
        self.gridlock_history = []
        self.wait_history     = []
        self.crossed_history  = []

        self.grid     = mesa.space.SingleGrid(GRID_SIZE, GRID_SIZE, torus=False)
        self.schedule = mesa.time.RandomActivation(self)
        self._next_id = 0

        self.datacollector = mesa.DataCollector(
            model_reporters={
                "Gridlock_Aktif": lambda m: m._count_active_gridlock(),
                "Rata_Rata_Wait": lambda m: m._avg_wait(),
                "Total_Lolos":   lambda m: m.total_crossed,
            }
        )

    def step(self):
        self.tick += 1

        # Lampu
        self.phase_timer += 1
        if self.phase_timer >= self.green_duration:
            self.phase_timer = 0
            self.phase_index = (self.phase_index + 1) % 4

        # Spawn (Poisson)
        for direction in self.DIRECTIONS:
            rate = self.arrival_rates[direction] / self.green_duration
            n    = min(int(np.random.poisson(rate)), 2)
            for _ in range(n):
                self._spawn_vehicle(direction)

        # Jalankan agen
        self.schedule.step()

        # Hapus yang sudah selesai
        for a in list(self.schedule.agents):
            if a.crossed:
                self.schedule.remove(a)

        # Rekam data
        self.datacollector.collect(self)
        self.gridlock_history.append(self._count_active_gridlock())
        self.wait_history.append(self._avg_wait())
        self.crossed_history.append(self.total_crossed)

    # ── Helpers ────────────────────────────────────────────────────────
    def _spawn_vehicle(self, origin: str):
        dest  = random.choices(
            list(self.DEST_PROB[origin].keys()),
            weights=list(self.DEST_PROB[origin].values()),
        )[0]
        entry = ENTRY_POINTS[origin][0]
        if self.grid.is_cell_empty(entry):
            agent       = VehicleAgent(self._next_id, self, origin, dest)
            agent.route = build_route(origin, dest)
            self._next_id += 1
            self.grid.place_agent(agent, entry)
            self.schedule.add(agent)

    def get_green_direction(self) -> str:
        return self.DIRECTIONS[self.phase_index]

    def get_light_state(self) -> dict:
        g = self.get_green_direction()
        return {d: ("hijau" if d == g else "merah") for d in self.DIRECTIONS}

    def _count_active_gridlock(self) -> int:
        return sum(
            1
            for cell in self.yellow_box_cells
            for a in self.grid.get_cell_list_contents([cell])
            if isinstance(a, VehicleAgent) and a.is_gridlocked
        )

    def _avg_wait(self) -> float:
        agents = [a for a in self.schedule.agents if isinstance(a, VehicleAgent)]
        return float(np.mean([a.wait_time for a in agents])) if agents else 0.0

    def get_grid_matrix(self):
        gs     = GRID_SIZE
        matrix = [[None] * gs for _ in range(gs)]
        for a in self.schedule.agents:
            if isinstance(a, VehicleAgent) and a.pos:
                x, y = a.pos
                if 0 <= x < gs and 0 <= y < gs:
                    matrix[y][x] = {
                        "color":      a.color,
                        "origin":     a.origin,
                        "dest":       a.dest,
                        "wait":       a.wait_time,
                        "gridlocked": a.is_gridlocked,
                    }
        return matrix
