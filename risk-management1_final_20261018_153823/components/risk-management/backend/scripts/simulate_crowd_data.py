import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITES_CSV_PATH = os.path.join(PROJECT_ROOT, "data", "tourist_sites.csv")

def load_sites(csv_path=SITES_CSV_PATH):
    sites_df = pd.read_csv(csv_path)
    required_cols = {"site_id", "site_name", "annual_visitors_2024", "capacity_per_day", "category"}
    missing = required_cols - set(sites_df.columns)
    if missing:
        raise ValueError(f"tourist_sites.csv is missing required columns: {missing}")
    sites = []
    for _, row in sites_df.iterrows():
        sites.append({
            "site_id": int(row["site_id"]),
            "site_name": row["site_name"],
            "annual_visitors": row["annual_visitors_2024"],
            "capacity_per_day": row["capacity_per_day"],
            "category": row["category"],
        })
    return sites

SITES = load_sites()

HIGH_IMPACT_DATES = [
    # 2024 (25 gazetted public holidays)
    "2024-01-15", "2024-01-25", "2024-02-04", "2024-02-24",
    "2024-03-08", "2024-03-24", "2024-03-29", "2024-04-10",
    "2024-04-12", "2024-04-13", "2024-04-23", "2024-05-01",
    "2024-05-23", "2024-05-24", "2024-06-17", "2024-06-21",
    "2024-07-20", "2024-08-19", "2024-09-16", "2024-09-17",
    "2024-10-16", "2024-11-01", "2024-11-15", "2024-12-14",
    "2024-12-25",
    # 2025 (24 confirmed of 25 gazetted holidays -- see note)
    "2025-01-13", "2025-01-14", "2025-02-04", "2025-02-12",
    "2025-02-26", "2025-03-13", "2025-03-31", "2025-04-13",
    "2025-04-14", "2025-04-15", "2025-04-18", "2025-05-01",
    "2025-05-12", "2025-05-13", "2025-06-07", "2025-06-10",
    "2025-07-10", "2025-08-08", "2025-09-05", "2025-09-07",
    "2025-10-06", "2025-10-20", "2025-11-05", "2025-12-04",
    "2025-12-25",
    # 2026 (25 gazetted holidays, matches app.py NATIONAL_HOLIDAY_DATES)
    "2026-01-03", "2026-01-15", "2026-02-01", "2026-02-04",
    "2026-02-15", "2026-03-02", "2026-03-21", "2026-04-01",
    "2026-04-03", "2026-04-13", "2026-04-14", "2026-05-01",
    "2026-05-28", "2026-05-30", "2026-05-31", "2026-06-29",
    "2026-07-29", "2026-08-26", "2026-08-27", "2026-09-26",
    "2026-10-25", "2026-11-08", "2026-11-24", "2026-12-23",
    "2026-12-25",
]

def get_season(month):
    if month in [12, 1, 2, 3]:
        return ("peak", 1.6)
    elif month in [4, 5, 6]:
        return ("shoulder", 1.0)
    elif month in [7, 8, 9]:
        return ("low", 0.8)
    else:
        return ("shoulder", 1.1)

def get_monthly_weather(month):
    weather = {
        1:  (27, 45),  2:  (28, 30),  3:  (29, 55),
        4:  (29, 120), 5:  (28, 180), 6:  (27, 160),
        7:  (27, 130), 8:  (27, 110), 9:  (27, 130),
        10: (27, 200), 11: (27, 300), 12: (27, 150)
    }
    return weather.get(month, (27, 100))

def generate_crowd_data():
    print(f"Generating simulated crowd data for {len(SITES)} sites...")
    records = []
    np.random.seed(42)

    start_date = datetime(2024, 1, 1)
    end_date = datetime(2025, 12, 31)
    current_date = start_date

    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        day_of_week = current_date.weekday()
        is_weekend = 1 if day_of_week >= 5 else 0
        is_holiday = 1 if date_str in HIGH_IMPACT_DATES else 0
        month = current_date.month
        season, season_mult = get_season(month)
        temp, rainfall = get_monthly_weather(month)

        daily_flights = int(np.random.normal(65 * season_mult, 8))
        daily_flights = max(20, min(100, daily_flights))

        # Hotel occupancy rate — regional demand indicator
        hotel_occupancy = round(min(max(
            0.30 + (season_mult - 0.8) * 0.35 +
            (0.15 if is_weekend else 0) +
            (0.25 if is_holiday else 0) +
            float(np.random.normal(0, 0.05)),
            0.10
        ), 1.0), 3)

        for site in SITES:
            base_daily = site["annual_visitors"] / 365
            weekend_mult = 1.4 if is_weekend else 1.0
            holiday_mult = 1.8 if is_holiday else 1.0
            noise = np.random.normal(1.0, 0.15)

            estimated_visitors = int(
                base_daily * season_mult * weekend_mult * holiday_mult * noise
            )
            estimated_visitors = max(0, min(estimated_visitors, site["capacity_per_day"]))

            crowd_score = round(estimated_visitors / site["capacity_per_day"], 3)
            crowd_score = min(crowd_score, 1.0)

            if crowd_score >= 0.75:
                risk_level = "High"
            elif crowd_score >= 0.45:
                risk_level = "Medium"
            else:
                risk_level = "Low"

            records.append({
                "date": date_str,
                "site_id": site["site_id"],
                "site_name": site["site_name"],
                "category": site["category"],
                "day_of_week": day_of_week,
                "month": month,
                "season": season,
                "is_weekend": is_weekend,
                "is_public_holiday": is_holiday,
                "avg_temperature_c": temp,
                "avg_rainfall_mm": rainfall,
                "daily_flights_at_cmb": daily_flights,
                "hotel_occupancy_rate": hotel_occupancy,
                "capacity_per_day": site["capacity_per_day"],
                "estimated_daily_visitors": estimated_visitors,
                "crowd_score_normalized": crowd_score,
                "risk_level": risk_level,
            })

        current_date += timedelta(days=1)

    df = pd.DataFrame(records)
    os.makedirs(os.path.join(PROJECT_ROOT, "data"), exist_ok=True)
    df.to_csv(os.path.join(PROJECT_ROOT, "data", "simulated_crowd_data.csv"), index=False)

    print(f"\nDone! Generated {len(df)} records")
    print(f"Sites covered: {df['site_id'].nunique()}")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"Columns: {list(df.columns)}")
    print(f"hotel_occupancy_rate included: {'hotel_occupancy_rate' in df.columns}")
    print(f"\nRisk level distribution:")
    print(df['risk_level'].value_counts())

if __name__ == "__main__":
    generate_crowd_data()