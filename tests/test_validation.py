import os
import tempfile
import unittest
from datetime import date

import pandas as pd

from fc.connectors import ExcelConnector, MemoryConnector
from fc.demo import make_demo_frames, write_demo_excel
from fc.kpi import Scope, summarize
from fc.pipeline import load_dataset
from fc.schema import SHEET_BY_NAME
from fc.validation import validate_sheet

TODAY = date(2026, 10, 4)


def prod(**over):
    base = {"Date": ["2026-09-01", "2026-09-02"], "Line": ["L1", "L1"], "Machine": ["M1", "M1"],
            "Output_Kg": [900, 950], "Input_Kg": [1000, 1000]}
    base.update(over)
    return pd.DataFrame(base)


def val(df, name="Production"):
    return validate_sheet(df, SHEET_BY_NAME[name], TODAY)


class TestValidation(unittest.TestCase):
    def test_valid_rows_pass(self):
        clean, rep, issues = val(prod())
        self.assertEqual(rep.rows_ok, 2)
        self.assertEqual(rep.rows_rejected, 0)

    def test_negative_value_rejected_with_excel_row(self):
        clean, rep, issues = val(prod(Output_Kg=[900, -5]))
        self.assertEqual(rep.rows_rejected, 1)
        err = [i for i in issues if i.severity == "error"][0]
        self.assertEqual(err.rows, (3,))  # baris data ke-2 = baris Excel 3

    def test_empty_required_rejected(self):
        clean, rep, _ = val(prod(Output_Kg=[900, None]))
        self.assertEqual(rep.rows_ok, 1)

    def test_text_number_rejected_not_silently_zero(self):
        clean, rep, issues = val(prod(Output_Kg=["1.000.000", 950]))
        self.assertEqual(rep.rows_rejected, 1)
        self.assertTrue(any("bukan angka" in i.message for i in issues))

    def test_future_and_ancient_dates_rejected(self):
        clean, rep, _ = val(prod(Date=["2027-01-01", "1990-01-01"]))
        self.assertEqual(rep.rows_ok, 0)

    def test_invalid_date_rejected_not_replaced(self):
        clean, rep, issues = val(prod(Date=["bukan tanggal", "2026-09-02"]))
        self.assertEqual(rep.rows_ok, 1)
        self.assertEqual(clean["Date"][0], pd.Timestamp("2026-09-02"))  # tidak diganti tanggal karangan

    def test_excel_serial_date(self):
        clean, rep, _ = val(prod(Date=[46266, 46267]))  # serial Excel
        self.assertEqual(rep.rows_ok, 2)
        self.assertEqual(clean["Date"][0], pd.Timestamp("2026-09-01"))

    def test_duplicates_rejected(self):
        clean, rep, issues = val(prod(Date=["2026-09-01", "2026-09-01"]))
        self.assertEqual(rep.rows_ok, 1)
        self.assertTrue(any("duplikat" in i.message.lower() for i in issues))

    def test_output_exceeds_input_rejected(self):
        clean, rep, _ = val(prod(Output_Kg=[1100, 950]))
        self.assertEqual(rep.rows_ok, 1)

    def test_missing_required_column_blocks_core_sheet(self):
        clean, rep, issues = val(prod().drop(columns=["Output_Kg"]))
        self.assertIsNone(clean)
        self.assertTrue(any(i.blocking for i in issues))

    def test_missing_kpi_column_is_warning_not_blocking(self):
        clean, rep, issues = val(prod().drop(columns=["Input_Kg"]))
        self.assertIsNotNone(clean)
        self.assertFalse(any(i.blocking for i in issues))
        self.assertTrue(any(i.severity == "warning" and i.column == "Input_Kg" for i in issues))

    def test_column_alias_utility_cost(self):
        clean, rep, _ = val(pd.DataFrame({"Cost": [100, 200]}), "Utility")
        self.assertIn("Electricity_Cost", clean.columns)

    def test_risk_scale_enforced(self):
        df = pd.DataFrame({"Risk": ["a", "b"], "Status": ["Open", "Open"], "Probability_Val": [3, 7], "Impact_Val": [2, 2]})
        clean, rep, _ = val(df, "Risk_Register")
        self.assertEqual(rep.rows_ok, 1)

    def test_period_datetime_normalized(self):
        df = pd.DataFrame({"Cost": [1, 2], "Period": pd.to_datetime(["2026-01-15", "2026-02-01"])})
        clean, _, _ = val(df, "Packaging")
        self.assertEqual(list(clean["Period"]), ["2026-01", "2026-02"])


class TestPipeline(unittest.TestCase):
    def test_missing_core_sheet_blocks_and_has_no_data(self):
        frames = make_demo_frames(today=TODAY)
        frames.pop("Packaging")
        ds = load_dataset(MemoryConnector(frames), today=TODAY)
        self.assertFalse(ds.ok)
        self.assertIsNone(ds.production)   # tidak ada data pengganti/dummy
        self.assertTrue(ds.report.blocking)

    def test_missing_optional_module_sheet_does_not_block(self):
        frames = make_demo_frames(today=TODAY)
        frames.pop("Risk_Register")
        ds = load_dataset(MemoryConnector(frames), today=TODAY)
        self.assertTrue(ds.ok)
        self.assertIsNone(ds.risk)

    def test_file_not_found_is_clear_error_without_dummy(self):
        ds = load_dataset(ExcelConnector("/tidak/ada/factory_data.xlsx"), today=TODAY)
        self.assertFalse(ds.ok)
        self.assertIn("tidak ditemukan", ds.report.issues[0].message)

    def test_excel_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            path = write_demo_excel(os.path.join(d, "demo.xlsx"), today=TODAY)
            ds = load_dataset(ExcelConnector(path), today=TODAY)
            self.assertTrue(ds.ok, ds.report.to_frame().to_string())
            self.assertEqual(ds.report.rows_rejected, 0)

    def test_existing_style_file_without_new_columns_still_loads(self):
        """File lama (tanpa Input_Kg/OEE/Plant/Period) tetap terbaca; KPI terkait 'tidak tersedia'."""
        f = make_demo_frames(today=TODAY)
        f["Production"] = f["Production"][["Date", "Line", "Machine", "Output_Kg"]]
        for n in ("Raw_Material", "Packaging", "Direct_Labor", "Utility", "Maintenance", "Depreciation"):
            f[n] = f[n].drop(columns=["Plant", "Period"])
        ds = load_dataset(MemoryConnector(f), today=TODAY)
        self.assertTrue(ds.ok)
        s = summarize(ds, Scope())
        self.assertTrue(s.cogm.available)
        self.assertTrue(s.cost_per_kg.available)
        self.assertFalse(s.yield_pct.available)
        self.assertFalse(s.oee.oee.available)
        self.assertIsNone(s.score.score)


if __name__ == "__main__":
    unittest.main()
