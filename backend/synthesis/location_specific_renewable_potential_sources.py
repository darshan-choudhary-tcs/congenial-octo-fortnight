"""
Synthetic Data Generator for Location-Specific Renewable Energy Potential
Generates time series data at 15-minute intervals for various Indian locations
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import json

# Indian cities with their approximate coordinates and terrain types
INDIAN_CITIES = [
    {"city": "Mumbai", "state": "Maharashtra", "lat": 19.0760, "lon": 72.8777, "terrain": "Coastal", "altitude": 14},
    {"city": "Delhi", "state": "Delhi", "lat": 28.7041, "lon": 77.1025, "terrain": "Plains", "altitude": 216},
    {"city": "Bangalore", "state": "Karnataka", "lat": 12.9716, "lon": 77.5946, "terrain": "Plains", "altitude": 920},
    {"city": "Chennai", "state": "Tamil Nadu", "lat": 13.0827, "lon": 80.2707, "terrain": "Coastal", "altitude": 7},
    {"city": "Shimla", "state": "Himachal Pradesh", "lat": 31.1048, "lon": 77.1734, "terrain": "Hills", "altitude": 2206},
    {"city": "Pune", "state": "Maharashtra", "lat": 18.5204, "lon": 73.8567, "terrain": "Plains", "altitude": 560},
    {"city": "Jaipur", "state": "Rajasthan", "lat": 26.9124, "lon": 75.7873, "terrain": "Plains", "altitude": 431},
    {"city": "Guwahati", "state": "Assam", "lat": 26.1445, "lon": 91.7362, "terrain": "Forest", "altitude": 50},
    {"city": "Kochi", "state": "Kerala", "lat": 9.9312, "lon": 76.2673, "terrain": "Coastal", "altitude": 0},
    {"city": "Manali", "state": "Himachal Pradesh", "lat": 32.2396, "lon": 77.1887, "terrain": "Hills", "altitude": 2050},
]

# Terrain factors for wind power calculation
TERRAIN_FACTORS = {
    "Coastal": 1.2,
    "Plains": 1.0,
    "Hills": 1.5,
    "Forest": 0.8
}

def generate_solar_irradiance(hour, minute, latitude, season_factor=1.0):
    """
    Generate realistic solar irradiance (W/m²)
    Peak values occur around noon, zero at night
    """
    time_decimal = hour + minute / 60.0

    # Solar irradiance follows a sine curve during daylight hours
    if 6 <= time_decimal <= 18:
        # Peak around noon (12:00)
        angle = (time_decimal - 6) / 12 * np.pi
        base_irradiance = np.sin(angle) * 1000 * season_factor
        # Add some randomness
        noise = np.random.normal(0, 50)
        irradiance = max(0, base_irradiance + noise)
    else:
        irradiance = 0

    # Adjust for latitude (higher latitudes get less solar energy)
    latitude_factor = 1 - abs(latitude - 20) / 100
    return round(irradiance * latitude_factor, 2)

def generate_wind_speed(hour, terrain, season_factor=1.0):
    """
    Generate wind speed in m/s
    Wind speeds vary by time of day and terrain
    """
    # Base wind speed varies by terrain
    base_speeds = {
        "Coastal": 8,
        "Plains": 5,
        "Hills": 12,
        "Forest": 3
    }

    base_speed = base_speeds.get(terrain, 5)

    # Wind typically picks up during afternoon
    time_factor = 1 + 0.3 * np.sin((hour - 6) / 12 * np.pi) if 6 <= hour <= 18 else 0.8

    wind_speed = base_speed * time_factor * season_factor
    noise = np.random.normal(0, 1.5)

    return max(0.5, round(wind_speed + noise, 2))

def generate_temperature(hour, minute, altitude, latitude, season='summer'):
    """
    Generate temperature in Celsius
    Temperature varies by time of day, altitude, and season
    """
    time_decimal = hour + minute / 60.0

    # Base temperature by season
    season_base = {
        'summer': 35,
        'monsoon': 28,
        'winter': 20,
        'spring': 27
    }

    base_temp = season_base.get(season, 27)

    # Daily temperature variation (cooler at night, warmer at 2-3 PM)
    if time_decimal < 6:
        daily_variation = -8
    elif time_decimal < 14:
        daily_variation = (time_decimal - 6) / 8 * 10 - 5
    elif time_decimal < 18:
        daily_variation = 5 - (time_decimal - 14) / 4 * 8
    else:
        daily_variation = -3 - (time_decimal - 18) / 6 * 5

    # Altitude effect (temperature decreases with altitude)
    altitude_effect = -altitude / 150

    # Latitude effect
    latitude_effect = (25 - latitude) * 0.3

    temperature = base_temp + daily_variation + altitude_effect + latitude_effect
    noise = np.random.normal(0, 1.5)

    return round(temperature + noise, 2)

def generate_pressure(altitude, temperature):
    """
    Generate atmospheric pressure in hPa (hectopascals)
    Pressure decreases with altitude and varies slightly with temperature
    """
    # Standard sea level pressure
    sea_level_pressure = 1013.25

    # Barometric formula (simplified)
    pressure = sea_level_pressure * np.exp(-altitude / 8500)

    # Small temperature adjustment
    temp_adjustment = (15 - temperature) * 0.1

    noise = np.random.normal(0, 2)

    return round(pressure + temp_adjustment + noise, 2)

def generate_wind_direction():
    """
    Generate wind direction in degrees (0-360)
    """
    # Common wind directions with some randomness
    base_directions = [0, 45, 90, 135, 180, 225, 270, 315]
    base = random.choice(base_directions)
    variation = np.random.normal(0, 15)

    direction = (base + variation) % 360
    return round(direction, 1)

def calculate_wind_power(wind_speed, altitude, temperature, pressure, terrain, wind_direction):
    """
    Calculate total wind power available in kW/m²
    Based on wind turbine power equation: P = 0.5 * ρ * A * v³ * Cp
    Where ρ is air density, A is swept area (assumed 1 m²), v is wind speed, Cp is efficiency
    """
    # Calculate air density (kg/m³) using ideal gas law
    # ρ = P / (R * T) where P is pressure (Pa), R is specific gas constant (287 J/(kg·K)), T is temperature (K)
    pressure_pa = pressure * 100  # Convert hPa to Pa
    temperature_k = temperature + 273.15  # Convert Celsius to Kelvin
    air_density = pressure_pa / (287 * temperature_k)

    # Power coefficient (Betz limit is 0.593, practical turbines achieve ~0.4-0.45)
    cp = 0.42

    # Swept area (m²) - using 1 m² for unit calculation
    area = 1.0

    # Wind power in Watts per m²
    power_watts = 0.5 * air_density * area * (wind_speed ** 3) * cp

    # Apply terrain factor
    terrain_factor = TERRAIN_FACTORS.get(terrain, 1.0)
    power_watts *= terrain_factor

    # Convert to kW/m²
    power_kw = power_watts / 1000

    return round(power_kw, 4)

def generate_hydro_potential(terrain, altitude, season='summer'):
    """
    Generate hydro power potential in MW
    Based on terrain type, altitude, and seasonal water availability
    """
    if terrain == "Coastal":
        # Limited hydro potential in coastal areas
        base_potential = np.random.uniform(0.5, 2.0)
    elif terrain == "Hills":
        # High hydro potential in hilly areas
        base_potential = np.random.uniform(10.0, 50.0)
    elif terrain == "Forest":
        # Moderate hydro potential in forest areas
        base_potential = np.random.uniform(5.0, 20.0)
    else:  # Plains
        # Low to moderate hydro potential
        base_potential = np.random.uniform(1.0, 10.0)

    # Seasonal factor (higher during monsoon)
    season_factors = {
        'summer': 0.6,
        'monsoon': 1.5,
        'winter': 0.8,
        'spring': 0.9
    }

    seasonal_multiplier = season_factors.get(season, 1.0)

    # Altitude bonus (higher altitude = more potential energy)
    altitude_bonus = 1 + (altitude / 3000)

    hydro_potential = base_potential * seasonal_multiplier * altitude_bonus
    noise = np.random.normal(0, 0.5)

    return max(0, round(hydro_potential + noise, 2))

def get_season(date):
    """
    Determine season based on date for India
    """
    month = date.month
    if month in [3, 4, 5]:
        return 'summer'
    elif month in [6, 7, 8, 9]:
        return 'monsoon'
    elif month in [10, 11]:
        return 'autumn'
    else:
        return 'winter'

def generate_data_for_location(city_info, start_date, end_date):
    """
    Generate time series data for a specific location
    """
    data = []
    current_time = start_date

    city = city_info['city']
    state = city_info['state']
    lat = city_info['lat']
    lon = city_info['lon']
    terrain = city_info['terrain']
    altitude = city_info['altitude']

    while current_time <= end_date:
        season = get_season(current_time)
        hour = current_time.hour
        minute = current_time.minute

        # Generate all parameters
        solar_irradiance = generate_solar_irradiance(hour, minute, lat)
        wind_speed = generate_wind_speed(hour, terrain)
        temperature = generate_temperature(hour, minute, altitude, lat, season)
        pressure = generate_pressure(altitude, temperature)
        wind_direction = generate_wind_direction()

        # Calculate derived fields
        wind_power = calculate_wind_power(
            wind_speed, altitude, temperature, pressure, terrain, wind_direction
        )
        hydro_potential = generate_hydro_potential(terrain, altitude, season)

        record = {
            'timestamp': current_time.strftime('%Y-%m-%d %H:%M:%S'),
            'timestamp_unix': int(current_time.timestamp()),
            'city': city,
            'state': state,
            'latitude': lat,
            'longitude': lon,
            'terrain': terrain,
            'altitude_m': altitude,
            'solar_irradiance_w_m2': solar_irradiance,
            'wind_speed_m_s': wind_speed,
            'temperature_celsius': temperature,
            'pressure_hpa': pressure,
            'wind_direction_degrees': wind_direction,
            'wind_power_kw_m2': wind_power,
            'hydro_potential_mw': hydro_potential
        }

        data.append(record)
        current_time += timedelta(minutes=15)

    return data

def main():
    """
    Main function to generate synthetic data
    """
    # print("🌞 Renewable Energy Synthetic Data Generator 🌬️")
    # print("=" * 60)

    # Generate data for 7 days
    start_date = datetime(2024, 6, 1, 0, 0, 0)  # Starting June 1, 2024 (Monsoon season)
    end_date = datetime(2024, 6, 7, 23, 45, 0)   # 7 days of data

    all_data = []

    # Generate data for each city
    for city_info in INDIAN_CITIES:
        # print(f"\nGenerating data for {city_info['city']}, {city_info['state']}...")
        city_data = generate_data_for_location(city_info, start_date, end_date)
        all_data.extend(city_data)
        # print(f"  ✓ Generated {len(city_data)} records")

    # Create DataFrame
    df = pd.DataFrame(all_data)

    # print(f"\n{'=' * 60}")
    # print(f"Total records generated: {len(df)}")
    # print(f"\nData Summary:")
    # print(df.describe())

    # Save to CSV
    csv_filename = 'renewable_energy_data.csv'
    df.to_csv(csv_filename, index=False)
    # print(f"\n✓ Data saved to {csv_filename}")

    # Save to JSON
    json_filename = 'renewable_energy_data.json'
    df.to_json(json_filename, orient='records', indent=2)
    # print(f"✓ Data saved to {json_filename}")

    # Display sample records
    # print(f"\n{'=' * 60}")
    # print("Sample Records (first 5):")
    # print(df.head().to_string())

    # Display statistics by city
    # print(f"\n{'=' * 60}")
    # print("Average Values by City:")
    city_stats = df.groupby('city').agg({
        'solar_irradiance_w_m2': 'mean',
        'wind_speed_m_s': 'mean',
        'temperature_celsius': 'mean',
        'wind_power_kw_m2': 'mean',
        'hydro_potential_mw': 'mean'
    }).round(2)
    # print(city_stats)

    return df

if __name__ == "__main__":
    df = main()
