"""Tool registry — wrap fungsi existing dari fc.kpi / fc.intel.*"""
from typing import Any, Dict


def _ok(text: str, raw: Any = None) -> Dict[str, Any]:
    return {"ok": True, "text": text, "raw": raw, "error": None}


def _fail(err: str) -> Dict[str, Any]:
    return {"ok": False, "text": "", "raw": None, "error": err}


# ==================== KPI ====================
def tool_kpi_summary(ds, scope, **_) -> Dict[str, Any]:
    """Ringkasan KPI: yield, scrap, OEE, COGM."""
    try:
        from fc.kpi import summarize
        s = summarize(ds, scope)
        lines = []
        for attr, label in [
            ("yield_kpi", "Yield"),
            ("scrap_kpi", "Scrap"),
            ("oee_kpi", "OEE"),
            ("cogm", "COGM"),
        ]:
            k = getattr(s, attr, None)
            if k is None:
                continue
            v = getattr(k, "value", None)
            note = getattr(k, "note", "")
            lines.append(f"- {label}: {v} {note}".strip())
        return _ok("\n".join(lines) or "(tidak ada KPI)", raw=s)
    except Exception as e:
        return _fail(str(e))


# ==================== PREDICTIVE ====================
def tool_forecast_output(ds, scope, periods: int = 7, **_) -> Dict[str, Any]:
    """Forecast output produksi N periode ke depan."""
    try:
        from fc.intel.predictive import forecast_output
        from fc.kpi import scope_production
        prod = scope_production(ds.production, scope) if ds.production is not None else None
        if prod is None or prod.empty:
            return _fail("data produksi kosong")
        r = forecast_output(prod, periods=periods)
        mape = getattr(r, "mape", "?")
        pred = getattr(r, "predicted", [])
        text = f"- MAPE: {mape}\n- Forecast {periods} periode: {pred}"
        return _ok(text, raw=r)
    except Exception as e:
        return _fail(str(e))


def tool_detect_anomalies(ds, scope, **_) -> Dict[str, Any]:
    """Deteksi anomali di data produksi."""
    try:
        from fc.intel.predictive import detect_anomalies
        from fc.kpi import scope_production
        prod = scope_production(ds.production, scope) if ds.production is not None else None
        if prod is None or prod.empty:
            return _fail("data produksi kosong")
        r = detect_anomalies(prod)
        n = len(getattr(r, "rows", []) or [])
        return _ok(f"- {n} anomali terdeteksi", raw=r)
    except Exception as e:
        return _fail(str(e))


# ==================== INVENTORY ====================
def tool_stockout_risk(ds, scope, **_) -> Dict[str, Any]:
    """Prediksi risiko stock-out per material."""
    try:
        from fc.intel.predictive import predict_stockout
        inv = ds.inventory
        if inv is None or inv.empty:
            return _fail("data inventory kosong")
        risks = predict_stockout(inv)
        lines = []
        for r in (risks or [])[:5]:
            lines.append(f"- {getattr(r, 'material', '?')}: "
                         f"{getattr(r, 'days_left', '?')} hari "
                         f"(severity {getattr(r, 'severity', '?')})")
        return _ok("\n".join(lines) or "(tidak ada risiko)", raw=risks)
    except Exception as e:
        return _fail(str(e))


# ==================== COST DNA ====================
def tool_cost_variance(ds, scope, **_) -> Dict[str, Any]:
    """Decompose variance COGM (current vs previous period)."""
    try:
        from fc.kpi import summarize, cogm_for_scope
        s = summarize(ds, scope)
        cogm = getattr(s, "cogm", None)
        if cogm is None:
            return _fail("COGM tidak tersedia")
        v = getattr(cogm, "value", None)
        return _ok(f"- COGM periode ini: Rp {v}", raw=cogm)
    except Exception as e:
        return _fail(str(e))


# ==================== RECOMMENDATIONS ====================
def tool_generate_recommendations(ds, scope, **_) -> Dict[str, Any]:
    """Ambil rekomendasi dari engine Fase 4."""
    try:
        from fc.intel.recommend import generate_recommendations
        from fc.kpi import summarize
        from fc.settings import get_active_targets
        summary = summarize(ds, scope)
        targets = get_active_targets(scope)
        recs = generate_recommendations(ds, summary, targets)
        lines = []
        for r in (recs or [])[:5]:
            lines.append(f"- [{getattr(r, 'priority', '?')}] "
                         f"{getattr(r, 'title', '?')}")
        return _ok("\n".join(lines) or "(tidak ada rekomendasi)", raw=recs)
    except Exception as e:
        return _fail(str(e))


