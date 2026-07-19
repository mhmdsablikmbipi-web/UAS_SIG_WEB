# =================================================================
# SIAPKAN_BATAS_WILAYAH.py
#
# Membuat layer konteks "Batas Kelurahan" & "Batas Kota Administrasi"
# menggunakan teknik Voronoi/Thiessen polygon dari titik tengah
# 267 kelurahan DKI Jakarta yang REAL (kode wilayah Kemendagri).
#
# CATATAN METODOLOGI (jujurkan ini di laporan!):
# Ini BUKAN batas administrasi resmi (yang bentuknya mengikuti jalan,
# sungai, dsb -- data itu perlu shapefile resmi BPS/Jakarta Satu Peta
# yang tidak open-source per-kelurahan). Voronoi polygon adalah teknik
# GIS standar untuk mengaproksimasi wilayah pengaruh dari seburan titik
# ketika batas poligon asli tidak tersedia (dipakai juga untuk analisis
# layanan publik, catchment area, dst). Poligon kelurahan di sini dibuat
# dengan membagi ruang sehingga tiap titik kelurahan berada tepat di
# tengah selnya sendiri -- cukup valid untuk KONTEKS visual & untuk
# menghitung "RPTRA per kelurahan", tapi TIDAK presisi di detail batas
# (tidak mengikuti jalan/sungai asli). Sebutkan keterbatasan ini di
# laporan jika dosen menanyakan sumber batas wilayah.
# =================================================================

import json
from pathlib import Path

import geopandas as gpd
from shapely import voronoi_polygons
from shapely.geometry import MultiPoint, Point

BASE = Path(__file__).parent
UTM48S = "EPSG:32748"

with open(BASE / "referensi_koordinat_kelurahan_jakarta.json", encoding="utf-8") as f:
    rows = json.load(f)

gdf_pts = gpd.GeoDataFrame(
    rows,
    geometry=[Point(r["lon"], r["lat"]) for r in rows],
    crs="EPSG:4326",
).to_crs(UTM48S)

print(f"Titik kelurahan: {len(gdf_pts)}")

mp = MultiPoint(list(gdf_pts.geometry))
# extend_to memberi 'pagar' luar supaya sel di tepi tidak tak-terhingga
hull = mp.convex_hull.buffer(4000)  # buffer 4 km di luar titik terluar
vor = voronoi_polygons(mp, extend_to=hull)
cells = list(vor.geoms)
print(f"Sel Voronoi dihasilkan: {len(cells)}")

# clip tiap sel ke convex hull (biar rapi, tidak menjorok jauh ke laut/luar)
clip_area = mp.convex_hull.buffer(1500)
cells = [c.intersection(clip_area) for c in cells]

# cocokkan tiap sel ke titik kelurahan asal (titik pasti ada di dalam selnya)
sindex_pts = gdf_pts.sindex
assigned = [None] * len(gdf_pts)
for cell in cells:
    if cell.is_empty:
        continue
    cand_idx = list(sindex_pts.query(cell, predicate="contains"))
    for idx in cand_idx:
        assigned[idx] = cell

n_missing = sum(1 for a in assigned if a is None)
print(f"Kelurahan tanpa sel Voronoi (fallback buffer titik): {n_missing}")

geoms = []
for i, cell in enumerate(assigned):
    if cell is None:
        # fallback: buffer kecil di sekitar titik (kasus langka/duplikat titik)
        cell = gdf_pts.geometry.iloc[i].buffer(600)
    geoms.append(cell)

gdf_kel = gdf_pts.drop(columns="geometry").copy()
gdf_kel["geometry"] = geoms
gdf_kel = gpd.GeoDataFrame(gdf_kel, geometry="geometry", crs=UTM48S)
gdf_kel = gdf_kel.rename(columns={"city": "kota", "district": "kecamatan", "village": "kelurahan"})
gdf_kel = gdf_kel.to_crs("EPSG:4326")
gdf_kel.to_file(BASE / "batas_kelurahan_jakarta.geojson", driver="GeoJSON")
print(f"-> batas_kelurahan_jakarta.geojson ditulis ({len(gdf_kel)} poligon)")

# dissolve per kota -> batas kota administrasi (poligon menyatu sempurna
# dengan batas kelurahan di atas karena berasal dari sel yang sama)
gdf_kota = gdf_kel.dissolve(by="kota", as_index=False)[["kota", "geometry"]]
gdf_kota.to_file(BASE / "batas_kota_jakarta.geojson", driver="GeoJSON")
print(f"-> batas_kota_jakarta.geojson ditulis ({len(gdf_kota)} poligon)")
for _, r in gdf_kota.iterrows():
    print(f"   - {r['kota']}")
