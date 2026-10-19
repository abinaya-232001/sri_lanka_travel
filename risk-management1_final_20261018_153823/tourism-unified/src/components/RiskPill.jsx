import React from "react";
import { useSiteI18n } from "@shared/i18n/react";
import { tokens, riskColors } from "../design/tokens";

const RISK_KEYS = {
  Low: "ldRiskLow",
  Medium: "ldRiskMedium",
  High: "ldRiskHigh",
};

export default function RiskPill({ level, size = "md" }) {
  const { t } = useSiteI18n();
  const c = riskColors(level);
  const label = String(t(RISK_KEYS[level] || "ldRiskUnknown")).toUpperCase();
  const padding = size === "lg" ? "8px 16px" : "5px 12px";
  const fontSize = size === "lg" ? "13px" : "11px";

  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "7px",
        padding,
        backgroundColor: c.bg,
        border: "1px solid " + c.border,
        borderRadius: "999px",
        fontSize,
        fontWeight: 700,
        letterSpacing: "0.04em",
        color: c.text,
        fontFamily: tokens.mono,
      }}
    >
      <span
        style={{
          width: size === "lg" ? "7px" : "6px",
          height: size === "lg" ? "7px" : "6px",
          borderRadius: "50%",
          backgroundColor: c.text,
        }}
      />
      {label}
    </span>
  );
}
