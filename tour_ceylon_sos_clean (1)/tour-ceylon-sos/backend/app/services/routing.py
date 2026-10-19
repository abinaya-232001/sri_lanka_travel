import math


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def nearest(lat, lng, items):
    """(item, distance_km) of the closest item that has latitude/longitude."""
    best, best_d = None, None
    for it in items:
        if it.latitude is None or it.longitude is None:
            continue
        d = haversine_km(lat, lng, it.latitude, it.longitude)
        if best_d is None or d < best_d:
            best, best_d = it, d
    return best, best_d


def nearest_station(lat, lng):
    """The SOS goes to the geographically nearest police or tourism police station."""
    from app.models import Station

    return nearest(lat, lng, Station.query.all())
