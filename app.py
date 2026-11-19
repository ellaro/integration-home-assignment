import logging
import re
from datetime import datetime

from flask import Flask, jsonify, render_template, request
from requests import Timeout

from services.hebcal_service import (
    HebcalHTTPError,
    HebcalServiceError,
    get_hebrew_date,
)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    handlers=[
        logging.FileHandler("app.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def validate_date(value):
    if not isinstance(value, str) or not DATE_PATTERN.fullmatch(value):
        raise ValueError("Date must use YYYY-MM-DD format.")

    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Please enter a valid calendar date.")

    return value


def convert_request(date_value, after_sunset):
    date_value = validate_date(date_value)
    try:
        return get_hebrew_date(date_value, after_sunset=after_sunset), None
    except Timeout:
        logger.warning("Hebcal request timed out for date %s", date_value)
        return None, ("The Hebcal service timed out. Please try again.", 504)
    except HebcalHTTPError as exc:
        logger.warning("Hebcal HTTP error %s for date %s", exc.status_code, date_value)
        return None, ("Hebcal could not process this date.", 502)
    except HebcalServiceError as exc:
        logger.error("Hebcal service error for date %s: %s", date_value, exc)
        return None, ("Unable to reach the Hebcal service.", 502)


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/convert")
def convert_post():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(error={"code": "INVALID_REQUEST", "message": "Send a JSON object."}), 400

    date_value = payload.get("date")
    after_sunset = payload.get("afterSunset", False)

    if not isinstance(after_sunset, bool):
        return jsonify(error={"code": "INVALID_REQUEST", "message": "afterSunset must be true or false."}), 400

    try:
        date_value = validate_date(date_value)
    except ValueError as exc:
        return jsonify(error={"code": "INVALID_DATE", "message": str(exc)}), 400

    result, failure = convert_request(date_value, after_sunset)
    if failure:
        message, status = failure
        code = "SERVICE_TIMEOUT" if status == 504 else "UPSTREAM_ERROR"
        return jsonify(error={"code": code, "message": message}), status
    return jsonify(result)


if __name__ == "__main__":
    app.run()
