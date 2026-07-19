# =================================================================
# SCRIPT PYTHON UNTUK QGIS
# "Peta Interaktif Monitoring Kapasitas TMU dan Aksesibilitas RPTRA
#  di DKI Jakarta" -- UAS SIG, Soal No. 1
#
# CARA PENGGUNAAN:
# 1. Buka QGIS Desktop
# 2. Menu: Plugins > Python Console > ikon "Open Script" (folder)
# 3. Pilih file ini: BUKA_DI_QGIS.py > klik Run (segitiga hijau)
# 4. Semua layer termuat otomatis dengan simbologi, label, dan popup
#    sesuai spesifikasi soal (siap langsung diekspor lewat qgis2web)
# 5. Simpan: File > Save As > pilih format .qgz
#
# LANGKAH SELANJUTNYA (lihat PANDUAN_LENGKAP.md untuk detail penuh):
#   -> Web > qgis2web > Create web map, atur popup = "Maptip",
#      centang semua layer di "Overlays", lalu Export/Update preview.
# =================================================================

import os
from qgis.core import (
    QgsProject, QgsVectorLayer, QgsRasterLayer,
    QgsMarkerSymbol, QgsFillSymbol,
    QgsRendererCategory, QgsCategorizedSymbolRenderer,
    QgsCoordinateReferenceSystem, QgsPalLayerSettings,
    QgsVectorLayerSimpleLabeling, QgsTextFormat,
    QgsLayerTreeGroup,
)
from qgis.PyQt.QtGui import QColor, QFont
from qgis.utils import iface

script_dir = os.path.dirname(os.path.abspath(__file__))

FILES = {
    "batas_kota":     os.path.join(script_dir, "batas_kota_jakarta.geojson"),
    "batas_kelurahan": os.path.join(script_dir, "batas_kelurahan_jakarta.geojson"),
    "buffer_tmu":     os.path.join(script_dir, "buffer_tmu_500m.geojson"),
    "tmu":            os.path.join(script_dir, "tmu_jakarta.geojson"),
    "rptra":          os.path.join(script_dir, "rptra_jakarta.geojson"),
}

project = QgsProject.instance()
project.setTitle("Peta Interaktif Monitoring Kapasitas TMU & Aksesibilitas RPTRA - DKI Jakarta")
project.setCrs(QgsCoordinateReferenceSystem("EPSG:4326"))

root = project.layerTreeRoot()
layers_added = []


def buat_label(layer, field, ukuran=7, warna="#222222", buffer_putih=True, min_scale=None):
    settings = QgsPalLayerSettings()
    settings.fieldName = field
    tf = QgsTextFormat()
    tf.setFont(QFont("Arial", ukuran))
    tf.setSize(ukuran)
    tf.setColor(QColor(warna))
    if buffer_putih:
        buf = tf.buffer()
        buf.setEnabled(True)
        buf.setSize(1.0)
        buf.setColor(QColor("#ffffff"))
        tf.setBuffer(buf)
    settings.setFormat(tf)
    labeling = QgsVectorLayerSimpleLabeling(settings)
    layer.setLabeling(labeling)
    layer.setLabelsEnabled(True)


def buat_maptip(layer, html):
    """Maptip = sumber popup saat diekspor lewat qgis2web (pilih 'Maptip'
    sebagai Popup content pada dialog export qgis2web)."""
    layer.setMapTipTemplate(html)


# ============================================================
# GROUP 1: KONTEKS WILAYAH (Batas Kota & Batas Kelurahan)
#          -- cocok untuk dimatikan agar fokus ke TMU/RPTRA,
#             sesuai instruksi soal bagian "Layer Control"
# ============================================================
grp_konteks = root.insertGroup(0, "1. Konteks Wilayah")

lyr_kota = QgsVectorLayer(FILES["batas_kota"], "Batas Kota Administrasi", "ogr")
if lyr_kota.isValid():
    sym = QgsFillSymbol.createSimple({
        "color": "0,0,0,0", "outline_color": "#222222",
        "outline_width": "0.9", "outline_style": "solid",
    })
    lyr_kota.renderer().setSymbol(sym)
    project.addMapLayer(lyr_kota, False)
    grp_konteks.addLayer(lyr_kota)
    buat_label(lyr_kota, "kota", ukuran=9, warna="#000000")
    layers_added.append(lyr_kota.name())
    print("OK  Batas Kota Administrasi dimuat")

