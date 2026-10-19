from functools import wraps

from flask import jsonify
from flask_jwt_extended import create_access_token, get_jwt, get_jwt_identity, verify_jwt_in_request


def token_for_tourist(tourist):
    return create_access_token(identity=str(tourist.id), additional_claims={"role": "tourist"})


def token_for_officer(officer):
    return create_access_token(identity=str(officer.id),
                               additional_claims={"role": "police", "station_id": officer.station_id})


def tourist_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        if get_jwt().get("role") != "tourist":
            return jsonify({"error": "Tourist login required"}), 403
        from app.models import Tourist

        tourist = Tourist.query.get(int(get_jwt_identity()))
        if not tourist:
            return jsonify({"error": "Account not found"}), 401
        return fn(tourist, *args, **kwargs)
    return wrapper


def police_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        if claims.get("role") != "police":
            return jsonify({"error": "Police login required"}), 403
        from app.models import Officer

        officer = Officer.query.get(int(get_jwt_identity()))
        if not officer or officer.station_id != int(claims.get("station_id", -1)):
            return jsonify({"error": "Account not found"}), 401
        return fn(officer, *args, **kwargs)
    return wrapper


def incident_access(incident):
    """'tourist' | 'police' | None — same rule as the socket rooms."""
    verify_jwt_in_request()
    claims = get_jwt()
    if claims.get("role") == "tourist" and int(get_jwt_identity()) == incident.tourist_id:
        return "tourist"
    if claims.get("role") == "police" and int(claims.get("station_id", -1)) == incident.station_id:
        return "police"
    return None
