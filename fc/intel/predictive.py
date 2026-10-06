"""Predictive Engine — forecast output, anomali, stock-out (BRD 8).

Aturan BRD 8:
  * MAPE ≤ 15% untuk forecast output (usulan)
  * Baseline pembanding: moving average
  * Metode transparan sebelum model kompleks
  * Semua model run dicatat di DB (tabel model_runs)
"""
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

# Optional imports — graceful fallback
try:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False

try:
    from sklearn.ensemble import IsolationForest
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


# ==================== FORECAST ====================

@dataclass
class ForecastResult:
    dates: List[date]
    values: List[float]
    lower: List[float]
    upper: List[float]
    mape: Optional[float]
    method: str
    note: str = ""


def _mape(actual: np.ndarray, predicted: np.ndarray) -> float:
    """Mean Absolute Percentage Error (%)."""
    mask = actual != 0
    if not mask.any():
        return float("nan")
    return float(np.mean(np.abs((actual[mask] - predicted[mask]) / actual[mask])) * 100)


def _sma_forecast(series: pd.Series, periods: int, window: int = 7) -> np.ndarray:
    """Simple Moving Average + linear trend."""
    if len(series) < window:
        return np.full(periods, series.mean())
    recent = series.iloc[-window:].values
    # Trend sederhana: rata-rata perubahan
    diffs = np.diff(recent)
    avg_trend = diffs.mean() if len(diffs) else 0
    base = recent.mean()
    return np.array([base + avg_trend * (i + 1) for i in range(periods)])


def _holt_winters_forecast(series: pd.Series, periods: int,
                           seasonal_periods: int = 7) -> Optional[np.ndarray]:
    """Holt-Winters Exponential Smoothing."""
    if not HAS_STATSMODELS:
        return None
    try:
        model = ExponentialSmoothing(
            series.values,
            trend="add",
            seasonal="add" if len(series) >= seasonal_periods * 2 else None,
            seasonal_periods=seasonal_periods if len(series) >= seasonal_periods * 2 else None,
            initialization_method="estimated",
        ).fit()
        return model.forecast(periods).values
    except Exception:
        return None


def forecast_output(prod_df: pd.DataFrame, periods: int = 7,
                    backtest: bool = True) -> ForecastResult:
    """Forecast output harian. periods = jumlah hari ke depan.

    Args:
        prod_df: DataFrame dengan kolom Date dan Output_Kg
        periods: jumlah hari yang diprediksi
        backtest: kalau True, hitung MAPE vs 30% data terakhir

    Returns:
        ForecastResult
    """
    if prod_df is None or prod_df.empty or "Date" not in prod_df.columns \
            or "Output_Kg" not in prod_df.columns:
        return ForecastResult([], [], [], [], None, "none", "Data tidak tersedia.")

    df = prod_df.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    agg = df.groupby("Date", as_index=False)["Output_Kg"].sum().sort_values("Date")

    if len(agg) < 14:
        return ForecastResult([], [], [], [], None, "none",
                              "Butuh minimal 14 hari data untuk forecast.")

    series = agg.set_index("Date")["Output_Kg"]
    last_date = series.index[-1].date()

    # Pilih metode
    method = "sma_7"
    forecast = None

    if HAS_STATSMODELS:
        hw = _holt_winters_forecast(series, periods)
        if hw is not None and not np.isnan(hw).any():
            forecast = hw
            method = "holt_winters"

    if forecast is None:
        forecast = _sma_forecast(series, periods)
        method = "sma_7"

    # MAPE via backtest
    mape_val = None
    if backtest and len(series) >= 30:
        cutoff = int(len(series) * 0.7)
        train = series.iloc[:cutoff]
        test = series.iloc[cutoff:]

        # Prediksi test dengan metode yang sama
        if method == "holt_winters":
            bt = _holt_winters_forecast(train, len(test))
        else:
            bt = _sma_forecast(train, len(test))

        if bt is not None:
            mape_val = _mape(test.values, bt)

    # Confidence interval (simple: ±10% atau dari std residual)
    residuals = series.diff().dropna()
    std_resid = residuals.std() if len(residuals) > 0 else 0
    ci_width = 1.96 * std_resid if std_resid > 0 else series.mean() * 0.1

    dates = [last_date + timedelta(days=i + 1) for i in range(periods)]
    lower = [max(0, v - ci_width) for v in forecast]
    upper = [v + ci_width for v in forecast]

    note = ""
    if mape_val is not None:
        if mape_val > 15:
            note = f"MAPE {mape_val:.1f}% > target 15% — pertimbangkan tambah data historis."
        else:
            note = f"MAPE {mape_val:.1f}% — sesuai target ≤ 15%."
    if not HAS_STATSMODELS:
        note += " (statsmodels tidak terinstall, memakai SMA+trend)"

    return ForecastResult(
        dates=dates,
        values=list(forecast),
        lower=lower,
        upper=upper,
        mape=mape_val,
        method=method,
        note=note.strip(),
    )


# ==================== ANOMALY DETECTION ====================

@dataclass
class AnomalyResult:
    total: int
    anomalies: pd.DataFrame
    method: str
    threshold_info: str


