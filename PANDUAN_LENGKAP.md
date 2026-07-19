# 📋 PANDUAN TUGAS SIG - UAS NO. 1
## Peta Interaktif Monitoring Kapasitas TMU & Aksesibilitas RPTRA di DKI Jakarta

*(Soal No. 2 -- Random Forest RW prioritas -- BELUM dikerjakan di paket ini,
sesuai arahan Anda untuk fokus No. 1 dulu.)*

---

## 📁 ISI PAKET INI

| File | Keterangan |
|---|---|
| `RPTRA.csv` | Data asli Anda (648 RPTRA: wilayah/kecamatan/kelurahan/nama) |
| `referensi_koordinat_kelurahan_jakarta.json` | 267 kelurahan DKI Jakarta + koordinat (kode wilayah Kemendagri) |
| `siapkan_data.py` | Script Python: cocokkan RPTRA ke koordinat, susun data TMU, hitung buffer 500m |
| `siapkan_batas_wilayah.py` | Script Python: bangun layer Batas Kota & Batas Kelurahan (Voronoi) |
| `rptra_jakarta.geojson` | 648 titik RPTRA + koordinat + fasilitas/kondisi/kategori |
| `tmu_jakarta.geojson` | 34 titik TMU + luas/status kapasitas/tahun berdiri |
| `buffer_tmu_500m.geojson` | Poligon buffer eksklusi 500m di sekitar tiap TMU |
| `batas_kota_jakarta.geojson` | Batas 6 kota/kabupaten administrasi (poligon Voronoi) |
| `batas_kelurahan_jakarta.geojson` | Batas 267 kelurahan (poligon Voronoi) |
| `ringkasan_statistik.json` / `.csv` | Statistik total & per-wilayah |
| `ringkasan_eksekutif.md` | **Paragraf ringkasan eksekutif** (poin tugas No. 3) |
| `BUKA_DI_QGIS.py` | Script loader QGIS -- muat semua layer dgn simbologi + popup siap qgis2web |
| `app_streamlit.py` | **Bonus**: versi Streamlit+Folium dengan dropdown filter wilayah & status |
| `CATATAN_SUMBER_DATA.md` | **WAJIB dibaca** -- transparansi data real vs representatif |

---

## ⚠️ CATATAN TENTANG DATA

Baca `CATATAN_SUMBER_DATA.md` untuk rincian lengkap. Ringkasnya: nama & lokasi
RPTRA adalah data asli Anda; koordinat kelurahan real dari kode wilayah
Kemendagri; nama & sebagian luas TMU real (riset TPU asli Jakarta); status
kapasitas TMU serta atribut fasilitas/kondisi RPTRA representatif (disusun
mengikuti tren nyata BPS DKI Jakarta). Batas wilayah dibuat dengan teknik
Voronoi dari titik kelurahan real -- bukan batas administrasi resmi presisi.
**Sebutkan semua ini secara transparan di laporan.**

---

## 🚀 LANGKAH 1: BUKA DI QGIS

1. Buka **QGIS Desktop** (3.x)
2. Menu **Plugins > Python Console** > ikon **Open Script** (folder) di
   toolbar Python Console
3. Pilih `BUKA_DI_QGIS.py` > klik tombol **Run** (▶)
4. Semua layer termuat otomatis, dikelompokkan dalam 4 grup layer:
   - **1. Konteks Wilayah** (Batas Kota, Batas Kelurahan -- default OFF)
   - **2. Buffer Eksklusi TMU (500m)**
   - **3. TMU - Status Kapasitas** (kategori Hijau/Kuning/Merah)
   - **4. RPTRA - Kategori Fasilitas** (kategori Biru/Ungu)
5. Simbologi, label, dan **Maptip** (popup) sudah diatur sesuai spesifikasi
   soal. Cek dengan **Identify Features** (klik ikon info, lalu klik marker
   TMU/RPTRA di peta) -- ini yang jadi screenshot "pop-up TMU/RPTRA yang
   diklik" untuk deliverable (b).
6. **Simpan proyek**: `File > Save As` > pilih format **.qgz**

### Kalau ingin memverifikasi analisis buffer secara manual di QGIS
(untuk laporan metodologi, tunjukkan Anda memakai Processing Toolbox-nya
QGIS, bukan cuma file jadi):
- `Vector > Geoprocessing Tools > Buffer` pada layer `TMU (Taman Makam Umum)`,
  Distance = `500 Meters` (klik ikon kalkulator di sebelah field Distance,
  pilih `Meters` -- QGIS otomatis reproject sementara ke unit meter)
- `Vector > Analysis Tools > Select by Location` untuk memilih RPTRA yang
  "Intersect" dengan hasil buffer -- ini yang menghasilkan angka
  "RPTRA <500m dari TMU" di ringkasan eksekutif

---

## 🌐 LANGKAH 2: EKSPOR KE WEB (qgis2web)

