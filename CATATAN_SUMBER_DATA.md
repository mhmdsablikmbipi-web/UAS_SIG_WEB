# Catatan Sumber Data (WAJIB dibaca sebelum menulis laporan)

Seperti paket tugas SIG Anda sebelumnya (evakuasi banjir Bandung Selatan),
sebagian data di paket ini **real** dan sebagian **representatif**. Sebutkan
ini secara transparan di laporan -- ini praktik wajar untuk tugas latihan
selama sumbernya jelas, dan justru menunjukkan Anda memahami provenance data.

## RPTRA (`rptra_jakarta.geojson`, 648 titik)

| Atribut | Status | Sumber |
|---|---|---|
| Nama RPTRA, wilayah, kecamatan, kelurahan, periode_data | **REAL** | `RPTRA.csv` yang Anda berikan |
| Koordinat kelurahan (dasar penempatan titik) | **REAL** | Kode wilayah administrasi Kemendagri (Permendagri No. 72/2019), dipublikasikan ulang di repo open-source `drizki/geografis` (MIT license, sumber asli `cahyadsn/wilayah` + Satu Peta + OSM) |
| Titik presisi tiap RPTRA (di-"jitter" di sekitar titik tengah kelurahan) | Representatif | `RPTRA.csv` tidak memuat koordinat presisi per-RPTRA |
| Fasilitas Utama, Kondisi, Kategori Fasilitas (Lengkap/Terbatas) | Representatif | `RPTRA.csv` tidak memuat atribut ini; disimulasikan (seeded random, reproducible) |

**1 baris tidak konsisten** ditemukan di `RPTRA.csv`: RPTRA di Kelurahan
Krendang tercatat berkecamatan "Cengkareng", padahal Krendang sebenarnya
berada di Kecamatan Tambora (kode wilayah 31.73.04.1005). Sudah dikoreksi
otomatis di `siapkan_data.py` (lihat `KECAMATAN_FIX`) -- sebutkan koreksi
ini di laporan sebagai bagian dari proses *data cleaning*.

## TMU (`tmu_jakarta.geojson`, 34 titik)

RPTRA.csv tidak menyertakan data TMU sama sekali, jadi seluruh daftar TMU
disusun dari riset nama & lokasi TPU yang benar-benar ada di Jakarta:

| Atribut | Status | Sumber |
|---|---|---|
| Nama TMU & kecamatan | **REAL** (nama TPU asli) | distamhut.jakarta.go.id (daftar TPU per wilayah), jakarta.go.id/pemakaman |
| Luas area sebagian TMU (Tanah Kusir, Menteng Pulo, Karet Bivak, Kampung Kandang, Jeruk Purut, Jagakarsa, Wijaya, Tegal Alur, Pondok Ranggon, Cipinang Besar, Semper, Bulak Turi) | **REAL** (angka luas terpublikasi) | Artikel berita (Okezone 2011), blog usaha nisan (indahprasasti, 2012), profil TPU (goodnewsfromindonesia, kamboja.co.id) |
| Luas area TMU lainnya | Representatif (estimasi wajar berdasar pola TPU kecil di Jakarta) | - |
| Status kapasitas (Kritis/Waspada/Tersedia) & persen tersisa | Representatif, tapi **mengikuti tren nyata**: BPS DKI Jakarta 2021 mencatat tingkat keterisian TPU se-Jakarta >95% (bahkan nyaris 100% di banyak lokasi); TMU yang secara berita memang dilaporkan "masih luas" (Tegal Alur, Pegadungan, Semper, Pondok Ranggon) diberi status Tersedia, sisanya Kritis/Waspada | jakarta.go.id/page/layanan-pemakaman-di-jakarta (BPS), berita "10 TPU Penuh di Jakarta Barat" |
| Tahun berdiri | Representatif (kecuali Karet Bivak yang memang dikenal berasal dari era kolonial, ~akhir 1700-an) | - |

**Total TPU riil di DKI Jakarta menurut BPS (2021): 82 lokasi, luas total
6.070.955 m².** Paket ini memuat 34 TMU representatif (subset yang
mencerminkan sebaran nyata per wilayah), bukan seluruh 82 lokasi -- sebutkan
ini di laporan sebagai batasan (scope) tugas.

## Batas Wilayah (`batas_kota_jakarta.geojson`, `batas_kelurahan_jakarta.geojson`)

**Bukan batas administrasi resmi.** Dibuat dengan teknik **Voronoi/Thiessen
polygon** dari 267 titik tengah kelurahan DKI Jakarta yang real (sumber sama
seperti koordinat RPTRA di atas). Voronoi polygon adalah teknik GIS standar
untuk mengaproksimasi wilayah pengaruh dari sebaran titik ketika poligon
batas asli tidak tersedia secara terbuka per-kelurahan (data resmi ada di
Jakarta Satu Peta / BPS, tapi tidak dalam format open-data siap unduh
per-kelurahan). Baik untuk **konteks visual** dan estimasi kasar "berapa
RPTRA per kelurahan", tapi **tidak presisi di detail garis batas** (tidak
mengikuti jalan/sungai asli seperti batas resmi). Jelaskan keterbatasan ini
bila dosen bertanya soal sumber batas wilayah.

## Kalau dosen meminta data 100% resmi

Ganti 3 file ini dengan data resmi tanpa mengubah script lain (semua script
membaca dari nama file yang sama):
- **Batas wilayah resmi**: unduh shapefile Kab_Kota/Kecamatan/Kelurahan DKI
  Jakarta dari `github.com/Alf-Anas/batas-administrasi-indonesia` (format
  SHP/KML/GeoJSON/GPKG, lisensi terbuka) lalu filter ke Provinsi DKI Jakarta.
- **Data TMU resmi**: cek ulang `data-tempat-pemakaman-umum-tpu` di
  `satudata.jakarta.go.id` (portal data lama `data.jakarta.go.id` sudah
  bermigrasi ke domain baru per pertengahan 2026).
