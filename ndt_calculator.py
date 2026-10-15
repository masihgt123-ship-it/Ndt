# -*- coding: utf-8 -*-
"""Numerical helpers. Results are estimates, not radiation-safety authorization."""
import math

# Copied from the supplied program; these data have NOT been independently verified.
ISOTOPES = {
    'Ir-192': {
        'gamma': 0.48,
        'hvl_pb': 4.8,
        'hvl_fe': 12.5,
        'half_life': 73.83,
        'name': 'ایریدیوم ۱۹۲',
        'energy': '0.38 MeV',
    },
    'Se-75': {
        'gamma': 0.20,
        'hvl_pb': 2.0,
        'hvl_fe': 8.0,
        'half_life': 119.78,
        'name': 'سلنیوم ۷۵',
        'energy': '0.32 MeV',
    },
    'Co-60': {
        'gamma': 1.32,
        'hvl_pb': 12.5,
        'hvl_fe': 21.0,
        'half_life': 1925.0,
        'name': 'کبالت ۶۰',
        'energy': '1.25 MeV',
    },
    'Cs-137': {
        'gamma': 0.33,
        'hvl_pb': 6.5,
        'hvl_fe': 16.0,
        'half_life': 11000.0,
        'name': 'سزیوم ۱۳۷',
        'energy': '0.66 MeV',
    },
}

_DIGITS = str.maketrans(
    '۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩٫',
    '01234567890123456789.',
)


def number(text, title, positive=False):
    try:
        value = float(str(text).strip().translate(_DIGITS))
    except (ValueError, TypeError):
        raise ValueError(f'{title}: عدد معتبر وارد کنید') from None

    if not math.isfinite(value):
        raise ValueError(f'{title}: مقدار باید متناهی باشد')

    if value < 0 or (positive and value == 0):
        requirement = 'بزرگ‌تر از صفر' if positive else 'صفر یا مثبت'
        raise ValueError(f'{title}: مقدار باید {requirement} باشد')

    return value


def checked_result(value):
    if not math.isfinite(value) or value < 0:
        raise ValueError('نتیجه خارج از محدوده محاسبه است')
    return value


def boundary_estimate(source, activity, dose_limit, lead_mm):
    iso = ISOTOPES[source]
    transmission = 2.0 ** (-lead_mm / iso['hvl_pb'])

    if activity > 0 and transmission == 0:
        raise ValueError(
            'تضعیف خارج از دقت عددی است؛ نتیجه قابل نمایش نیست'
        )

    # Approximate conversion inherited from the supplied code.
    dose_1m = checked_result(
        iso['gamma'] * activity * 10000.0 * transmission
    )
    distance = checked_result(math.sqrt(dose_1m / dose_limit))

    if activity > 0 and distance == 0:
        raise ValueError('نتیجه خارج از دقت عددی است')

    return distance, transmission


def decay(source, initial, days):
    fraction = 2.0 ** (-days / ISOTOPES[source]['half_life'])
    return (
        checked_result(initial * fraction),
        100.0 * (1.0 - fraction),
    )


def xray_distance(measured_rate, reference_distance, target_rate):
    """Inverse-square extrapolation for unchanged beam conditions."""
    return checked_result(
        reference_distance * math.sqrt(measured_rate / target_rate)
    )


def exposure_seconds(
    reference_seconds,
    reference_activity,
    reference_sfd,
    current_activity,
    current_sfd,
):
    """Same isotope, material, thickness, film and processing conditions."""
    result = checked_result(
        reference_seconds
        * (reference_activity / current_activity)
        * (current_sfd / reference_sfd) ** 2
    )

    if result == 0:
        raise ValueError('زمان خارج از دقت عددی است')

    return result
