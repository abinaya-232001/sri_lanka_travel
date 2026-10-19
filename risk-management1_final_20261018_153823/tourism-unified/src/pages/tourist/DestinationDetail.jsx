import React, { useState, useEffect, useRef } from "react";
import { useSiteI18n } from "@shared/i18n/react";
import { tokens, riskColors } from "../../design/tokens";
import { crowdPhraseKey } from "../../components/CrowdChip";
import { WeatherPanel, NearbyPanel, ShouldIGoNowCard } from "../../components/SiteIntelligence";
import { alternativeSites } from "../../utils/geo";
import { api } from "../../api/client";
import { useApi } from "../../hooks/useApi";
import RiskPill from "../../components/RiskPill";
import BestTimeGrid from "../../components/BestTimeGrid";
import ForecastChart from "../../components/ForecastChart";
import HourlyPatternChart from "../../components/HourlyPatternChart";
import { getSiteInsights } from "../../design/siteInsights";
import { siteImagePath } from "../../utils/siteImage";
import { Clock, Compass, Shirt, ShieldAlert } from "lucide-react";
import "../../design/animations.css";

const FEATURE_LABEL_KEYS = {
  daily_flights_at_cmb: "ldFeatFlightArrivals",
  hotel_occupancy_rate: "ldFeatHotelOccupancy",
  capacity_per_day: "ldFeatSiteCapacity",
  is_public_holiday: "ldFeatPublicHoliday",
  is_weekend: "ldFeatWeekend",
  month: "ldFeatTimeOfYear",
  avg_temperature_c: "ldFeatTemperature",
  category_encoded: "ldFeatDestType",
  avg_rainfall_mm: "ldFeatRainfall",
  season_encoded: "ldFeatSeason",
  day_of_week: "ldFeatDayOfWeek",
  district_encoded: "ldFeatLocation",
  is_eco_friendly: "ldFeatEcoSite",
  is_unesco: "ldFeatUnesco",
  entrance_fee_lkr: "ldFeatEntranceFee",
  is_festival_period: "ldFeatFestival",
};

function explainSentence(factor, t) {
  const label = t(FEATURE_LABEL_KEYS[factor.feature] || "") || factor.label || factor.feature;
  const pct = Math.abs(Math.round(factor.shap_contribution * 100));
  const dir = factor.direction === "increases_crowd" ? t("ldExplainRaises") : t("ldExplainLowers");
  return label[0].toUpperCase() + label.slice(1) + " " + dir + " " + t("ldExplainCrowding").replace("{pct}", pct);
}

