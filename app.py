"""
app.py
UI Streamlit untuk Simulasi Perempatan MM UGM
Teknik Pemodelan & Simulasi - UGM
Mesa 2.3 + Streamlit
"""

import streamlit as st
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import to_rgba
from model import IntersectionModel, GRID_SIZE, YELLOW_BOX, ENTRY_POINTS, CENTER

# ─────────────────────────────────────────────
# KONFIGURASI HALAMAN
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Simulasi Perempatan MM UGM",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# CSS KUSTOM
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

h1, h2, h3, .big-title {
    font-family: 'Space Mono', monospace !important;
}

/* Header utama */
.main-header {
    background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 50%, #0f172a 100%);
    border-radius: 16px;
    padding: 24px 32px;
    margin-bottom: 20px;
    border: 1px solid #334155;
    position: relative;
    overflow: hidden;
}
.main-header::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle at 30% 50%, rgba(59,130,246,0.08) 0%, transparent 60%);
}
.main-header h1 {
    color: #f1f5f9;
    font-size: 1.4rem;
    margin: 0;
    font-family: 'Space Mono', monospace !important;
    letter-spacing: -0.5px;
}
.main-header p {
    color: #94a3b8;
    font-size: 0.85rem;
    margin: 4px 0 0 0;
}

/* KPI cards */
.kpi-card {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 16px 20px;
    text-align: center;
}
.kpi-value {
    font-family: 'Space Mono', monospace;
    font-size: 2rem;
    font-weight: 700;
    line-height: 1;
}
.kpi-label {
    font-size: 0.75rem;
    color: #94a3b8;
    margin-top: 4px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.kpi-red   { color: #ef4444; }
.kpi-blue  { color: #60a5fa; }
.kpi-green { color: #34d399; }
.kpi-amber { color: #fbbf24; }

/* Badge skenario */
.badge-a {
    background: #dc2626;
    color: white;
    border-radius: 6px;
    padding: 3px 10px;
    font-size: 0.8rem;
    font-family: 'Space Mono', monospace;
    font-weight: 700;
}
.badge-b {
    background: #16a34a;
    color: white;
    border-radius: 6px;
    padding: 3px 10px;
    font-size: 0.8rem;
    font-family: 'Space Mono', monospace;
    font-weight: 700;
}

/* Lampu lalu lintas */
.light-container {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    margin: 8px 0;
}
.light-item {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.8rem;
}
.dot-green  { width:12px; height:12px; border-radius:50%; background:#22c55e; display:inline-block; box-shadow: 0 0 6px #22c55e; }
.dot-red    { width:12px; height:12px; border-radius:50%; background:#ef4444; display:inline-block; }

/* Info box */
.info-box {
    background: #0f172a;
    border-left: 3px solid #3b82f6;
    border-radius: 0 8px 8px 0;
    padding: 12px 16px;
    font-size: 0.82rem;
    color: #cbd5e1;
    margin: 8px 0;
}

/* Section title */
.section-title {
    font-family: 'Space Mono', monospace;
    font-size: 0.85rem;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin: 16px 0 8px 0;
    border-bottom: 1px solid #1e293b;
    padding-bottom: 6px;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🚦 Simulasi Stokastik Perempatan MM UGM</h1>
    <p>Evaluasi Efektivitas Kebijakan "Belok Kiri Jalan Terus" · Jl. Kaliurang ↔ Jl. Agro · Teknik Pemodelan & Simulasi</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SIDEBAR – PANEL KONTROL
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="section-title">⚙️ Kontrol Simulasi</div>', unsafe_allow_html=True)

    scenario = st.radio(
        "Kebijakan Lalu Lintas",
        options=["A", "B"],
        format_func=lambda x: (
            "Skenario A — Belok Kiri Jalan Terus"
            if x == "A"
            else "Skenario B — Belok Kiri Ikut Lampu"
        ),
        help="Skenario A: kendaraan dari Kaliurang langsung belok kiri.\nSkenario B: harus menunggu lampu hijau."
    )

    st.markdown('<div class="section-title">🚗 Laju Kedatangan Kendaraan</div>', unsafe_allow_html=True)
    st.caption("Rata-rata kendaraan per siklus (Distribusi Poisson λ)")

    arr_north  = st.slider("Utara — Jl. Kaliurang",  min_value=2, max_value=30, value=12, step=1)
    arr_west   = st.slider("Barat — Jl. Teknika Sel.", min_value=2, max_value=30, value=8,  step=1)
    arr_south  = st.slider("Selatan — Jl. Persatuan", min_value=2, max_value=30, value=8,  step=1)
    arr_east   = st.slider("Timur — Jl. Agro",        min_value=2, max_value=30, value=4,  step=1)

    st.markdown('<div class="section-title">🔴 Siklus Lampu</div>', unsafe_allow_html=True)
    green_dur = st.slider("Durasi Hijau per Arah (detik)", min_value=10, max_value=60, value=25, step=5)

    st.markdown('<div class="section-title">▶️ Eksekusi</div>', unsafe_allow_html=True)
    max_ticks = st.slider("Durasi Simulasi (tick)", min_value=50, max_value=500, value=200, step=50)
    speed     = st.slider("Kecepatan Animasi", min_value=1, max_value=10, value=5,
                           help="1 = lambat (jelas), 10 = cepat (ringkas)")

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        run_btn = st.button("▶ Mulai", use_container_width=True, type="primary")
    with col_btn2:
        stop_btn = st.button("⏹ Stop", use_container_width=True)

    st.markdown("---")
    st.markdown("""
    <div class="info-box">
    <b>Legenda Warna Kendaraan</b><br>
    🔵 Utara (Kaliurang) &nbsp;&nbsp; 🟢 Barat (Teknika)<br>
    🟡 Selatan (Persatuan) &nbsp; 🟣 Timur (Agro)<br>
    🔴 Terjebak / Gridlock
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="info-box">
    <b>Hipotesis Utama</b><br>
    Skenario A memicu gridlock di Yellow Box karena kendaraan Utara (belok kiri) berpapasan
    dengan arus Barat/Selatan → menghambat seluruh perempatan.
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SESSION STATE – simpan model & histori
# ─────────────────────────────────────────────
if "model" not in st.session_state:
    st.session_state.model = None
if "running" not in st.session_state:
    st.session_state.running = False
if "gl_history" not in st.session_state:
    st.session_state.gl_history = []
if "wait_history" not in st.session_state:
    st.session_state.wait_history = []
if "crossed_history" not in st.session_state:
    st.session_state.crossed_history = []

if run_btn:
    st.session_state.model = IntersectionModel(
        scenario=scenario,
        arrival_north=arr_north,
        arrival_west=arr_west,
        arrival_south=arr_south,
        arrival_east=arr_east,
        green_duration=green_dur,
    )
    st.session_state.running = True
    st.session_state.gl_history = []
    st.session_state.wait_history = []
    st.session_state.crossed_history = []

if stop_btn:
    st.session_state.running = False

# ─────────────────────────────────────────────
# LAYOUT UTAMA: KPI + Animasi + Grafik
# ─────────────────────────────────────────────

# ── Baris KPI ──────────────────────────────────────────
kpi_row = st.columns(4)
kpi_gl     = kpi_row[0].empty()
kpi_wait   = kpi_row[1].empty()
kpi_cross  = kpi_row[2].empty()
kpi_tick   = kpi_row[3].empty()

# ── Lampu Lalu Lintas Real-time ─────────────────────────
light_placeholder = st.empty()

# ── Animasi Grid ────────────────────────────────────────
main_cols = st.columns([3, 2])
with main_cols[0]:
    st.markdown('<div class="section-title">🗺️ Animasi Persimpangan (Grid 20×20)</div>', unsafe_allow_html=True)
    grid_placeholder = st.empty()

with main_cols[1]:
    st.markdown('<div class="section-title">📊 Grafik Real-time</div>', unsafe_allow_html=True)
    chart_placeholder = st.empty()

# ── Status bar ──────────────────────────────────────────
status_bar = st.empty()

# ─────────────────────────────────────────────
# FUNGSI VISUALISASI GRID
# ─────────────────────────────────────────────

def render_grid(model: IntersectionModel):
    """Gambar grid persimpangan sebagai matplotlib figure."""
    gs = model.grid_size
    fig, ax = plt.subplots(figsize=(6, 6))
    fig.patch.set_facecolor("#0f172a")
    ax.set_facecolor("#0f172a")

    # Gambar aspal (latar)
    for x in range(gs):
        for y in range(gs):
            is_road = _is_road(x, y)
            color = "#1e293b" if is_road else "#0a0f1e"
            rect = plt.Rectangle((x, y), 1, 1, color=color, linewidth=0)
            ax.add_patch(rect)

    # Yellow box
    for (bx, by) in YELLOW_BOX:
        rect = plt.Rectangle((bx, by), 1, 1,
                               facecolor="#fbbf2418", edgecolor="#fbbf24",
                               linewidth=0.3)
        ax.add_patch(rect)

    # Garis putih marka jalan
    _draw_road_markings(ax, gs)

    # Kendaraan
    matrix = model.get_grid_matrix()
    for row_i, row in enumerate(matrix):
        for col_i, cell in enumerate(row):
            if cell:
                cx_v = col_i + 0.5
                cy_v = row_i + 0.5
                color = cell["color"]
                circle = plt.Circle((cx_v, cy_v), 0.38,
                                     color=color, zorder=5)
                ax.add_patch(circle)
                if cell["gridlocked"]:
                    ring = plt.Circle((cx_v, cy_v), 0.45,
                                       color="#ef4444", fill=False,
                                       linewidth=1.5, zorder=6)
                    ax.add_patch(ring)

    # Label lampu
    lights = model.get_light_state()
    _draw_traffic_lights(ax, lights)

    ax.set_xlim(0, gs)
    ax.set_ylim(0, gs)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(
        f"Skenario {'A — Belok Kiri Jalan Terus' if model.scenario == 'A' else 'B — Ikut Lampu'}  |  Tick {model.tick}",
        color="#94a3b8",
        fontsize=9,
        pad=6,
        fontfamily="monospace",
    )
    plt.tight_layout(pad=0.5)
    return fig


def _is_road(x, y):
    """Tentukan apakah sel (x,y) adalah jalan berdasarkan grid 25x25."""
    # Rentang jalan diperlebar dari x=10 sampai 14 dan y=10 sampai 14
    if 10 <= x <= 14: return True
    if 10 <= y <= 14: return True
    return False

def _draw_road_markings(ax, gs):
    """Gambar garis marka pembatas jalur."""
    # Garis pembatas (median) di tengah jalan
    ax.plot([0, gs], [12, 12], color="#334155", lw=1.2, linestyle="-", zorder=2)
    ax.plot([12, 12], [0, gs], color="#334155", lw=1.2, linestyle="-", zorder=2)
    
    # Border yellow box disinkronkan dari x=10 sampai 14 (lebar 5)
    yb_rect = plt.Rectangle((10, 10), 5, 5,
                              facecolor="none", edgecolor="#fbbf24",
                              linewidth=1.2, linestyle="--", zorder=3)
    ax.add_patch(yb_rect)
    ax.text(12.5, 12.5, "YELLOW\nBOX", color="#fbbf2466",
            ha="center", va="center", fontsize=6.5,
            fontfamily="monospace", zorder=4)

def _draw_traffic_lights(ax, lights):
    """Gambar indikator lampu persis di area entry points agar rapi."""
    positions = {
        "Utara":   (13, 24, "U↓"),
        "Barat":   (0, 13, "B→"),
        "Selatan": (11, 0, "S↑"),
        "Timur":   (24, 11, "←T"),
    }
    for direction, (lx, ly, label) in positions.items():
        clr = "#22c55e" if lights[direction] == "hijau" else "#ef4444"
        circle = plt.Circle((lx, ly), 0.7, color=clr, zorder=8)
        ax.add_patch(circle)
        ax.text(lx, ly, label, ha="center", va="center",
                fontsize=4.5, color="white", fontweight="bold", zorder=9)


def render_charts(gl_hist, wait_hist, crossed_hist):
    """Render grafik histori gridlock, wait, lolos."""
    fig, axes = plt.subplots(3, 1, figsize=(5, 6))
    fig.patch.set_facecolor("#0f172a")

    datasets = [
        (gl_hist,      "#ef4444", "Gridlock Aktif",       "count"),
        (wait_hist,    "#fbbf24", "Rata-rata Waktu Tunda (tick)", "detik"),
        (crossed_hist, "#34d399", "Total Kendaraan Lolos", "unit"),
    ]

    for ax, (data, color, title, unit) in zip(axes, datasets):
        ax.set_facecolor("#0f172a")
        ax.spines[:].set_color("#1e293b")
        ax.tick_params(colors="#64748b", labelsize=7)
        if data:
            ax.plot(data, color=color, lw=1.5)
            ax.fill_between(range(len(data)), data,
                             alpha=0.15, color=color)
        ax.set_title(title, color="#94a3b8", fontsize=8,
                     fontfamily="monospace", pad=3)
        ax.set_ylabel(unit, color="#64748b", fontsize=7)

    plt.tight_layout(pad=0.8)
    return fig


def render_kpis(model, placeholder_map):
    gl  = model._count_active_gridlock()
    wt  = model._avg_wait()
    cr  = model.total_crossed
    t   = model.tick

    placeholder_map["gl"].markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value kpi-red">{gl}</div>
        <div class="kpi-label">⛔ Gridlock Aktif</div>
    </div>""", unsafe_allow_html=True)

    placeholder_map["wait"].markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value kpi-amber">{wt:.1f}</div>
        <div class="kpi-label">⏱ Rata-rata Tunda (tick)</div>
    </div>""", unsafe_allow_html=True)

    placeholder_map["cross"].markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value kpi-green">{cr}</div>
        <div class="kpi-label">✅ Kendaraan Lolos</div>
    </div>""", unsafe_allow_html=True)

    placeholder_map["tick"].markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value kpi-blue">{t}</div>
        <div class="kpi-label">🕐 Tick / Detik</div>
    </div>""", unsafe_allow_html=True)


def render_lights(model):
    lights = model.get_light_state()
    icons  = {"hijau": '<span class="dot-green"></span>', "merah": '<span class="dot-red"></span>'}
    names  = {"Utara": "Utara (Kaliurang)", "Barat": "Barat (Teknika)", "Selatan": "Selatan (Persatuan)", "Timur": "Timur (Agro)"}
    items = "".join(
        f'<div class="light-item">{icons[state]} {names[d]}</div>'
        for d, state in lights.items()
    )
    light_placeholder.markdown(
        f'<div class="light-container">{items}</div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────
# LOOP SIMULASI UTAMA
# ─────────────────────────────────────────────

if st.session_state.running and st.session_state.model is not None:
    model = st.session_state.model
    kpi_holders = {
        "gl": kpi_gl, "wait": kpi_wait,
        "cross": kpi_cross, "tick": kpi_tick,
    }
    delay = max(0.02, 0.2 - speed * 0.018)   # 0.02s – 0.18s

    while st.session_state.running and model.tick < max_ticks:
        model.step()

        # Update histori
        st.session_state.gl_history      = model.gridlock_history
        st.session_state.wait_history    = model.wait_history
        st.session_state.crossed_history = model.crossed_history

        # Render tiap N tick agar tidak terlalu lambat
        render_every = max(1, 11 - speed)
        if model.tick % render_every == 0:
            render_kpis(model, kpi_holders)
            render_lights(model)
            grid_fig = render_grid(model)
            grid_placeholder.pyplot(grid_fig, use_container_width=True)
            plt.close(grid_fig)

            chart_fig = render_charts(
                st.session_state.gl_history,
                st.session_state.wait_history,
                st.session_state.crossed_history,
            )
            chart_placeholder.pyplot(chart_fig, use_container_width=True)
            plt.close(chart_fig)

        status_bar.markdown(
            f"⏳ Simulasi berjalan... tick **{model.tick}** / {max_ticks}"
        )
        time.sleep(delay)

    st.session_state.running = False
    status_bar.success(f"✅ Simulasi selesai! Total {model.tick} tick — {model.total_crossed} kendaraan lolos, {model.gridlock_count} gridlock tercatat.")

    # ─── Tampilkan Ringkasan Analisis ───
    st.markdown("---")
    st.markdown('<div class="section-title">📋 Ringkasan Hasil & Analisis</div>', unsafe_allow_html=True)

    df_result = model.datacollector.get_model_vars_dataframe()
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("**Statistik Akhir**")
        summary = {
            "Skenario": f"{'A — Belok Kiri Jalan Terus' if model.scenario == 'A' else 'B — Ikut Lampu'}",
            "Total Tick": model.tick,
            "Total Kendaraan Lolos": model.total_crossed,
            "Total Gridlock Tercatat": model.gridlock_count,
            "Gridlock Aktif Max": int(max(model.gridlock_history)) if model.gridlock_history else 0,
            "Rata-rata Tunda Max (tick)": f"{max(model.wait_history):.1f}" if model.wait_history else "0",
        }
        st.table(pd.DataFrame(summary.items(), columns=["Metrik", "Nilai"]))

    with c2:
        if not df_result.empty:
            st.markdown("**Grafik Gridlock vs Waktu**")
            fig2, ax2 = plt.subplots(figsize=(5, 2.5))
            fig2.patch.set_facecolor("#0f172a")
            ax2.set_facecolor("#0f172a")
            ax2.plot(df_result["Gridlock_Aktif"].values, color="#ef4444", lw=1.5)
            ax2.fill_between(
                range(len(df_result)),
                df_result["Gridlock_Aktif"].values,
                alpha=0.2, color="#ef4444",
            )
            ax2.set_xlabel("Tick", color="#64748b", fontsize=8)
            ax2.set_ylabel("Gridlock", color="#64748b", fontsize=8)
            ax2.tick_params(colors="#64748b", labelsize=7)
            ax2.spines[:].set_color("#1e293b")
            st.pyplot(fig2, use_container_width=True)
            plt.close(fig2)

    # Insight otomatis
    gl_max = int(max(model.gridlock_history)) if model.gridlock_history else 0
    insight_color = "#ef444433" if model.scenario == "A" else "#16a34a33"
    insight_border = "#ef4444" if model.scenario == "A" else "#22c55e"
    insight_text = (
        f"⚠️ Skenario A menghasilkan <b>{gl_max} gridlock aktif maksimum</b>. "
        "Kendaraan dari Utara yang belok kiri memicu bottleneck di Yellow Box "
        "dan menghambat arus dari Teknika Selatan & Persatuan."
        if model.scenario == "A"
        else f"✅ Skenario B menghasilkan <b>{gl_max} gridlock aktif maksimum</b>. "
        "Dengan kendaraan Utara mengikuti lampu, konflik di Yellow Box berkurang "
        "dan arus dari Teknika Selatan & Persatuan menjadi lebih lancar."
    )
    st.markdown(
        f'<div style="background:{insight_color}; border-left: 4px solid {insight_border}; '
        f'padding:14px 18px; border-radius:0 10px 10px 0; font-size:0.88rem; color:#e2e8f0; margin-top:8px;">'
        f'{insight_text}</div>',
        unsafe_allow_html=True,
    )

    # Download data
    st.markdown("---")
    csv = df_result.to_csv(index_label="Tick")
    st.download_button(
        "⬇ Download Data Simulasi (CSV)",
        data=csv,
        file_name=f"simulasi_mmuigm_skenario{model.scenario}.csv",
        mime="text/csv",
    )

elif not st.session_state.running:
    # Tampilan idle
    st.markdown("""
    <div style="text-align:center; padding: 60px 20px; color: #334155;">
        <div style="font-size: 3rem; margin-bottom: 16px;">🚦</div>
        <div style="font-family: monospace; font-size: 1rem; color: #475569;">
            Atur parameter di sidebar, lalu tekan <b>▶ Mulai</b>
        </div>
        <div style="font-size: 0.8rem; color:#334155; margin-top: 12px;">
            Skenario A = Belok Kiri Jalan Terus &nbsp;|&nbsp; Skenario B = Ikut Lampu Merah
        </div>
    </div>
    """, unsafe_allow_html=True)