# ==================== MAINTENANCE ====================
def tool_maintenance_signals(ds, scope, **_) -> Dict[str, Any]:
    """Deteksi sinyal maintenance: downtime tinggi, top mesin bermasalah."""
    try:
        from fc.kpi import summarize, scope_production
        prod = scope_production(ds.production, scope) if ds.production is not None else None
        if prod is None or prod.empty:
            return _fail("data produksi kosong")

        lines = []
        if "Downtime_Min" in prod.columns:
            total_dt = float(prod["Downtime_Min"].sum())
            avg_dt = float(prod["Downtime_Min"].mean())
            lines.append(f"- Total downtime: {total_dt:.0f} menit")
            lines.append(f"- Rata-rata downtime/entri: {avg_dt:.1f} menit")

            if "Machine" in prod.columns:
                top = (prod.groupby("Machine")["Downtime_Min"]
                       .sum().sort_values(ascending=False).head(3))
                lines.append("- Top 3 mesin downtime:")
                for m, v in top.items():
                    lines.append(f"  • {m}: {float(v):.0f} menit")

        s = summarize(ds, scope)
        oee = getattr(s, "oee_kpi", None)
        if oee is not None:
            lines.append(f"- OEE: {getattr(oee, 'value', '?')} "
                         f"{getattr(oee, 'note', '')}")

        return _ok("\n".join(lines) or "(tidak ada sinyal)", raw=s)
    except Exception as e:
        return _fail(str(e))


# ==================== QUALITY ====================
def tool_quality_signals(ds, scope, **_) -> Dict[str, Any]:
    """Deteksi sinyal kualitas: yield, scrap, top produk bermasalah."""
    try:
        from fc.kpi import summarize, scope_production
        prod = scope_production(ds.production, scope) if ds.production is not None else None
        if prod is None or prod.empty:
            return _fail("data produksi kosong")

        s = summarize(ds, scope)
        lines = []
        y = getattr(s, "yield_kpi", None)
        sc = getattr(s, "scrap_kpi", None)
        if y is not None:
            lines.append(f"- Yield: {getattr(y, 'value', '?')} "
                         f"{getattr(y, 'note', '')}")
        if sc is not None:
            lines.append(f"- Scrap: {getattr(sc, 'value', '?')} "
                         f"{getattr(sc, 'note', '')}")

        if "Product" in prod.columns and "Scrap_Kg" in prod.columns:
            top = (prod.groupby("Product")["Scrap_Kg"]
                   .sum().sort_values(ascending=False).head(3))
            lines.append("- Top 3 produk scrap:")
            for p, v in top.items():
                lines.append(f"  • {p}: {float(v):.0f} Kg")

        return _ok("\n".join(lines) or "(tidak ada sinyal)", raw=s)
    except Exception as e:
        return _fail(str(e))


# ==================== RISK REGISTER ====================
def tool_risk_register(ds, scope, **_) -> Dict[str, Any]:
    """Ambil risk register, urutkan berdasarkan skor P×I."""
    try:
        risk = ds.risk
        if risk is None or risk.empty:
            return _fail("data risk register kosong")

        rows = []
        for _, r in risk.iterrows():
            title = str(r.get("Risk", "?"))
            prob = r.get("Probability_Val", 0)
            imp = r.get("Impact_Val", 0)
            status = str(r.get("Status", "?"))
            try:
                score = int(prob) * int(imp)
            except (ValueError, TypeError):
                score = 0
            rows.append((score, title, prob, imp, status))

        rows.sort(key=lambda x: x[0], reverse=True)
        lines = []
        for score, title, prob, imp, status in rows[:8]:
            lines.append(f"- [{status}] {title} "
                         f"(P={prob}, I={imp}, skor={score})")

        return _ok("\n".join(lines) or "(tidak ada risiko)", raw=risk)
    except Exception as e:
        return _fail(str(e))


# ==================== REGISTRY ====================
TOOLS: Dict[str, Dict[str, Any]] = {
    "kpi_summary": {
        "fn": tool_kpi_summary,
        "desc": "Ringkasan KPI: yield, scrap, OEE, COGM",
    },
    "forecast_output": {
        "fn": tool_forecast_output,
        "desc": "Forecast output produksi N periode ke depan",
    },
    "detect_anomalies": {
        "fn": tool_detect_anomalies,
        "desc": "Deteksi anomali data produksi",
    },
    "stockout_risk": {
        "fn": tool_stockout_risk,
        "desc": "Prediksi risiko stock-out material",
    },
    "cost_variance": {
        "fn": tool_cost_variance,
        "desc": "Variance decomposition COGM antar periode",
    },
    "recommendations": {
        "fn": tool_generate_recommendations,
        "desc": "Rekomendasi dari engine Fase 4",
    },
    "maintenance_signals": {
        "fn": tool_maintenance_signals,
        "desc": "Downtime + top mesin bermasalah",
    },
    "quality_signals": {
        "fn": tool_quality_signals,
        "desc": "Yield + scrap + top produk bermasalah",
    },
    "risk_register": {
        "fn": tool_risk_register,
        "desc": "Risk register diurutkan by skor P×I",
    },
}


def call_tool(name: str, ds, scope, **kwargs) -> Dict[str, Any]:
    """Panggil tool by name. Return dict standar."""
    if name not in TOOLS:
        return _fail(f"tool '{name}' tidak terdaftar")
    try:
        return TOOLS[name]["fn"](ds, scope, **kwargs)
    except Exception as e:
        return _fail(f"{name}: {e}")


def list_tools() -> list:
    """List nama + deskripsi semua tool."""
    return [(k, v["desc"]) for k, v in TOOLS.items()]