# -*- coding: utf-8 -*-
"""
NDT Industrial Radiography Core Calculator
Supports Gamma Isotopes (Ir-192, Se-75, Co-60, Cs-137) and Industrial X-Ray Units
"""
import math

ISOTOPE_DATA = {
    'Ir-192': {
        'name_fa': 'ایریدیوم ۱۹۲',
        'gamma_const': 0.48,      # R·h^-1·Ci^-1 at 1 m
        'half_life_days': 73.83,
        'hvl_lead_mm': 4.8,       # Lead HVL in mm
        'hvl_steel_mm': 12.5,     # Steel HVL in mm
        'base_factor': 1.0
    },
    'Se-75': {
        'name_fa': 'سلنیوم ۷۵',
        'gamma_const': 0.20,
        'half_life_days': 119.8,
        'hvl_lead_mm': 2.0,
        'hvl_steel_mm': 8.0,
        'base_factor': 0.85
    },
    'Co-60': {
        'name_fa': 'کبالت ۶۰',
        'gamma_const': 1.32,
        'half_life_days': 1925.2,
        'hvl_lead_mm': 12.5,
        'hvl_steel_mm': 21.0,
        'base_factor': 2.1
    },
    'Cs-137': {
        'name_fa': 'سزیم ۱۳۷',
        'gamma_const': 0.33,
        'half_life_days': 11000.0,
        'hvl_lead_mm': 6.5,
        'hvl_steel_mm': 16.0,
        'base_factor': 1.2
    }
}

def get_xray_hvl_lead(kv):
    """Half Value Layer (mm Pb) for X-Ray based on Tube Voltage"""
    if kv <= 100:
        return 0.25
    elif kv <= 150:
        return 0.35
    elif kv <= 200:
        return 0.55
    elif kv <= 250:
        return 0.90
    else:
        return 1.40

def calculate_gamma_safe_distance(isotope_key, curie, lead_shield_mm=0.0, limit_dose=7.5):
    """
    Calculate safe distance in meters for Gamma Isotopes
    Formula: D = sqrt((Gamma * A * 10000 * 2^(-t/HVL)) / Dose_limit)
    """
    if isotope_key not in ISOTOPE_DATA:
        return 0.0
    
    data = ISOTOPE_DATA[isotope_key]
    gamma = data['gamma_const']
    hvl = data['hvl_lead_mm']
    
    # Transmission factor through lead collimator/shield
    transmission = math.pow(2.0, -(max(0.0, lead_shield_mm) / hvl)) if hvl > 0 else 1.0
    dose_rate_1m = gamma * max(0.0, curie) * 10000.0 * transmission  # micro-Sv/h at 1 meter
    
    safe_dist = math.sqrt(max(0.0001, dose_rate_1m) / max(0.01, limit_dose))
    return round(safe_dist, 2)

def calculate_xray_safe_distance(kv, ma, lead_shield_mm=0.0, limit_dose=7.5):
    """
    Calculate safe distance in meters for Directional Industrial X-Ray Unit.
    Unshielded output approx: Output(R/min at 1m) ~ (kV / 100)^2.5 * 0.15 * mA
    Converted to micro-Sv/h: 1 R/h ~ 10,000 micro-Sv/h
    """
    safe_kv = max(50.0, kv)
    safe_ma = max(0.5, ma)
    
    # Empirical output dose rate at 1 meter in micro-Sv/h (unshielded beam direction)
    output_rate_1m = math.pow(safe_kv / 100.0, 2.4) * 0.14 * safe_ma * 60.0 * 10000.0
    
    hvl_lead = get_xray_hvl_lead(safe_kv)
    transmission = math.pow(2.0, -(max(0.0, lead_shield_mm) / hvl_lead)) if hvl_lead > 0 else 1.0
    
    effective_dose_rate = output_rate_1m * transmission
    safe_dist = math.sqrt(max(0.0001, effective_dose_rate) / max(0.01, limit_dose))
    return round(safe_dist, 2)

def calculate_exposure_time(mode, activity_or_ma, kv=200, thickness_mm=10.0, sfd_cm=70.0, film_factor=1.0):
    """
    Calculates exposure time in seconds
    """
    sfd_cm = max(10.0, sfd_cm)
    dist_factor = math.pow(sfd_cm / 50.0, 2.0)
    
    if mode == 'X-Ray':
        ma = max(0.5, activity_or_ma)
        # Steel absorption equivalent for X-Ray
        hvl_steel = 4.0 + (kv / 50.0)
        thick_factor = math.pow(2.0, max(0.0, thickness_mm) / hvl_steel)
        # Base X-ray exposure constant
        base_seconds = (45.0 * thick_factor * dist_factor * film_factor) / (ma * (kv / 150.0))
        return round(max(1.0, base_seconds), 1)
    else:
        curie = max(0.1, activity_or_ma)
        iso_data = ISOTOPE_DATA.get(mode, ISOTOPE_DATA['Ir-192'])
        hvl_steel = iso_data['hvl_steel_mm']
        thick_factor = math.pow(2.0, max(0.0, thickness_mm) / hvl_steel)
        base_seconds = (iso_data['base_factor'] * film_factor * thick_factor * dist_factor * 120.0) / (curie / 10.0)
        return round(max(1.0, base_seconds), 1)