Sesuai soal, pilih **salah satu** dari 3 opsi tool. Paket ini disiapkan untuk
**qgis2web** (No-Code) sebagai pilihan utama, plus **bonus Streamlit** untuk
fitur dropdown yang tidak didukung qgis2web (lihat Langkah 3).

1. Install plugin: `Plugins > Manage and Install Plugins` > cari **qgis2web** > Install
2. Setelah proyek dari Langkah 1 terbuka, buka `Web > qgis2web > Create a web map`
3. Tab **Layers and Groups**:
   - Centang semua layer yang mau tampil di peta web
   - Untuk **TMU** dan **RPTRA**: set **Popup content = "Maptip"**
     (ini yang mengambil template popup HTML yang sudah diisi
     `buat_maptip()` di `BUKA_DI_QGIS.py` -- kalau dibiarkan default
     "All Attributes", popup akan menampilkan semua kolom mentah,
     kurang rapi untuk dipresentasikan)
   - Centang **"Cluster"** = OFF (soal minta semua titik terlihat, bukan
     mengelompok jadi 1 angka)
4. Tab **Appearance**: isi **Layer List → "Expanded"** supaya checkbox
   kategori (Tersedia/Waspada/Kritis, Lengkap/Terbatas) langsung terlihat
   di legenda web -- inilah cara qgis2web mendekati "filter" untuk
   kategori (klik checkbox kategori = menyembunyikan kategori itu saja)
5. Tab **Export**: centang **"Add address search"** (opsional, mencari
   lokasi) dan **"Add layer search"** dengan field `nama_tmu` / `nama_rptra`
   kalau ingin kotak pencarian nama
6. Klik **Update Preview** untuk cek dulu di jendela browser lokal, lalu
   **Export** ke folder (misal `webmap_export/`)
7. Buka folder hasil ekspor, cek `index.html` berjalan lokal, lalu **upload
   ke GitHub Pages**:
   ```
   git init
   git add .
   git commit -m "Web map monitoring TMU RPTRA Jakarta"
   git branch -M main
   git remote add origin <URL repo GitHub Anda>
   git push -u origin main
   ```
   lalu di GitHub: `Settings > Pages > Source: main branch` > tunggu
   1-2 menit > dapat **Live URL** (deliverable a)

### ⚠️ Batasan qgis2web yang perlu Anda catat di laporan
qgis2web **hanya bisa toggle checkbox per kategori/layer** di panel legenda
-- ia **tidak bisa** membuat dropdown "Wilayah Administrasi" yang menyaring
titik lintas-layer sekaligus seperti pada contoh gambar yang Anda kirim.
Untuk soal ini itu **opsional** ("Filter Dinamis (Opsional tapi Disukai)"),
jadi qgis2web saja sudah cukup memenuhi syarat wajib. Kalau tetap ingin
dropdown wilayah yang berfungsi penuh, pakai bonus di Langkah 3.

---

## 🌐 LANGKAH 3 (BONUS): VERSI STREAMLIT DENGAN DROPDOWN FILTER ASLI

`app_streamlit.py` memakai data **persis sama** (baca file geojson yang sama
dari folder ini), jadi kedua versi selalu konsisten.

```bash
pip install streamlit folium streamlit-folium geopandas
streamlit run app_streamlit.py
```

Fitur yang tersedia: dropdown **Wilayah Administrasi** & **Status Kapasitas
TMU** (menyaring TMU + RPTRA sekaligus, lintas-layer -- ini yang tidak bisa
dilakukan qgis2web), checkbox layer, legenda, kartu statistik, dan paragraf
ringkasan eksekutif otomatis. Untuk publikasi gratis, upload ke
[share.streamlit.io](https://share.streamlit.io) (Streamlit Community Cloud)
dengan menghubungkan repo GitHub yang sama.

---

## ✅ CHECKLIST DELIVERABLES (sesuai soal)

- [ ] **a. Live URL** -- setelah export qgis2web + push ke GitHub Pages
      (Langkah 2), atau URL Streamlit Cloud (Langkah 3)
- [ ] **b. Screenshot 1**: tampilan penuh peta + legenda terlihat
- [ ] **b. Screenshot 2**: popup TMU **atau** RPTRA yang sedang diklik
      (klik marker di peta web hasil export, atau screenshot Identify
      Features di QGIS sebelum ekspor)
- [ ] **c. Laporan**: cantumkan paragraf `ringkasan_eksekutif.md`, isi
      `CATATAN_SUMBER_DATA.md` (transparansi data), serta metodologi
      buffer 500m (Langkah 1, bagian Processing Toolbox) sebagai bukti
      analisis spasial di QGIS

---

## 🗺️ CAKUPAN DATA

**34 TMU** dan **648 RPTRA** tersebar di 6 kota/kabupaten administrasi DKI
Jakarta (Jakarta Pusat, Selatan, Timur, Barat, Utara, Kepulauan Seribu).
Lihat `ringkasan_eksekutif.md` untuk rincian angka per wilayah.
