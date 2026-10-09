"""Shared UI components untuk Decidiq — header, health score, section, partial, proyeksi."""
import calendar as _cal
import pandas as _pd
import streamlit as st


# ==================== META ====================
GRANULARITY_META = {
    "Harian":    {"icon": "📅", "color": "#3B82F6", "desc": "Data per tanggal"},
    "Bulanan":   {"icon": "📆", "color": "#8B5CF6", "desc": "Data agregat per bulan"},
    "Snapshot":  {"icon": "📸", "color": "#F59E0B", "desc": "Data saat ini (real-time)"},
    "Total":     {"icon": "Σ",  "color": "#64748B", "desc": "Total periode terfilter"},
    "Multi":     {"icon": "📊", "color": "#EC4899", "desc": "Kombinasi beberapa granularitas"},
    "Live":      {"icon": "⚡", "color": "#10B981", "desc": "Real-time"},
}


# ==================== CSS ====================
CSS = """
<style>
.dq-page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    padding: 0 0 16px 0;
    border-bottom: 1px solid #E9D5FF;
    margin-bottom: 20px;
    flex-wrap: wrap;
    gap: 12px;
}
.dq-page-header-left { flex: 1; min-width: 300px; }
.dq-page-header-title {
    font-size: 2rem;
    font-weight: 800;
    color: #0F172A;
    letter-spacing: -1px;
    line-height: 1.15;
    margin-bottom: 6px;
    background: linear-gradient(90deg, #1E1B4B 0%, #8B5CF6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    display: inline-block;
}
.dq-page-header-sub {
    font-size: 0.9rem;
    color: #64748B;
    line-height: 1.5;
}
.dq-page-header-right {
    display: flex;
    gap: 8px;
    align-items: center;
    flex-wrap: wrap;
}
.dq-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    border-radius: 999px;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    white-space: nowrap;
    border: 1px solid;
}
.dq-badge-granularity {
    background: color-mix(in srgb, var(--g-color, #8B5CF6) 10%, white);
    color: var(--g-color, #8B5CF6);
    border-color: color-mix(in srgb, var(--g-color, #8B5CF6) 30%, transparent);
}
.dq-badge-period {
    background: #F5F3FF;
    color: #6D28D9;
    border-color: #C4B5FD;
}

/* Mini Health Score */
.dq-mini-health {
    background: linear-gradient(135deg, #0F172A 0%, #1E1B4B 100%);
    border-radius: 12px;
    padding: 14px 18px;
    color: white;
    box-shadow: 0 6px 16px rgba(30, 27, 75, 0.2);
    border: 1px solid rgba(139, 92, 246, 0.3);
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 20px;
    position: relative;
    overflow: hidden;
}
.dq-mini-health::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 4px; height: 100%;
    background: var(--h-color, #8B5CF6);
}
.dq-mini-health-score {
    font-size: 1.8rem;
    font-weight: 900;
    letter-spacing: -1px;
    line-height: 1;
    color: #FFFFFF;
}
.dq-mini-health-score-max {
    font-size: 0.75rem;
    color: #94A3B8;
    font-weight: 600;
}
.dq-mini-health-info { flex: 1; min-width: 120px; }
.dq-mini-health-label {
    font-size: 0.65rem;
    letter-spacing: 1.2px;
    color: #A78BFA;
    font-weight: 700;
    text-transform: uppercase;
    margin-bottom: 4px;
}
.dq-mini-health-status {
    font-size: 0.82rem;
    font-weight: 700;
    letter-spacing: 0.8px;
    text-transform: uppercase;
}
.dq-mini-health-track {
    flex: 1;
    height: 6px;
    background: rgba(148, 163, 184, 0.18);
    border-radius: 999px;
    overflow: hidden;
    min-width: 100px;
}
.dq-mini-health-fill {
    height: 100%;
    border-radius: 999px;
    transition: width 0.5s ease;
}

/* Section Divider */
.dq-section-divider {
    margin: 32px 0 20px 0;
    padding: 18px 24px;
    background: linear-gradient(90deg, var(--s-bg1, #F5F3FF) 0%, var(--s-bg2, #FFFFFF) 100%);
    border-left: 5px solid var(--s-color, #8B5CF6);
    border-radius: 12px;
    display: flex;
    align-items: center;
    gap: 16px;
}
.dq-section-divider-icon {
    font-size: 1.8rem;
    line-height: 1;
}
.dq-section-divider-body { flex: 1; }
.dq-section-divider-title {
    font-size: 1.2rem;
    font-weight: 800;
    color: #1E1B4B;
    letter-spacing: -0.3px;
    margin-bottom: 3px;
}
.dq-section-divider-sub {
    font-size: 0.82rem;
    color: #64748B;
    line-height: 1.4;
}
.dq-section-divider-badge {
    background: var(--s-color, #8B5CF6);
    color: #FFFFFF;
    font-size: 0.65rem;
    font-weight: 800;
    letter-spacing: 1.2px;
    padding: 5px 12px;
    border-radius: 999px;
    text-transform: uppercase;
    white-space: nowrap;
}
</style>
"""


