import React, { useState, useEffect, useRef } from "react";
import { useSiteI18n } from "@shared/i18n/react";
import "../../design/animations.css";
import { tokens, riskColors } from "../../design/tokens";
import { api } from "../../api/client";
import { useApi } from "../../hooks/useApi";
import CrowdChip, { crowdPhraseKey } from "../../components/CrowdChip";
import { useFavorites } from "../../hooks/useFavorites";
import { useWeather, tourismWeatherAdvice } from "../../hooks/useWeather";
import SriLankaMap from "../../components/SriLankaMap";
import { siteImagePath } from "../../utils/siteImage";

const RISK_OPTIONS = [
  { value: "Low", labelKey: "ldRiskLow" },
  { value: "Medium", labelKey: "ldRiskMedium" },
  { value: "High", labelKey: "ldRiskHigh" },
];
const CATEGORY_LABEL_KEYS = {
  Beach: "ldCatLabelBeach",
  Nature: "ldCatLabelNature",
  Heritage: "ldCatLabelHeritage",
  Religious: "ldCatLabelReligious",
};
const OUTDOOR_CATEGORIES = ["Beach", "Nature", "Wildlife"];
const CATEGORY_OPTIONS = [
  { value: "Beach", labelKey: "ldCatBeach" },
  { value: "Nature", labelKey: "ldCatNature" },
  { value: "Heritage", labelKey: "ldCatHeritage" },
  { value: "Religious", labelKey: "ldCatReligious" },
  { value: "Wildlife", labelKey: "ldCatWildlife" },
  { value: "Landmark", labelKey: "ldCatLandmark" },
  { value: "Leisure", labelKey: "ldCatLeisure" },
];
const REFERENCE_LOCATION = { latitude: 6.9271, longitude: 79.8612, label: "Colombo" };

const SEARCH_CATEGORY_WORDS = {
  beach: "Beach", beaches: "Beach",
  nature: "Nature", forest: "Nature", lake: "Nature", falls: "Nature", waterfall: "Nature",
  heritage: "Heritage", historic: "Heritage", historical: "Heritage", ancient: "Heritage",
  religious: "Religious", temple: "Religious", shrine: "Religious",
  wildlife: "Wildlife", safari: "Wildlife", park: "Wildlife",
};
const SEARCH_CROWD_WORDS = {
  quiet: "Low", low: "Low", empty: "Low", peaceful: "Low",
  busy: "High", crowded: "High", popular: "High",
};

function parseSearchQuery(query) {
  const words = query.toLowerCase().split(/\s+/).filter(Boolean);
  let category = null;
  let crowdLevel = null;
  const textWords = [];
  for (const w of words) {
    if (SEARCH_CATEGORY_WORDS[w]) { category = SEARCH_CATEGORY_WORDS[w]; continue; }
    if (SEARCH_CROWD_WORDS[w]) { crowdLevel = SEARCH_CROWD_WORDS[w]; continue; }
    textWords.push(w);
  }
  return { category, crowdLevel, text: textWords.join(" ") };
}

function matchesSearch(site, parsed) {
  if (parsed.category && site.category !== parsed.category) return false;
  if (parsed.crowdLevel && site.risk_level !== parsed.crowdLevel) return false;
  if (parsed.text) {
    const haystack = ((site.site_name || "") + " " + (site.district || "")).toLowerCase();
    if (!haystack.includes(parsed.text)) return false;
  }
  return true;
}

