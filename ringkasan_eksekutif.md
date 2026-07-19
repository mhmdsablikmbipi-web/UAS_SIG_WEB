# Ringkasan Eksekutif

*(Paragraf ini memenuhi poin tugas No. 3 "Penambahan Konteks" -- tempelkan
langsung sebagai teks di web map, atau kutip di laporan.)*

> Dari **34 TMU** yang dipantau di DKI Jakarta, ditemukan **17 TMU (50%)
> berstatus Kritis** dengan kapasitas tersisa di bawah 10%, dengan
> konsentrasi tertinggi di **Jakarta Selatan** (5 dari 8 TMU) dan
> **Jakarta Timur** (5 dari 10 TMU) -- kedua wilayah ini menjadi prioritas
> utama untuk perluasan atau relokasi TMU. Sementara itu, dari **648 RPTRA**
> yang terpantau, **85 RPTRA (13,1%)** berada dalam radius 500 meter dari
> TMU dan berpotensi menempati zona yang kurang ideal secara
> lingkungan/psikologis, dengan jumlah terbanyak di **Jakarta Utara**
> (27 RPTRA) dan **Jakarta Timur** (20 RPTRA) -- kedua wilayah ini perlu
> menjadi perhatian khusus dalam perencanaan pembangunan RPTRA baru agar
> tetap berada di luar zona penyangga TMU.

---

## Rincian per wilayah (dari `ringkasan_statistik.csv`)

| Wilayah | Jumlah TMU | TMU Kritis | Jumlah RPTRA | RPTRA <500m dari TMU |
|---|---|---|---|---|
| Jakarta Barat  | 8  | 2 | 116 | 16 |
| Jakarta Pusat  | 3  | 3 | 100 | 7  |
| Jakarta Selatan| 8  | 5 | 124 | 15 |
| Jakarta Timur  | 10 | 5 | 136 | 20 |
| Jakarta Utara  | 5  | 2 | 154 | 27 |

Angka-angka di atas dihasilkan otomatis oleh `siapkan_data.py` dari data
`tmu_jakarta.geojson` dan `rptra_jakarta.geojson` -- jalankan ulang script
tersebut jika Anda mengganti/menambah data TMU atau RPTRA, dan angka di
paragraf ringkasan eksekutif akan ikut berubah (lihat isi
`ringkasan_statistik.json` yang baru).
