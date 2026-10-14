# -*- coding: utf-8 -*-
"""Validated calculation core for the NDT gamma radiography estimator.

All reference isotope values are illustrative; verify them against source and
radiation-protection documentation before operational use.
"""
from __future__ import annotations
import math
from datetime import date
from typing import Dict, Optional

# Gamma constants: R·m²/(h·Ci); HVLs in mm; half-life in days.
ISOTOPES: Dict[str, Dict[str, object]] = {
    "Ir-192": {"half_life": 73.83, "gamma": 0.48, "hvl_pb": 4.8, "hvl_steel": 12.5, "energy": "حدود 0.20 تا 0.61 MeV"},
    "Se-75":  {"half_life": 119.8, "gamma": 0.20, "hvl_pb": 2.0, "hvl_steel": 8.0, "energy": "約 0.ள?"},
    "Co-60":  {"half_life": 1925.0, "gamma": 1.32, "hvl_pb": 12.5, "hvl_steel": 21.0, "energy": "1.17 و 1.33 MeV"},
    "Cs-137": {"half_life": 10986.0, "gamma": 0.33, "hvl_pb": 6.5, "hvl_steel": 16.0, "energy": "0.662 MeV"},
}
# Replace textual energy entry with standard approximate line range.
ISOTOPES["Se-75"]["energy"] = "حدود 0.07–0.40 MeV"
DOSE_LIMITS = {"مرز عمومی (نمونه)": 2.5, "مرز کنترل (نمونه)": 7.5, "منطقه هشدار (نمونه)": 25.0}


def _positive(value: float, name: str, allow_zero: bool = False) -> float:
    try:
        x = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name}: مقدار عددی معتبر وارد کنید.") from exc
    if not math.isfinite(x) or (x < 0 if allow_zero else x <= 0):
        op = "صفر یا بیشتر" if allow_zero else "بزرگ‌تر از صفر"
        raise ValueError(f"{name} باید {op} باشد.")
    return x


def _isotope(name: str) -> Dict[str, object]:
    try:
        return ISOTOPES[name]
    except KeyError as exc:
        raise ValueError("ایزوتوپ انتخاب‌شده در جدول موجود نیست.") from exc


def attenuation(thickness_mm: float, hvl_mm: float) -> float:
    """Transmission fraction through a material, using its supplied HVL."""
    thickness = _positive(thickness_mm, "ضخامت", allow_zero=True)
    hvl = _positive(hvl_mm, "HVL")
    return 0.5 ** (thickness / hvl)


def safe_distance(isotope: str, activity_ci: float, dose_usv_h: float,
                  thickness_mm: float = 0.0, material: str = "lead") -> float:
    """Boundary distance in metres using the requested inverse-square model.

    d = sqrt(Gamma * Activity * 10000 * transmission / Dose_uSv_h)
    Gamma uses R·m²/(h·Ci), and 10000 converts R/h to µSv/h approximately.
    """
    data = _isotope(isotope)
    activity = _positive(activity_ci, "اکتیویته")
    dose = _positive(dose_usv_h, "حد دز")
    key = "hvl_pb" if material.lower() in ("lead", "pb", "سرب") else "hvl_steel"
    trans = attenuation(thickness_mm, float(data[key]))
    return math.sqrt(float(data["gamma"]) * activity * 10000.0 * trans / dose)


def dose_rate_at(isotope: str, activity_ci: float, distance_m: float,
                 thickness_mm: float = 0.0, material: str = "lead") -> float:
    data = _isotope(isotope)
    activity = _positive(activity_ci, "اکتیویته")
    distance = _positive(distance_m, "فاصله")
    key = "hvl_pb" if material.lower() in ("lead", "pb", "سرب") else "hvl_steel"
    return float(data["gamma"]) * activity * 10000.0 * attenuation(thickness_mm, float(data[key])) / distance**2


def activity_after(isotope: str, initial_ci: float, days: float) -> float:
    data = _isotope(isotope)
    initial = _positive(initial_ci, "اکتیویته اولیه", allow_zero=True)
    elapsed = _positive(days, "روز سپری‌شده", allow_zero=True)
    return initial * 0.5 ** (elapsed / float(data["half_life"]))


def activity_daily(isotope: str, initial_ci: float, calibration_date: date,
                   today: Optional[date] = None) -> dict:
    if not isinstance(calibration_date, date):
        raise ValueError("تاریخ مبنا نامعتبر است.")
    current = today or date.today()
    elapsed = (current - calibration_date).days
    if elapsed < 0:
        raise ValueError("تاریخ مبنا نمی‌تواند در آینده باشد.")
    values = [(current.fromordinal(current.toordinal() + i),
               activity_after(isotope, initial_ci, elapsed + i)) for i in range(7)]
    return {"days_elapsed": elapsed, "activity_now": values[0][1], "daily": values}


def exposure_time(isotope: str, steel_mm: float, film_factor: float,
                  sfd_cm: float, activity_ci: float) -> dict:
    """Chart-calibrated estimate in minutes.

    t = Film_Factor * 2**(steel thickness / steel HVL) * (SFD/100)**2 / Activity
    Film_Factor must come from the user's validated exposure chart/system and
    is entered in Ci·min at 1 m and zero reference thickness. This is not a
    universal exposure constant and this estimate must not replace approved charts.
    """
    data = _isotope(isotope)
    thickness = _positive(steel_mm, "ضخامت فولاد", allow_zero=True)
    factor = _positive(film_factor, "ضریب فیلم/جدول")
    sfd = _positive(sfd_cm, "فاصله منبع تا فیلم")
    activity = _positive(activity_ci, "اکتیویته")
    hvl = float(data["hvl_steel"])
    relative_exposure = factor * 2.0 ** (thickness / hvl) * (sfd / 100.0) ** 2
    minutes = relative_exposure / activity
    return {"exposure_cimin": relative_exposure, "time_min": minutes, "time_sec": minutes * 60.0}


def isotope_specs() -> list:
    """Rows suitable for a reference table."""
    return [(name, values["half_life"], values["gamma"], values["hvl_pb"],
             values["hvl_steel"], values["energy"]) for name, values in ISOTOPES.items()]
