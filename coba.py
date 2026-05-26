import streamlit as st
import mesa
import random
import time

# ==========================================
# 1. DEFINISI AGEN & MODEL (BACKEND)
# ==========================================
class VehicleAgent(mesa.Agent):
    def __init__(self, unique_id, model, arah_asal, tujuan):
        super().__init__(unique_id, model)
        self.arah_asal = arah_asal
        self.tujuan = tujuan
        self.delay_timer = 0

    def step(self):
        if self.delay_timer > 0:
            self.delay_timer -= 1
            return
        
        # Logika pergerakan sederhana (simulasi maju)
        # Di sini kita bisa menambahkan probabilitas delay stokastik nanti
        if self.model.skenario == "Jalan Terus" and self.arah_asal == "Utara":
            if self.model.lampu_hijau_saat_ini != "Utara" and random.random() < 0.3:
                self.delay_timer = random.randint(2, 4) # Terkena tunda/gridlock

class IntersectionModel(mesa.Model):
    def __init__(self, skenario, laju_kedatangan):
        super().__init__()
        self.skenario = skenario
        self.laju_kedatangan = laju_kedatangan
        self.schedule = mesa.time.RandomActivation(self)
        self.grid = mesa.space.MultiGrid(15, 15, torus=False)
        
        self.fase_lampu = ["Utara", "Barat", "Selatan", "Timur"]
        self.indeks_fase = 0
        self.timer_lampu = 0
        self.durasi_hijau = 5
        self.lampu_hijau_saat_ini = "Utara"
        self.current_id = 0
        self.total_gridlock = 0

    def step(self):
        # A. Update Siklus Lampu
        self.timer_lampu += 1
        if self.timer_lampu > self.durasi_hijau:
            self.timer_lampu = 0
            self.indeks_fase = (self.indeks_fase + 1) % 4
            
        self.lampu_hijau_saat_ini = self.fase_lampu[self.indeks_fase]

        # B. Spawner Kendaraan Berdasarkan Parameter Laju Input Slider
        if random.random() < (self.laju_kedatangan / 100):
            asal_pilihan = random.choice(["Utara", "Barat", "Selatan"])
            agen_baru = VehicleAgent(self.current_id, self, asal_pilihan, "Agro")
            self.schedule.add(agen_baru)
            self.current_id += 1

        # C. Hitung Potensi Gridlock (Jika memotong jalan saat lampu merah)
        if self.lampu_hijau_saat_ini != "Utara" and self.skenario == "Jalan Terus":
            self.total_gridlock += random.randint(0, 1)

        self.schedule.step()

# ==========================================
# 2. PENGATURAN ANTARMUKA WEB (FRONTEND STREAMLIT)
# ==========================================
st.set_page_config(page_title="Simulasi MM UGM", layout="wide")

st.title("🚦 Pemodelan Sistem Antrean Perempatan MM UGM")
st.caption("Evaluasi Efektivitas Kebijakan 'Belok Kiri Jalan Terus' Menggunakan Agent-Based Modeling")

# --- PANEL KIRI (SIDEBAR) ---
st.sidebar.header("🎛️ Parameter Input")
skenario_dipilih = st.sidebar.selectbox(
    "Pilih Skenario Lalu Lintas:",
    ["Jalan Terus", "Ikut Lampu Lalu Lintas"]
)

laju_input = st.sidebar.slider(
    "Laju Kedatangan Kendaraan (Probabilitas %):", 
    min_value=10, max_value=90, value=50, step=10
)

durasi_simulasi = st.sidebar.slider(
    "Durasi Detik Simulasi (Tick):", 
    min_value=10, max_value=50, value=20, step=5
)

Mulai_tombol = st.sidebar.button("▶️ Jalankan Simulasi")

# --- PANEL KANAN (MAIN AREA) ---
# Wadah kosong (placeholders) agar visual bisa diperbarui secara dinamis dinamis
kolom_metrik1, kolom_metrik2, kolom_metrik3 = st.columns(3)
status_lampu_box = kolom_metrik1.empty()
total_kendaraan_box = kolom_metrik2.empty()
gridlock_box = kolom_metrik3.empty()

st.subheader("📺 Animasi Pergerakan Arus")
animasi_box = st.empty()

# --- LOGIKA EKSEKUSI APLIKASI WEB ---
if Mulai_tombol:
    # Inisialisasi Ulang Model Setiap Kali Tombol Diklik
    model = IntersectionModel(skenario=skenario_dipilih, laju_kedatangan=laju_input)
    
    for tick in range(durasi_simulasi):
        # Jalankan 1 langkah simulasi backend
        model.step()
        
        # Perbarui Kartu Metrik di Halaman Web secara Real-time
        status_lampu_box.metric("🟢 Lampu Hijau Saat Ini", model.lampu_hijau_saat_ini)
        total_kendaraan_box.metric("🚗 Total Kendaraan Masuk", model.current_id)
        gridlock_box.metric("⚠️ Estimasi Kejadian Gridlock", model.total_gridlock)
        
        # Membuat representasi visual teks sederhana untuk pergerakan kendaraan
        log_visual = f"**[Detik {tick}]** Jalur Utara-Agro aktif. "
        log_visual += f"Ada {model.schedule.get_agent_count()} kendaraan aktif di dalam persimpangan.\n\n"
        
        # Tampilkan status ke komponen animasi
        animasi_box.info(log_visual)
        
        # Beri jeda waktu agar efek animasi berjalan natural (tidak langsung selesai)
        time.sleep(0.5)
        
    st.success("🎉 Simulasi selesai dijalankan! Silakan ubah parameter di panel kiri untuk analisis data lainnya.")
else:
    st.info("Atur parameter input di panel kiri lalu klik tombol **Jalankan Simulasi** untuk melihat hasilnya di sini.")