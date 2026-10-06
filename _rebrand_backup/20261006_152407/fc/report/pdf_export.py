"""Ekspor Executive Report ke PDF (BRD 2.5)."""
from datetime import datetime
from typing import Optional

from fpdf import FPDF

from ..intel.alert_impact import compute_alerts
from ..intel.period_compare import available_periods, compare_periods
from ..kpi import Scope, inventory_table, summarize, variance_table
from ..pipeline import Dataset


def _safe(text: str) -> str:
    """Konversi karakter non-Latin1 agar bisa dengan font default."""
    replacements = {
        "—": "-", "–": "-", "•": "-", "×": "x", "÷": "/",
        "−": "-",
        "≥": ">=", "≤": "<=", "±": "+/-", "→": "->",
        "Δ": "Delta", "🔴": "[!]", "🟡": "[*]", "🔵": "[i]",
        "✅": "[OK]", "⚠️": "[!]", "💰": "Rp",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text.encode("latin-1", "replace").decode("latin-1")


class ReportPDF(FPDF):
    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_auto_page_break(auto=True, margin=15)
        self.set_margins(15, 15, 15)

    def header(self):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 6, "AI Factory Controller - Executive Report", align="L")
        self.cell(0, 6, datetime.now().strftime("%d-%m-%Y %H:%M"),
                  align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(200, 200, 200)
        self.line(15, 22, 195, 22)
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Hal. {self.page_no()}", align="C")

    def chapter_title(self, text: str):
        self.ln(3)
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(30, 58, 138)
        self.cell(0, 8, _safe(text), new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(30, 58, 138)
        self.line(15, self.get_y(), 195, self.get_y())
        self.ln(3)
        self.set_text_color(0, 0, 0)

    def subtitle(self, text: str):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(60, 60, 60)
        self.cell(0, 6, _safe(text), new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(0, 0, 0)

    def body_text(self, text: str, size: int = 10):
        self.set_font("Helvetica", "", size)
        self.multi_cell(0, 5, _safe(text))
        self.ln(1)

    def kpi_row(self, items: list):
        w = (self.w - 30) / len(items)
        for label, value, note in items:
            self.set_font("Helvetica", "", 8)
            self.set_text_color(100, 100, 100)
            self.cell(w, 4, _safe(label.upper()), border=0)
        self.ln(4)
        for label, value, note in items:
            self.set_font("Helvetica", "B", 12)
            self.set_text_color(15, 23, 42)
            self.cell(w, 6, _safe(value), border=0)
        self.ln(6)
        if any(note for _, _, note in items):
            for label, value, note in items:
                if note:
                    self.set_font("Helvetica", "I", 7)
                    self.set_text_color(120, 120, 120)
                    self.cell(w, 3, _safe(note[:40]), border=0)
            self.ln(5)
        self.set_text_color(0, 0, 0)


def _fmt(kpi, fmt: str) -> str:
    if kpi is None:
        return "-"
    if hasattr(kpi, "available") and kpi.available:
        return fmt.format(kpi.value)
    return "-"


def generate_pdf(ds: Dataset, scope: Scope,
                 output_path: Optional[str] = None,
                 targets=None) -> str:
    """Buat PDF Executive Report. Return path file.

    Args:
        ds: Dataset
        scope: Scope filter
        output_path: Optional path output
        targets: Targets KPI — kalau None pakai DEFAULT dari config
    """
    if targets is None:
        from ..config import TARGETS as DEFAULT_TARGETS
        targets = DEFAULT_TARGETS

    if output_path is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"executive_report_{ts}.pdf"

    pdf = ReportPDF()
    pdf.add_page()

    # === COVER ===
    pdf.ln(30)
    pdf.set_font("Helvetica", "B", 24)
    pdf.set_text_color(30, 58, 138)
    pdf.cell(0, 12, "EXECUTIVE REPORT", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 14)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 10, "AI Factory Controller", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, "Manufacturing Intelligence Platform",
             align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(15)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(0, 6, f"Sumber data: {_safe(ds.report.source_label)}",
             align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Dibaca: {ds.report.loaded_at}",
             align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Periode: {scope.start or '-'} s/d {scope.end or '-'}",
             align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Plant: {scope.plant or 'Semua'} | Line: {scope.line or 'Semua'}",
             align="C", new_x="LMARGIN", new_y="NEXT")

    # Target aktif (info)
    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6,
             f"Target aktif: Yield >= {targets.yield_min:g}% | "
             f"Scrap <= {targets.scrap_max:g}% | OEE >= {targets.oee_min:g}%",
             align="C", new_x="LMARGIN", new_y="NEXT")

    if ds.is_demo:
        pdf.ln(6)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(200, 100, 0)
        pdf.cell(0, 8, "*** DEMO DATA - bukan data pabrik sebenarnya ***",
                 align="C", new_x="LMARGIN", new_y="NEXT")

    # === PAGE 2: RINGKASAN KPI ===
    pdf.add_page()
    pdf.chapter_title("1. Ringkasan KPI")

    s = summarize(ds, scope)

    pdf.kpi_row([
        ("Output", _fmt(s.output_kg, "{:,.0f} Kg"), ""),
        ("Yield", _fmt(s.yield_pct, "{:.2f}%"), ""),
        ("Scrap", _fmt(s.scrap_pct, "{:.2f}%"), ""),
        ("OEE", _fmt(s.oee.oee, "{:.2f}%"), ""),
    ])
    pdf.kpi_row([
        ("COGM", _fmt(s.cogm, "Rp {:,.0f}"), ""),
        ("Cost/Kg", _fmt(s.cost_per_kg, "Rp {:,.0f}"), ""),
        ("Controller Score",
         f"{s.score.score}/100" if s.score.score is not None else "-",
         s.score.category if s.score.score is not None else ""),
        ("Baris Produksi", f"{s.production_rows:,}", ""),
    ])

    # === ALERT AKTIF ===
    alerts = compute_alerts(s, targets)

    if alerts:
        pdf.chapter_title("2. Peringatan Aktif (berdasarkan dampak Rp)")
        total_annual = sum(abs(a.annual_rp) for a in alerts)
        pdf.body_text(
            f"Total potensi dampak: Rp {total_annual:,.0f}/tahun. "
            f"Berikut diurutkan berdasarkan prioritas:", size=10
        )
        pdf.ln(2)

        for i, a in enumerate(alerts, 1):
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(180, 30, 30)
            pdf.cell(0, 6, _safe(f"{i}. {a.title}"),
                     new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(60, 60, 60)
            pdf.cell(0, 5, _safe(f"   {a.message}"),
                     new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(200, 100, 0)
            pdf.cell(0, 5,
                     _safe(f"   Dampak: Rp {a.monthly_rp:,.0f}/bulan "
                           f"(Rp {a.annual_rp:,.0f}/tahun)"),
                     new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "I", 8)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(0, 5, _safe(f"   Saran: {a.fix_hint}"),
                     new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)
        pdf.set_text_color(0, 0, 0)

    # === PERBANDINGAN PERIODE ===
    periods = available_periods(ds)
    if len(periods) >= 2:
        pdf.add_page()
        pdf.chapter_title("3. Perbandingan Periode (MoM)")
        prev, curr = periods[-2], periods[-1]
        pdf.body_text(f"Membandingkan {prev} dengan {curr}", size=10)
        pdf.ln(2)

        comps = compare_periods(ds, prev, curr)

        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(30, 58, 138)
        pdf.set_text_color(255, 255, 255)
        col_w = [40, 35, 35, 30, 25, 30]
        headers = ["KPI", prev, curr, "Delta", "Delta %", "Status"]
        for w, h in zip(col_w, headers):
            pdf.cell(w, 8, _safe(h), border=1, fill=True, align="C")
        pdf.ln()

        pdf.set_text_color(0, 0, 0)
        for c in comps:
            improving = c.is_improving
            status = "Membaik" if improving is True else \
                     ("Memburuk" if improving is False else "Stabil")

            pdf.set_font("Helvetica", "", 9)
            pdf.cell(col_w[0], 7, _safe(c.label), border=1)
            pdf.cell(col_w[1], 7, _safe(c.fmt_value(c.prev_value)), border=1, align="R")
            pdf.cell(col_w[2], 7, _safe(c.fmt_value(c.curr_value)), border=1, align="R")
            pdf.cell(col_w[3], 7, _safe(c.fmt_delta()), border=1, align="R")
            pdf.cell(col_w[4], 7, _safe(c.fmt_pct()), border=1, align="R")

            if improving is False:
                pdf.set_text_color(180, 30, 30)
            elif improving is True:
                pdf.set_text_color(20, 130, 60)
            pdf.cell(col_w[5], 7, _safe(status), border=1, align="C")
            pdf.set_text_color(0, 0, 0)
            pdf.ln()

    # === STRUKTUR COGM ===
    if s.breakdown:
        pdf.add_page()
        pdf.chapter_title("4. Struktur COGM")
        total = sum(s.breakdown.values())
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(30, 58, 138)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(80, 8, "Komponen", border=1, fill=True)
        pdf.cell(50, 8, "Nilai (Rp)", border=1, fill=True, align="R")
        pdf.cell(40, 8, "Porsi (%)", border=1, fill=True, align="R")
        pdf.ln()

        pdf.set_text_color(0, 0, 0)
        for cat, val in sorted(s.breakdown.items(), key=lambda x: -x[1]):
            pct = val / total * 100 if total else 0
            pdf.set_font("Helvetica", "", 9)
            pdf.cell(80, 7, _safe(cat), border=1)
            pdf.cell(50, 7, f"{val:,.0f}", border=1, align="R")
            pdf.cell(40, 7, f"{pct:.1f}%", border=1, align="R")
            pdf.ln()

        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(80, 8, "TOTAL COGM", border=1, fill=True)
        pdf.cell(50, 8, f"{total:,.0f}", border=1, fill=True, align="R")
        pdf.cell(40, 8, "100%", border=1, fill=True, align="R")
        pdf.ln()

    # === INVENTARIS ===
    if ds.inventory is not None and not ds.inventory.empty:
        pdf.add_page()
        pdf.chapter_title("5. Inventaris")
        try:
            it = inventory_table(ds.inventory)
            slow = int((it["Status"] == "Slow Moving").sum())
            dead = int((it["Status"] == "Dead Stock").sum())
            pdf.body_text(
                f"Total material: {len(it)} | "
                f"Slow Moving: {slow} | Dead Stock: {dead}", size=10
            )
            pdf.ln(2)

            pdf.set_font("Helvetica", "B", 9)
            pdf.set_fill_color(30, 58, 138)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(60, 8, "Material", border=1, fill=True)
            pdf.cell(35, 8, "Stock (Kg)", border=1, fill=True, align="R")
            pdf.cell(35, 8, "Usage/bln", border=1, fill=True, align="R")
            pdf.cell(40, 8, "Status", border=1, fill=True, align="C")
            pdf.ln()

            pdf.set_text_color(0, 0, 0)
            for _, r in it.iterrows():
                pdf.set_font("Helvetica", "", 9)
                pdf.cell(60, 7, _safe(str(r["Material"]))[:28], border=1)
                pdf.cell(35, 7, f"{r['Stock_Kg']:,.0f}", border=1, align="R")
                pdf.cell(35, 7, f"{r['Monthly_Usage']:,.0f}", border=1, align="R")
                status = str(r["Status"])
                if status == "Dead Stock":
                    pdf.set_text_color(180, 30, 30)
                elif status == "Slow Moving":
                    pdf.set_text_color(200, 130, 30)
                pdf.cell(40, 7, _safe(status), border=1, align="C")
                pdf.set_text_color(0, 0, 0)
                pdf.ln()
        except Exception as e:
            pdf.body_text(f"Tidak dapat memuat tabel inventaris: {e}")

    pdf.output(output_path)
    return output_path