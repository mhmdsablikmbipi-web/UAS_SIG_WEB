# =================================================================
# SIAPKAN_DATA.py
# Persiapan data untuk "Peta Interaktif Monitoring Kapasitas TMU dan
# Aksesibilitas RPTRA di DKI Jakarta" (UAS SIG - Soal No. 1)
#
# Script ini:
#   1. Membaca RPTRA.csv (data asli mahasiswa: 648 RPTRA, nama +
#      wilayah/kecamatan/kelurahan) dan melengkapi koordinatnya
#      menggunakan referensi kode wilayah Kemendagri per-kelurahan
#      (referensi_koordinat_kelurahan_jakarta.json).
#   2. Membangun dataset TMU (Taman Makam Umum) representatif
#      menggunakan nama & luas TPU yang benar-benar ada di Jakarta
#      (lihat CATATAN_SUMBER_DATA.md untuk daftar sumber), dengan
#      status kapasitas yang disimulasikan mengikuti tren nyata
#      (BPS DKI Jakarta 2021: rata-rata keterisian TPU se-Jakarta
#      sudah >95%, sebagian nyaris 100%).
#   3. Menghitung buffer eksklusi 500 m di sekitar tiap TMU
#      (Vector > Geoprocessing > Buffer -- versi Python dari operasi
#      yang sama seperti akan dilakukan mahasiswa di QGIS Processing
#      Toolbox) dan menandai RPTRA yang jatuh di dalam buffer tsb.
#   4. Menulis seluruh layer ke GeoJSON (EPSG:4326) + ringkasan
#      statistik CSV/JSON untuk paragraf ringkasan eksekutif.
#
# CATATAN KEJUJURAN DATA (baca CATATAN_SUMBER_DATA.md untuk detail):
#   - Nama & wilayah/kecamatan/kelurahan RPTRA: DATA ASLI dari
#     RPTRA.csv yang diberikan mahasiswa.
#   - Koordinat kelurahan: REAL, dari basis kode wilayah Kemendagri
#     Permendagri No. 72/2019 (bersumber dari repo cahyadsn/wilayah,
#     dipublikasikan ulang di drizki/geografis, MIT license).
#   - Titik RPTRA presisi & atribut fasilitas/kondisi: REPRESENTATIF
#     (di-jitter di sekitar titik tengah kelurahan; RPTRA.csv tidak
#     memuat koordinat presisi maupun atribut fasilitas/kondisi).
#   - Nama & luas sebagian TMU: REAL (bersumber Distamhut Jakarta,
#     BPS DKI Jakarta, berita daring -- lihat catatan sumber).
#   - Status kapasitas TMU & atribut RPTRA lain: REPRESENTATIF,
#     disusun mengikuti tren nyata tingkat keterisian TPU Jakarta.
# =================================================================

import json
import math
import random
import unicodedata
from pathlib import Path

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

random.seed(42)  # reproducible

BASE = Path(__file__).parent
RPTRA_CSV = BASE / "RPTRA.csv"
KELURAHAN_REF = BASE / "referensi_koordinat_kelurahan_jakarta.json"

CITY_MAP = {
    "KOTA ADM. JAKARTA SELATAN": "KOTA ADMINISTRASI JAKARTA SELATAN",
    "KOTA ADM. JAKARTA TIMUR": "KOTA ADMINISTRASI JAKARTA TIMUR",
    "KOTA ADM. JAKARTA BARAT": "KOTA ADMINISTRASI JAKARTA BARAT",
    "KOTA ADM. JAKARTA UTARA": "KOTA ADMINISTRASI JAKARTA UTARA",
    "KOTA ADM. JAKARTA PUSAT": "KOTA ADMINISTRASI JAKARTA PUSAT",
    "KAB. ADM. KEP. SERIBU": "KABUPATEN ADMINISTRASI KEPULAUAN SERIBU",
}
# beberapa kelurahan pada RPTRA.csv salah kecamatan (typo sumber data
# asli) -- perbaikan manual berdasarkan kode wilayah Kemendagri:
KECAMATAN_FIX = {
    ("KOTA ADM. JAKARTA BARAT", "CENGKARENG", "KRENDANG"): "TAMBORA",
}


def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).upper()
    s = s.replace(".", "")
    return "".join(s.split())


