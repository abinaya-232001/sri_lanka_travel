import { useSiteI18n } from "@shared/i18n/react";
import { useWeather, tourismWeatherAdvice } from "../hooks/useWeather";
import { useAirQuality, tourismAirQualityAdvice } from "../hooks/useAirQuality";
import { nearestSites } from "../utils/geo";

export function HoverCard({ icon, label, detail }) {
  return (
    <div
      className="site-intel-hovercard"
      style={{
        position: "relative",
        padding: "10px 14px",
        borderRadius: 10,
        border: "1px solid #e4e7ec",
        background: "#fff",
        cursor: detail ? "help" : "default",
        transition: "all 180ms ease",
        minWidth: 120,
      }}
    >
      <div style={{ fontSize: 13, display: "flex", alignItems: "center", gap: 6, fontWeight: 500 }}>
        <span>{icon}</span>
        <span>{label}</span>
      </div>
      {detail && (
        <div
          className="site-intel-tooltip"
          style={{
            position: "absolute",
            bottom: "calc(100% + 8px)",
            left: 0,
            background: "#1a1f2b",
            color: "#fff",
            fontSize: 12,
            lineHeight: 1.4,
            padding: "8px 10px",
            borderRadius: 8,
            width: 200,
            zIndex: 20,
            opacity: 0,
            visibility: "hidden",
            transition: "opacity 160ms ease",
            boxShadow: "0 8px 20px rgba(0,0,0,0.25)",
            pointerEvents: "none",
          }}
        >
          {detail}
        </div>
      )}
      <style>{`
        .site-intel-hovercard:hover { transform: translateY(-2px); box-shadow: 0 6px 16px rgba(20,40,90,0.10); background: #f8faff; }
        .site-intel-hovercard:hover .site-intel-tooltip { opacity: 1; visibility: visible; }
      `}</style>
    </div>
  );
}

function formatTime(iso) {
  try {
    return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  } catch {
    return "\u2013";
  }
}

const GOLDEN_HOUR_MIN = 30;
const BLUE_HOUR_MIN = 15;

function computeLightWindows(sunriseIso, sunsetIso) {
  if (!sunriseIso || !sunsetIso) return null;
  const sunrise = new Date(sunriseIso);
  const sunset = new Date(sunsetIso);
  const addMinutes = (date, mins) => new Date(date.getTime() + mins * 60000);
  return {
    goldenMorningStart: sunrise,
    goldenMorningEnd: addMinutes(sunrise, GOLDEN_HOUR_MIN),
    goldenEveningStart: addMinutes(sunset, -GOLDEN_HOUR_MIN),
    goldenEveningEnd: sunset,
    blueMorningStart: addMinutes(sunrise, -BLUE_HOUR_MIN),
    blueMorningEnd: sunrise,
    blueEveningStart: sunset,
    blueEveningEnd: addMinutes(sunset, BLUE_HOUR_MIN),
  };
}

