import pandas as pd
import numpy as np

# --- Configuration ---
year = 2025
start_date = f'{year}-01-01'
end_date = f'{year}-12-31 23:45:00'
freq = '15T'
timestamps = pd.date_range(start=start_date, end=end_date, freq=freq)
n = len(timestamps)

# Helper Arrays
day_of_year = np.array(timestamps.dayofyear)
hour_of_day = np.array(timestamps.hour) + np.array(timestamps.minute) / 60.0
is_peak = (hour_of_day >= 18) & (hour_of_day <= 22)

np.random.seed(42)

# ==========================================
# 1. GENERATE CLEAN BASELINE (So we have something to break)
# ==========================================

# Demand
base_load = np.random.normal(loc=500, scale=20, size=n)
is_sunday = timestamps.dayofweek == 6
base_load[is_sunday] *= 0.85
energy_required_kwh = np.maximum(base_load + np.random.normal(0, 15, n), 200).round(2)

# Generation
solar_season = 1 + 0.35 * np.sin(2 * np.pi * (day_of_year - 60) / 365)
solar_curve = np.maximum(0, np.sin((hour_of_day - 6) * np.pi / 13))
generation_solar_kwh = (400 * solar_curve * solar_season * np.random.uniform(0.9, 1.0, n)).round(2)

wind_season = 1 + 0.6 * np.sin(2 * np.pi * (day_of_year - 170) / 365)
generation_wind_kwh = (150 * 0.4 * wind_season * np.random.weibull(2.5, size=n)).round(2)

hydro_season = 1 + 0.8 * np.sin(2 * np.pi * (day_of_year - 200) / 365)
generation_hydro_kwh = (100 * hydro_season * np.random.uniform(0.95, 1.05, n)).round(2)

total_generated_kwh = (generation_solar_kwh + generation_wind_kwh + generation_hydro_kwh).round(2)

# Sources
deficit = energy_required_kwh - total_generated_kwh
source_coal_kwh = np.maximum(deficit, 0).round(2)
scale_factor = np.where(deficit < 0, energy_required_kwh / total_generated_kwh, 1)

source_solar_kwh = (generation_solar_kwh * scale_factor).round(2)
source_wind_kwh = (generation_wind_kwh * scale_factor).round(2)
source_hydro_kwh = (generation_hydro_kwh * scale_factor).round(2)

# Rates
def get_rate(low, high, peak_adder):
    base = np.random.uniform(low, high, n)
    return np.where(is_peak, base + peak_adder, base)

rate_solar_inr = get_rate(2.0, 2.5, 0.4).round(2)
rate_wind_inr = get_rate(3.0, 3.3, 0.3).round(2)
rate_hydro_inr = get_rate(4.5, 5.5, 0.5).round(2)
rate_coal_inr = get_rate(4.6, 5.5, 0.5).round(2)

total_cost_inr = (
    (source_solar_kwh * rate_solar_inr) +
    (source_wind_kwh * rate_wind_inr) +
    (source_hydro_kwh * rate_hydro_inr) +
    (source_coal_kwh * rate_coal_inr)
).round(2)

average_unit_price_inr = np.zeros(n)
mask = energy_required_kwh > 0
average_unit_price_inr[mask] = (total_cost_inr[mask] / energy_required_kwh[mask]).round(2)

providers_list = ['Adani Power', 'Tata Power', 'Torrent Power', 'CESC', 'State DISCOM']
grid_provider = np.where(source_coal_kwh > 0, np.random.choice(providers_list, n), 'Self')

# Assemble DataFrame
df = pd.DataFrame({
    'timestamp': timestamps,
    'energy_required_kwh': energy_required_kwh,
    'generation_solar_kwh': generation_solar_kwh,
    'generation_wind_kwh': generation_wind_kwh,
    'generation_hydro_kwh': generation_hydro_kwh,
    'total_generated_kwh': total_generated_kwh,
    'source_solar_kwh': source_solar_kwh,
    'source_wind_kwh': source_wind_kwh,
    'source_hydro_kwh': source_hydro_kwh,
    'source_coal_kwh': source_coal_kwh,
    'rate_solar_inr': rate_solar_inr,
    'rate_wind_inr': rate_wind_inr,
    'rate_hydro_inr': rate_hydro_inr,
    'rate_coal_inr': rate_coal_inr,
    'total_cost_inr': total_cost_inr,
    'average_unit_price_inr': average_unit_price_inr,
    'grid_provider': grid_provider
})

# ==========================================
# 2. INJECT ANOMALIES (The "Messy" Part)
# ==========================================

# A. Subtraction Mistakes (5% of data)
# Logic: We randomly change 'source_coal_kwh' WITHOUT updating 'total_generated' or 'energy_required'.
# This breaks the equation: Required = Solar + Wind + Hydro + Coal
idx_math_error = np.random.choice(df.index, size=int(n * 0.05), replace=False)
df.loc[idx_math_error, 'source_coal_kwh'] = np.random.uniform(0, 1000, size=len(idx_math_error)).round(2)

# B. Negative Energy "Leak" (1% of data)
# Physics violation: Negative coal consumption or negative demand
idx_neg = np.random.choice(df.index, size=int(n * 0.01), replace=False)
df.loc[idx_neg, 'source_coal_kwh'] = np.random.uniform(-50, -5, size=len(idx_neg)).round(2)
df.loc[idx_neg[:10], 'energy_required_kwh'] = -100.00 # Severe error

# C. Solar at Night (Sensor Glitch)
# Find night hours (0-4 AM) and inject solar generation
night_mask = (df['timestamp'].dt.hour < 5)
idx_night_solar = df[night_mask].sample(frac=0.1).index # 10% of night hours
df.loc[idx_night_solar, 'generation_solar_kwh'] = np.random.uniform(50, 150, size=len(idx_night_solar)).round(2)
# Ensure we update source_solar too so it looks "valid" but wrong contextually
df.loc[idx_night_solar, 'source_solar_kwh'] = df.loc[idx_night_solar, 'generation_solar_kwh']

# D. Cost Calculation Errors (Price Gouging/Undercharging)
# 3% of data: Cost is double what it should be, or zero
idx_cost_err = np.random.choice(df.index, size=int(n * 0.03), replace=False)
df.loc[idx_cost_err, 'total_cost_inr'] = df.loc[idx_cost_err, 'total_cost_inr'] * np.random.choice([0.1, 2.0, 10.0], size=len(idx_cost_err))

# E. Massive Outliers (Spikes)
# 0.5% of data: Demand spikes to 5000+
idx_spike = np.random.choice(df.index, size=int(n * 0.005), replace=False)
df.loc[idx_spike, 'energy_required_kwh'] = np.random.uniform(5000, 9000, size=len(idx_spike)).round(2)

# F. Missing Data (NaNs)
# 2% of Grid Provider is NaN
idx_nan = np.random.choice(df.index, size=int(n * 0.02), replace=False)
df.loc[idx_nan, 'grid_provider'] = np.nan
# 1% of Coal Rate is NaN
idx_nan_rate = np.random.choice(df.index, size=int(n * 0.01), replace=False)
df.loc[idx_nan_rate, 'rate_coal_inr'] = np.nan

# Save Corrupted Data
csv_name = 'industrial_energy_anomalies_2025.csv'
df.to_csv(csv_name, index=False)

print(f"Corrupted File generated: {csv_name}")
print("Sample of Anomalies (Negative Coal):")
print(df[df['source_coal_kwh'] < 0][['timestamp', 'source_coal_kwh', 'grid_provider']].head())
