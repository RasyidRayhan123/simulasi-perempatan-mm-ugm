import streamlit as st
from mesa import Agent, Model
from mesa.datacollection import DataCollector
import numpy as np
import pandas as pd
import time

# ==========================================
# 1. DEFINISI AGEN (KENDARAAN)
# ==========================================
class CarAgent(Agent):
    def __init__(self, model, origin, destination):
        super().__init__(model)
        self.origin = origin              # Asal: "Utara", "Barat", "Selatan"
        self.destination = destination    # Tujuan: "Agro" atau "Lurus"
        self.wait_time = 0                # Waktu tunggu (detik/tick)
        self.position = "Queue"           # Posisi: Queue -> YellowBox -> Cleared

    def step(self):
        # Setiap detik, jika belum lolos, waktu tunggu bertambah
        if self.position != "Cleared":
            self.wait_time += 1

# ==========================================
# 2. DEFINISI MODEL (PERSIMPANGAN)
# ==========================================
class IntersectionModel(Model):
    def __init__(self, skenario="Belok Kiri Jalan Terus", lambda_n=15, lambda_w=10, lambda_s=12):
        super().__init__() 
        self.skenario = skenario
        self.running = True
        
        # Parameter Distribusi Kedatangan (Poisson) per siklus (100 detik)
        self.lambda_n = lambda_n / 100  # Rata-rata kedatangan per detik
        self.lambda_w = lambda_w / 100
        self.lambda_s = lambda_s / 100
        
        # Zona Area
        self.queues = {"Utara": [], "Barat": [], "Selatan": []}
        self.yellow_box = [] # Maksimal 5 kendaraan
        self.cleared_cars = []
        
        # Variabel Lampu Lalu Lintas
        self.tick_count = 0
        self.light_state = "Utara" # Siklus: Utara -> Barat -> Selatan -> Timur (masing-masing 25 detik)
        
        # Metrik Output
        self.gridlock_count = 0
        
        # Data Collector untuk grafik Streamlit
        self.datacollector = DataCollector(
            model_reporters={
                "Rata-rata Waktu Tunggu (detik)": self.compute_avg_wait_time,
                "Antrean di Zona Tengah (Gridlock Risk)": lambda m: len(m.yellow_box),
                "Total Gridlock Terjadi": lambda m: m.gridlock_count
            }
        )

    def spawn_cars(self):
        """Membuat kendaraan baru menggunakan Distribusi Poisson dan Probabilitas Tujuan"""
        # Kedatangan dari Utara
        if np.random.poisson(self.lambda_n) > 0:
            dest = "Agro" if np.random.random() < 0.3 else "Lurus"
            car = CarAgent(self, "Utara", dest) # Hapus self.next_id()
            self.queues["Utara"].append(car)
            
        if np.random.poisson(self.lambda_w) > 0:
            dest = "Agro" if np.random.random() < 0.4 else "Lurus"
            car = CarAgent(self, "Barat", dest) # Hapus self.next_id()
            self.queues["Barat"].append(car)

    def update_lights(self):
        """Siklus lampu lalu lintas tiap 25 detik"""
        cycle_time = self.tick_count % 100
        if cycle_time < 25: self.light_state = "Utara"
        elif cycle_time < 50: self.light_state = "Barat"
        elif cycle_time < 75: self.light_state = "Selatan"
        else: self.light_state = "Timur"

    def process_movement(self):
        """Logika pergerakan dan Bottleneck / Gridlock"""
        # 1. Coba keluarkan kendaraan dari Yellow Box ke Jl. Agro (Bottleneck logic)
        if len(self.yellow_box) > 0:
            car_exiting = self.yellow_box[0]
            delay = np.random.uniform(3, 6) if self.skenario == "Belok Kiri Jalan Terus" and self.light_state in ["Barat", "Selatan"] else np.random.uniform(1, 2)            

            # Jika lolos delay acak (disederhanakan dengan probabilitas)
            if np.random.random() > (delay / 10): 
                car_exiting.position = "Cleared"
                self.cleared_cars.append(self.yellow_box.pop(0))

        # 2. Masukkan kendaraan dari antrean ke Yellow Box
        # Cek arah Barat
        if self.light_state == "Barat" and len(self.queues["Barat"]) > 0:
            if len(self.yellow_box) < 5: # Kapasitas tengah aman
                car = self.queues["Barat"].pop(0)
                car.position = "YellowBox"
                self.yellow_box.append(car)
            else:
                self.gridlock_count += 1 # Terjadi Spillback/Gridlock!
                
        # Cek arah Utara (Aturan Belok Kiri)
        if len(self.queues["Utara"]) > 0:
            front_car = self.queues["Utara"][0]
            if front_car.destination == "Agro":
                # Kapan dia boleh maju?
                can_move = False
                if self.skenario == "Belok Kiri Jalan Terus":
                    can_move = True # Selalu nyelonong
                elif self.skenario == "Belok Kiri Ikut Lampu":
                    can_move = (self.light_state == "Utara") # Nunggu lampu hijau
                    
                if can_move and len(self.yellow_box) < 5:
                    car = self.queues["Utara"].pop(0)
                    car.position = "YellowBox"
                    self.yellow_box.append(car)

    def compute_avg_wait_time(self):
        if not self.cleared_cars: return 0
        return np.mean([car.wait_time for car in self.cleared_cars])

    def step(self):
        self.spawn_cars()
        self.update_lights()
        self.process_movement()
        self.agents.shuffle_do("step")
        self.datacollector.collect(self)
        self.tick_count += 1

