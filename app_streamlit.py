# =================================================================
# app_streamlit.py  (BONUS - opsi Low-Code sesuai soal UAS)
#
# "Peta Interaktif Monitoring Kapasitas TMU dan Aksesibilitas RPTRA
#  di DKI Jakarta" -- versi Streamlit + Folium.
#
# Dibuat sebagai ALTERNATIF ke qgis2web khusus untuk fitur "Filter
# Dinamis" (dropdown Wilayah Administrasi & Status Kapasitas TMU)
# yang TIDAK didukung qgis2web (qgis2web hanya bisa toggle checkbox
# per-kategori/layer, bukan dropdown atribut). Data yang dipakai
# PERSIS SAMA dengan yang dimuat di QGIS lewat BUKA_DI_QGIS.py, jadi
# kedua versi akan selalu konsisten.
#
# CARA MENJALANKAN:
#   pip install streamlit folium streamlit-folium geopandas
#   streamlit run app_streamlit.py
# =================================================================

import json
from pathlib import Path

import folium
import geopandas as gpd
import streamlit as st
from folium.plugins import Fullscreen
from streamlit_folium import st_folium

BASE = Path(__file__).parent

st.set_page_config(page_title="Monitoring TMU & RPTRA DKI Jakarta", layout="wide")

# ------------------------------------------------------------------
# Load data (cache supaya tidak dibaca ulang tiap interaksi)
# ------------------------------------------------------------------
@st.cache_data
def load_data():
    tmu = gpd.read_file(BASE / "tmu_jakarta.geojson")
    rptra = gpd.read_file(BASE / "rptra_jakarta.geojson")
    buffer = gpd.read_file(BASE / "buffer_tmu_500m.geojson")
    kota = gpd.read_file(BASE / "batas_kota_jakarta.geojson")
    kelurahan = gpd.read_file(BASE / "batas_kelurahan_jakarta.geojson")
    with open(BASE / "ringkasan_statistik.json", encoding="utf-8") as f:
        ringkasan = json.load(f)
    return tmu, rptra, buffer, kota, kelurahan, ringkasan


tmu, rptra, buffer, kota, kelurahan, ringkasan = load_data()

STATUS_COLOR = {"Tersedia": "#2ecc71", "Waspada": "#f1c40f", "Kritis": "#e74c3c"}
FASILITAS_COLOR = {"Lengkap": "#3498db", "Terbatas": "#9b59b6"}

# ------------------------------------------------------------------
# Sidebar -- filter dinamis (dropdown asli, sesuai permintaan soal)
# ------------------------------------------------------------------
st.sidebar.title("Filter Peta")

daftar_wilayah = ["Semua Wilayah"] + sorted(tmu["wilayah"].unique().tolist())
wilayah_pilih = st.sidebar.selectbox("Wilayah Administrasi", daftar_wilayah)

daftar_status = ["Semua Status", "Tersedia", "Waspada", "Kritis"]
status_pilih = st.sidebar.selectbox("Status Kapasitas TMU", daftar_status)

st.sidebar.markdown("### Tampilkan Layer & Legenda")
show_kota = st.sidebar.checkbox("Batas Kota Administrasi", value=True)
show_kelurahan = st.sidebar.checkbox("Batas Kelurahan", value=False)
show_buffer = st.sidebar.checkbox("Buffer Eksklusi TMU (500m)", value=True)
show_tmu = st.sidebar.checkbox("Marker TMU", value=True)
show_rptra = st.sidebar.checkbox("Marker RPTRA", value=True)

# ------------------------------------------------------------------
# Terapkan filter
# ------------------------------------------------------------------
tmu_f = tmu.copy()
rptra_f = rptra.copy()
buffer_f = buffer.copy()

if wilayah_pilih != "Semua Wilayah":
    tmu_f = tmu_f[tmu_f["wilayah"] == wilayah_pilih]
    rptra_f = rptra_f[rptra_f["wilayah"] == wilayah_pilih]
    buffer_f = buffer_f[buffer_f["wilayah"] == wilayah_pilih]

if status_pilih != "Semua Status":
    tmu_f = tmu_f[tmu_f["status_kapasitas"] == status_pilih]
    buffer_f = buffer_f[buffer_f["status_kapasitas"] == status_pilih]

# ------------------------------------------------------------------
# Header + statistik ringkas
# ------------------------------------------------------------------
st.title("Monitoring Kapasitas TMU & Aksesibilitas RPTRA - DKI Jakarta")

col1, col2, col3, col4 = st.columns(4)
col1.metric("RPTRA Tampil", len(rptra_f))
col2.metric("TMU Tampil", len(tmu_f))
col3.metric("TMU Kritis (<10%)", int((tmu_f["status_kapasitas"] == "Kritis").sum()))
col4.metric("RPTRA <500m dr TMU", int(rptra_f["dalam_buffer_tmu"].sum()) if "dalam_buffer_tmu" in rptra_f else 0)

