import React, { useState } from "react";
import { useSiteI18n } from "@shared/i18n/react";
import { tokens, riskColors } from "../design/tokens";
import { api } from "../api/client";
import { useApi } from "../hooks/useApi";

const MONTH_KEYS = [
  "ldMonthJan", "ldMonthFeb", "ldMonthMar", "ldMonthApr", "ldMonthMay", "ldMonthJun",
  "ldMonthJul", "ldMonthAug", "ldMonthSep", "ldMonthOct", "ldMonthNov", "ldMonthDec",
];

export default function BestTimeGrid({ siteId, initialMonth }) {
  const { t } = useSiteI18n();
  const [month, setMonth] = useState(initialMonth || new Date().getMonth() + 1);
  const { data, loading } = useApi(() => api.bestTimes(siteId, month), [siteId, month], { skip: !siteId });

  return (
    <div style={{ backgroundColor: tokens.surface, border: "1px solid " + tokens.border, borderRadius: tokens.radiusLg, padding: "22px", boxShadow: tokens.shadowSm }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
        <div style={{ fontSize: "13px", fontWeight: 700, color: tokens.textPrimary }}>{t("ldBestDaysToVisit")}</div>
        <select
          value={month}
          onChange={(e) => setMonth(Number(e.target.value))}
          style={{ padding: "6px 10px", backgroundColor: tokens.surfaceAlt, border: "1px solid " + tokens.borderStrong, borderRadius: tokens.radiusSm, color: tokens.textPrimary, fontSize: "15px", outline: "none" }}
        >
          {MONTH_KEYS.map((key, i) => <option key={key} value={i + 1}>{t(key)}</option>)}
        </select>
      </div>

      {loading && <div style={{ color: tokens.textTertiary, fontSize: "13px" }}>{t("ldLoadingWeeklyPattern")}</div>}

      {data && data.weekly_prediction && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(7, 1fr)", gap: "8px" }}>
          {data.weekly_prediction.map((d) => {
            const c = riskColors(d.risk_level);
            return (
              <div
                key={d.day_num}
                style={{
                  padding: "12px 6px", textAlign: "center", borderRadius: tokens.radiusSm,
                  backgroundColor: c.bg, border: "1px solid " + c.border,
                }}
              >
                <div style={{ fontSize: "14px", color: tokens.textTertiary, marginBottom: "6px", fontWeight: 600 }}>
                  {d.day.slice(0, 3)}
                </div>
                <div style={{ fontSize: "15px", fontWeight: 800, color: c.text, fontFamily: tokens.mono }}>
                  {(d.crowd_score * 100).toFixed(1)}%
                </div>
                {d.recommended && <div style={{ fontSize: "13px", marginTop: "4px" }}>&#10003;</div>}
              </div>
            );
          })}
        </div>
      )}

      {data && data.weekly_prediction && (
        <div style={{ marginTop: "10px", fontSize: "14px", color: tokens.textFaint }}>
          {t("ldWeeklyPatternNote")}
        </div>
      )}
      {data && data.best_days && data.best_days.length > 0 && (
        <div style={{ marginTop: "14px", fontSize: "15px", color: tokens.textSecondary }}>
          {t("ldQuietest")} <strong style={{ color: tokens.accentBright }}>{data.best_days.map((b) => b.day).join(", ")}</strong>
        </div>
      )}
    </div>
  );
}