export function WeatherPanel({ siteProfile }) {
  const { t } = useSiteI18n();
  const lat = siteProfile && siteProfile.latitude;
  const lon = siteProfile && siteProfile.longitude;
  const { weather, status } = useWeather(lat, lon);
  const light = weather ? computeLightWindows(weather.sunrise, weather.sunset) : null;
  const advice = tourismWeatherAdvice(weather, siteProfile && siteProfile.category);

  if (!lat || !lon) {
    return (
      <div style={{ fontSize: 13, color: "#999", fontStyle: "italic" }}>
        {t("ldCoordsUnavailable")}
      </div>
    );
  }

  return (
    <div>
      {status === "loading" && <div style={{ fontSize: 13, color: "#888" }}>{t("ldLoadingConditions")}</div>}
      {status === "error" && <div style={{ fontSize: 13, color: "#b3261e" }}>{t("ldWeatherLoadFailed")}</div>}
      {weather && (
        <>
          {advice && (
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 12,
                padding: "12px 16px",
                borderRadius: 12,
                marginBottom: 12,
                background: advice.score >= 75 ? "#eafaf0" : advice.score >= 50 ? "#fff8e6" : "#fdecec",
              }}
            >
              <div
                style={{
                  fontSize: 22,
                  fontWeight: 700,
                  color: advice.score >= 75 ? "#1c7c4f" : advice.score >= 50 ? "#9a6a00" : "#b3261e",
                }}
              >
                {advice.score}
              </div>
              <div>
                <div style={{ fontWeight: 600, fontSize: 14 }}>{advice.recommendation}</div>
                <div style={{ fontSize: 11, color: "#999", marginTop: 2 }}>{t("ldWeatherNote")}</div>
                {advice.reasons.length > 0 && (
                  <div style={{ fontSize: 12, color: "#666" }}>{advice.reasons.join(", ")}</div>
                )}
              </div>
            </div>
          )}
          <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
            <HoverCard icon={"\uD83C\uDF21\uFE0F"} label={(weather.temperature_c != null ? weather.temperature_c : "\u2013") + "\u00B0C"} detail={t("ldFeelsLike") + " " + (weather.feels_like_c != null ? weather.feels_like_c : "\u2013") + "\u00B0C"} />
            <HoverCard icon={"\uD83C\uDF27\uFE0F"} label={(weather.rain_probability_percent != null ? weather.rain_probability_percent : "\u2013") + "% " + t("ldRain")} detail={t("ldRainToday") + " " + (weather.rainfall_mm || 0) + " mm"} />
            <HoverCard icon={"\uD83D\uDCA8"} label={(weather.wind_speed_kmh != null ? weather.wind_speed_kmh : "\u2013") + " " + t("ldWind")} />
            <HoverCard icon={"\uD83D\uDCA7"} label={(weather.humidity_percent != null ? weather.humidity_percent : "\u2013") + "% " + t("ldHumidity")} />
            <HoverCard icon={"\u2600\uFE0F"} label={"UV " + (weather.uv_index != null ? weather.uv_index : "\u2013")} detail={weather.uv_index >= 8 ? t("ldUvVeryHigh") : t("ldUvModerate")} />
            <HoverCard icon={"\uD83D\uDC41\uFE0F"} label={weather.visibility_m ? (weather.visibility_m / 1000).toFixed(1) + " " + t("ldVisibilityKm") : t("ldVisibilityUnknown")} />
            <HoverCard icon={"\uD83C\uDF05"} label={weather.sunrise ? t("ldSunrise") + " " + formatTime(weather.sunrise) : t("ldSunrise") + " \u2013"} />
            <HoverCard icon={"\uD83C\uDF07"} label={weather.sunset ? t("ldSunset") + " " + formatTime(weather.sunset) : t("ldSunset") + " \u2013"} />
            {light && <HoverCard icon={"\uD83C\uDF05"} label={t("ldGoldenHour")} detail={formatTime(light.goldenMorningStart) + "\u2013" + formatTime(light.goldenMorningEnd) + " & " + formatTime(light.goldenEveningStart) + "\u2013" + formatTime(light.goldenEveningEnd)} />}
            {light && <HoverCard icon={"\uD83D\uDD35"} label={t("ldBlueHour")} detail={formatTime(light.blueMorningStart) + "\u2013" + formatTime(light.blueMorningEnd) + " & " + formatTime(light.blueEveningStart) + "\u2013" + formatTime(light.blueEveningEnd)} />}
          </div>
          <div style={{ fontSize: 11, color: "#999", marginTop: 8 }}>
            {t("ldWeatherAttribution")}
          </div>
        </>
      )}
    </div>
  );
}

export function NearbyPanel({ siteProfile, allSitesArray, onSelectSite, date }) {
  const { t } = useSiteI18n();
  if (!siteProfile || !siteProfile.latitude || !allSitesArray || allSitesArray.length === 0) {
    return (
      <div style={{ fontSize: 13, color: "#999", fontStyle: "italic" }}>
        {t("ldNearbyUnavailable")}
      </div>
    );
  }
  const nearby = nearestSites(siteProfile, allSitesArray, 6);
  if (nearby.length === 0) return null;
  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
      {nearby.map((n) => (
        <div key={n.site_id} onClick={() => onSelectSite && onSelectSite(n.site_id, date)} style={{ cursor: onSelectSite ? "pointer" : "default" }}><HoverCard icon={"\uD83D\uDCCD"} label={n.site_name + " \u2014 " + n.distance_km + " km"} detail={n.district + " \u00B7 " + n.category} /></div>
      ))}
    </div>
  );
}