lyr_kel = QgsVectorLayer(FILES["batas_kelurahan"], "Batas Kelurahan", "ogr")
if lyr_kel.isValid():
    sym = QgsFillSymbol.createSimple({
        "color": "0,0,0,0", "outline_color": "#aaaaaa",
        "outline_width": "0.25", "outline_style": "dot",
    })
    lyr_kel.renderer().setSymbol(sym)
    lyr_kel.setLabelsEnabled(False)
    project.addMapLayer(lyr_kel, False)
    grp_konteks.addLayer(lyr_kel)
    layers_added.append(lyr_kel.name())
    print("OK  Batas Kelurahan dimuat (nonaktifkan jika peta terasa ramai)")
    lyr_kel.setItemVisibilityChecked(False)  # default OFF, sesuai contoh soal

# ============================================================
# GROUP 2: BUFFER EKSKLUSI TMU 500 M (poligon transparan)
# ============================================================
grp_buffer = root.insertGroup(1, "2. Buffer Eksklusi TMU (500 m)")

lyr_buffer = QgsVectorLayer(FILES["buffer_tmu"], "Buffer Eksklusi TMU 500m", "ogr")
if lyr_buffer.isValid():
    sym = QgsFillSymbol.createSimple({
        "color": "255,0,0,35",              # merah transparan
        "outline_color": "#cc0000",
        "outline_width": "0.4",
        "outline_style": "dash",
    })
    lyr_buffer.renderer().setSymbol(sym)
    project.addMapLayer(lyr_buffer, False)
    grp_buffer.addLayer(lyr_buffer)
    layers_added.append(lyr_buffer.name())
    print("OK  Buffer Eksklusi TMU 500m dimuat")

# ============================================================
# GROUP 3: TMU (Taman Makam Umum) -- kategori status kapasitas
#   Hijau = Tersedia (>30%) | Kuning = Waspada (10-30%) | Merah = Kritis (<10%)
# ============================================================
grp_tmu = root.insertGroup(2, "3. TMU - Status Kapasitas")

lyr_tmu = QgsVectorLayer(FILES["tmu"], "TMU (Taman Makam Umum)", "ogr")
if lyr_tmu.isValid():
    status_style = {
        "Tersedia": ("#2ecc71", "circle"),   # hijau, kapasitas > 30%
        "Waspada":  ("#f1c40f", "circle"),   # kuning, 10-30%
        "Kritis":   ("#e74c3c", "circle"),   # merah, < 10%
    }
    categories = []
    for status, (color, shape) in status_style.items():
        sym = QgsMarkerSymbol.createSimple({
            "name": shape, "color": color, "size": "4.5",
            "outline_color": "#ffffff", "outline_width": "0.6",
        })
        categories.append(QgsRendererCategory(status, sym, status))
    lyr_tmu.setRenderer(QgsCategorizedSymbolRenderer("status_kapasitas", categories))
    project.addMapLayer(lyr_tmu, False)
    grp_tmu.addLayer(lyr_tmu)
    buat_label(lyr_tmu, "nama_tmu", ukuran=6, warna="#7a0000")
    buat_maptip(lyr_tmu, """
        <div style="font-family:Arial;font-size:12px">
        <b>[% "nama_tmu" %]</b><br/>
        Luas Area: [% "luas_area_ha" %] ha ([% "luas_area_m2" %] m&sup2;)<br/>
        Status Kapasitas: <b>[% "status_kapasitas" %]</b> ([% "kapasitas_tersisa_persen" %]% tersisa)<br/>
        Tahun Berdiri: [% "tahun_berdiri" %]<br/>
        Wilayah: [% "wilayah" %], Kec. [% "kecamatan" %]
        </div>
    """)
    layers_added.append(lyr_tmu.name())
    print("OK  Layer TMU dimuat (kategori: Tersedia/Waspada/Kritis)")

# ============================================================
# GROUP 4: RPTRA -- kategori fasilitas
#   Biru = Fasilitas Lengkap | Ungu = Fasilitas Terbatas
# ============================================================
grp_rptra = root.insertGroup(3, "4. RPTRA - Kategori Fasilitas")