# ==========================================
# 3. ANTARMUKA STREAMLIT (UI)
# ==========================================
st.set_page_config(layout="wide", page_title="Simulasi Simpang UGM")
st.title("🚦 Simulasi Stokastik: Evaluasi Aturan Belok Kiri di Simpang MM UGM")

# Sidebar Interaktif
st.sidebar.header("⚙️ Parameter Simulasi")
scenario = st.sidebar.radio("Pilih Kebijakan/Skenario:", ("Belok Kiri Jalan Terus", "Belok Kiri Ikut Lampu"))
lambda_n = st.sidebar.slider("Laju Kendaraan Utara/Siklus (Poisson λ)", 5, 30, 15)
lambda_w = st.sidebar.slider("Laju Kendaraan Barat/Siklus (Poisson λ)", 5, 30, 10)
run_sim = st.sidebar.button("▶️ Jalankan Simulasi")

if run_sim:
    model = IntersectionModel(skenario=scenario, lambda_n=lambda_n, lambda_w=lambda_w)
    
    # Placeholder untuk grafik real-time
    col1, col2, col3 = st.columns(3)
    metric_wait = col1.empty()
    metric_gridlock = col2.empty()
    metric_yellow = col3.empty()
    
    chart_placeholder = st.empty()
    
    # Progress bar simulasi (misal kita simulasi 300 detik / 5 menit)
    progress_bar = st.progress(0)
    
    for i in range(300):
        model.step()
        data = model.datacollector.get_model_vars_dataframe()
        
        # Update UI setiap 10 tick agar tidak lag
        if i % 10 == 0:
            metric_wait.metric("Rata-rata Waktu Tunggu", f"{data['Rata-rata Waktu Tunggu (detik)'].iloc[-1]:.1f} dtk")
            metric_gridlock.metric("Kejadian Gridlock", f"{data['Total Gridlock Terjadi'].iloc[-1]} kali")
            metric_yellow.metric("Mobil Nyangkut di Tengah", f"{data['Antrean di Zona Tengah (Gridlock Risk)'].iloc[-1]} unit")
            
            chart_placeholder.line_chart(data[["Rata-rata Waktu Tunggu (detik)", "Antrean di Zona Tengah (Gridlock Risk)"]])
            
            progress_bar.progress((i + 1) / 300)
            time.sleep(0.05) # Efek animasi delay

    st.success(f"✅ Simulasi selesai! Skenario: {scenario} memunculkan total {model.gridlock_count} kejadian macet total di tengah persimpangan.")