def load_kelurahan_lookup():
    with open(KELURAHAN_REF, encoding="utf-8") as f:
        rows = json.load(f)
    lookup = {}
    by_kec = {}
    for r in rows:
        key = (norm(r["city"]), norm(r["district"]), norm(r["village"]))
        lookup[key] = (r["lat"], r["lon"])
        by_kec.setdefault((norm(r["city"]), norm(r["district"])), []).append(r)
        by_kec.setdefault(norm(r["city"]), []).append(r)
    return lookup, by_kec


def jitter(lat, lon, seed_text, radius_m=550):
    """Sebar titik acak (tapi reproducible) di sekitar centroid kelurahan,
    supaya RPTRA yang satu kelurahan tidak numpuk di 1 titik persis."""
    rnd = random.Random(seed_text)
    r = radius_m * math.sqrt(rnd.random())
    theta = rnd.uniform(0, 2 * math.pi)
    dlat = (r * math.cos(theta)) / 111_320
    dlon = (r * math.sin(theta)) / (111_320 * math.cos(math.radians(lat)))
    return lat + dlat, lon + dlon


# ============================================================
# 1. RPTRA -- lengkapi koordinat dari data asli mahasiswa
# ============================================================
print("=" * 60)
print("1. MEMPROSES RPTRA.csv ...")
print("=" * 60)

df = pd.read_csv(RPTRA_CSV, sep=";")
df.columns = [c.strip() for c in df.columns]
lookup, _ = load_kelurahan_lookup()

FASILITAS_OPSI = ["Perpustakaan", "Biopori", "Playground", "Lapangan Olahraga", "Panggung Serbaguna"]
KONDISI_OPSI = [("Baik", 0.55), ("Cukup", 0.30), ("Perlu Perbaikan", 0.15)]


def pilih_kondisi(rnd):
    x = rnd.random()
    cum = 0
    for label, p in KONDISI_OPSI:
        cum += p
        if x <= cum:
            return label
    return KONDISI_OPSI[-1][0]


records = []
tidak_match = 0
for i, row in df.iterrows():
    wilayah_raw = str(row["wilayah"]).strip()
    kec = str(row["kecamatan"]).strip()
    kel = str(row["kelurahan"]).strip()
    nama = str(row["nama_rptra"]).strip()
    periode = row.get("periode_data", "")

    city = CITY_MAP.get(wilayah_raw, wilayah_raw)
    kec_fixed = KECAMATAN_FIX.get((wilayah_raw, kec, kel), kec)
    key = (norm(city), norm(kec_fixed), norm(kel))

    if key not in lookup:
        tidak_match += 1
        continue

    lat0, lon0 = lookup[key]
    seed_text = f"{wilayah_raw}|{kec}|{kel}|{nama}|{i}"
    rnd = random.Random(seed_text)
    lat, lon = jitter(lat0, lon0, seed_text)

    n_fasilitas = rnd.choices([1, 2, 3, 4], weights=[0.25, 0.35, 0.30, 0.10])[0]
    fasilitas = rnd.sample(FASILITAS_OPSI, n_fasilitas)
    kondisi = pilih_kondisi(rnd)
    lengkap = (n_fasilitas >= 3) and (kondisi != "Perlu Perbaikan")

    records.append({
        "nama_rptra": nama,
        "wilayah": wilayah_raw,
        "kecamatan": kec,
        "kelurahan": kel,
        "periode_data": periode,
        "fasilitas_utama": ", ".join(fasilitas),
        "kondisi": kondisi,
        "kategori_fasilitas": "Lengkap" if lengkap else "Terbatas",
        "latitude": round(lat, 6),
        "longitude": round(lon, 6),
    })

print(f"  RPTRA diproses : {len(records)} / {len(df)}  (tidak cocok: {tidak_match})")

gdf_rptra = gpd.GeoDataFrame(
    records,
    geometry=[Point(r["longitude"], r["latitude"]) for r in records],
    crs="EPSG:4326",
)
gdf_rptra.to_file(BASE / "rptra_jakarta.geojson", driver="GeoJSON")
print(f"  -> rptra_jakarta.geojson ditulis ({len(gdf_rptra)} titik)")
print(f"     Lengkap : {(gdf_rptra.kategori_fasilitas=='Lengkap').sum()}"
      f"   Terbatas: {(gdf_rptra.kategori_fasilitas=='Terbatas').sum()}")

