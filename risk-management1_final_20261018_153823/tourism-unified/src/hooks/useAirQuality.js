import { useState, useEffect } from "react";

export function useAirQuality(latitude, longitude) {
  const [airQuality, setAirQuality] = useState(null);
  const [status, setStatus] = useState("idle");

  useEffect(() => {
    if (!latitude || !longitude) return;
    let cancelled = false;
    setStatus("loading");

    const url =
      `https://air-quality-api.open-meteo.com/v1/air-quality?latitude=${latitude}&longitude=${longitude}` +
      `&current=us_aqi,pm2_5,pm10,ozone,carbon_monoxide,nitrogen_dioxide,sulphur_dioxide` +
      `&timezone=auto`;

    fetch(url)
      .then((r) => r.json())
      .then((data) => {
        if (cancelled) return;
        setAirQuality(normalize(data));
        setStatus("success");
      })
      .catch(() => {
        if (!cancelled) setStatus("error");
      });

    return () => {
      cancelled = true;
    };
  }, [latitude, longitude]);

  return { airQuality, status };
}

function normalize(data) {
  const c = data.current || {};
  return {
    us_aqi: c.us_aqi,
    pm2_5: c.pm2_5,
    pm10: c.pm10,
    ozone: c.ozone,
    carbon_monoxide: c.carbon_monoxide,
    nitrogen_dioxide: c.nitrogen_dioxide,
    sulphur_dioxide: c.sulphur_dioxide,
    category: describeAqi(c.us_aqi),
  };
}

function describeAqi(aqi) {
  if (aqi == null) return null;
  if (aqi <= 50) return "Good";
  if (aqi <= 100) return "Moderate";
  if (aqi <= 150) return "Unhealthy for Sensitive Groups";
  if (aqi <= 200) return "Unhealthy";
  if (aqi <= 300) return "Very Unhealthy";
  return "Hazardous";
}

export function tourismAirQualityAdvice(airQuality) {
  if (!airQuality || airQuality.us_aqi == null) return null;
  const aqi = airQuality.us_aqi;
  let score = 100;
  const reasons = [];

  if (aqi > 200) { score -= 40; reasons.push("very unhealthy air quality"); }
  else if (aqi > 150) { score -= 28; reasons.push("unhealthy air quality"); }
  else if (aqi > 100) { score -= 15; reasons.push("air quality unhealthy for sensitive groups"); }
  else if (aqi > 50) { score -= 5; reasons.push("moderate air quality"); }

  score = Math.max(0, Math.min(100, score));
  const recommendation =
    score >= 85 ? "Good air quality" : score >= 60 ? "Acceptable air quality" : "Poor air quality \u2014 caution advised";

  return { score, recommendation, reasons, category: airQuality.category, aqi };
}