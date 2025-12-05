"""
Profile API endpoints for company profile and historical data
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from loguru import logger
from typing import Optional, Dict, Any, List
import pandas as pd
import os
from datetime import datetime

from app.database.db import get_db
from app.database.models import Profile, User
from app.auth.security import get_current_active_user
from app.auth.schemas import ProfileResponse
from pydantic import BaseModel

router = APIRouter()


class HistoricalDataPoint(BaseModel):
    """Single data point from historical data"""
    timestamp: str
    energy_required_kwh: float
    total_generated_kwh: float
    source_solar_kwh: float
    source_wind_kwh: float
    source_hydro_kwh: float
    source_coal_kwh: float
    total_cost_inr: float
    average_unit_price_inr: float


class HistoricalDataSummary(BaseModel):
    """Aggregated historical data for dashboard"""
    total_renewable_kwh: float
    total_non_renewable_kwh: float
    renewable_percentage: float
    non_renewable_percentage: float
    total_cost_inr: float
    average_unit_price_inr: float
    total_energy_required_kwh: float

    # Monthly aggregates
    monthly_data: List[Dict[str, Any]]

    # Energy source breakdown
    energy_mix: Dict[str, float]

    # Provider distribution
    provider_distribution: List[Dict[str, Any]]

    # Data range
    start_date: str
    end_date: str
    total_records: int


@router.get("/profile", response_model=ProfileResponse)
async def get_company_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get company profile with KPIs and sustainability targets.
    Returns profile from company-specific database.
    """
    try:
        # Query profile from company database
        # For admin, user_id will be 1 (first user in company DB)
        # For other users in the same company, they share the same profile
        profile = db.query(Profile).first()

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company profile not found. Please complete setup first."
            )

        logger.info(f"Retrieved profile for user: {current_user.username}")

        return ProfileResponse(
            id=profile.id,
            user_id=profile.user_id,
            industry=profile.industry,
            location=profile.location,
            sustainability_target_kp1=profile.sustainability_target_kp1,
            sustainability_target_kp2=profile.sustainability_target_kp2,
            budget=profile.budget,
            historical_data_path=profile.historical_data_path,
            created_at=profile.created_at,
            updated_at=profile.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve profile: {str(e)}"
        )


@router.get("/profile/historical-data", response_model=HistoricalDataSummary)
async def get_historical_data(
    aggregation: str = Query("monthly", regex="^(daily|monthly|all)$"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get parsed and aggregated historical energy data.

    Parameters:
    - aggregation: Level of aggregation (daily, monthly, all)

    Returns aggregated data including:
    - Total renewable vs non-renewable percentages
    - Monthly consumption trends
    - Cost analysis
    - Energy source breakdown
    - Provider distribution
    """
    try:
        # Get profile to find historical data path
        profile = db.query(Profile).first()

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company profile not found"
            )

        if not profile.historical_data_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No historical data uploaded"
            )

        if not os.path.exists(profile.historical_data_path):
            logger.error(f"Historical data file not found: {profile.historical_data_path}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Historical data file not found on server"
            )

        logger.info(f"Reading historical data from: {profile.historical_data_path}")

        # Read CSV file
        df = pd.read_csv(profile.historical_data_path)

        # Validate required columns
        required_columns = [
            'timestamp', 'energy_required_kwh', 'source_solar_kwh',
            'source_wind_kwh', 'source_hydro_kwh', 'source_coal_kwh',
            'total_cost_inr', 'average_unit_price_inr'
        ]

        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"CSV missing required columns: {', '.join(missing_columns)}"
            )

        # Parse timestamp
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')

        # Calculate renewable and non-renewable totals
        df['renewable_kwh'] = df['source_solar_kwh'] + df['source_wind_kwh'] + df['source_hydro_kwh']
        df['non_renewable_kwh'] = df['source_coal_kwh']

        # Calculate total renewable and non-renewable
        total_renewable = df['renewable_kwh'].sum()
        total_non_renewable = df['non_renewable_kwh'].sum()
        total_energy = total_renewable + total_non_renewable

        renewable_percentage = (total_renewable / total_energy * 100) if total_energy > 0 else 0
        non_renewable_percentage = (total_non_renewable / total_energy * 100) if total_energy > 0 else 0

        # Calculate totals
        total_cost = df['total_cost_inr'].sum()
        avg_unit_price = df['average_unit_price_inr'].mean()
        total_energy_required = df['energy_required_kwh'].sum()

        # Monthly aggregation
        df['month'] = df['timestamp'].dt.to_period('M')
        monthly_agg = df.groupby('month').agg({
            'energy_required_kwh': 'sum',
            'renewable_kwh': 'sum',
            'non_renewable_kwh': 'sum',
            'total_cost_inr': 'sum',
            'source_solar_kwh': 'sum',
            'source_wind_kwh': 'sum',
            'source_hydro_kwh': 'sum',
            'source_coal_kwh': 'sum'
        }).reset_index()

        monthly_agg['month_str'] = monthly_agg['month'].astype(str)
        monthly_agg['renewable_percentage'] = (monthly_agg['renewable_kwh'] /
                                               (monthly_agg['renewable_kwh'] + monthly_agg['non_renewable_kwh']) * 100)

        monthly_data = []
        for _, row in monthly_agg.iterrows():
            monthly_data.append({
                'month': row['month_str'],
                'energy_required_kwh': float(row['energy_required_kwh']),
                'renewable_kwh': float(row['renewable_kwh']),
                'non_renewable_kwh': float(row['non_renewable_kwh']),
                'total_cost_inr': float(row['total_cost_inr']),
                'renewable_percentage': float(row['renewable_percentage']),
                'source_solar_kwh': float(row['source_solar_kwh']),
                'source_wind_kwh': float(row['source_wind_kwh']),
                'source_hydro_kwh': float(row['source_hydro_kwh']),
                'source_coal_kwh': float(row['source_coal_kwh'])
            })

        # Energy mix breakdown
        energy_mix = {
            'Solar': float(df['source_solar_kwh'].sum()),
            'Wind': float(df['source_wind_kwh'].sum()),
            'Hydro': float(df['source_hydro_kwh'].sum()),
            'Coal': float(df['source_coal_kwh'].sum())
        }

        # Provider distribution (if column exists)
        provider_distribution = []
        if 'grid_provider' in df.columns:
            provider_agg = df.groupby('grid_provider').agg({
                'energy_required_kwh': 'sum'
            }).reset_index()

            for _, row in provider_agg.iterrows():
                provider_distribution.append({
                    'provider': row['grid_provider'],
                    'energy_kwh': float(row['energy_required_kwh'])
                })

        # Date range
        start_date = df['timestamp'].min().strftime('%Y-%m-%d')
        end_date = df['timestamp'].max().strftime('%Y-%m-%d')

        logger.info(f"Historical data parsed: {len(df)} records from {start_date} to {end_date}")

        return HistoricalDataSummary(
            total_renewable_kwh=float(total_renewable),
            total_non_renewable_kwh=float(total_non_renewable),
            renewable_percentage=float(renewable_percentage),
            non_renewable_percentage=float(non_renewable_percentage),
            total_cost_inr=float(total_cost),
            average_unit_price_inr=float(avg_unit_price),
            total_energy_required_kwh=float(total_energy_required),
            monthly_data=monthly_data,
            energy_mix=energy_mix,
            provider_distribution=provider_distribution,
            start_date=start_date,
            end_date=end_date,
            total_records=len(df)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error parsing historical data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse historical data: {str(e)}"
        )
