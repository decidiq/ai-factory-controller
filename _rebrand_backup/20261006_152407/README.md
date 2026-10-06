# AI Factory Controller — Tahap 1A (Fondasi Data & KPI)

Lapisan analitik **read-only**: membaca data dari Excel (Google Sheets, Odoo, SAP/QAD menyusul),
memvalidasi, lalu menghitung KPI dengan rumus resmi BRD bagian 6.

## Menjalankan
```bash
pip install -r requirements.txt
streamlit run app.py            # pilih "Mode Demo" atau arahkan ke file Excel Anda
python -m unittest discover -s tests -t .   # 35 uji otomatis (tidak butuh Streamlit)
```
Untuk mencoba tanpa data sendiri: pilih **Mode Demo**, atau **File Excel** dengan path
`sample/factory_data_demo.xlsx`. Login sementara: username apa saja, pilih role.

## Struktur
```
app.py                  entry point Streamlit (sidebar, filter, routing)
fc/config.py            target & ambang KPI (satu tempat untuk diubah)
fc/schema.py            kamus data (BRD 5.4): sheet, kolom, tipe, satuan, level wajib
fc/validation.py        aturan validasi (BRD 5.5), laporan temuan + nomor baris Excel
fc/connectors/          konektor hanya-baca: excel.py, memory.py (base.py = kontrak)
fc/pipeline.py          konektor -> validasi -> Dataset
fc/kpi.py               rumus KPI (BRD 6) - fungsi murni, tanpa Streamlit
fc/demo.py              data contoh untuk Mode Demo
fc/ui/                  tampilan: dashboard, kualitas data, styles, auth (SEMENTARA)
tests/                  uji otomatis
```

## Pemetaan BRD -> kode
| BRD | Implementasi |
|---|---|
| 5.1 Konektor hanya-baca | `fc/connectors/` (Excel; konektor lain cukup implement `read_all()`) |
| 5.4 Kamus data | `fc/schema.py` + halaman **Kualitas Data** |
| 5.5 Validasi & tanpa data dummy | `fc/validation.py`, `fc/pipeline.py`; data contoh hanya di **Mode Demo** (berlabel) |
| 6 Rumus KPI | `fc/kpi.py` (COGM, Cost/Kg, Yield, Scrap, OEE, Variance, Days Inventory, Risk, Controller Score) |
| 6.2 Ambang alert | `fc/config.py` |

## Kolom baru yang disarankan pada Excel Anda
File lama tetap terbaca. Kolom di bawah membuat KPI tertentu aktif; tanpa kolom itu KPI
menampilkan "Data tidak tersedia" (bukan angka tebakan).

| Sheet | Kolom | Mengaktifkan |
|---|---|---|
| Production | `Input_Kg` | Yield, Scrap |
| Production | `Scrap_Kg` | Scrap akurat, OEE (Quality) |
| Production | `Planned_Time_Min`, `Downtime_Min`, `Ideal_Rate_Kg_per_Min` | OEE |
| Production | `Plant` | Filter Plant |
| Semua sheet biaya | `Plant`, `Period` (YYYY-MM) | Cost/Kg per Plant dan per periode |

## Belum termasuk (sesuai rencana)
- Login/hak akses nyata, database & audit trail permanen (modul `fc/ui/auth.py` masih sementara).
- Konektor Google Sheets, Odoo, SAP/QAD.
- Migrasi halaman lain (Production, Cost, Variance, Inventory, Risk, Executive Report, Copilot).
  Fungsi hitungnya sudah ada di `fc/kpi.py`; halaman lama di `dashboard.py` tetap bisa dipakai sementara.