# ============================================================
# 2. TMU -- dataset representatif dari nama & luas TPU nyata
#    (nama, kecamatan, luas real bila diketahui -- lihat
#     CATATAN_SUMBER_DATA.md untuk sumber tiap baris)
# ============================================================
print()
print("=" * 60)
print("2. MENYUSUN DATASET TMU ...")
print("=" * 60)

# (nama, wilayah, kecamatan, kelurahan_acuan, luas_ha, tahun_berdiri, status)
# status: "Tersedia" (>30%), "Waspada" (10-30%), "Kritis" (<10%)
TMU_RAW = [
    ("TPU Tanah Kusir I/II", "KOTA ADM. JAKARTA SELATAN", "KEBAYORAN LAMA", "KEBAYORAN LAMA SELATAN", 55.04, 1970, "Kritis"),
    ("TPU Menteng Pulo", "KOTA ADM. JAKARTA SELATAN", "SETIABUDI", "MENTENG ATAS", 41.32, 1970, "Kritis"),
    ("TPU Kampung Kandang", "KOTA ADM. JAKARTA SELATAN", "JAGAKARSA", "JAGAKARSA", 22.94, 1975, "Waspada"),
    ("TPU Jeruk Purut", "KOTA ADM. JAKARTA SELATAN", "PASAR MINGGU", "CILANDAK TIMUR", 9.12, 1968, "Waspada"),
    ("TPU Jagakarsa", "KOTA ADM. JAKARTA SELATAN", "JAGAKARSA", "JAGAKARSA", 0.71, 1980, "Kritis"),
    ("TPU Wijaya", "KOTA ADM. JAKARTA SELATAN", "CILANDAK", "CILANDAK BARAT", 0.58, 1978, "Kritis"),
    ("TPU Pejaten Timur", "KOTA ADM. JAKARTA SELATAN", "PASAR MINGGU", "PEJATEN TIMUR", 2.10, 1985, "Waspada"),
    ("TPU Cipete Selatan", "KOTA ADM. JAKARTA SELATAN", "CILANDAK", "CIPETE SELATAN", 1.40, 1982, "Kritis"),
    ("TPU Karet Bivak", "KOTA ADM. JAKARTA PUSAT", "TANAH ABANG", "KARET TENGSIN", 16.20, 1795, "Kritis"),
    ("TPU Petamburan", "KOTA ADM. JAKARTA PUSAT", "TANAH ABANG", "PETAMBURAN", 1.05, 1974, "Kritis"),
    ("TPU Kober Tanah Abang", "KOTA ADM. JAKARTA PUSAT", "TANAH ABANG", "KEBON KACANG", 0.65, 1976, "Kritis"),
    ("TPU Tegal Alur I/II", "KOTA ADM. JAKARTA BARAT", "KALIDERES", "TEGAL ALUR", 62.88, 1979, "Tersedia"),
    ("TPU Pegadungan", "KOTA ADM. JAKARTA BARAT", "KALIDERES", "PEGADUNGAN", 6.50, 1990, "Tersedia"),
    ("TPU Basmol", "KOTA ADM. JAKARTA BARAT", "KEMBANGAN", "JOGLO", 3.20, 1983, "Waspada"),
    ("TPU Semanan", "KOTA ADM. JAKARTA BARAT", "KALIDERES", "SEMANAN", 2.05, 1987, "Waspada"),
    ("TPU Sukabumi Selatan", "KOTA ADM. JAKARTA BARAT", "KEBON JERUK", "SUKABUMI SELATAN", 1.45, 1981, "Kritis"),
    ("TPU Kepa Duri", "KOTA ADM. JAKARTA BARAT", "KEBON JERUK", "DURI KEPA", 0.95, 1979, "Kritis"),
    ("TPU Joglo", "KOTA ADM. JAKARTA BARAT", "KEMBANGAN", "JOGLO", 2.10, 1984, "Waspada"),
    ("TPU Utan Jati", "KOTA ADM. JAKARTA BARAT", "KALIDERES", "KALIDERES", 1.55, 1986, "Waspada"),
    ("TPU Pondok Ranggon", "KOTA ADM. JAKARTA TIMUR", "CIPAYUNG", "PONDOK RANGGON", 70.00, 1987, "Tersedia"),
    ("TPU Cipinang Besar", "KOTA ADM. JAKARTA TIMUR", "JATINEGARA", "CIPINANG BESAR SELATAN", 16.02, 1972, "Kritis"),
    ("TPU Kebon Pala", "KOTA ADM. JAKARTA TIMUR", "MAKASAR", "KEBON PALA", 3.10, 1976, "Waspada"),
    ("TPU Rawa Terate", "KOTA ADM. JAKARTA TIMUR", "CAKUNG", "RAWA TERATE", 2.40, 1988, "Waspada"),
    ("TPU Malaka", "KOTA ADM. JAKARTA TIMUR", "DUREN SAWIT", "MALAKA SARI", 1.55, 1990, "Kritis"),
    ("TPU Pondok Kelapa", "KOTA ADM. JAKARTA TIMUR", "DUREN SAWIT", "PONDOK KELAPA", 2.20, 1989, "Waspada"),
    ("TPU Susukan", "KOTA ADM. JAKARTA TIMUR", "CIRACAS", "SUSUKAN", 3.05, 1983, "Waspada"),
    ("TPU Kampung Rambutan", "KOTA ADM. JAKARTA TIMUR", "CIRACAS", "KAMPUNG RAMBUTAN", 2.35, 1980, "Kritis"),
    ("TPU Utan Kayu", "KOTA ADM. JAKARTA TIMUR", "MATRAMAN", "UTAN KAYU UTARA", 1.10, 1974, "Kritis"),
    ("TPU UKI Cawang", "KOTA ADM. JAKARTA TIMUR", "KRAMAT JATI", "CAWANG", 0.55, 1977, "Kritis"),
    ("TPU Semper", "KOTA ADM. JAKARTA UTARA", "CILINCING", "SEMPER BARAT", 57.57, 1985, "Tersedia"),
    ("TPU Bulak Turi", "KOTA ADM. JAKARTA UTARA", "CILINCING", "CILINCING", 0.40, 1990, "Kritis"),
    ("TPU Sungai Bambu", "KOTA ADM. JAKARTA UTARA", "TANJUNG PRIOK", "SUNGAI BAMBU", 1.35, 1978, "Kritis"),
    ("TPU Jembatan Item", "KOTA ADM. JAKARTA UTARA", "TANJUNG PRIOK", "PAPANGGO", 1.05, 1981, "Waspada"),
    ("TPU Rorotan", "KOTA ADM. JAKARTA UTARA", "CILINCING", "ROROTAN", 3.60, 1995, "Tersedia"),
]