lyr_rptra = QgsVectorLayer(FILES["rptra"], "RPTRA (Ruang Publik Ramah Anak)", "ogr")
if lyr_rptra.isValid():
    fac_style = {
        "Lengkap": "#3498db",     # biru
        "Terbatas": "#9b59b6",    # ungu
    }
    categories = []
    for kat, color in fac_style.items():
        sym = QgsMarkerSymbol.createSimple({
            "name": "circle", "color": color, "size": "3.2",
            "outline_color": "#ffffff", "outline_width": "0.4",
        })
        categories.append(QgsRendererCategory(kat, sym, f"Fasilitas {kat}"))
    lyr_rptra.setRenderer(QgsCategorizedSymbolRenderer("kategori_fasilitas", categories))
    project.addMapLayer(lyr_rptra, False)
    grp_rptra.addLayer(lyr_rptra)
    buat_maptip(lyr_rptra, """
        <div style="font-family:Arial;font-size:12px">
        <b>[% "nama_rptra" %]</b><br/>
        Fasilitas Utama: [% "fasilitas_utama" %]<br/>
        Kondisi: [% "kondisi" %]<br/>
        Kategori: <b>[% "kategori_fasilitas" %]</b><br/>
        Wilayah: [% "wilayah" %], Kec. [% "kecamatan" %], Kel. [% "kelurahan" %]<br/>
        <i>[% CASE WHEN "dalam_buffer_tmu" THEN '&#9888; berada &lt;500m dari TMU' ELSE '' END %]</i>
        </div>
    """)
    layers_added.append(lyr_rptra.name())
    print("OK  Layer RPTRA dimuat (kategori: Lengkap/Terbatas)")

# ============================================================
# 5. BASEMAP OpenStreetMap
# ============================================================
try:
    uri = "type=xyz&url=https://tile.openstreetmap.org/{z}/{x}/{y}.png&zmax=19&zmin=0"
    lyr_osm = QgsRasterLayer(uri, "OpenStreetMap (Basemap)", "wms")
    if lyr_osm.isValid():
        project.addMapLayer(lyr_osm, False)
        root.insertLayer(len(root.children()), lyr_osm)
        layers_added.append(lyr_osm.name())
        print("OK  Basemap OSM dimuat")
except Exception as e:
    print(f"   (Basemap OSM gagal: {e})")

# ============================================================
# 6. ZOOM KE DKI JAKARTA
# ============================================================
try:
    canvas = iface.mapCanvas()
    canvas.setExtent(lyr_kota.extent() if lyr_kota.isValid() else canvas.extent())
    canvas.refresh()
except Exception:
    pass

# ============================================================
# 7. RINGKASAN STATISTIK DI CONSOLE (untuk paragraf eksekutif)
# ============================================================
try:
    import json
    with open(os.path.join(script_dir, "ringkasan_statistik.json"), encoding="utf-8") as f:
        r = json.load(f)
    print("\n" + "-" * 60)
    print("RINGKASAN EKSEKUTIF (dari ringkasan_statistik.json):")
    print(f"  Total TMU  : {r['total_tmu']}  (Kritis={r['tmu_kritis']}, "
          f"Waspada={r['tmu_waspada']}, Tersedia={r['tmu_tersedia']})")
    print(f"  Total RPTRA: {r['total_rptra']}  (Lengkap={r['rptra_lengkap']}, "
          f"Terbatas={r['rptra_terbatas']})")
    print(f"  RPTRA dalam radius 500m dari TMU: {r['rptra_dalam_buffer_tmu']}")
    for w, s in r["per_wilayah"].items():
        print(f"    {w}: {s['jumlah_tmu']} TMU ({s['tmu_kritis']} kritis), "
              f"{s['jumlah_rptra']} RPTRA ({s['rptra_dalam_buffer_tmu']} dlm buffer)")
    print("-" * 60)
except Exception as e:
    print(f"   (Tidak bisa membaca ringkasan_statistik.json: {e})")

print("\n" + "=" * 60)
print("PROYEK BERHASIL DIMUAT!")
print("=" * 60)
print(f"Layer dimuat ({len(layers_added)}):")
for l in layers_added:
    print(f"  - {l}")
print("\nLANGKAH SELANJUTNYA:")
print("  1. File > Save As > format .qgz")
print("  2. Tambahkan judul peta, legenda, skala via Layout Manager")
print("     (jika screenshot untuk laporan diambil dari Print Layout)")
print("  3. Web > qgis2web > Create web map untuk ekspor ke Leaflet")
print("     (lihat PANDUAN_LENGKAP.md bagian 'Ekspor via qgis2web')")
print("=" * 60)