def detect_anomalies(prod_df: pd.DataFrame,
                     contamination: float = 0.05) -> AnomalyResult:
    """Deteksi anomali scrap. Pakai Isolation Forest kalau tersedia, else IQR.

    Args:
        prod_df: DataFrame dengan Scrap_Kg dan Input_Kg
        contamination: estimasi proporsi anomali (5% default)

    Returns:
        AnomalyResult
    """
    cols = {"Scrap_Kg", "Input_Kg"}
    if prod_df is None or prod_df.empty or not cols <= set(prod_df.columns):
        return AnomalyResult(0, pd.DataFrame(), "none", "Butuh kolom Scrap_Kg & Input_Kg.")

    df = prod_df.copy()
    df["Scrap_Pct"] = (df["Scrap_Kg"] / df["Input_Kg"].replace(0, np.nan)) * 100
    df = df.dropna(subset=["Scrap_Pct"])

    if len(df) < 10:
        return AnomalyResult(0, pd.DataFrame(), "none", "Butuh minimal 10 baris data.")

    X = df[["Scrap_Pct"]].values

    if HAS_SKLEARN:
        model = IsolationForest(contamination=contamination, random_state=42)
        preds = model.fit_predict(X)
        df["Is_Anomaly"] = preds == -1
        method = "isolation_forest"
        threshold_info = f"contamination={contamination}"
    else:
        # IQR fallback
        q1, q3 = np.percentile(df["Scrap_Pct"], [25, 75])
        iqr = q3 - q1
        upper = q3 + 2.0 * iqr
        df["Is_Anomaly"] = df["Scrap_Pct"] > upper
        method = "iqr"
        threshold_info = f"Q3 + 2×IQR = {upper:.2f}%"

    anomalies = df[df["Is_Anomaly"]].copy()
    return AnomalyResult(
        total=int(df["Is_Anomaly"].sum()),
        anomalies=anomalies,
        method=method,
        threshold_info=threshold_info,
    )


# ==================== STOCK-OUT PREDICTION ====================

@dataclass
class StockOutRisk:
    material: str
    stock_kg: float
    monthly_usage: float
    daily_usage: float
    days_until_empty: Optional[float]
    status: str  # critical | warning | ok


def predict_stockout(inventory_df: pd.DataFrame,
                     critical_days: int = 14,
                     warning_days: int = 30) -> List[StockOutRisk]:
    """Prediksi kapan material akan habis.

    Args:
        inventory_df: DataFrame dengan Material, Stock_Kg, Monthly_Usage
        critical_days: < N hari = critical
        warning_days: < N hari = warning

    Returns:
        list of StockOutRisk
    """
    if inventory_df is None or inventory_df.empty:
        return []
    if not {"Material", "Stock_Kg", "Monthly_Usage"} <= set(inventory_df.columns):
        return []

    results = []
    for _, row in inventory_df.iterrows():
        stock = float(row["Stock_Kg"])
        usage = float(row["Monthly_Usage"])
        daily = usage / 30.0 if usage > 0 else 0

        if daily <= 0:
            days = None
            status = "ok" if stock > 0 else "critical"
        else:
            days = stock / daily
            if days < critical_days:
                status = "critical"
            elif days < warning_days:
                status = "warning"
            else:
                status = "ok"

        results.append(StockOutRisk(
            material=str(row["Material"]),
            stock_kg=stock,
            monthly_usage=usage,
            daily_usage=daily,
            days_until_empty=days,
            status=status,
        ))

    # Sort: critical dulu, lalu by days
    status_order = {"critical": 0, "warning": 1, "ok": 2}
    results.sort(key=lambda r: (status_order[r.status],
                                 r.days_until_empty if r.days_until_empty is not None else 9999))
    return results


# ==================== SLOW-MOVING PREDICTION ====================

@dataclass
class SlowMovingRisk:
    material: str
    current_days: Optional[float]
    trend: str  # rising | falling | stable
    predicted_days_30d: Optional[float]
    risk_level: str


def predict_slow_moving(inventory_df: pd.DataFrame,
                        slow_moving_days: int = 45) -> List[SlowMovingRisk]:
    """Prediksi material yang akan jadi slow-moving 30 hari ke depan.

    Simple heuristic: kalau days_inventory sekarang > 0.7 × slow_moving_days,
    dan trend tidak menurun, tandai sebagai calon slow-moving.
    """
    if inventory_df is None or inventory_df.empty:
        return []

    results = []
    for _, row in inventory_df.iterrows():
        stock = float(row.get("Stock_Kg", 0))
        usage = float(row.get("Monthly_Usage", 0))

        if usage <= 0:
            current = None
            trend = "stable"
            predicted = None
            risk = "dead_stock" if stock > 0 else "ok"
        else:
            current = stock / (usage / 30.0)
            # Asumsi usage stabil
            predicted = current * 0.9  # konservatif: turun 10%
            trend = "stable"
            if current > slow_moving_days:
                risk = "slow_moving"
            elif current > slow_moving_days * 0.7:
                risk = "watch"
            else:
                risk = "ok"

        results.append(SlowMovingRisk(
            material=str(row.get("Material", "?")),
            current_days=current,
            trend=trend,
            predicted_days_30d=predicted,
            risk_level=risk,
        ))

    return results