STATUS_RANGE = {"Tersedia": (31, 70), "Waspada": (10, 30), "Kritis": (1, 9)}

_, by_kec = load_kelurahan_lookup()


def cari_koordinat_tmu(wilayah_raw, kec, kel_acuan):
    city = CITY_MAP.get(wilayah_raw, wilayah_raw)
    key = (norm(city), norm(kec), norm(kel_acuan))
    if key in lookup:
        return lookup[key]
    # fallback: kelurahan lain manapun dalam kecamatan yang sama
    cand = by_kec.get((norm(city), norm(kec)))
    if cand:
        r = cand[0]
        return r["lat"], r["lon"]
    cand = by_kec.get(norm(city))
    r = cand[0]
    return r["lat"], r["lon"]


tmu_records = []
for nama, wilayah, kec, kel_acuan, luas_ha, tahun, status in TMU_RAW:
    lat0, lon0 = cari_koordinat_tmu(wilayah, kec, kel_acuan)
    rnd = random.Random(nama)
    lat, lon = jitter(lat0, lon0, nama, radius_m=250)
    lo, hi = STATUS_RANGE[status]
    kapasitas_persen = rnd.randint(lo, hi)
    tmu_records.append({
        "nama_tmu": nama,
        "wilayah": wilayah,
        "kecamatan": kec,
        "kelurahan": kel_acuan.title(),
        "luas_area_ha": luas_ha,
        "luas_area_m2": round(luas_ha * 10_000),
        "tahun_berdiri": tahun,
        "kapasitas_tersisa_persen": kapasitas_persen,
        "status_kapasitas": status,
        "latitude": round(lat, 6),
        "longitude": round(lon, 6),
    })

gdf_tmu = gpd.GeoDataFrame(
    tmu_records,
    geometry=[Point(r["longitude"], r["latitude"]) for r in tmu_records],
    crs="EPSG:4326",
)
gdf_tmu.to_file(BASE / "tmu_jakarta.geojson", driver="GeoJSON")
print(f"  -> tmu_jakarta.geojson ditulis ({len(gdf_tmu)} titik)")
for s in ["Kritis", "Waspada", "Tersedia"]:
    print(f"     {s:9s}: {(gdf_tmu.status_kapasitas==s).sum()}")

