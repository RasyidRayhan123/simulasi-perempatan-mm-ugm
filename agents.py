"""
agents.py
VehicleAgent: agen kendaraan di perempatan MM UGM
"""

import mesa
import random


class VehicleAgent(mesa.Agent):
    """
    Merepresentasikan satu kendaraan di perempatan.

    Atribut:
        origin   : "Utara" | "Barat" | "Selatan" | "Timur"
        dest     : "Lurus" | "Kiri" | "Kanan"
        wait_time: jumlah tick kendaraan ini sudah menunggu
        delay_timer: sisa tick tunda akibat bottleneck
        crossed  : apakah sudah keluar dari persimpangan
        in_yellow_box: apakah sedang di zona tengah persimpangan
        color    : warna untuk visualisasi
    """

    def __init__(self, unique_id, model, origin: str, dest: str):
        super().__init__(unique_id, model)
        self.origin = origin
        self.dest = dest
        self.wait_time = 0
        self.delay_timer = 0
        self.crossed = False
        self.in_yellow_box = False
        self.route = []

        color_map = {
            "Utara":   "#3B82F6",
            "Barat":   "#22C55E",
            "Selatan": "#F59E0B",
            "Timur":   "#A855F7",
        }
        self.color = color_map.get(origin, "#6B7280")
        self.is_gridlocked = False

    # ------------------------------------------------------------------
    # FUNGSI UTAMA
    # ------------------------------------------------------------------
    def step(self):
        if self.crossed:
            return

        # A. Delay timer akibat bottleneck
        if self.delay_timer > 0:
            self.delay_timer -= 1
            self.wait_time += 1
            return

        current_pos = self.pos
        if current_pos is None:
            return

        in_yb = current_pos in self.model.yellow_box_cells
        self.in_yellow_box = in_yb

        # B. Tentukan sel berikutnya dari rute
        next_pos = self._get_next_pos(current_pos)
        if next_pos is None:
            self._exit()
            return

        # C. Cek lampu (Hanya berhenti jika sudah sampai di garis berhenti)
        if self._at_stopline(current_pos):
            green_dir = self.model.get_green_direction()
            
            # Skenario A: Utara belok kiri menerobos lampu merah
            if self.model.scenario == "A" and self.origin == "Utara" and self.dest == "Kiri":
                pass 
                
            # Skenario B: Utara belok kiri wajib ikut lampu
            elif self.model.scenario == "B" and self.origin == "Utara" and self.dest == "Kiri":
                if green_dir not in ("Utara", "Timur"):
                    self.wait_time += 1
                    return
                    
            # Aturan normal untuk lajur dan kendaraan lainnya
            else:
                if green_dir != self.origin:
                    self.wait_time += 1
                    return

        # D. Konflik Skenario A – bottleneck stokastik di yellow box
        if (self.model.scenario == "A"
                and self.origin == "Utara"
                and self.dest == "Kiri"
                and in_yb
                and self._check_conflict_traffic()):
            self.delay_timer = random.randint(3, 7)
            self.wait_time += 1
            self.color = "#EF4444"
            self.is_gridlocked = True
            return

        # E. Cek apakah sel depan kosong
        if not self.model.grid.is_cell_empty(next_pos):
            self.wait_time += 1
            if in_yb and self.model.get_green_direction() != self.origin:
                self.is_gridlocked = True
                self.color = "#EF4444"
            return

        # F. Gerak maju
        self.model.grid.move_agent(self, next_pos)
        self.is_gridlocked = False
        self.color = {
            "Utara": "#3B82F6",
            "Barat": "#22C55E",
            "Selatan": "#F59E0B",
            "Timur": "#A855F7",
        }.get(self.origin, "#6B7280")

        # Keluar jika sudah di akhir rute
        if self.route and next_pos == self.route[-1]:
            self._exit()

    # ------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------
    def _at_stopline(self, pos):
        """Mengecek apakah kendaraan tepat berada di garis berhenti lampu merah."""
        stoplines = {
            "Utara": (13, 15),
            "Barat": (9, 13),
            "Selatan": (11, 9),
            "Timur": (15, 11)
        }
        return pos == stoplines.get(self.origin)

    def _get_next_pos(self, current_pos):
        if not self.route:
            return None
        try:
            idx = self.route.index(current_pos)
            if idx + 1 < len(self.route):
                return self.route[idx + 1]
        except ValueError:
            pass
        return None

    def _near_intersection(self, pos):
        cx, cy = self.model.center
        x, y = pos
        return abs(x - cx) <= 3 and abs(y - cy) <= 3

    def _check_conflict_traffic(self):
        """Mengecek apakah ada kendaraan dari arah lain yang sedang menuju Jl. Agro (Timur)"""
        for cell in self.model.yellow_box_cells:
            for agent in self.model.grid.get_cell_list_contents([cell]):
                if isinstance(agent, VehicleAgent) and not agent.crossed:
                    # Konflik 1: Dari Barat (Teknika Sel) mau LURUS ke Timur (Agro)
                    if agent.origin == "Barat" and agent.dest == "Lurus":
                        return True
                    # Konflik 2: Dari Selatan (Persatuan) mau belok KANAN ke Timur (Agro)
                    if agent.origin == "Selatan" and agent.dest == "Kanan":
                        return True
        return False

    def _exit(self):
        if self.crossed:
            return
        self.crossed = True
        self.model.total_crossed += 1
        if self.wait_time > 5:
            self.model.gridlock_count += 1
        try:
            if self.pos is not None:
                self.model.grid.remove_agent(self)
        except Exception:
            pass