function FeedbackForm({ siteId, date, onSaved }) {
  const { t } = useSiteI18n();
  const [crowd, setCrowd] = useState(null);
  const [accuracy, setAccuracy] = useState(null);
  const [visitTime, setVisitTime] = useState("");
  const [done, setDone] = useState(false);
  const [sending, setSending] = useState(false);
  const [saveWarning, setSaveWarning] = useState(null);
  const [saveError, setSaveError] = useState(null);

  const submit = async () => {
    if (!crowd || !accuracy) return;
    setSending(true);
    setSaveError(null);
    try {
      const res = await api.feedback({ site_id: Number(siteId), visit_date: date, visit_time: visitTime || null, observed_crowd: crowd, accuracy });
      if (res && res.status === "success") {
        setSaveWarning(res.warning || null);
        setDone(true);
        if (onSaved) onSaved();
      } else {
        setSaveError((res && res.message) || t("ldFeedbackSaveError"));
      }
    } catch (e) {
      setSaveError(t("ldFeedbackNetworkError"));
    }
    setSending(false);
  };

  const crowdLabels = ["ldCrowdVeryEmpty", "ldCrowdQuiet", "ldCrowdModerate", "ldCrowdBusy", "ldCrowdOvercrowded"];
  const accuracyOptions = [["ldAccurate", 1], ["ldSlightlyOff", 2], ["ldVeryInaccurate", 3]];

  if (done) {
    return (
      <div style={{ padding: "16px 20px", backgroundColor: tokens.accentSoft, border: "1px solid " + tokens.accentBorder, borderRadius: tokens.radiusMd, color: tokens.accentBright, fontSize: "15px", fontWeight: 600 }}>
        {t("ldFeedbackThanks")}
        {saveWarning && (
          <div style={{ marginTop: "6px", fontSize: "14px", fontWeight: 500, color: tokens.textTertiary }}>
            {t("ldFeedbackBackupWarning")}
          </div>
        )}
      </div>
    );
  }

  return (
    <div style={{ padding: "20px", backgroundColor: tokens.surface, border: "1px solid " + tokens.border, borderRadius: tokens.radiusMd }}>
      <div style={{ fontSize: "15px", fontWeight: 600, color: tokens.textSecondary, marginBottom: "12px" }}>{t("ldFeedbackQuestion")}</div>
      <div style={{ display: "flex", gap: "6px", flexWrap: "wrap", marginBottom: "14px" }}>
        {crowdLabels.map((labelKey, i) => (
          <button key={i} onClick={() => setCrowd(i + 1)} style={{ padding: "8px 12px", fontSize: "14px", fontWeight: 600, backgroundColor: crowd === i + 1 ? tokens.accentSoft : tokens.surfaceAlt, border: "1px solid " + (crowd === i + 1 ? tokens.accentBorder : tokens.borderStrong), borderRadius: tokens.radiusSm, color: crowd === i + 1 ? tokens.accentBright : tokens.textSecondary, cursor: "pointer" }}>
            {t(labelKey)}
          </button>
        ))}
      </div>
      <div style={{ display: "flex", gap: "8px", marginBottom: "16px" }}>
        {accuracyOptions.map(([labelKey, val]) => (
          <button key={val} onClick={() => setAccuracy(val)} style={{ flex: 1, padding: "9px", fontSize: "14px", fontWeight: 600, backgroundColor: accuracy === val ? tokens.accentSoft : tokens.surfaceAlt, border: "1px solid " + (accuracy === val ? tokens.accentBorder : tokens.borderStrong), borderRadius: tokens.radiusSm, color: accuracy === val ? tokens.accentBright : tokens.textSecondary, cursor: "pointer" }}>
            {t(labelKey)}
          </button>
        ))}
      </div>
      <div style={{ marginBottom: "16px" }}>
        <div style={{ fontSize: "14px", color: tokens.textTertiary, marginBottom: "6px" }}>{t("ldVisitTimeOptional")}</div>
        <input type="time" value={visitTime} onChange={(e) => setVisitTime(e.target.value)} style={{ padding: "8px 12px", backgroundColor: tokens.surfaceAlt, border: "1px solid " + tokens.borderStrong, borderRadius: tokens.radiusSm, color: tokens.textPrimary, fontSize: "15px" }} />
      </div>
      {(!crowd || !accuracy) && (
        <div style={{ fontSize: "14px", color: tokens.textTertiary, marginBottom: "8px" }}>
          {!crowd && !accuracy ? t("ldSelectCrowdAndAccuracy") : !crowd ? t("ldSelectCrowdLevel") : t("ldSelectAccuracy")}
        </div>
      )}
      {saveError && (
        <div style={{ fontSize: "14px", color: "#C84B31", marginBottom: "8px", fontWeight: 600 }}>
          {saveError}
        </div>
      )}
      <button onClick={submit} disabled={!crowd || !accuracy || sending} style={{ width: "100%", padding: "11px", backgroundColor: crowd && accuracy ? tokens.accentBright : tokens.surfaceAlt, color: crowd && accuracy ? "#FFF8F2" : tokens.textFaint, border: "none", borderRadius: tokens.radiusSm, fontSize: "15px", fontWeight: 700, cursor: crowd && accuracy ? "pointer" : "not-allowed" }}>
        {sending ? t("ldSubmitting") : t("ldSubmitFeedback")}
      </button>
    </div>
  );
}

