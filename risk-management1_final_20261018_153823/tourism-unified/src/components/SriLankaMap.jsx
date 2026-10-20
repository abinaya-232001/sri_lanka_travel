import React, { useEffect, useRef, useState } from "react";
import { useSiteI18n } from "@shared/i18n/react";
import { tokens, riskColors } from "../design/tokens";
import { api } from "../api/client";
import { useApi } from "../hooks/useApi";

const PRESSURE_KEYS = {
  Low: "ldRiskLow",
  Moderate: "ldPressureModerate",
  High: "ldRiskHigh",
  Critical: "ldPressureCritical",
  Unknown: "ldRiskUnknown",
};

// One source of truth for map markers AND legend dots.
const LEVEL_COLORS = {
  Low: "#2A9D8F",
  Moderate: "#E9C46A",
  High: "#F57C00",
  Critical: "#B71C1C",
};
const LEVEL_RANK = { Unknown: 0, Low: 1, Moderate: 2, High: 3, Critical: 4 };

export default function SriLankaMap() {
  const { t } = useSiteI18n();
  const containerRef = useRef(null);
  const mapRef = useRef(null);
  const [date] = useState(new Date().toISOString().split("T")[0]);
  const { data: sitesData } = useApi(() => api.sites(), []);
  const { data: pressureData } = useApi(() => api.tourismPressure(), []);

  const [leafletReady, setLeafletReady] = useState(Boolean(window.L));
  useEffect(() => {
    if (window.L) {
      setLeafletReady(true);
      return undefined;
    }
    const timer = window.setInterval(() => {
      if (window.L) {
        setLeafletReady(true);
        window.clearInterval(timer);
      }
    }, 80);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    if (!leafletReady || !window.L || !containerRef.current || !sitesData || !sitesData.sites) return;
    if (mapRef.current) { mapRef.current.remove(); mapRef.current = null; }

    const map = window.L.map(containerRef.current, { scrollWheelZoom: true }).setView([7.6, 80.9], 7);
    window.L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "&copy; OpenStreetMap contributors",
      maxZoom: 12,
    }).addTo(map);

    const pressureBySite = {};
    if (pressureData && pressureData.sites) {
      pressureData.sites.forEach((s) => { pressureBySite[s.site_id] = s; });
    }

    const levelOf = (site) => {
      const p = pressureBySite[site.site_id];
      return p ? p.pressure_level : "Unknown";
    };
    // Draw low levels first so Critical markers end up on top.
    const ordered = sitesData.sites.slice().sort((a, b) => (LEVEL_RANK[levelOf(a)] || 0) - (LEVEL_RANK[levelOf(b)] || 0));

    ordered.forEach((site) => {
      if (!site.latitude || !site.longitude) return;
      const pressure = pressureBySite[site.site_id];
      const level = pressure ? pressure.pressure_level : "Unknown";
      const color = LEVEL_COLORS[level] || tokens.textFaint;
      const levelLabel = t(PRESSURE_KEYS[level] || "ldRiskUnknown");

      const marker = window.L.circleMarker([site.latitude, site.longitude], {
        radius: 7, color: "#ffffff", fillColor: color, fillOpacity: 0.85, weight: 1.5,
      }).addTo(map);

      marker.bindPopup(
        "<strong>" + site.site_name + "</strong><br/>" +
        site.district + " &middot; " + site.category + "<br/>" +
        t("ldTourismPressure") + " " + levelLabel +
        (pressure ? " (" + Math.round(pressure.pressure_ratio * 100) + "%)" : "")
      );
    });

    mapRef.current = map;
    return () => { if (mapRef.current) { mapRef.current.remove(); mapRef.current = null; } };
  }, [leafletReady, sitesData, pressureData, t]);

  return (
    <div style={{ backgroundColor: tokens.surface, border: "1px solid " + tokens.border, borderRadius: tokens.radiusLg, overflow: "hidden", boxShadow: tokens.shadowSm }}>
      <div style={{ padding: "18px 22px", borderBottom: "1px solid " + tokens.border, display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px" }}>
        <div>
          <div style={{ fontSize: "22px", fontWeight: 600, color: tokens.textPrimary }}>{t("ldMapTitle")}</div>
          <div style={{ fontSize: "16px", color: "#1C1917", marginTop: "4px" }}>
            {t("ldMapSubtitle")}
          </div>
        </div>
        <div style={{ display: "flex", gap: "14px", fontSize: "15px", color: "#1C1917" }}>
          <LegendDot color={LEVEL_COLORS.Low} label={t("ldRiskLow")} />
          <LegendDot color={LEVEL_COLORS.Moderate} label={t("ldPressureModerate")} />
          <LegendDot color={LEVEL_COLORS.High} label={t("ldRiskHigh")} />
          <LegendDot color={LEVEL_COLORS.Critical} label={t("ldPressureCritical")} />
        </div>
      </div>
      <div ref={containerRef} style={{ height: "480px" }} />
    </div>
  );
}

function LegendDot({ color, label }) {
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: "5px" }}>
      <span style={{ width: "8px", height: "8px", borderRadius: "50%", backgroundColor: color }} />
      {label}
    </span>
  );
}
