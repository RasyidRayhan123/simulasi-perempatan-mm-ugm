# Simulasi Perempatan MM UGM

## Cara Menjalankan

### 1. Aktifkan virtual environment
```bash
# Windows
sim_env\Scriptsctivate

# Mac/Linux
source sim_env/bin/activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Jalankan Streamlit
```bash
streamlit run app.py
```
Buka browser di http://localhost:8501

## Struktur File
-      - UI Streamlit (frontend interaktif)
-    - IntersectionModel (Mesa ABM)
-   - VehicleAgent (logika kendaraan)
- 

## Skenario
- **A**: Belok Kiri Jalan Terus (kondisi eksisting)
- **B**: Belok Kiri Ikut Lampu (usulan perbaikan)

## Parameter (dapat diubah via sidebar)
- Laju kedatangan per arah (Distribusi Poisson)
- Durasi hijau per fase (detik)
- Durasi simulasi (tick)
