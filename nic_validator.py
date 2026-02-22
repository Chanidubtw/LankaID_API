import re
from datetime import datetime, timedelta
from typing import Optional, Tuple


def parse_nic(nic: str) -> Tuple[Optional[dict], Optional[str]]:
    """
    Parse a Sri Lankan NIC number and extract DOB and gender.
    Returns (result_dict, error_message)
    """
    nic = nic.strip().upper()

    old_pattern = re.compile(r'^(\d{9})(V|X)$')
    new_pattern = re.compile(r'^\d{12}$')

    if old_pattern.match(nic):
        nic_format = "old"
        year = 1900 + int(nic[:2])
        day_of_year = int(nic[2:5])
        serial = nic[5:9]
        check = nic[9]
    elif new_pattern.match(nic):
        nic_format = "new"
        year = int(nic[:4])
        day_of_year = int(nic[4:7])
        serial = nic[7:11]
        check = nic[11]
    else:
        return None, "Invalid NIC format. Expected 9 digits + V/X (old) or 12 digits (new)."

    # Determine gender
    if day_of_year > 500:
        gender = "Female"
        day_of_year -= 500
    else:
        gender = "Male"

    # Validate day of year range
    if day_of_year < 1 or day_of_year > 366:
        return None, "Invalid day-of-year encoded in NIC."

    # Convert day of year to actual date
    try:
        base = datetime(year, 1, 1)
        dob = (base + timedelta(days=day_of_year - 2)).date()
    except ValueError:
        return None, "Invalid date encoded in NIC."

    # Make sure it's not a future date
    if dob > datetime.today().date():
        return None, "NIC encodes a future date of birth, which is invalid."

    return {
        "valid": True,
        "nic": nic,
        "format": nic_format,
        "date_of_birth": dob.isoformat(),
        "gender": gender,
        "age": calculate_age(dob),
    }, None


def calculate_age(dob) -> int:
    today = datetime.today().date()
    age = today.year - dob.year
    if (today.month, today.day) < (dob.month, dob.day):
        age -= 1
    return age


def verify_nic_with_dob(nic: str, provided_dob: str) -> Tuple[Optional[dict], Optional[str]]:
    """
    Verify that the NIC matches the provided date of birth.
    provided_dob should be in YYYY-MM-DD format.
    """
    result, error = parse_nic(nic)
    if error:
        return None, error

    try:
        provided_date = datetime.strptime(provided_dob, "%Y-%m-%d").date()
    except ValueError:
        return None, "Invalid date format. Use YYYY-MM-DD."

    nic_dob = result["date_of_birth"]
    match = (nic_dob == provided_date.isoformat())

    return {
        "nic": result["nic"],
        "format": result["format"],
        "match": match,
        "nic_date_of_birth": nic_dob,
        "provided_date_of_birth": provided_date.isoformat(),
        "gender": result["gender"],
        "age": result["age"],
    }, None


def get_gender_from_nic(nic: str):
    """Extract only the gender from a NIC number."""
    nic = nic.strip().upper()
    import re
    old_pattern = re.compile(r'^(\d{9})(V|X)$')
    new_pattern = re.compile(r'^\d{12}$')
    if old_pattern.match(nic):
        nic_format = "old"
        day_of_year = int(nic[2:5])
    elif new_pattern.match(nic):
        nic_format = "new"
        day_of_year = int(nic[4:7])
    else:
        return None, "Invalid NIC format. Expected 9 digits + V/X (old) or 12 digits (new)."
    gender = "Female" if day_of_year > 500 else "Male"
    return {"valid": True, "nic": nic, "format": nic_format, "gender": gender}, None
