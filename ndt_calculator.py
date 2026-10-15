# -*- coding: utf-8 -*-
"""Point-source estimates; not radiation-safety authorization."""
import math

# Inherited data; NOT independently validated for shielding design.
# gamma: R*m²/(Ci*h)
# HVL: mm
# half_life: days
ISOTOPES = {
    'Ir-192': dict(
        name='ایریدیوم ۱۹۲',
        half_life=73.83,
        gamma=0.48,
        hvl_pb=4.8,
        hvl_fe=12.5,
        energy='0.38 MeV',
    ),
    'Se-75': dict(
        name='سلنیوم ۷۵',
        half_life=119.78,
        gamma=0.20,
        hvl_pb=2.0,
        hvl_fe=8.0,
        energy='0.32 MeV',
    ),
    'Co-60': dict(
        name='کبالت ۶۰',
        half_life=1925.0,
        gamma=1.32,
        hvl_pb=12.5,
        hvl_fe=21.0,
        energy='1.25 MeV',
    ),
    'Cs-137': dict(
        name='سزیوم ۱۳۷',
        half_life=11000.0,
        gamma=0.33,
        hvl_pb=6.5,
        hvl_fe=16.0,
        energy='0.66 MeV',
    ),
}

DIGITS = str.maketrans(
    '۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩٫',
    '01234567890123456789.',
)
LN2 = math.log(2.0)


def number(text, title='ورودی', positive=False):
    if isinstance(text, bool):
        raise ValueError(f'{title}: عدد معتبر وارد کنید')

    try:
        value = float(str(text).strip().translate(DIGITS))
    except (ValueError, TypeError, OverflowError):
        raise ValueError(
            f'{title}: عدد معتبر و بدون جداکننده هزارگان وارد کنید'
        ) from None

    if not math.isfinite(value):
        raise ValueError(f'{title}: عدد باید متناهی باشد')

    if value < 0 or (positive and value == 0):
        rule = 'بزرگ‌تر از صفر' if positive else 'صفر یا مثبت'
        raise ValueError(f'{title}: مقدار باید {rule} باشد')

    return value


def isotope(source):
    try:
        return ISOTOPES[source]
    except (KeyError, TypeError):
        raise ValueError('ایزوتوپ انتخاب‌شده معتبر نیست') from None


def _exp(log_value):
    """Reject overflow and positive results rounded to zero."""
    try:
        value = math.exp(log_value)
    except OverflowError:
        value = math.inf

    if not math.isfinite(value) or value <= 0:
        raise ValueError(
            'نتیجه خارج از محدوده عددی است؛ صفر قابل گزارش نیست'
        )

    return value


def measured_distance(measured_rate, reference_distance, target_rate):
    """
    Inverse-square extrapolation.

    Requires unchanged beam, direction, shielding and suitable geometry.
    Rates must have the same units; distances use the same length unit.
    """
    rate = number(measured_rate, 'نرخ دوز مرجع', True)
    distance = number(reference_distance, 'فاصله مرجع', True)
    target = number(target_rate, 'نرخ دوز هدف', True)

    return _exp(
        math.log(distance)
        + 0.5 * (math.log(rate) - math.log(target))
    )


def xray_distance(measured_rate, reference_distance, target_rate):
    return measured_distance(
        measured_rate,
        reference_distance,
        target_rate,
    )


def boundary_estimate(source, activity, dose_limit, lead_mm):
    """
    Legacy educational gamma model.

    The R -> microSv conversion is approximate.
    No buildup, scatter, leakage or real beam geometry is modelled.
    NOT suitable for approving a radiation boundary or shielding.
    """
    data = isotope(source)

    activity = number(activity, 'اکتیویته')
    target = number(dose_limit, 'نرخ دوز هدف', True)
    lead = number(lead_mm, 'ضخامت سرب')

    hvl = number(data['hvl_pb'], 'HVL سرب', True)
    gamma = number(data['gamma'], 'ثابت گاما', True)

    log_t = -LN2 * (lead / hvl)
    transmission = _exp(log_t)

    if activity == 0:
        return 0.0, transmission

    log_dose = (
        math.log(gamma)
        + math.log(activity)
        + math.log(10000.0)
        + log_t
    )

    distance = _exp(
        0.5 * (log_dose - math.log(target))
    )

    return distance, transmission


def decay(source, initial, days):
    data = isotope(source)

    initial = number(initial, 'اکتیویته اولیه')
    days = number(days, 'روزهای سپری‌شده')
    half_life = number(data['half_life'], 'نیمه‌عمر', True)

    exponent = -LN2 * (days / half_life)

    if initial:
        remaining = _exp(math.log(initial) + exponent)
    else:
        remaining = 0.0

    # expm1 preserves precision for very small decay fractions.
    percent = -100.0 * math.expm1(exponent)

    return remaining, percent


def exposure_seconds(
    reference_seconds,
    reference_activity,
    reference_sfd,
    current_activity,
    current_sfd,
):
    """
    Scale a validated exposure.

    Isotope, material, thickness, film and processing must be unchanged.
    Both SFD inputs must use the same unit.
    """
    t = number(reference_seconds, 'زمان مرجع', True)
    ar = number(reference_activity, 'اکتیویته مرجع', True)
    dr = number(reference_sfd, 'SFD مرجع', True)

    a = number(current_activity, 'اکتیویته فعلی', True)
    d = number(current_sfd, 'SFD جدید', True)

    return _exp(
        math.log(t)
        + math.log(ar)
        - math.log(a)
        + 2.0 * (math.log(d) - math.log(dr))
    )