function FeedbackList({ siteId, refreshKey }) {
  const { t } = useSiteI18n();
  const { data, loading } = useApi(() => api.getFeedback(), [siteId, refreshKey]);
  const crowdLabels = ["ldCrowdVeryEmpty", "ldCrowdQuiet", "ldCrowdModerate", "ldCrowdBusy", "ldCrowdOvercrowded"];
  const accuracyLabels = { 1: "ldAccurate", 2: "ldSlightlyOff", 3: "ldVeryInaccurate" };

  if (loading) return null;
  const records = (data && data.feedback) ? data.feedback : [];
  const siteRecords = records
    .filter((r) => Number(r.site_id) === Number(siteId))
    .map((r) => ({
      date: r.visit_date || r.date || "",
      time: r.visit_time || r.time || "",
      crowd: r.observed_crowd_level != null ? r.observed_crowd_level : r.actual_crowd_level,
      accuracy: r.accuracy_rating != null ? r.accuracy_rating : r.rating,
      comment: r.comment || "",
    }))
    .sort((a, b) => (b.date || "").localeCompare(a.date || ""))
    .slice(0, 5);

  if (siteRecords.length === 0) return null;

  return (
    <div style={{ marginTop: "16px" }}>
      <div style={{ fontSize: "14px", fontWeight: 700, color: tokens.textTertiary, textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: "10px" }}>{t("ldRecentVisitorFeedback")}</div>
      {siteRecords.map((r, i) => (
        <div key={i} style={{ padding: "12px 14px", backgroundColor: tokens.surfaceAlt, border: "1px solid " + tokens.border, borderRadius: tokens.radiusSm, marginBottom: i < siteRecords.length - 1 ? "8px" : 0 }}>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: "15px", fontWeight: 600, color: tokens.textSecondary, marginBottom: r.comment ? "6px" : 0 }}>
            <span>{r.crowd >= 1 && r.crowd <= 5 ? t(crowdLabels[r.crowd - 1]) : t("ldUnknownCrowdLevel")}</span>
            <span style={{ color: tokens.textTertiary, fontWeight: 500 }}>{r.date}{r.time ? " ".concat(String.fromCharCode(183), " ", r.time) : ""}</span>
          </div>
          <div style={{ fontSize: "14px", color: tokens.textTertiary, marginBottom: r.comment ? "6px" : 0 }}>
            {t("ldPredictionRated").replace("{rating}", t(accuracyLabels[r.accuracy]) || t("ldNotAvailable"))}
          </div>
          {r.comment && (
            <div style={{ fontSize: "15px", color: tokens.textSecondary, lineHeight: 1.5 }}>{r.comment}</div>
          )}
        </div>
      ))}
    </div>
  );
}