function useAnimatedNumber(target, duration) {
  const [value, setValue] = useState(target);
  const prevRef = useRef(target);
  useEffect(() => {
    const start = prevRef.current;
    const diff = target - start;
    if (diff === 0) return;
    const t0 = performance.now();
    let raf;
    function step(now) {
      const p = Math.min(1, (now - t0) / duration);
      const eased = 1 - Math.pow(1 - p, 3);
      setValue(Math.round(start + diff * eased));
      if (p < 1) raf = requestAnimationFrame(step);
      else prevRef.current = target;
    }
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [target, duration]);
  return value;
}

function SkeletonCard() {
  return (
    <div className="sj-skeleton" style={{ height: "300px", borderRadius: tokens.radiusXl, border: "1px solid " + tokens.border }} />
  );
}

function FilterPill({ active, onClick, children }) {
  return (
    <button
      onClick={onClick}
      style={{
        padding: "8px 16px",
        borderRadius: "999px",
        border: "1px solid " + (active ? tokens.accentBorder : tokens.border),
        backgroundColor: active ? tokens.accentSoft : "transparent",
        color: active ? tokens.accent : tokens.textSecondary,
        fontSize: "15px",
        fontWeight: 600,
        cursor: "pointer",
        transition: "all 0.2s " + tokens.easeOut,
        fontFamily: tokens.font,
        whiteSpace: "nowrap",
      }}
    >
      {children}
    </button>
  );
}

function DestinationCard({ site, index, isTopPick, onClick, date, isFavorite, onToggleFavorite, isComparing, onToggleCompare }) {
  const { t } = useSiteI18n();
  const [hovered, setHovered] = useState(false);
  const [imgFailed, setImgFailed] = useState(false);
  const [uncertainty, setUncertainty] = useState(null);
  const [uncertaintyFetched, setUncertaintyFetched] = useState(false);

  useEffect(() => {
    setImgFailed(false);
  }, [site.image]);

  useEffect(() => {
    if (hovered && !uncertaintyFetched && site.site_id && date) {
      setUncertaintyFetched(true);
      api.uncertainty(site.site_id, date)
        .then((res) => setUncertainty(res))
        .catch(() => setUncertainty(null));
    }
  }, [hovered, uncertaintyFetched, site.site_id, date]);
  const c = riskColors(site.risk_level);
  const catLabel = t(CATEGORY_LABEL_KEYS[site.category] || "ldCatLabelSite");

  return (
    <div
      onClick={onClick}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        position: "relative",
        height: "300px",
        borderRadius: tokens.radiusXl,
        overflow: "hidden",
        cursor: "pointer",
        border: "1px solid " + (isTopPick ? tokens.accentBorder : (hovered ? tokens.borderStrong : tokens.border)),
        backgroundColor: tokens.surface,
        boxShadow: hovered ? ("0 20px 48px -12px " + c.text.replace(")", ",0.35)").replace("rgb", "rgba")) : tokens.shadowSm,
        transform: hovered ? "translateY(-6px)" : "translateY(0)",
        transition: "all 0.4s " + tokens.easeOut,
        animation: "fadeUp 0.6s " + tokens.easeOut + " both",
        animationDelay: (Math.min(index, 20) * 0.05) + "s",
      }}
    >
      {isTopPick && (
        <div style={{ position: "absolute", top: "16px", left: "16px", zIndex: 2, padding: "4px 10px", borderRadius: "999px", backgroundColor: tokens.accentBright, fontSize: "14px", fontWeight: 800, letterSpacing: "0.06em", color: "#FFFFFF" }}>
          {t("ldBestPick")}
        </div>
      )}
      <button
        onClick={(e) => { e.stopPropagation(); onToggleFavorite(site.site_id); }}
        style={{ position: "absolute", top: isTopPick ? "56px" : "16px", right: "16px", left: "auto", zIndex: 3, width: "32px", height: "32px", borderRadius: "50%", border: "none", backgroundColor: "rgba(15,23,42,0.55)", backdropFilter: "blur(4px)", color: isFavorite ? "#FBBF24" : "#FFFFFF", fontSize: "16px", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}
        aria-label={isFavorite ? t("ldRemoveFavorite") : t("ldAddFavorite")}
      >
        {isFavorite ? "\u2605" : "\u2606"}
      </button>
      <button
        onClick={(e) => { e.stopPropagation(); onToggleCompare(site.site_id); }}
        style={{ position: "absolute", top: isTopPick ? "96px" : "56px", right: "16px", left: "auto", zIndex: 3, padding: "5px 10px", borderRadius: "999px", border: "1px solid " + (isComparing ? "rgba(191,126,70,0.7)" : "rgba(255,255,255,0.35)"), backgroundColor: isComparing ? "#BF7E46" : "rgba(15,23,42,0.55)", backdropFilter: "blur(4px)", color: "#FFFFFF", fontSize: "14px", fontWeight: 700, cursor: "pointer" }}
      >
        {isComparing ? "\u2713 " + t("ldComparing") : "+ " + t("ldCompare")}
      </button>
      {!imgFailed ? (
        <img
          src={site.image}
          alt={site.name}
          style={{
            position: "absolute",
            inset: 0,
            width: "100%",
            height: "100%",
            objectFit: "cover",
            transform: hovered ? "scale(1.08)" : "scale(1)",
            transition: "transform 0.7s " + tokens.easeOut,
          }}
          onError={() => setImgFailed(true)}
        />
      ) : (
        <div
          style={{
            position: "absolute",
            inset: 0,
            background: "radial-gradient(circle at 30% 20%, rgba(20,184,166,0.18), transparent 60%), linear-gradient(160deg, #EFF5F4 0%, #FFFFFF 100%)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <span style={{ fontSize: "15px", fontWeight: 800, letterSpacing: "0.15em", color: tokens.textFaint }}>
            {catLabel}
          </span>
        </div>
      )}
      <div style={{ position: "absolute", inset: 0, background: "linear-gradient(to top, rgba(15,23,42,0.85) 0%, rgba(15,23,42,0.25) 55%, rgba(15,23,42,0.0) 100%)" }} />
      {!isTopPick && (
        <div style={{ position: "absolute", top: "16px", right: "16px", width: "10px", height: "10px", borderRadius: "50%", backgroundColor: c.text, boxShadow: c.glow }} />
      )}
      <div style={{ position: "absolute", top: "16px", left: isTopPick ? "auto" : "16px", right: isTopPick ? "16px" : "auto", padding: "4px 10px", borderRadius: "999px", backgroundColor: "rgba(255,255,255,0.85)", backdropFilter: "blur(6px)", fontSize: "14px", fontWeight: 700, letterSpacing: "0.06em", color: tokens.textSecondary, border: "1px solid " + tokens.border }}>
        {catLabel}
      </div>
      <div style={{ position: "absolute", bottom: 0, left: 0, right: 0, padding: "22px" }}>
        <div style={{ fontSize: "14px", fontWeight: 700, color: tokens.accentBright, textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: "8px" }}>
          {site.region}
        </div>
        <div style={{ fontSize: "19px", fontWeight: 800, color: "#FFFFFF", marginBottom: "6px", letterSpacing: "-0.01em" }}>
          {site.name}
        </div>
        <div style={{ fontSize: "15px", color: "rgba(255,255,255,0.75)", marginBottom: "10px" }}>
          {t(crowdPhraseKey(site.crowd_score))}
        </div>
        <CrowdChip score={site.crowd_score} level={site.risk_level} />
        {uncertainty && Array.isArray(uncertainty.prediction_interval_10_90) && (
          <div style={{ fontSize: "14px", color: "rgba(255,255,255,0.65)", marginTop: "6px" }}>
            {t("ldTypicalRange")} {Math.round(uncertainty.prediction_interval_10_90[0] * 100)}% - {Math.round(uncertainty.prediction_interval_10_90[1] * 100)}%
          </div>
        )}
      </div>
    </div>
  );
}

function SearchableDistrictSelect({ districts, value, onChange, placeholder }) {
  const { t } = useSiteI18n();
  const resolvedPlaceholder = placeholder || t("ldAllDistricts");
  const [query, setQuery] = useState(value === "All" ? "" : value);
  const [isOpen, setIsOpen] = useState(false);
  const [highlightIndex, setHighlightIndex] = useState(-1);
  const wrapperRef = useRef(null);
  const inputRef = useRef(null);

  const options = ["All", ...districts];
  const filtered = query.trim() === "" || query === "All"
    ? options
    : options.filter(d => d.toLowerCase().includes(query.toLowerCase()));

  useEffect(() => {
    function handleClickOutside(e) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
        setIsOpen(false);
        setQuery(value === "All" ? "" : value);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [value]);

  useEffect(() => {
    setQuery(value === "All" ? "" : value);
  }, [value]);

  function selectOption(opt) {
    onChange(opt);
    setQuery(opt === "All" ? "" : opt);
    setIsOpen(false);
    setHighlightIndex(-1);
    if (inputRef.current) inputRef.current.blur();
  }

  function handleKeyDown(e) {
    if (!isOpen && (e.key === "ArrowDown" || e.key === "Enter")) {
      setIsOpen(true);
      return;
    }
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setHighlightIndex(i => Math.min(i + 1, filtered.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setHighlightIndex(i => Math.max(i - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (highlightIndex >= 0 && filtered[highlightIndex]) {
        selectOption(filtered[highlightIndex]);
      } else if (filtered.length === 1) {
        selectOption(filtered[0]);
      }
    } else if (e.key === "Escape") {
      setIsOpen(false);
      setQuery(value === "All" ? "" : value);
      if (inputRef.current) inputRef.current.blur();
    }
  }

  return (
    <div ref={wrapperRef} style={{ position: "relative", width: "100%" }}>
      <input
        ref={inputRef}
        type="text"
        value={query}
        placeholder={resolvedPlaceholder}
        onFocus={() => setIsOpen(true)}
        onChange={(e) => {
          setQuery(e.target.value);
          setIsOpen(true);
          setHighlightIndex(-1);
        }}
        onKeyDown={handleKeyDown}
        style={{
          width: "100%",
          padding: "10px 12px",
          borderRadius: "8px",
          border: "1px solid rgba(0,0,0,0.15)",
          background: "#ffffff",
          color: "#1a1a1a",
          fontSize: "14px",
          outline: "none",
          boxSizing: "border-box"
        }}
      />
      {isOpen && filtered.length > 0 && (
        <ul style={{
          position: "absolute",
          top: "calc(100% + 4px)",
          left: 0,
          right: 0,
          maxHeight: "220px",
          overflowY: "auto",
          margin: 0,
          padding: "4px",
          listStyle: "none",
          background: "#ffffff",
          border: "1px solid rgba(0,0,0,0.15)",
          borderRadius: "8px",
          zIndex: 50,
          boxShadow: "0 8px 24px rgba(0,0,0,0.18)"
        }}>
          {filtered.map((opt, i) => (
            <li
              key={opt}
              onMouseDown={() => selectOption(opt)}
              onMouseEnter={() => setHighlightIndex(i)}
              style={{
                padding: "8px 10px",
                borderRadius: "6px",
                cursor: "pointer",
                fontSize: "14px",
                color: "#1a1a1a",
                background: i === highlightIndex ? "rgba(0,0,0,0.06)" : "transparent"
              }}
            >
              {opt}
            </li>
          ))}
        </ul>
      )}
      {isOpen && filtered.length === 0 && (
        <div style={{
          position: "absolute", top: "calc(100% + 4px)", left: 0, right: 0,
          padding: "10px 12px", background: "#ffffff", border: "1px solid rgba(0,0,0,0.15)",
          borderRadius: "8px", color: "rgba(0,0,0,0.45)", fontSize: "15px", zIndex: 50
        }}>
          {t("ldNoMatchingDistricts")}
        </div>
      )}
    </div>
  );
}

function ComparisonBar({ compareIds, sites, onClear, onRemove }) {
  const { t } = useSiteI18n();
  const [expanded, setExpanded] = useState(false);
  const selected = compareIds.map((id) => sites.find((s) => s.site_id === id)).filter(Boolean);
  if (selected.length === 0) return null;
  return (
    <div style={{ position: "fixed", left: 0, right: 0, bottom: 0, zIndex: 40, padding: "16px 24px", backgroundColor: "#0F172A", color: "#FFFFFF" }}>
      {!expanded ? (
        <div style={{ display: "flex", alignItems: "center", gap: "14px", flexWrap: "wrap", maxWidth: "1280px", margin: "0 auto" }}>
          <span style={{ fontSize: "15px", fontWeight: 700 }}>{t("ldSelectedToCompare").replace("{count}", selected.length)}</span>
          {selected.map((s) => (
            <span key={s.site_id} style={{ display: "flex", alignItems: "center", gap: "6px", padding: "5px 10px", borderRadius: "999px", backgroundColor: "rgba(255,255,255,0.12)", fontSize: "14px" }}>
              {s.site_name}
              <button onClick={() => onRemove(s.site_id)} style={{ background: "none", border: "none", color: "#FFFFFF", cursor: "pointer", fontSize: "14px", padding: 0 }}>&times;</button>
            </span>
          ))}
          <button onClick={() => setExpanded(true)} disabled={selected.length < 2} style={{ marginLeft: "auto", padding: "9px 18px", borderRadius: "8px", border: "none", backgroundColor: selected.length < 2 ? "rgba(255,255,255,0.15)" : "#BF7E46", color: "#FFFFFF", fontWeight: 700, fontSize: "15px", cursor: selected.length < 2 ? "not-allowed" : "pointer" }}>
            {selected.length < 2 ? t("ldComparePickTwo") : t("ldCompare")}
          </button>
          <button onClick={onClear} style={{ padding: "9px 14px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.3)", backgroundColor: "transparent", color: "#FFFFFF", fontSize: "15px", cursor: "pointer" }}>{t("clear")}</button>
        </div>
      ) : (
        <div style={{ maxWidth: "1280px", margin: "0 auto" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px" }}>
            <span style={{ fontSize: "15px", fontWeight: 700 }}>{t("ldComparingDestinations").replace("{count}", selected.length)}</span>
            <button onClick={() => setExpanded(false)} style={{ background: "none", border: "none", color: "#FFFFFF", cursor: "pointer", fontSize: "15px" }}>{t("close")} &times;</button>
          </div>
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "15px" }}>
              <thead>
                <tr>
                  <td style={{ padding: "8px 12px", color: "rgba(255,255,255,0.6)" }}></td>
                  {selected.map((s) => (
                    <td key={s.site_id} style={{ padding: "8px 12px", fontWeight: 700 }}>{s.site_name}</td>
                  ))}
                </tr>
              </thead>
              <tbody>
                {[
                  [t("ldCompareTableDistrict"), (s) => s.district],
                  [t("ldCompareTableCategory"), (s) => s.category],
                  [t("ldCompareTableCrowd"), (s) => Math.round(s.crowd_score * 100) + "%"],
                  [t("ldCompareTableRisk"), (s) => s.risk_level],
                ].map(([label, getVal]) => (
                  <tr key={label} style={{ borderTop: "1px solid rgba(255,255,255,0.15)" }}>
                    <td style={{ padding: "8px 12px", color: "rgba(255,255,255,0.6)" }}>{label}</td>
                    {selected.map((s) => (
                      <td key={s.site_id} style={{ padding: "8px 12px" }}>{getVal(s)}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div style={{ fontSize: "14px", color: "rgba(255,255,255,0.5)", marginTop: "10px" }}>
            {t("ldCompareFootnote")}
          </div>
        </div>
      )}
    </div>
  );
}

export default function Discover({ onSelectSite }) {
  const { t } = useSiteI18n();
  const [date, setDate] = useState(new Date().toISOString().split("T")[0]);
  const [riskTolerance, setRiskTolerance] = useState("High");
  const [maxFee, setMaxFee] = useState("");
  const [showFavoritesOnly, setShowFavoritesOnly] = useState(false);
  const [districtFilter, setDistrictFilter] = useState("All");
    const [sortBy, setSortBy] = useState("default"); // "default" | "asc" | "desc"
  const [searchQuery, setSearchQuery] = useState("");
  const [compareIds, setCompareIds] = useState([]);
  const toggleCompare = (id) => setCompareIds((prev) => prev.includes(id) ? prev.filter((x) => x !== id) : (prev.length < 3 ? [...prev, id] : prev));
  const { isFavorite, toggleFavorite } = useFavorites();
  const [rainFriendlyOnly, setRainFriendlyOnly] = useState(false);
  const [categoryFilters, setCategoryFilters] = useState([]);
  const { weather: refWeather } = useWeather(REFERENCE_LOCATION.latitude, REFERENCE_LOCATION.longitude);
  const rainLikely = refWeather && refWeather.rain_probability_percent != null && refWeather.rain_probability_percent >= 40;

  const [notifPermission, setNotifPermission] = useState(
    typeof Notification !== "undefined" ? Notification.permission : "unsupported"
  );
  const lastNotifiedDateRef = useRef(null);

  const enableAlerts = () => {
    if (typeof Notification === "undefined") return;
    Notification.requestPermission().then(setNotifPermission);
  };

  const { data, loading, error, refetch } = useApi(
    () => api.personalizedRanking({ date, riskTolerance, maxFee: maxFee ? Number(maxFee) : undefined, limit: 0 }),
    [date, riskTolerance, maxFee]
  );

  const allSites = data && data.ranking ? data.ranking : [];
  const districts = ["All", ...Array.from(new Set(allSites.map(s => s.district).filter(Boolean))).sort()];

  useEffect(() => {
    if (notifPermission !== "granted" || !data || !data.ranking) return;
    if (lastNotifiedDateRef.current === date) return;
    const highCount = data.ranking.filter((s) => s.risk_level === "High").length;
    if (highCount > 0) {
      const bodyKey = highCount === 1 ? "ldNotifCrowdedSingular" : "ldNotifCrowdedPlural";
      new Notification(t("ldCrowdAlert"), {
        body: t(bodyKey).replace("{count}", highCount),
        icon: "/favicon.ico",
      });
    }
    lastNotifiedDateRef.current = date;
  }, [data, date, notifPermission]);
  const parsedSearch = parseSearchQuery(searchQuery);
  const sites = (showFavoritesOnly ? allSites.filter(s => isFavorite(s.site_id)) : allSites).filter(s => districtFilter === "All" || s.district === districtFilter).filter(s => !rainFriendlyOnly || !OUTDOOR_CATEGORIES.includes(s.category)).filter(s => categoryFilters.length === 0 || categoryFilters.includes(s.category)).filter(s => matchesSearch(s, parsedSearch));
    const sortedSites = sortBy === "default" ? sites : [...sites].sort((a, b) =>
      sortBy === "asc" ? (a.crowd_score - b.crowd_score) : (b.crowd_score - a.crowd_score));
  const totalMatching = showFavoritesOnly ? sites.length : (data && data.total_matching != null ? data.total_matching : sites.length);
  const animatedCount = useAnimatedNumber(totalMatching, 500);

  const greatCount = sites.filter((s) => s.risk_level === "Low").length;
  const bestPick = sites.length > 0 ? sites[0].site_name : null;
  const briefing = sites.length === 0
    ? t("ldBriefingNone")
    : bestPick
      ? t(totalMatching === 1 ? "ldBriefingOptionSingular" : "ldBriefingOptionPlural")
          .replace("{count}", totalMatching)
          .replace("{great}", greatCount)
          .replace("{name}", bestPick)
      : t("ldBriefingAvailable");

  return (
    <div style={{ minHeight: "100vh", background: tokens.bgGradient, color: tokens.textPrimary, fontFamily: tokens.font }}>
      <div style={{ maxWidth: "1120px", margin: "0 auto", padding: "8px 28px 64px" }}>
        <div className="ld-read-panel" style={{ marginBottom: "40px", animation: "fadeUp 0.6s " + tokens.easeOut + " both", textAlign: "left" }}>
          <div style={{ display: "inline-flex", alignItems: "center", gap: "8px", padding: "6px 14px", borderRadius: "999px", backgroundColor: "#FDECD8", border: "1px solid rgba(191,126,70,0.35)", fontSize: "14px", fontWeight: 700, color: "#6E4524", letterSpacing: "0.06em", marginBottom: "18px" }}>
            <span style={{ width: "6px", height: "6px", borderRadius: "50%", backgroundColor: "#BF7E46" }} />
            {t("ldAiPowered")} - {animatedCount} {t("ldSitesMatched")}
          </div>
          <h1 style={{ fontSize: "clamp(40px, 4.6vw, 56px)", fontWeight: 600, letterSpacing: "-0.02em", lineHeight: 1.08, margin: "0 0 12px", color: "#1C1917" }}>
            {t("ldWhereShouldYouGo")}{" "}
            <span style={{ color: "#BF7E46" }}>
              {t("ldToday")}
            </span>
          </h1>
          <p style={{ fontSize: "18px", color: "#1C1917", maxWidth: "640px", margin: "0 0 4px", lineHeight: 1.5, fontWeight: 600 }}>
            {briefing}
          </p>
          <p style={{ fontSize: "16px", color: "#1C1917", maxWidth: "640px", margin: 0, lineHeight: 1.5 }}>
            {t("ldDiscoverSubtitle")}
          </p>
        </div>

        <div style={{ marginBottom: "36px", animation: "fadeUp 0.6s " + tokens.easeOut + " 0.05s both" }}>
          <SriLankaMap />
        </div>

        <div style={{ marginBottom: "20px" }}>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder={t("ldSearchPlaceholder")}
            style={{ width: "100%", padding: "14px 18px", borderRadius: tokens.radiusMd, border: "1px solid " + tokens.borderStrong, backgroundColor: tokens.surface, color: tokens.textPrimary, fontSize: "16px", outline: "none", fontFamily: tokens.font, boxSizing: "border-box" }}
          />
          {searchQuery.trim() !== "" && (
            <div style={{ fontSize: "14px", color: tokens.textTertiary, marginTop: "6px" }}>
              {parsedSearch.category && t("ldSearchCategory") + " " + parsedSearch.category + "  "}
              {parsedSearch.crowdLevel && t("ldSearchCrowd") + " " + parsedSearch.crowdLevel + "  "}
              {parsedSearch.text && t("ldSearchMatching") + " \"" + parsedSearch.text + "\""}
            </div>
          )}
        </div>
        <div style={{ display: "flex", gap: "22px", flexWrap: "wrap", alignItems: "flex-end", marginBottom: "36px", padding: "22px 24px", backgroundColor: tokens.glass, backdropFilter: "blur(20px)", border: "1px solid " + tokens.border, borderRadius: tokens.radiusLg, boxShadow: tokens.shadowMd, animation: "fadeUp 0.6s " + tokens.easeOut + " 0.1s both" }}>
          <div>
            <label style={labelStyle}>{t("ldDate")}</label>
            <input type="date" value={date} onChange={(e) => setDate(e.target.value)} style={inputStyle} />
          </div>
          <div>
            <label style={labelStyle}>{t("ldCrowdTolerance")}</label>
            <div style={{ display: "flex", gap: "6px" }}>
              {RISK_OPTIONS.map((r) => (
                <FilterPill key={r.value} active={riskTolerance === r.value} onClick={() => setRiskTolerance(r.value)}>{t(r.labelKey)}</FilterPill>
              ))}
              <FilterPill active={showFavoritesOnly} onClick={() => setShowFavoritesOnly((v) => !v)}>{t("ldFavoritesOnly")}</FilterPill>
              <FilterPill active={rainFriendlyOnly} onClick={() => setRainFriendlyOnly((v) => !v)}>{t("ldRainFriendly")}</FilterPill>
            </div>
          </div>
          <div>
            <label style={labelStyle}>{t("ldExploreByInterest")}</label>
            <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
              {CATEGORY_OPTIONS.map((c) => (
                <FilterPill key={c.value} active={categoryFilters.includes(c.value)} onClick={() => setCategoryFilters((prev) => prev.includes(c.value) ? prev.filter((x) => x !== c.value) : [...prev, c.value])}>{t(c.labelKey)}</FilterPill>
              ))}
            </div>
          </div>
          <div>
            <label style={labelStyle}>{t("ldDistrict")}</label>
              <SearchableDistrictSelect districts={districts.filter(d => d !== "All")} value={districtFilter} onChange={setDistrictFilter} />
          </div>
          <div>
            <label style={labelStyle}>{t("ldSortByCrowd")}</label>
            <button
              onClick={() => setSortBy(sortBy === "asc" ? (sortBy === "desc" ? "default" : "desc") : "asc")}
              style={{ ...inputStyle, cursor: "pointer", textAlign: "left" }}
            >
              {sortBy === "asc" ? t("ldSortLowHigh") : sortBy === "desc" ? t("ldSortHighLow") : t("ldSortDefault")}
            </button>
          </div>
          <div>
            <label style={labelStyle}>{t("ldMaxEntranceFee")}</label>
            <input type="number" placeholder={t("ldAny")} value={maxFee} onChange={(e) => setMaxFee(e.target.value)} style={{ ...inputStyle, width: "110px" }} />
          </div>
          <button onClick={refetch} style={buttonStyle}>{t("ldRefreshResults")}</button>
          {notifPermission === "default" && (
            <button onClick={enableAlerts} style={{ ...buttonStyle, backgroundColor: tokens.surfaceAlt, color: tokens.textPrimary }}>&#128276; {t("ldEnableAlerts")}</button>
          )}
        </div>

        {error && (
          <div style={{ padding: "20px 24px", backgroundColor: tokens.dangerSoft, border: "1px solid " + tokens.dangerBorder, borderRadius: tokens.radiusMd, color: tokens.danger, marginBottom: "24px", fontSize: "14px" }}>
            {t("ldBackendError")} ({error})
          </div>
        )}

        {rainLikely && !rainFriendlyOnly && (
          <div style={{ padding: "14px 20px", backgroundColor: tokens.accentSoft, border: "1px solid " + tokens.accentBorder, borderRadius: tokens.radiusMd, color: tokens.textSecondary, marginBottom: "20px", fontSize: "15px" }}>
            {"\uD83C\uDF27\uFE0F " + t("ldRainLikely").replace("{location}", REFERENCE_LOCATION.label) + " "}
            <button onClick={() => setRainFriendlyOnly(true)} style={{ background: "none", border: "none", padding: 0, color: tokens.accentBright, fontWeight: 700, cursor: "pointer", fontSize: "15px", textDecoration: "underline" }}>
              {t("ldShowRainFriendly")}
            </button>
          </div>
        )}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: "20px" }}>
          {loading && Array.from({ length: 12 }).map((_, i) => <SkeletonCard key={i} />)}
          {!loading && sortedSites.map((site, i) => (
            <DestinationCard
              key={site.site_id}
              index={i}
              isTopPick={i < 3}
              date={date}
              isFavorite={isFavorite(site.site_id)}
              onToggleFavorite={toggleFavorite}
              isComparing={compareIds.includes(site.site_id)}
              onToggleCompare={toggleCompare}
              site={{
                name: site.site_name,
                region: site.district,
                category: site.category,
                crowd_score: site.crowd_score,
                risk_level: site.risk_level,
                site_id: site.site_id,
                image: siteImagePath(site.site_name),
              }}
              onClick={() => onSelectSite && onSelectSite(site.site_id, date)}
            />
          ))}
        </div>

        {!loading && !error && sites.length === 0 && (
          <div style={{ padding: "80px 0", textAlign: "center", color: tokens.textTertiary }}>
            {t("ldNoDestinationsMatch")}
          </div>
        )}
      </div>
      <ComparisonBar compareIds={compareIds} sites={allSites} onClear={() => setCompareIds([])} onRemove={(id) => toggleCompare(id)} />
    </div>
  );
}

const labelStyle = { display: "block", fontSize: "15px", fontWeight: 600, color: "#1C1917", marginBottom: "8px" };
const inputStyle = { padding: "10px 14px", backgroundColor: tokens.surfaceAlt, border: "1px solid " + tokens.borderStrong, borderRadius: tokens.radiusSm, color: tokens.textPrimary, fontSize: "16px", outline: "none", fontFamily: tokens.font };
const buttonStyle = { padding: "11px 22px", background: "#BF7E46", color: "#FFF8F2", border: "none", borderRadius: tokens.radiusSm, fontSize: "15px", fontWeight: 700, cursor: "pointer", boxShadow: "0 8px 20px rgba(191,126,70,0.25)" };