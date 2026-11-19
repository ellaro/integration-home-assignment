import requests


HEBCAL_URL = "https://www.hebcal.com/converter"


class HebcalServiceError(Exception):
    """Raised when Hebcal returns unusable data or the request fails."""


class HebcalHTTPError(HebcalServiceError):
    def __init__(self, status_code):
        self.status_code = status_code
        super().__init__(f"Hebcal returned HTTP {status_code}")


def get_hebrew_date(date_value, after_sunset=False, timeout=5):
    params = {
        "cfg": "json",
        "date": date_value,
        "g2h": "1",
    }
    if after_sunset:
        params["gs"] = "on"

    try:
        response = requests.get(HEBCAL_URL, params=params, timeout=timeout)
        response.raise_for_status()
    except requests.Timeout:
        raise
    except requests.HTTPError as exc:
        status_code = exc.response.status_code if exc.response is not None else 502
        raise HebcalHTTPError(status_code) from exc
    except requests.RequestException as exc:
        raise HebcalServiceError(str(exc)) from exc

    try:
        payload = response.json()
    except (requests.JSONDecodeError, ValueError) as exc:
        raise HebcalServiceError("Hebcal returned invalid JSON.") from exc

    parts = payload.get("heDateParts") or {}
    return {
        "hebrew": payload.get("hebrew"),
        "heDateParts": {
            "year": parts.get("y"),
            "month": parts.get("m"),
            "day": parts.get("d"),
        },
        "events": payload.get("events") or [],
        "afterSunset": bool(payload.get("afterSunset", after_sunset)),
    }
