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
    background: linear-gradient(90deg, #242748 0%, #1a1d3d 100%);
    border-left: 5px solid var(--s-color, #a489ff);
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
    color: #f5f6ff;
    letter-spacing: -0.03em;
    margin-bottom: 3px;
}
.dq-section-divider-sub {
    font-size: 0.82rem;
    color: #adb6d5;
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


# ==================== EMPTY STATE ====================
def render_empty_state(title: str, reason: str, icon: str = "📭",
                        cta_label: str = None, cta_action=None,
                        hint: str = None) -> None:
    """Render empty state yang informatif dengan title + reason + next action.
    
    Args:
        title: Judul singkat, mis. "Tidak Ada Data Produksi"
        reason: Penjelasan kenapa kosong, mis. "Filter terlalu sempit..."
        icon: Emoji besar, default 📭
        cta_label: Label tombol aksi, mis. "Reset Filter"
        cta_action: Callable yang dipanggil saat tombol diklik
        hint: Saran tambahan (opsional), mis. "Coba ubah rentang tanggal di sidebar"
    """
    # Hint block (kalau ada)
    hint_html = ""
    if hint:
        hint_html = (
            f'<div style="background: #EFF6FF; border-left: 3px solid #3B82F6;'
            f'border-radius: 8px; padding: 10px 14px; margin-top: 16px;'
            f'font-size: 0.82rem; color: #1E3A8A; text-align: left;'
            f'max-width: 500px; margin-left: auto; margin-right: auto;">'
            f'<strong>💡 Saran:</strong> {hint}'
            f'</div>'
        )

    html = (
        f'<div style="background: #F8FAFC; border: 1px dashed #CBD5E1;'
        f'border-radius: 12px; padding: 40px 30px; text-align: center;'
        f'margin: 20px 0;">'
        f'<div style="font-size: 3.5rem; margin-bottom: 14px;">{icon}</div>'
        f'<div style="font-size: 1.15rem; font-weight: 700; color: #1E1B4B;'
        f'margin-bottom: 10px;">{title}</div>'
        f'<div style="font-size: 0.9rem; color: #64748B; line-height: 1.55;'
        f'max-width: 500px; margin-left: auto; margin-right: auto;">'
        f'{reason}</div>'
        f'{hint_html}'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)

    # Tombol CTA (kalau ada)
    if cta_label and cta_action:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(cta_label, type="primary",
                         width='stretch',
                         key=f"empty_cta_{cta_label}"):
                cta_action()


def is_filter_too_narrow(prod_df, unfiltered_df=None) -> bool:
    """Cek apakah filter terlalu sempit (data ada, tapi kosong setelah filter)."""
    if unfiltered_df is None:
        return False
    has_unfiltered = unfiltered_df is not None and len(unfiltered_df) > 0
    has_filtered = prod_df is not None and len(prod_df) > 0
    return has_unfiltered and not has_filtered
# ==================== PREMIUM COMPONENTS (Fase 1) ====================

def metric_card(label: str, value: str, help_text: str = "",
                delta: str = None, delta_color: str = "#32731E",
                icon: str = "") -> None:
    """KPI card premium — label uppercase, value besar, optional delta.

    Args:
        label: Nama KPI (auto-uppercase via CSS)
        value: Nilai utama (sudah diformat)
        help_text: Subtitle kecil di bawah value (opsional)
        delta: Teks delta (mis. "+3.2%"), opsional
        delta_color: Warna delta (default hijau)
        icon: Emoji/ikon di kiri label (opsional)
    """
    icon_html = f'<span style="margin-right:6px;">{icon}</span>' if icon else ""
    help_html = (
        f'<div style="font-size:0.72rem;color:#687080;margin-top:6px;'
        f'line-height:1.4;">{help_text}</div>'
        if help_text else ""
    )
    delta_html = (
        f'<span style="color:{delta_color};font-weight:700;font-size:0.8rem;'
        f'margin-left:8px;">{delta}</span>'
        if delta else ""
    )
    html = (
        f'<div style="background:#FFFFFF;border:1px solid #E7E0F1;'
        f'border-radius:12px;padding:18px 20px;height:100%;'
        f'box-shadow:0 1px 3px rgba(45,26,91,0.04);">'
        f'<div style="font-size:0.68rem;font-weight:700;letter-spacing:0.08em;'
        f'text-transform:uppercase;color:#687080;margin-bottom:12px;">'
        f'{icon_html}{label}</div>'
        f'<div style="font-size:1.65rem;font-weight:800;letter-spacing:-0.04em;'
        f'color:#262730;line-height:1.15;">{value}{delta_html}</div>'
        f'{help_html}'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def status_badge(status: str) -> str:
    """Return HTML string badge untuk status. Pakai di st.markdown(..., unsafe_allow_html=True).

    Status yang didukung: Healthy, Watch, Critical, Good, Excellent, Fair, Needs Attention.
    """
    styles = {
        "Healthy":          ("#E8F6DF", "#32731E"),
        "Watch":            ("#FFF5D6", "#876007"),
        "Critical":         ("#FFE9E9", "#B52C36"),
        "Good":             ("#E8F6DF", "#32731E"),
        "Excellent":        ("#E8F6DF", "#32731E"),
        "Fair":             ("#FFF5D6", "#876007"),
        "Needs Attention":  ("#FFE9E9", "#B52C36"),
    }
    bg, fg = styles.get(status, ("#F1F5F9", "#475569"))
    return (
        f'<span style="display:inline-block;background:{bg};color:{fg};'
        f'border-radius:999px;padding:4px 10px;font-size:0.68rem;'
        f'font-weight:700;letter-spacing:0.04em;text-transform:uppercase;">'
        f'{status}</span>'
    )


def panel_card(title: str = "", subtitle: str = "", icon: str = "") -> None:
    """Header untuk panel. Panggil DI DALAM `with st.container(border=True)`.

    Usage:
        with st.container(border=True):
            panel_card("Cost by Plant", "Simulated calculation", "💰")
            st.bar_chart(...)
    """
    icon_html = f'{icon} ' if icon else ""
    subtitle_html = (
        f'<div style="font-size:0.8rem;color:#687080;margin-top:4px;'
        f'line-height:1.4;">{subtitle}</div>'
        if subtitle else ""
    )
    html = (
        f'<div style="margin-bottom:16px;">'
        f'<div style="font-size:1.15rem;font-weight:800;color:#1E1B4B;'
        f'letter-spacing:-0.3px;">{icon_html}{title}</div>'
        f'{subtitle_html}'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)
# ==================== DARK THEME COMPONENTS (Fase 2) ====================

def score_panel(score: float, status: str, summary: str,
                delta_text: str = "", accent: str = "#a489ff") -> None:
    """Hero banner: score besar + progress bar."""
    pct_val = max(0, min(100, score))
    delta_html = (
        f'<p style="font-size:0.75rem;color:#adb6d5;margin-top:12px;">{delta_text}</p>'
        if delta_text else ""
    )
    html = (
        f'<section style="background:linear-gradient(110deg,#30265e,#211b47 55%,#171b3c);'
        f'border:1px solid #5e5090;border-radius:16px;padding:26px 28px;'
        f'box-shadow:0 9px 30px rgba(6,9,23,0.13);">'
        f'<div style="display:grid;grid-template-columns:minmax(0,1fr) minmax(210px,38%);'
        f'gap:24px;align-items:center;">'
        f'<div>'
        f'<p style="font-size:0.62rem;color:#c9b9f8;font-weight:800;'
        f'letter-spacing:0.12em;text-transform:uppercase;margin:0;">OVERALL PERFORMANCE SCORE</p>'
        f'<div style="display:flex;align-items:baseline;gap:12px;margin-top:10px;">'
        f'<strong style="font-size:3.4rem;font-weight:800;letter-spacing:-0.045em;'
        f'line-height:1;color:#ffffff;">{pct_val:.0f}</strong>'
        f'<span style="font-size:1rem;color:#c8c2ee;">/ 100</span>'
        f'</div>'
        f'<p style="color:#e3defa;line-height:1.55;margin-top:14px;font-size:0.85rem;">{summary}</p>'
        f'</div>'
        f'<div>'
        f'<div style="display:flex;justify-content:space-between;gap:12px;'
        f'font-weight:700;margin-bottom:12px;font-size:0.78rem;color:#d6d1f7;">'
        f'<span>Performance index</span><span>{pct_val:.0f}%</span></div>'
        f'<div style="height:8px;background:#55517e;border-radius:50px;overflow:hidden;">'
        f'<span style="display:block;height:100%;width:{pct_val}%;'
        f'background:linear-gradient(90deg,#9a7af8,#6cdae7);border-radius:50px;'
        f'transition:width .35s;"></span></div>'
        f'{delta_html}'
        f'</div>'
        f'</div>'
        f'</section>'
    )
    st.markdown(html, unsafe_allow_html=True)


def section_header(title: str, note: str = "", badge: str = "") -> None:
    """Section header: title + note di kiri, badge di kanan."""
    badge_html = (
        f'<span style="display:inline-flex;align-items:center;border:1px solid #765da7;'
        f'background:#302650;color:#e3cfff;border-radius:30px;padding:6px 11px;'
        f'font-weight:700;font-size:0.66rem;white-space:nowrap;'
        f'letter-spacing:0.06em;">{badge}</span>'
        if badge else ""
    )
    note_html = (
        f'<p style="font-size:0.72rem;color:#adb6d5;margin:6px 0 0 0;'
        f'line-height:1.4;">{note}</p>'
        if note else ""
    )
    html = (
        f'<div style="display:flex;justify-content:space-between;align-items:flex-end;'
        f'gap:12px;margin-bottom:14px;">'
        f'<div>'
        f'<h2 style="font-size:1.35rem;font-weight:800;letter-spacing:-0.025em;'
        f'color:#ffffff;margin:0;line-height:1.2;">{title}</h2>'
        f'{note_html}'
        f'</div>'
        f'{badge_html}'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def kpi_card(label: str, value: str, note: str = "",
             accent: str = "#a489ff", status: str = "",
             status_color: str = "#adb6d5") -> None:
    """KPI card dengan accent bar atas + label + value + status pill."""
    note_html = (
        f'<div style="font-size:0.68rem;color:#8793bc;margin-top:10px;'
        f'line-height:1.35;">{note}</div>'
        if note else ""
    )
    status_html = (
        f'<span style="display:inline-flex;align-items:center;border-radius:6px;'
        f'padding:3px 8px;font-size:0.62rem;font-weight:800;background:#343955;'
        f'color:{status_color};margin-top:8px;letter-spacing:0.04em;'
        f'text-transform:uppercase;">{status}</span>'
        if status else ""
    )
    html = (
        f'<div style="position:relative;background:#1b1e3e;'
        f'border:1px solid #343858;border-radius:12px;padding:16px 17px;'
        f'min-height:130px;height:100%;display:flex;flex-direction:column;'
        f'justify-content:flex-start;">'
        f'<span style="position:absolute;top:0;left:17px;width:35px;height:3px;'
        f'background:{accent};border-radius:0 0 5px 5px;"></span>'
        f'<div style="font-size:0.62rem;color:#b8bedb;font-weight:600;'
        f'text-transform:uppercase;letter-spacing:0.06em;line-height:1.3;">'
        f'{label}</div>'
        f'<div style="font-size:1.55rem;font-weight:800;letter-spacing:-0.04em;'
        f'margin:12px 0 0 0;color:#ffffff;line-height:1.15;">{value}</div>'
        f'{status_html}'
        f'{note_html}'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def highlight_card(title: str, body: str, color: str = "#77edb4",
                   bg: str = "#172d35", line: str = "#276956") -> None:
    """Colored info block (Pencapaian / Perhatian / Risiko / Rekomendasi)."""
    html = (
        f'<div style="padding:16px 18px;background:{bg};border:1px solid {line};'
        f'border-radius:12px;min-height:120px;line-height:1.55;">'
        f'<h3 style="color:{color};font-weight:800;font-size:1.05rem;'
        f'margin:0 0 10px 0;letter-spacing:-0.02em;">{title}</h3>'
        f'<p style="color:#d8dcf2;font-size:0.78rem;margin:0;'
        f'line-height:1.55;">{body}</p>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def filter_bar(*,
               period_options=None,
               plant_options=None,
               key_prefix: str = "fb") -> dict:
    """Filter bar standard. Return dict {period, plant}."""
    period_options = period_options or ["Semua Periode"]
    plant_options = plant_options or ["Semua Plant"]

    c1, c2, c3 = st.columns([1, 1, 2], gap="small")
    with c1:
        period = st.selectbox("Periode", period_options, key=f"{key_prefix}_period")
    with c2:
        plant = st.selectbox("Plant", plant_options, key=f"{key_prefix}_plant")
    return {"period": period, "plant": plant}
# ==================== NUMBER FORMATTING (Indonesian) ====================
import math as _math


def fmt_thousand(v, decimals: int = 0):
    """Format angka jadi string dengan titik ribuan Indonesia.

    Contoh:
        2889047350 → '2.889.047.350'
        1234.5678  → '1.234,57'
    """
    try:
        if v is None:
            return "—"
        f = float(v)
        if _math.isnan(f) or _math.isinf(f):
            return "—"
        if decimals > 0:
            return f"{f:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"{f:,.0f}".replace(",", ".")
    except (ValueError, TypeError):
        return str(v) if v is not None else "—"


def fmt_pct(v, decimals: int = 2):
    """Format persentase Indonesia. -3.7872 → '-3,79%'"""
    try:
        if v is None:
            return "—"
        f = float(v)
        if _math.isnan(f) or _math.isinf(f):
            return "—"
        return f"{f:.{decimals}f}".replace(".", ",") + "%"
    except (ValueError, TypeError):
        return str(v) if v is not None else "—"


def fmt_rp(v, decimals: int = 0, compact: bool = False):
    """Format Rupiah.

    compact=False: 'Rp 2.889.047.350'
    compact=True:  'Rp 2,89 M' (miliar) / 'Rp 2,9 jt' (juta) / 'Rp 2,9 rb' (ribu)
    """
    try:
        if v is None:
            return "—"
        f = float(v)
        if _math.isnan(f) or _math.isinf(f):
            return "—"
        if compact:
            if abs(f) >= 1_000_000_000:
                return "Rp " + f"{f/1_000_000_000:.2f}".replace(".", ",") + " M"
            if abs(f) >= 1_000_000:
                return "Rp " + f"{f/1_000_000:.1f}".replace(".", ",") + " jt"
            if abs(f) >= 1_000:
                return "Rp " + f"{f/1_000:.1f}".replace(".", ",") + " rb"
        if decimals > 0:
            return "Rp " + f"{f:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return "Rp " + f"{f:,.0f}".replace(",", ".")
    except (ValueError, TypeError):
        return str(v) if v is not None else "—"


# Pattern keyword untuk auto-detection
_PCT_KEYWORDS = ("pct", "%", "percent", "persen", "rate", "ratio",
                 "yield", "oee", "scrap", "utilization", "achievement")
_RP_KEYWORDS = ("rp", "harga", "price", "biaya", "cost", "budget", "actual",
                "variance", "revenue", "saving", "impact", "amount",
                "cogm", "cash", "value", "nilai")
_QTY_KEYWORDS = ("qty", "quantity", "volume", "unit", "kg", "pcs", "count",
                 "rows", "baris", "jumlah", "stock", "usage",
                 "output", "input")


def fmt_df_id(df, thousand_cols=None, pct_cols=None, rp_cols=None, auto=True):
    """Format semua kolom numerik di dataframe jadi string Indonesia.

    Args:
        df: pandas DataFrame
        thousand_cols: kolom yang diformat dengan titik ribuan
        pct_cols: kolom yang diformat sebagai persen
        rp_cols: kolom yang diformat sebagai Rupiah
        auto: True = auto-detect berdasarkan nama kolom

    Returns:
        DataFrame copy dengan kolom sudah diformat.
    """
    import pandas as pd

    if df is None or (hasattr(df, "empty") and df.empty):
        return df

    out = df.copy()
    thousand_cols = set(thousand_cols or [])
    pct_cols = set(pct_cols or [])
    rp_cols = set(rp_cols or [])

    for col in out.columns:
        col_str = str(col).lower()

        # Explicit override
        if col in pct_cols or col_str in pct_cols:
            out[col] = out[col].apply(fmt_pct)
            continue
        if col in rp_cols or col_str in rp_cols:
            out[col] = out[col].apply(fmt_rp)
            continue
        if col in thousand_cols or col_str in thousand_cols:
            out[col] = out[col].apply(fmt_thousand)
            continue

        if not auto:
            continue

        # Skip non-numeric
        if not pd.api.types.is_numeric_dtype(out[col]):
            continue

        # Auto-detect: pct → rp → qty → default numeric
        if any(k in col_str for k in _PCT_KEYWORDS):
            out[col] = out[col].apply(fmt_pct)
        elif any(k in col_str for k in _RP_KEYWORDS):
            out[col] = out[col].apply(fmt_rp)
        elif any(k in col_str for k in _QTY_KEYWORDS):
            out[col] = out[col].apply(fmt_thousand)
        elif pd.api.types.is_integer_dtype(out[col]):
            out[col] = out[col].apply(fmt_thousand)
        elif pd.api.types.is_float_dtype(out[col]):
            # Float besar → thousand; float kecil (ratio) → biarkan
            try:
                col_data = out[col].dropna()
                if len(col_data) > 0 and col_data.abs().max() > 10:
                    out[col] = out[col].apply(fmt_thousand)
            except Exception:
                pass

    return out


def dataframe_id(df, **kwargs):
    """Wrapper st.dataframe dengan format Indonesia otomatis.

    Pakai seperti: dataframe_id(df, width='stretch', hide_index=True)
    """
    formatted = fmt_df_id(df)
    st.dataframe(formatted, **kwargs)
# ==================== HTML TABLE RENDERER (Fix dataframe kosong di production) ====================
def render_table(df, max_height: str = "400px", compact: bool = False):
    """
    Render DataFrame sebagai HTML table yang fully dark-controllable.
    Menggantikan st.dataframe() untuk konsistensi theme di production.

    Args:
        df: pandas DataFrame
        max_height: tinggi maksimal (default 400px, scroll jika lebih)
        compact: mode kompak (padding lebih kecil)
    """
    if df is None:
        st.info("Tidak ada data untuk ditampilkan.")
        return
    try:
        if df.empty:
            st.info("Tidak ada data untuk ditampilkan.")
            return
    except Exception:
        pass

    padding = "6px 10px" if compact else "10px 14px"
    font_size = "0.72rem" if compact else "0.78rem"

    headers = "".join(f"<th>{c}</th>" for c in df.columns)

    rows_html = []
    for _, row in df.iterrows():
        cells = []
        for v in row:
            s = "" if v is None else str(v)
            cells.append(f"<td>{s}</td>")
        rows_html.append(f"<tr>{''.join(cells)}</tr>")

    html = f"""
    <div style="
        border: 1px solid #343858;
        border-radius: 10px;
        overflow: hidden;
        background: #1a1d3d;
        margin: 8px 0 16px 0;
        max-height: {max_height};
        overflow-y: auto;
        overflow-x: auto;
    ">
        <table class="dq-html-table" style="
            width: 100%;
            border-collapse: collapse;
            font-size: {font_size};
            font-family: 'DM Sans', sans-serif;
        ">
            <thead style="position: sticky; top: 0; z-index: 1;">
                <tr style="background: #242844;">{headers}</tr>
            </thead>
            <tbody>{''.join(rows_html)}</tbody>
        </table>
    </div>
    <style>
    .dq-html-table th {{
        background: #242844 !important;
        color: #adb6d5 !important;
        text-align: left;
        padding: {padding};
        border-bottom: 1px solid #343858;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        font-size: 0.68rem;
        white-space: nowrap;
    }}
    .dq-html-table td {{
        color: #e6e8f6 !important;
        padding: {padding};
        border-bottom: 1px solid #2d3155;
    }}
    .dq-html-table tr:hover td {{
        background: #242844;
    }}
    .dq-html-table tr:last-child td {{
        border-bottom: 0;
    }}
    </style>
    """
    st.markdown(html, unsafe_allow_html=True)