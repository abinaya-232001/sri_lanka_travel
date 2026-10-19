import React from "react";
import { useSiteI18n } from "@shared/i18n/react";
import { tokens } from "../design/tokens";
import { api } from "../api/client";
import { useApi } from "../hooks/useApi";

function useAnimatedNumber(target, duration) {
  const [value, setValue] = React.useState(0);
  React.useEffect(() => {
    if (target == null) return;
    const t0 = performance.now();
    let raf;
    function step(now) {
      const p = Math.min(1, (now - t0) / duration);
      const eased = 1 - Math.pow(1 - p, 3);
      setValue(Math.round(target * eased));
      if (p < 1) raf = requestAnimationFrame(step);
    }
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [target, duration]);
  return value;
}

function StatBlock({ label, value, suffix }) {
  return (
    <div style={{ textAlign: "center" }}>
      <div style={{ fontSize: "38px", fontWeight: 800, color: "#1C1917", fontFamily: tokens.mono, letterSpacing: "-0.02em" }}>
        {value}{suffix || ""}
      </div>
      <div style={{ fontSize: "12.5px", color: "#6B625A", marginTop: "6px", textTransform: "uppercase", letterSpacing: "0.08em", fontWeight: 700 }}>
        {label}
      </div>
    </div>
  );
}

function StepCard({ number, title, text }) {
  return (
    <div style={{ flex: "1 1 260px", padding: "28px 24px", backgroundColor: tokens.surface, border: "1px solid " + tokens.border, borderRadius: tokens.radiusLg, boxShadow: tokens.shadowSm }}>
      <div style={{ width: "34px", height: "34px", borderRadius: "10px", backgroundColor: tokens.accentSoft, color: tokens.accent, display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 800, fontSize: "14px", marginBottom: "16px" }}>
        {number}
      </div>
      <div style={{ fontSize: "15.5px", fontWeight: 700, color: tokens.textPrimary, marginBottom: "8px" }}>
        {title}
      </div>
      <div style={{ fontSize: "13.5px", color: tokens.textSecondary, lineHeight: 1.6 }}>
        {text}
      </div>
    </div>
  );
}

function FeatureCard({ title, text }) {
  return (
    <div style={{ flex: "1 1 260px", padding: "28px 24px", backgroundColor: tokens.surfaceAlt, borderRadius: tokens.radiusLg, border: "1px solid " + tokens.border }}>
      <div style={{ fontSize: "15px", fontWeight: 700, color: tokens.textPrimary, marginBottom: "8px" }}>
        {title}
      </div>
      <div style={{ fontSize: "13.5px", color: tokens.textSecondary, lineHeight: 1.6 }}>
        {text}
      </div>
    </div>
  );
}

export default function Home({ onGetStarted }) {
  const { t } = useSiteI18n();
  const { data: sitesData } = useApi(() => api.sites(), []);

  const siteCount = sitesData && sitesData.sites ? sitesData.sites.length : null;

  const animatedSites = useAnimatedNumber(siteCount, 900);

  return (
    <div style={{ minHeight: "100%", background: tokens.bgGradient, color: tokens.textPrimary, fontFamily: tokens.font }}>
      <div style={{ maxWidth: "1100px", margin: "0 auto", padding: "84px 32px 40px", textAlign: "center" }}>
        <div className="ld-read-panel">
          <h1 style={{ fontSize: "clamp(38px, 6vw, 64px)", fontWeight: 800, letterSpacing: "-0.03em", lineHeight: 1.05, margin: "0 0 20px", color: "#1C1917" }}>
            {t("ldKnowBefore")}{" "}
            <span style={{ color: "#BF7E46" }}>
              {t("ldEveryTime")}
            </span>
          </h1>
          <p style={{ fontSize: "17px", color: "#6B625A", maxWidth: "600px", margin: "0 auto 36px", lineHeight: 1.6, fontWeight: 550 }}>
            {t("ldHeroBodyDetail")}
          </p>
          <div style={{ display: "flex", gap: "14px", justifyContent: "center", flexWrap: "wrap", marginBottom: "28px" }}>
            <button
              onClick={onGetStarted}
              style={{ padding: "14px 30px", background: "#BF7E46", color: "#FFF8F2", border: "none", borderRadius: tokens.radiusSm, fontSize: "14.5px", fontWeight: 700, cursor: "pointer", boxShadow: "0 10px 26px rgba(191,126,70,0.28)" }}
            >
              {t("ldExploreDestinations")}
            </button>
            <a
              href="#how-it-works"
              className="ld-ghost-btn"
              style={{ padding: "14px 30px", borderRadius: tokens.radiusSm, fontSize: "14.5px", fontWeight: 700, cursor: "pointer", textDecoration: "none", display: "inline-flex", alignItems: "center" }}
            >
              {t("ldSeeHowItWorks")}
            </a>
          </div>

          <div style={{ display: "flex", justifyContent: "center", gap: "56px", flexWrap: "wrap", padding: "22px 0 0", borderTop: "1px solid rgba(13, 44, 48, 0.12)" }}>
            <StatBlock label={t("ldSitesMonitored")} value={siteCount != null ? animatedSites : "\u2014"} />
          </div>
        </div>
      </div>

      <div id="how-it-works" style={{ maxWidth: "1100px", margin: "0 auto", padding: "64px 32px" }}>
        <div className="ld-read-panel ld-read-panel--tight" style={{ textAlign: "center", marginBottom: "40px" }}>
          <div style={{ fontSize: "12px", fontWeight: 700, color: "#BF7E46", textTransform: "uppercase", letterSpacing: "0.12em", marginBottom: "10px" }}>
            {t("ldHowItWorks")}
          </div>
          <h2 style={{ fontSize: "clamp(24px, 3vw, 32px)", fontWeight: 800, letterSpacing: "-0.02em", margin: 0, color: "#1C1917" }}>
            {t("ldThreeSteps")}
          </h2>
        </div>
        <div style={{ display: "flex", gap: "20px", flexWrap: "wrap" }}>
          <StepCard number="1" title={t("ldStep1Title")} text={t("ldStep1Text")} />
          <StepCard number="2" title={t("ldStep2Title")} text={t("ldStep2Text")} />
          <StepCard number="3" title={t("ldStep3Title")} text={t("ldStep3Text")} />
        </div>
      </div>

      <div style={{ maxWidth: "1100px", margin: "0 auto", padding: "24px 32px 72px" }}>
        <div style={{ display: "flex", gap: "20px", flexWrap: "wrap" }}>
          <FeatureCard title={t("ldFeatureExplainTitle")} text={t("ldFeatureExplainText")} />
          <FeatureCard title={t("ldFeatureUncertaintyTitle")} text={t("ldFeatureUncertaintyText")} />
          <FeatureCard title={t("ldFeatureRankingTitle")} text={t("ldFeatureRankingText")} />
        </div>
      </div>

      <div style={{ padding: "32px", textAlign: "center" }}>
        <div className="ld-read-panel ld-read-panel--tight" style={{ fontSize: "12.5px", color: "#6B625A", display: "inline-block" }}>
          {t("ldFooterTagline")}
        </div>
      </div>
    </div>
  );
}
