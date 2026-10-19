export function distanceKm(lat1, lon1, lat2, lon2) {
  const R = 6371;
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2;
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

function toRad(deg) {
  return (deg * Math.PI) / 180;
}

export function nearestSites(origin, allSites, count = 5) {
  return allSites
    .filter((s) => s.site_id !== origin.site_id && s.latitude && s.longitude)
    .map((s) => ({
      ...s,
      distance_km: Math.round(distanceKm(origin.latitude, origin.longitude, s.latitude, s.longitude) * 10) / 10,
    }))
    .sort((a, b) => a.distance_km - b.distance_km)
    .slice(0, count);
}

export function estimateTravelMinutes(km, mode = "driving") {
  const speedKmh = { driving: 40, walking: 4.5 }[mode] ?? 40;
  return Math.round((km / speedKmh) * 60);
}

export function alternativeSites(origin, candidateSites, count = 3) {
  const scored = candidateSites
    .filter((s) => s.site_id !== origin.site_id && s.latitude && s.longitude)
    .map((s) => ({
      ...s,
      distance_km: Math.round(distanceKm(origin.latitude, origin.longitude, s.latitude, s.longitude) * 10) / 10,
      same_category: origin.category && s.category === origin.category,
    }));

  scored.sort((a, b) => {
    if (a.same_category !== b.same_category) return a.same_category ? -1 : 1;
    return a.distance_km - b.distance_km;
  });

  return scored.slice(0, count);
}