# ============================================================
# 3. BUFFER EKSKLUSI 500 M (proyeksi UTM 48S -> buffer -> WGS84)
#    Operasi ini identik dengan Vector > Geoprocessing > Buffer
#    di QGIS Processing Toolbox (jarak 500 m, proyeksi metrik).
# ============================================================
print()
print("=" * 60)
print("3. MENGHITUNG BUFFER EKSKLUSI 500 M ...")
print("=" * 60)

UTM48S = "EPSG:32748"
gdf_tmu_utm = gdf_tmu.to_crs(UTM48S)
buffer_utm = gdf_tmu_utm.copy()
buffer_utm["geometry"] = buffer_utm.geometry.buffer(500)
gdf_buffer = buffer_utm.to_crs("EPSG:4326")[
    ["nama_tmu", "wilayah", "status_kapasitas", "geometry"]
]
gdf_buffer.to_file(BASE / "buffer_tmu_500m.geojson", driver="GeoJSON")
print(f"  -> buffer_tmu_500m.geojson ditulis ({len(gdf_buffer)} poligon, radius 500 m)")

# tandai RPTRA yang jatuh di dalam buffer TMU manapun
rptra_utm = gdf_rptra.to_crs(UTM48S)
buffer_union = buffer_utm.union_all()
gdf_rptra["dalam_buffer_tmu"] = rptra_utm.geometry.within(buffer_union)
gdf_rptra.to_file(BASE / "rptra_jakarta.geojson", driver="GeoJSON")  # overwrite w/ flag
n_dalam_buffer = int(gdf_rptra["dalam_buffer_tmu"].sum())
print(f"  RPTRA yang berada < 500 m dari TMU: {n_dalam_buffer} dari {len(gdf_rptra)}")

# ============================================================
# 4. RINGKASAN STATISTIK (untuk paragraf ringkasan eksekutif)
# ============================================================
print()
print("=" * 60)
print("4. RINGKASAN STATISTIK")
print("=" * 60)

ringkasan = {
    "total_tmu": int(len(gdf_tmu)),
    "tmu_kritis": int((gdf_tmu.status_kapasitas == "Kritis").sum()),
    "tmu_waspada": int((gdf_tmu.status_kapasitas == "Waspada").sum()),
    "tmu_tersedia": int((gdf_tmu.status_kapasitas == "Tersedia").sum()),
    "total_rptra": int(len(gdf_rptra)),
    "rptra_lengkap": int((gdf_rptra.kategori_fasilitas == "Lengkap").sum()),
    "rptra_terbatas": int((gdf_rptra.kategori_fasilitas == "Terbatas").sum()),
    "rptra_dalam_buffer_tmu": n_dalam_buffer,
    "per_wilayah": {},
}

for wilayah in sorted(gdf_tmu["wilayah"].unique()):
    tmu_w = gdf_tmu[gdf_tmu.wilayah == wilayah]
    rptra_w = gdf_rptra[gdf_rptra.wilayah == wilayah]
    ringkasan["per_wilayah"][wilayah] = {
        "jumlah_tmu": int(len(tmu_w)),
        "tmu_kritis": int((tmu_w.status_kapasitas == "Kritis").sum()),
        "jumlah_rptra": int(len(rptra_w)),
        "rptra_dalam_buffer_tmu": int(rptra_w["dalam_buffer_tmu"].sum()),
    }

with open(BASE / "ringkasan_statistik.json", "w", encoding="utf-8") as f:
    json.dump(ringkasan, f, ensure_ascii=False, indent=2)

rows = []
for w, s in ringkasan["per_wilayah"].items():
    rows.append({"wilayah": w, **s})
pd.DataFrame(rows).to_csv(BASE / "ringkasan_statistik.csv", index=False)

print(json.dumps(ringkasan, ensure_ascii=False, indent=2))
print()
print("Selesai. File yang dihasilkan:")
for fn in ["rptra_jakarta.geojson", "tmu_jakarta.geojson", "buffer_tmu_500m.geojson",
           "ringkasan_statistik.json", "ringkasan_statistik.csv"]:
    p = BASE / fn
    print(f"  - {fn} ({p.stat().st_size:,} bytes)")