function scoreBand(score, t) {
  if (score >= 75) return { bg: "#eafaf0", text: "#1c7c4f", label: t("ldGreatTimeToGo") };
  if (score >= 50) return { bg: "#fff8e6", text: "#9a6a00", label: t("ldOkTimeToGo") };
  return { bg: "#fdecec", text: "#b3261e", label: t("ldBetterToWait") };
}

const RISK_KEYS = { Low: "ldRiskLow", Medium: "ldRiskMedium", High: "ldRiskHigh" };

export function ShouldIGoNowCard({ siteProfile, prediction, uncertainty }) {
  const { t } = useSiteI18n();
  const lat = siteProfile && siteProfile.latitude;
  const lon = siteProfile && siteProfile.longitude;
  const { weather } = useWeather(lat, lon);
  const advice = tourismWeatherAdvice(weather, siteProfile && siteProfile.category);

  const { airQuality } = useAirQuality(lat, lon);
  const aqAdvice = tourismAirQualityAdvice(airQuality);
  const aqScore = aqAdvice ? aqAdvice.score : null;

  if (!prediction) return null;

  const crowdScore = Math.round((1 - prediction.crowd_score) * 100);
  const weatherScore = advice ? advice.score : null;
  const scores = [crowdScore, weatherScore, aqScore].filter((s) => s != null);
  const overallScore = Math.round(scores.reduce((a, b) => a + b, 0) / scores.length);
  const band = scoreBand(overallScore, t);

  const rows = [{ icon: "\uD83D\uDC65", label: t("ldCrowd"), value: t(RISK_KEYS[prediction.risk_level] || "ldRiskUnknown") }];
  if (advice) rows.push({ icon: "\u2600\uFE0F", label: t("ldWeather"), value: advice.recommendation });
  if (aqAdvice) rows.push({ icon: "\uD83C\uDF2B\uFE0F", label: t("ldAirQuality"), value: aqAdvice.category + " (AQI " + aqAdvice.aqi + ")" });
  if (weather && weather.visibility_m) {
    rows.push({ icon: "\uD83D\uDC41\uFE0F", label: t("ldVisibility"), value: (weather.visibility_m / 1000).toFixed(1) + " km" });
  }
  if (uncertainty && uncertainty.uncertainty_level) rows.push({ icon: "\uD83D\uDCCA", label: t("ldConfidence"), value: uncertainty.uncertainty_level });

  return (
    <div style={{ padding: "24px", borderRadius: 16, background: band.bg, border: "1px solid " + band.text + "33" }}>
      <div style={{ fontSize: 12, fontWeight: 700, letterSpacing: "0.08em", color: band.text, marginBottom: 14, textTransform: "uppercase" }}>
        {t("ldShouldYouGoNow")}
      </div>
      <div style={{ fontSize: 11, color: band.text, opacity: 0.75, marginBottom: 10 }}>
        {t("ldCombinedScore")}
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 20, marginBottom: 18, flexWrap: "wrap" }}>
        <div style={{ fontSize: 40, fontWeight: 800, color: band.text }}>{overallScore}</div>
        <div style={{ fontSize: 16, fontWeight: 700, color: band.text }}>{band.label}</div>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: 10 }}>
        {rows.map((r, i) => (
          <div key={i} style={{ display: "flex", alignItems: "center", gap: 8, padding: "10px 12px", background: "#fff", borderRadius: 10, fontSize: 13 }}>
            <span>{r.icon}</span>
            <div>
              <div style={{ fontSize: 11, color: "#888" }}>{r.label}</div>
              <div style={{ fontWeight: 600 }}>{r.value}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
