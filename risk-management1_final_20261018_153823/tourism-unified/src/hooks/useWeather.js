import { useState, useEffect } from "react";

export function useWeather(latitude, longitude) {
  const [weather, setWeather] = useState(null);
  const [status, setStatus] = useState("idle");

  useEffect(() => {
    if (!latitude || !longitude) return;
    let cancelled = false;
    setStatus("loading");

    const url =
      `https://api.open-meteo.com/v1/forecast?latitude=${latitude}&longitude=${longitude}` +
      `&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation_probability,` +
      `precipitation,weather_code,wind_speed_10m,wind_direction_10m,uv_index,visibility` +
      `&daily=sunrise,sunset,uv_index_max` +
      `&timezone=auto`;

    fetch(url)
      .then((r) => r.json())
      .then((data) => {
        if (cancelled) return;
        setWeather(normalize(data));
        setStatus("success");
      })
      .catch(() => {
        if (!cancelled) setStatus("error");
      });

    return () => {
      cancelled = true;
    };
  }, [latitude, longitude]);

  return { weather, status };
}

function normalize(data) {
  const c = data.current || {};
  const d = data.daily || {};
  return {
    temperature_c: c.temperature_2m,
    feels_like_c: c.apparent_temperature,
    humidity_percent: c.relative_humidity_2m,
    rain_probability_percent: c.precipitation_probability,
    rainfall_mm: c.precipitation,
    wind_speed_kmh: c.wind_speed_10m,
    wind_direction_deg: c.wind_direction_10m,
    uv_index: c.uv_index,
    visibility_m: c.visibility,
    condition: describeWeatherCode(c.weather_code),
    sunrise: d.sunrise ? d.sunrise[0] : null,
    sunset: d.sunset ? d.sunset[0] : null,
  };
}

function describeWeatherCode(code) {
  const map = {
    0: "Clear sky", 1: "Mostly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Fog", 51: "Light drizzle", 53: "Drizzle", 55: "Heavy drizzle",
    61: "Light rain", 63: "Rain", 65: "Heavy rain", 71: "Light snow", 80: "Rain showers",
    81: "Rain showers", 82: "Violent showers", 95: "Thunderstorm",
  };
  return map[code] || "Unknown";
}

export function tourismWeatherAdvice(weather, category) {
  if (!weather) return null;
  let score = 100;
  const reasons = [];

  if (weather.rain_probability_percent > 60) { score -= 30; reasons.push("high chance of rain"); }
  else if (weather.rain_probability_percent > 30) { score -= 12; reasons.push("some chance of rain"); }

  if (weather.wind_speed_kmh > 35) { score -= 15; reasons.push("strong wind"); }
  if (weather.uv_index >= 8) { score -= 5; reasons.push("very high UV"); }
  if (weather.visibility_m && weather.visibility_m < 4000) { score -= 15; reasons.push("reduced visibility"); }

  if (category && category.toLowerCase().includes("waterfall") && weather.rainfall_mm > 5) {
    score -= 10; reasons.push("recent rainfall may make rocks slippery");
  }

  score = Math.max(0, Math.min(100, score));
  const recommendation =
    score >= 75 ? "Good time to visit" : score >= 50 ? "Visit with some caution" : "Consider a different time";

  return { score, recommendation, reasons };
}