export default function DestinationDetail({ siteId, date, onBack, onSelectSite }) {
  const { t } = useSiteI18n();
  const { data: prediction, loading: predLoading } = useApi(() => api.predict(siteId, date), [siteId, date], { skip: !siteId });
  const { data: forecast, loading: forecastLoading } = useApi(() => api.forecast(siteId, date), [siteId, date], { skip: !siteId });
  const { data: explain, loading: explainLoading } = useApi(() => api.explain(siteId, date), [siteId, date], { skip: !siteId });
  const { data: alertData } = useApi(() => api.alert(siteId, date), [siteId, date], { skip: !siteId });
  const { data: green } = useApi(() => api.greenSites(date), [date], { skip: !siteId });

  const [notifPermission, setNotifPermission] = useState(
    typeof Notification !== "undefined" ? Notification.permission : "unsupported"
  );
  const notifiedRef = useRef(new Set());

  const enableAlerts = () => {
    if (typeof Notification === "undefined") return;
    Notification.requestPermission().then(setNotifPermission);
  };

  useEffect(() => {
    if (notifPermission !== "granted") return;
    if (!alertData || !alertData.alert || !siteId || !date) return;
    const key = siteId + "-" + date;
    if (notifiedRef.current.has(key)) return;
    notifiedRef.current.add(key);
    const title = (prediction && prediction.site_name) || t("ldCrowdAlert");
    new Notification(title, { body: alertData.message, icon: "/favicon.ico" });
  }, [alertData, siteId, date, notifPermission, prediction]);
  const { data: uncertainty } = useApi(() => api.uncertainty(siteId, date), [siteId, date], { skip: !siteId });
  const { data: surge } = useApi(() => api.surgePrediction(siteId, date, 7), [siteId, date], { skip: !siteId });
  const { data: allSites } = useApi(() => api.sites(), []);
  const [feedbackRefresh, setFeedbackRefresh] = useState(0);

  if (!siteId) {
    return <div style={{ padding: "60px", color: tokens.textTertiary, backgroundColor: tokens.bg, minHeight: "100vh" }}>{t("ldNoDestinationSelected")}</div>;
  }

  const siteProfile = allSites && allSites.sites ? allSites.sites.find((s) => s.site_id === Number(siteId)) : null;
  const crowdPct = prediction ? Math.round(prediction.crowd_score * 100) : null;
  const c = riskColors(prediction ? prediction.risk_level : "Medium");
  const alternatives = green && green.green_sites && siteProfile ? alternativeSites(siteProfile, green.green_sites, 3) : [];
  const month = date ? new Date(date).getMonth() + 1 : new Date().getMonth() + 1;

  return (
    <div style={{ minHeight: "100vh", background: tokens.bgGradient, color: tokens.textPrimary, fontFamily: tokens.font, padding: "40px 32px 80px" }}>
      <div style={{ maxWidth: "920px", margin: "0 auto" }}>
        {onBack && (
          <button onClick={onBack} className="ld-ghost-btn" style={{ marginBottom: "24px", padding: "9px 18px", borderRadius: tokens.radiusSm, cursor: "pointer", fontSize: "15px", fontWeight: 700 }}>
            &larr; {t("ldBackToDiscover")}
          </button>
        )}

        {predLoading && <div style={{ padding: "40px 0", color: tokens.textTertiary }}>{t("ldLoadingPrediction")}</div>}

        {prediction && (
          <>
            <div className="ld-read-panel ld-read-panel--tight" style={{ marginBottom: "18px" }}>
            <div style={{ marginBottom: "8px", color: "#BF7E46", fontSize: "14px", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.12em" }}>
              {prediction.date}
              {prediction.is_holiday && (
                <span style={{ marginLeft: "10px", padding: "3px 10px", borderRadius: "999px", backgroundColor: tokens.warmSoft, color: tokens.warm, border: "1px solid " + tokens.warmBorder }}>
                  {t("ldPublicHoliday")}
                </span>
              )}
            </div>
            <h1 style={{ fontSize: "clamp(40px, 4.6vw, 56px)", fontWeight: 600, margin: "0 0 10px", letterSpacing: "-0.02em", lineHeight: 1.08, color: "#1C1917" }}>
  {prediction.site_name}
</h1>
            <img
              src={siteImagePath(prediction.site_name)}
              alt={prediction.site_name}
              style={{
                width: "100%",
                height: "220px",
                objectFit: "cover",
                borderRadius: tokens.radiusMd,
                margin: "0 0 16px",
                background: "#d7e4e2",
              }}
              onError={(e) => {
                e.currentTarget.style.display = "none";
              }}
            />

<button
  type="button"
  style={{
    padding: "10px 18px",
    marginBottom: "18px",
    backgroundColor: tokens.accentBright,
    color: "#FFF8F2",
    border: "none",
    borderRadius: tokens.radiusSm,
    fontSize: "15px",
    fontWeight: 700,
    cursor: "pointer",
  }}
>
  + {t("ldAddToItinerary")}
</button>

{siteProfile && (
              <div style={{ display: "flex", gap: "18px", flexWrap: "wrap", marginBottom: "8px", fontSize: "15px", color: "#6B625A" }}>
                <span>{siteProfile.district}, {siteProfile.province}</span>
                <span>&middot;</span>
                <span>{siteProfile.category}</span>
                <span>&middot;</span>
                <span>{t("ldCapacityPerDay").replace("{count}", siteProfile.capacity_per_day.toLocaleString())}</span>
                <span>&middot;</span>
                <span>{t("ldEntranceFeeLkr").replace("{fee}", siteProfile.entrance_fee_lkr.toLocaleString())}</span>
                {siteProfile.is_unesco && <span style={{ color: tokens.accentBright }}>&middot; {t("ldUnescoSite")}</span>}
                {siteProfile.is_eco_friendly && <span style={{ color: tokens.accentBright }}>&middot; {t("ldEcoFriendly")}</span>}
              </div>
            )}
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: "24px", padding: "28px", backgroundColor: tokens.surface, border: "1px solid " + tokens.border, borderRadius: tokens.radiusLg, marginBottom: "24px", flexWrap: "wrap", boxShadow: tokens.shadowSm }}>
              <div style={{ fontSize: "52px", fontWeight: 800, color: c.text, fontFamily: tokens.mono, textShadow: c.glow }}>
                {crowdPct}%
              </div>
              <div style={{ fontSize: "14px", color: tokens.textTertiary, marginTop: "2px" }}>
                {t("ldCrowdLevelNote")}
              </div>
              <div>
                <RiskPill level={prediction.risk_level} size="lg" />
                <div style={{ marginTop: "10px", fontSize: "14px", color: tokens.textSecondary, maxWidth: "480px" }}>
                  {t(crowdPhraseKey(prediction.crowd_score))} &mdash; {prediction.recommendation}
                </div>
                {uncertainty && (
                  <div style={{ marginTop: "8px", fontSize: "14px", color: tokens.textTertiary }}>
                    {t("ldModelConfidence")} {uncertainty.uncertainty_level} ({t("ldPredictedRange")} {Math.round(uncertainty.prediction_interval_10_90[0] * 100)}&ndash;{Math.round(uncertainty.prediction_interval_10_90[1] * 100)}%)
                  </div>
                )}
              </div>
            </div>

            {notifPermission === "default" && (
              <button
                onClick={enableAlerts}
                style={{ padding: "10px 18px", backgroundColor: tokens.surfaceAlt, color: tokens.textPrimary, border: "1px solid " + tokens.border, borderRadius: tokens.radiusSm, fontSize: "15px", fontWeight: 600, cursor: "pointer", marginBottom: "16px" }}
              >
                &#128276; {t("ldEnableCrowdAlerts")}
              </button>
            )}
            {alertData && alertData.alert && (
              <div style={{ padding: "18px 20px", backgroundColor: tokens.dangerSoft, border: "1px solid " + tokens.dangerBorder, borderRadius: tokens.radiusMd, marginBottom: "24px", color: tokens.textPrimary, fontSize: "14px" }}>
                &#9888; {alertData.message}
              </div>
            )}
            {surge && surge.surges_detected > 0 && surge.surges && surge.surges[0] && (
              <div style={{ padding: "18px 20px", backgroundColor: tokens.warmSoft, border: "1px solid " + tokens.warmBorder, borderRadius: tokens.radiusMd, marginBottom: "24px", color: tokens.textPrimary, fontSize: "14px" }}>
                &#9888; {surge.surges[0].message}
              </div>
            )}
          </>
        )}


        {prediction && siteProfile && (
          <div style={{ marginBottom: "28px" }}>
            <ShouldIGoNowCard siteProfile={siteProfile} prediction={prediction} uncertainty={uncertainty} />
          </div>
        )}
        {!forecastLoading && forecast && forecast.forecast && (
          <div style={{ marginBottom: "28px" }}>
            <div style={sectionTitle}>{t("ldSevenDayForecast")}</div>
            <ForecastChart forecast={forecast.forecast} />
          </div>
        )}

        <div style={{ marginBottom: "28px" }}>
          <div style={sectionTitle}>{t("ldBestTimeToVisit")}</div>
          <BestTimeGrid siteId={siteId} initialMonth={month} />
        </div>

        {siteProfile && prediction && (
          <div style={{ marginBottom: "28px" }}>
            <div style={sectionTitle}>{t("ldTypicalHourlyPattern")}</div>
            <HourlyPatternChart category={siteProfile.category} crowdScore={prediction.crowd_score} />
          </div>
        )}

        {siteProfile && (
          <div style={{ marginBottom: "28px" }}>
            <div style={sectionTitle}>{t("ldRightNow")}</div>
            <WeatherPanel siteProfile={siteProfile} />
          </div>
        )}

        {siteProfile && allSites && allSites.sites && (
          <div style={{ marginBottom: "28px" }}>
            <div style={sectionTitle}>{t("ldNearbyDestinations")}</div>
            <NearbyPanel siteProfile={siteProfile} allSitesArray={allSites.sites} onSelectSite={onSelectSite} date={date} />
          </div>
        )}

        {!explainLoading && explain && explain.top_factors && (
          <div style={{ marginBottom: "28px" }}>
            <div style={sectionTitle}>{t("ldWhyThisPrediction")}</div>
            <div style={{ padding: "20px", backgroundColor: tokens.surface, border: "1px solid " + tokens.border, borderRadius: tokens.radiusMd }}>
              {explain.top_factors.slice(0, 4).map((f, i) => (
                <div key={i} style={{ fontSize: "14px", color: tokens.textSecondary, lineHeight: 1.7, marginBottom: i < 3 ? "8px" : 0 }}>
                  &bull; {explainSentence(f, t)}
                </div>
              ))}
            </div>
          </div>
        )}

        {alternatives.length > 0 && (
          <div style={{ marginBottom: "28px" }}>
            <div style={sectionTitle}>{t("ldQuieterAlternatives")}</div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))", gap: "12px" }}>
              {alternatives.map((a) => (
                <div key={a.site_id} style={{ padding: "16px", backgroundColor: tokens.surface, border: "1px solid " + tokens.border, borderRadius: tokens.radiusMd }}>
                  <div style={{ fontSize: "15px", fontWeight: 700, marginBottom: "6px" }}>{a.site_name}</div>
                  <div style={{ fontSize: "14px", color: tokens.textTertiary, marginBottom: "10px" }}>{a.district} &middot; {a.category}{a.distance_km != null && (" \u00B7 " + a.distance_km + " km")}</div>
                  <RiskPill level={a.risk_level} />
                </div>
              ))}
            </div>
          </div>
        )}

        {(() => {
          const insights = prediction ? getSiteInsights(prediction.site_name) : null;
          if (!insights) return null;
          return (
            <div style={{ marginBottom: "28px" }}>
              <div style={sectionTitle}>{t("ldGoodToKnow")}</div>
              <div style={{ padding: "20px", backgroundColor: tokens.surface, border: "1px solid " + tokens.border, borderRadius: tokens.radiusMd }}>
                {insights.highlights.map((h, i) => (
                  <div key={i} style={{ fontSize: "14px", color: tokens.textSecondary, lineHeight: 1.7, marginBottom: "8px" }}>
                    &bull; {h}
                  </div>
                ))}
                {insights.context && (
                  <div style={{ fontSize: "15px", color: tokens.textTertiary, lineHeight: 1.6, marginTop: "12px", paddingTop: "12px", borderTop: "1px solid " + tokens.border }}>
                    {insights.context}
                  </div>
                )}
                {insights.food && (
                  <div style={{ fontSize: "15px", color: tokens.textTertiary, lineHeight: 1.6, marginTop: "10px" }}>
                    <strong style={{ color: tokens.textSecondary }}>{t("ldFood")} </strong>{insights.food}
                  </div>
                )}
              </div>
            </div>
          );
        })()}

        {(() => {
          const insights = prediction ? getSiteInsights(prediction.site_name) : null;
          if (!insights) return null;
          if (!insights.activities && !insights.recommendedDuration && !insights.dressCode && !insights.safety) return null;
          const subHeader = { fontSize: "14px", fontWeight: 600, color: tokens.textTertiary, textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: "8px", display: "flex", alignItems: "center", gap: "6px" };
          const divider = { borderTop: "1px solid " + tokens.border, marginTop: "16px", paddingTop: "16px" };
          return (
            <div style={{ marginBottom: "28px", animation: "fadeUp 0.5s cubic-bezier(0.16, 1, 0.3, 1) both" }}>
              <div style={sectionTitle}>{t("ldVisitorEssentials")}</div>
              <div style={{ padding: "24px", backgroundColor: tokens.surface, border: "1px solid " + tokens.border, borderRadius: tokens.radiusMd }}>
                {insights.recommendedDuration && (
                  <div>
                    <div style={subHeader}><Clock size={13} /> {t("ldRecommendedVisit")}</div>
                    <div style={{ fontSize: "16px", fontWeight: 700, color: tokens.textPrimary }}>{insights.recommendedDuration}</div>
                  </div>
                )}
                {insights.activities && (
                  <div style={insights.recommendedDuration ? divider : {}}>
                    <div style={subHeader}><Compass size={13} /> {t("ldThingsToDo")}</div>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
                      {insights.activities.map((act, i) => (
                        <span key={i} style={{ fontSize: "15px", padding: "6px 12px", borderRadius: "999px", backgroundColor: tokens.accentSoft, border: "1px solid " + tokens.accentBorder, color: tokens.textSecondary, animation: `fadeUp 0.4s cubic-bezier(0.16, 1, 0.3, 1) ${i * 0.06}s both` }}>{act}</span>
                      ))}
                    </div>
                  </div>
                )}
                {insights.dressCode && (
                  <div style={(insights.recommendedDuration || insights.activities) ? divider : {}}>
                    <div style={subHeader}><Shirt size={13} /> {t("ldWhatToWear")}</div>
                    <div style={{ fontSize: "14px", color: tokens.textSecondary, lineHeight: 1.6 }}>{insights.dressCode}</div>
                  </div>
                )}
                {insights.safety && (
                  <div style={(insights.recommendedDuration || insights.activities || insights.dressCode) ? divider : {}}>
                    <div style={subHeader}><ShieldAlert size={13} /> {t("ldGoodToKnowBeforeGo")}</div>
                    <div style={{ padding: "14px 16px", backgroundColor: tokens.surfaceAlt, border: "1px solid " + tokens.border, borderRadius: tokens.radiusSm }}>
                      {insights.safety.map((s, i) => (
                        <div key={i} style={{ fontSize: "15px", color: tokens.textSecondary, lineHeight: 1.6, marginBottom: i < insights.safety.length - 1 ? "4px" : 0 }}>&bull; {s}</div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        })()}
          <div style={sectionTitle}>{t("ldYourFeedback")}</div>
          <FeedbackForm siteId={siteId} date={date} onSaved={() => setFeedbackRefresh((n) => n + 1)} />
          <FeedbackList siteId={siteId} refreshKey={feedbackRefresh} />
      </div>
    </div>
  );
}

const sectionTitle = { fontSize: "14px", fontWeight: 700, color: tokens.textTertiary, textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: "12px" };