st.markdown(
    f"""**Ringkasan Eksekutif:** Dari {ringkasan['total_tmu']} TMU yang dipantau di DKI Jakarta,
    **{ringkasan['tmu_kritis']} TMU berstatus Kritis** (kapasitas tersisa di bawah 10%) dan
    memerlukan perluasan/relokasi segera, sementara **{ringkasan['tmu_tersedia']} TMU** masih
    berstatus Tersedia. Dari {ringkasan['total_rptra']} RPTRA yang terpantau,
    **{ringkasan['rptra_dalam_buffer_tmu']} RPTRA ({ringkasan['rptra_dalam_buffer_tmu']/ringkasan['total_rptra']*100:.1f}%)
    berada dalam radius 500 m dari TMU** dan berpotensi berada di zona yang kurang ideal
    (isu lingkungan/psikologis), sehingga perlu menjadi perhatian dalam perencanaan RPTRA baru."""
)

# ------------------------------------------------------------------
# Peta
# ------------------------------------------------------------------
m = folium.Map(location=[-6.2088, 106.8456], zoom_start=11, tiles="cartodbpositron")
Fullscreen().add_to(m)

if show_kota:
    folium.GeoJson(
        kota, name="Batas Kota Administrasi",
        style_function=lambda x: {"fillOpacity": 0, "color": "#222222", "weight": 1.5},
        tooltip=folium.GeoJsonTooltip(fields=["kota"]),
    ).add_to(m)

if show_kelurahan:
    folium.GeoJson(
        kelurahan, name="Batas Kelurahan",
        style_function=lambda x: {"fillOpacity": 0, "color": "#aaaaaa", "weight": 0.4, "dashArray": "2,2"},
        tooltip=folium.GeoJsonTooltip(fields=["kelurahan", "kecamatan"]),
    ).add_to(m)

if show_buffer:
    folium.GeoJson(
        buffer_f, name="Buffer Eksklusi TMU 500m",
        style_function=lambda x: {"fillColor": "#ff0000", "fillOpacity": 0.12, "color": "#cc0000", "weight": 0.6, "dashArray": "4,3"},
    ).add_to(m)

if show_tmu:
    fg_tmu = folium.FeatureGroup(name="Marker TMU")
    for _, row in tmu_f.iterrows():
        color = STATUS_COLOR.get(row["status_kapasitas"], "#888888")
        popup_html = (
            f"<b>{row['nama_tmu']}</b><br>"
            f"Luas Area: {row['luas_area_ha']} ha<br>"
            f"Status Kapasitas: <b>{row['status_kapasitas']}</b> ({row['kapasitas_tersisa_persen']}% tersisa)<br>"
            f"Tahun Berdiri: {row['tahun_berdiri']}<br>"
            f"Wilayah: {row['wilayah']}, Kec. {row['kecamatan']}"
        )
        folium.CircleMarker(
            location=[row.geometry.y, row.geometry.x],
            radius=6, color="white", weight=1, fill=True,
            fill_color=color, fill_opacity=0.95,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=row["nama_tmu"],
        ).add_to(fg_tmu)
    fg_tmu.add_to(m)

if show_rptra:
    fg_rptra = folium.FeatureGroup(name="Marker RPTRA")
    for _, row in rptra_f.iterrows():
        color = FASILITAS_COLOR.get(row["kategori_fasilitas"], "#888888")
        warn = " &#9888; &lt;500m dari TMU" if row.get("dalam_buffer_tmu") else ""
        popup_html = (
            f"<b>{row['nama_rptra']}</b><br>"
            f"Fasilitas Utama: {row['fasilitas_utama']}<br>"
            f"Kondisi: {row['kondisi']}<br>"
            f"Kategori: <b>{row['kategori_fasilitas']}</b>{warn}<br>"
            f"Wilayah: {row['wilayah']}, Kec. {row['kecamatan']}, Kel. {row['kelurahan']}"
        )
        folium.CircleMarker(
            location=[row.geometry.y, row.geometry.x],
            radius=3.2, color="white", weight=0.5, fill=True,
            fill_color=color, fill_opacity=0.9,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=row["nama_rptra"],
        ).add_to(fg_rptra)
    fg_rptra.add_to(m)

folium.LayerControl(collapsed=False).add_to(m)

# legenda manual (folium tidak punya legenda bawaan)
legend_html = """
<div style="position: fixed; bottom: 30px; left: 30px; z-index: 9999;
            background: white; padding: 10px 14px; border-radius: 6px;
            box-shadow: 0 1px 6px rgba(0,0,0,.3); font-size: 13px; font-family: Arial;">
  <b>Legenda</b><br>
  <span style="color:#2ecc71;">&#9679;</span> TMU Tersedia (&gt;30%)<br>
  <span style="color:#f1c40f;">&#9679;</span> TMU Waspada (10-30%)<br>
  <span style="color:#e74c3c;">&#9679;</span> TMU Kritis (&lt;10%)<br>
  <span style="color:#3498db;">&#9679;</span> RPTRA Fasilitas Lengkap<br>
  <span style="color:#9b59b6;">&#9679;</span> RPTRA Fasilitas Terbatas<br>
  <span style="color:#cc0000;">&#9634;</span> Buffer Eksklusi TMU 500m
</div>
"""
m.get_root().html.add_child(folium.Element(legend_html))

st_folium(m, use_container_width=True, height=650, returned_objects=[])