def _inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


# ==================== PAGE HEADER ====================
def page_header(title: str, subtitle: str = "",
                granularity: str = "Bulanan",
                period_label: str = None,
                icon: str = "") -> None:
    _inject_css()
    meta = GRANULARITY_META.get(granularity, GRANULARITY_META["Bulanan"])
    g_icon = meta["icon"]
    g_color = meta["color"]
    title_html = f"{icon} {title}" if icon else title

    period_badge = ""
    if period_label:
        period_badge = (
            f'<span class="dq-badge dq-badge-period">📅 {period_label}</span>'
        )

    html = (
        f'<div class="dq-page-header">'
        f'<div class="dq-page-header-left">'
        f'<div class="dq-page-header-title">{title_html}</div>'
        f'<div class="dq-page-header-sub">{subtitle}</div>'
        f'</div>'
        f'<div class="dq-page-header-right">'
        f'<span class="dq-badge dq-badge-granularity" style="--g-color: {g_color};">'
        f'{g_icon} {granularity}</span>'
        f'{period_badge}'
        f'</div>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


# ==================== MINI HEALTH SCORE ====================
def mini_health_score(score: float, status: str, color: str) -> None:
    html = (
        f'<div class="dq-mini-health" style="--h-color: {color};">'
        f'<div><div class="dq-mini-health-score">{score:.0f}'
        f'<span class="dq-mini-health-score-max">/100</span></div></div>'
        f'<div class="dq-mini-health-info">'
        f'<div class="dq-mini-health-label">🏥 Plant Health Score</div>'
        f'<div class="dq-mini-health-status" style="color: {color};">● {status}</div>'
        f'</div>'
        f'<div class="dq-mini-health-track">'
        f'<div class="dq-mini-health-fill" style="width: {score}%; '
        f'background: linear-gradient(90deg, #8B5CF6 0%, {color} 100%);"></div>'
        f'</div>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


# ==================== FORMAT PERIOD LABEL ====================
def format_period_label(scope) -> str:
    if scope is None:
        return None
    start = getattr(scope, "start", None)
    end = getattr(scope, "end", None)
    if start and end:
        if start == end:
            return str(start)
        return f"{start} → {end}"
    return None


# ==================== HEALTH SCORE CALCULATOR ====================
def compute_health_score(s, targets):
    components, weights = [], []

    if s.yield_pct.available:
        components.append(min(100.0, max(0.0, (s.yield_pct.value / targets.yield_min) * 100)))
        weights.append(0.30)
    if s.oee.oee.available:
        components.append(min(100.0, max(0.0, (s.oee.oee.value / targets.oee_min) * 100)))
        weights.append(0.30)
    if s.scrap_pct.available:
        components.append(min(100.0, max(0.0, (1 - s.scrap_pct.value / (targets.scrap_max * 2)) * 100)))
        weights.append(0.20)
    if s.cost_per_kg.available:
        components.append(85.0)
        weights.append(0.20)

    if not components:
        return 0.0, "No Data", "#94A3B8"

    tw = sum(weights)
    score = sum(c * w for c, w in zip(components, weights)) / tw if tw else 0.0

    if score >= 90:
        return score, "Excellent", "#10B981"
    elif score >= 80:
        return score, "Good", "#8B5CF6"
    elif score >= 70:
        return score, "Fair", "#F59E0B"
    return score, "Needs Attention", "#EF4444"


# ==================== SECTION DIVIDER ====================
def section_divider(title: str, subtitle: str = "", icon: str = "📊",
                    badge: str = None, color: str = "#8B5CF6",
                    bg1: str = "#F5F3FF", bg2: str = "#FFFFFF") -> None:
    badge_html = ""
    if badge:
        badge_html = f'<div class="dq-section-divider-badge">{badge}</div>'

    html = (
        f'<div class="dq-section-divider" '
        f'style="--s-color: {color}; --s-bg1: {bg1}; --s-bg2: {bg2};">'
        f'<div class="dq-section-divider-icon">{icon}</div>'
        f'<div class="dq-section-divider-body">'
        f'<div class="dq-section-divider-title">{title}</div>'
        f'<div class="dq-section-divider-sub">{subtitle}</div>'
        f'</div>'
        f'{badge_html}'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


# ==================== PARTIAL PERIOD DETECTOR ====================
def detect_partial_periods(production_df) -> set:
    """Deteksi period (YYYY-MM) yang belum lengkap 1 bulan."""
    if production_df is None or len(production_df) == 0:
        return set()
    if "Date" not in production_df.columns:
        return set()
    try:
        df = production_df.copy()
        df["Date"] = _pd.to_datetime(df["Date"], errors="coerce")
        df = df.dropna(subset=["Date"])
        if df.empty:
            return set()

        df["Period"] = df["Date"].dt.strftime("%Y-%m")
        last_period = df["Period"].max()

        last_month_dates = df[df["Period"] == last_period]["Date"]
        days_in_data = last_month_dates.dt.day.nunique()
        last_date = last_month_dates.max()
        total_days = _cal.monthrange(last_date.year, last_date.month)[1]

        partials = set()
        if days_in_data < total_days:
            partials.add(last_period)
        return partials
    except Exception:
        return set()


def partial_period_note(period: str, production_df) -> str:
    """Catatan info untuk bulan partial."""
    if production_df is None or "Date" not in production_df.columns:
        return ""
    try:
        df = production_df.copy()
        df["Date"] = _pd.to_datetime(df["Date"], errors="coerce")
        df = df.dropna(subset=["Date"])
        df["Period"] = df["Date"].dt.strftime("%Y-%m")
        subset = df[df["Period"] == period]
        if subset.empty:
            return ""
        days_in_data = subset["Date"].dt.day.nunique()
        last_date = subset["Date"].max()
        total_days = _cal.monthrange(last_date.year, last_date.month)[1]
        month_name = _cal.month_name[last_date.month]
        return (f"Bulan **{month_name} {last_date.year}** baru "
                f"**{days_in_data} dari {total_days} hari**. "
                f"Angka belum final — akan berubah saat bulan selesai.")
    except Exception:
        return ""


def partial_warning_banner(partial_periods: set, production_df) -> None:
    """Warning box jika ada bulan partial."""
    if not partial_periods:
        return
    period = sorted(partial_periods)[-1]
    note = partial_period_note(period, production_df)
    if not note:
        return
    html = (
        f'<div style="background: linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%);'
        f'border-left: 4px solid #F59E0B;border-radius: 10px;padding: 14px 18px;'
        f'margin: 12px 0 20px 0;display: flex;gap: 12px;align-items: start;">'
        f'<div style="font-size: 1.3rem;flex-shrink:0;">⚠️</div>'
        f'<div style="font-size: 0.88rem;color: #78350F;line-height: 1.5;">'
        f'<strong style="color:#92400E;">Data Belum Lengkap:</strong> {note}'
        f'</div>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


# ==================== PERIOD SELECTOR ====================
def period_selector(ds, key: str = "global_period_selector",
                    label: str = "🔍 Pilih Periode untuk Analisis Breakdown",
                    show_partial: bool = True):
    """Dropdown untuk memilih periode (bulan) atau Total."""
    if ds.costs is None or ds.costs.empty or "Period" not in ds.costs.columns:
        return None, [], set()

    periods = sorted([str(p) for p in ds.costs["Period"].dropna().unique() if str(p).strip()])
    partials = detect_partial_periods(ds.production) if show_partial else set()

    options = ["📊 Semua Periode (Total)"]
    period_map = {"📊 Semua Periode (Total)": None}

    for p in periods:
        lbl = f"📅 {p}"
        if p in partials:
            lbl += "  ⚠️ PARTIAL"
        options.append(lbl)
        period_map[lbl] = p

    selected = st.selectbox(label, options=options, index=0, key=key)
    return period_map[selected], periods, partials


def filter_dataset_by_period(ds, period: str):
    """Filter ds.costs dan ds.production ke periode tertentu."""
    if period is None:
        return ds.costs, ds.production

    costs_f = ds.costs[ds.costs["Period"] == period].copy()

    prod_f = ds.production.copy()
    if "Date" in prod_f.columns:
        prod_f["Date"] = _pd.to_datetime(prod_f["Date"])
        prod_f["Period"] = prod_f["Date"].dt.strftime("%Y-%m")
        prod_f = prod_f[prod_f["Period"] == period]

    return costs_f, prod_f


# ==================== PROYEKSI COGM AKHIR BULAN ====================
def project_month_end_cogm(costs_filtered, prod_filtered, period: str):
    """Proyeksi COGM akhir bulan berdasarkan data partial."""
    result = {
        "cost_so_far": 0.0,
        "days_elapsed": 0,
        "days_total": 0,
        "cost_projected": 0.0,
        "output_projected": 0.0,
        "is_partial": False,
    }

    if costs_filtered is None or costs_filtered.empty:
        return result
    if prod_filtered is None or prod_filtered.empty:
        return result

    try:
        cost_so_far = float(costs_filtered["Cost"].sum())
        result["cost_so_far"] = cost_so_far

        df = prod_filtered.copy()
        df["Date"] = _pd.to_datetime(df["Date"], errors="coerce")
        df = df.dropna(subset=["Date"])

        days_elapsed = df["Date"].dt.day.nunique()
        result["days_elapsed"] = days_elapsed

        year, month = map(int, period.split("-"))
        days_total = _cal.monthrange(year, month)[1]
        result["days_total"] = days_total

        if days_elapsed < days_total:
            result["is_partial"] = True
            ratio = days_total / days_elapsed if days_elapsed > 0 else 1
            result["cost_projected"] = cost_so_far * ratio
            output_so_far = float(df["Output_Kg"].sum())
            result["output_projected"] = output_so_far * ratio
        else:
            result["cost_projected"] = cost_so_far
            result["output_projected"] = float(df["Output_Kg"].sum())
    except Exception:
        pass

    return result


def render_projection_card(proj: dict, accent: str = "#F59E0B") -> None:
    """Kartu proyeksi COGM akhir bulan untuk periode partial."""
    if not proj.get("is_partial"):
        return
    if proj["days_elapsed"] == 0:
        return

    cost_so_far = proj["cost_so_far"]
    cost_proj = proj["cost_projected"]
    days_elapsed = proj["days_elapsed"]
    days_total = proj["days_total"]

    def _fmt(v):
        if abs(v) >= 1_000_000_000:
            return f"Rp {v/1_000_000_000:.2f} M"
        if abs(v) >= 1_000_000:
            return f"Rp {v/1_000_000:.1f} jt"
        return f"Rp {v:,.0f}"

    html = (
        f'<div style="background: linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%);'
        f'border-left: 4px solid {accent};border-radius: 12px;'
        f'padding: 18px 22px;margin-bottom: 16px;">'
        f'<div style="font-size:0.7rem;font-weight:800;letter-spacing:1.5px;'
        f'color:#92400E;text-transform:uppercase;margin-bottom:8px;">'
        f'📈 Proyeksi Akhir Bulan (Estimasi)</div>'
        f'<div style="display:flex;gap:24px;flex-wrap:wrap;align-items:baseline;">'
        f'<div>'
        f'<div style="font-size:0.72rem;color:#78350F;margin-bottom:4px;">'
        f'Saat ini ({days_elapsed}/{days_total} hari)</div>'
        f'<div style="font-size:1.1rem;font-weight:800;color:#78350F;">{_fmt(cost_so_far)}</div>'
        f'</div>'
        f'<div style="font-size:1.4rem;color:#B45309;">→</div>'
        f'<div>'
        f'<div style="font-size:0.72rem;color:#78350F;margin-bottom:4px;">'
        f'Proyeksi akhir bulan</div>'
        f'<div style="font-size:1.4rem;font-weight:900;color:#92400E;'
        f'letter-spacing:-0.5px;">{_fmt(cost_proj)}</div>'
        f'</div>'
        f'</div>'
        f'<div style="font-size:0.72rem;color:#92400E;margin-top:10px;font-style:italic;">'
        f'⚠️ Angka estimasi berdasarkan rata-rata harian. '
        f'Akan lebih akurat saat bulan mendekati closing.</div>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)