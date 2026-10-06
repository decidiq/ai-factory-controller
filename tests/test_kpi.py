import unittest
from datetime import date

import pandas as pd

from fc.kpi import (KPI, Scope, controller_score, cogm_for_scope, cost_per_kg, inventory_table,
                    oee_kpi, risk_table, scrap_kpi, summarize, variance_table, yield_kpi)
from fc.pipeline import load_dataset
from fc.connectors import MemoryConnector
from fc.demo import make_demo_frames

PROD = pd.DataFrame({
    "Date": pd.to_datetime(["2026-01-01", "2026-01-02"]),
    "Output_Kg": [900.0, 950.0], "Input_Kg": [1000.0, 1000.0], "Scrap_Kg": [50.0, 50.0],
    "Planned_Time_Min": [400, 400], "Downtime_Min": [100, 100], "Ideal_Rate_Kg_per_Min": [3.5, 3.5],
})
COSTS = pd.DataFrame({
    "Category": ["Material", "Packaging", "Labor", "Utility", "Maintenance", "Depreciation"],
    "Cost": [600.0, 100.0, 200.0, 150.0, 100.0, 50.0],
    "Plant": pd.Series([pd.NA] * 6, dtype="string"), "Period": pd.Series([pd.NA] * 6, dtype="string"),
})


class TestKPI(unittest.TestCase):
    def test_yield_scrap(self):
        y = yield_kpi(PROD)
        self.assertAlmostEqual(y.value, 92.5)               # 1850 / 2000
        self.assertAlmostEqual(scrap_kpi(PROD, y).value, 5.0)  # 100 / 2000

    def test_oee_components(self):
        r = oee_kpi(PROD)
        self.assertAlmostEqual(r.availability.value, 75.0)         # 600 / 800
        self.assertAlmostEqual(r.performance.value, 1950 / 2100 * 100)
        self.assertAlmostEqual(r.quality.value, 1850 / 1950 * 100)
        self.assertAlmostEqual(r.oee.value, 0.75 * (1950 / 2100) * (1850 / 1950) * 100)

    def test_oee_is_not_hardcoded_87(self):
        self.assertNotAlmostEqual(oee_kpi(PROD).oee.value, 87.0)

    def test_oee_unavailable_when_columns_missing(self):
        r = oee_kpi(PROD.drop(columns=["Downtime_Min"]))
        self.assertFalse(r.oee.available)
        self.assertIn("Downtime_Min", r.oee.note)

    def test_oee_performance_over_100_is_flagged(self):
        p = PROD.copy()
        p["Ideal_Rate_Kg_per_Min"] = 3.0
        r = oee_kpi(p)
        self.assertGreater(r.performance.value, 100)
        self.assertIn("Ideal_Rate", r.performance.note)

    def test_yield_unavailable_without_input(self):
        y = yield_kpi(PROD.drop(columns=["Input_Kg"]))
        self.assertFalse(y.available)

    def test_scrap_estimate_flagged(self):
        p = PROD.drop(columns=["Scrap_Kg"])
        s = scrap_kpi(p, yield_kpi(p))
        self.assertEqual(s.status, "estimate")
        self.assertAlmostEqual(s.value, 7.5)

    def test_cogm_and_cost_per_kg(self):
        k, br = cogm_for_scope(COSTS, PROD, Scope())
        self.assertAlmostEqual(k.value, 1200.0)
        self.assertAlmostEqual(br["Utility"], 150.0)
        self.assertAlmostEqual(cost_per_kg(k, 1850.0).value, 1200 / 1850)

    def test_cost_per_kg_unavailable_for_plant_filter_without_dimension(self):
        k, _ = cogm_for_scope(COSTS, PROD, Scope(plant="Plant A"))
        self.assertFalse(k.available)
        self.assertIn("Plant", k.note)

    def test_cost_per_kg_unavailable_for_line_filter(self):
        k, _ = cogm_for_scope(COSTS, PROD, Scope(line="Line 1"))
        self.assertFalse(k.available)

    def test_cost_per_kg_unavailable_when_date_filtered_without_period(self):
        k, _ = cogm_for_scope(COSTS, PROD, Scope(start=date(2026, 1, 2)))
        self.assertFalse(k.available)
        self.assertIn("Period", k.note)

    def test_cost_filter_by_plant_and_period(self):
        c = COSTS.copy()
        c["Plant"] = pd.Series(["A", "A", "A", "B", "B", "B"], dtype="string")
        c["Period"] = pd.Series(["2026-01"] * 6, dtype="string")
        k, _ = cogm_for_scope(c, PROD, Scope(plant="A"))
        self.assertAlmostEqual(k.value, 900.0)  # 600+100+200

    def test_controller_score(self):
        s = controller_score(KPI(92.5, "ok"), KPI(5.0, "ok"), KPI(66.0, "ok"))
        self.assertEqual(s.score, 70)
        self.assertEqual(s.category, "Need Improvement")
        self.assertEqual(len(s.reasons), 3)

    def test_controller_score_excellent_and_unavailable(self):
        self.assertEqual(controller_score(KPI(99.0, "ok"), KPI(1.0, "ok"), KPI(90.0, "ok")).score, 100)
        s = controller_score(KPI(99.0, "ok"), KPI(1.0, "ok"), KPI(None, "unavailable"))
        self.assertIsNone(s.score)
        self.assertIn("OEE", s.note)

    def test_variance_inventory_risk(self):
        v = variance_table(pd.DataFrame({"Category": ["A", "B", "C"], "Budget": [100.0, 100.0, 0.0], "Actual": [110.0, 90.0, 5.0]}))
        self.assertEqual(list(v["Status"][:2]), ["Over Budget", "Under Budget"])
        self.assertAlmostEqual(v["Utilization_Pct"][0], 110.0)
        self.assertTrue(pd.isna(v["Variance_Pct"][2]))  # budget 0 -> tidak ada pembagian nol
        inv = inventory_table(pd.DataFrame({"Material": ["a", "b", "c"], "Stock_Kg": [900.0, 100.0, 100.0], "Monthly_Usage": [300.0, 300.0, 0.0]}))
        self.assertAlmostEqual(inv["Days_Inventory"][0], 90.0)
        self.assertEqual(list(inv["Status"]), ["Slow Moving", "Normal", "Dead Stock"])
        r = risk_table(pd.DataFrame({"Risk": ["x", "y"], "Probability_Val": [3, 1], "Impact_Val": [3, 2]}))
        self.assertEqual(list(r["Score"]), [9, 2])
        self.assertEqual(list(r["Level"]), ["Tinggi", "Rendah"])

    def test_demo_dataset_end_to_end(self):
        ds = load_dataset(MemoryConnector(make_demo_frames(today=date(2026, 10, 4))), is_demo=True, today=date(2026, 10, 4))
        self.assertTrue(ds.ok, ds.report.to_frame().to_string())
        self.assertEqual(ds.report.rows_rejected, 0)
        s = summarize(ds, Scope())
        for k in (s.cost_per_kg, s.yield_pct, s.scrap_pct, s.oee.oee):
            self.assertTrue(k.available)
        self.assertIsNotNone(s.score.score)
        sp = summarize(ds, Scope(plant="Plant A (Cikarang)"))
        self.assertTrue(sp.cost_per_kg.available)
        self.assertLess(sp.output_kg.value, s.output_kg.value)


if __name__ == "__main__":
    unittest.main()
