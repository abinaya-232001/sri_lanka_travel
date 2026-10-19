import React from "react";
import { useSiteI18n } from "@shared/i18n/react";
import { tokens, riskColors } from "../design/tokens";

export function crowdPhraseKey(score) {
  const s = typeof score === "number" ? score : parseFloat(score);
  if (Number.isNaN(s)) return "ldCrowdUnknown";
  if (s >= 0.75) return "ldCrowdVeryCrowded";
  if (s >= 0.45) return "ldCrowdFillingUp";
  if (s >= 0.2) return "ldCrowdFairlyQuiet";
  return "ldCrowdQuietNow";
}

export default function CrowdChip({ score, level }) {
  const { t } = useSiteI18n();
  const c = riskColors(level);
  const phrase = t(crowdPhraseKey(score));

  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "6px",
        padding: "6px 14px",
        backgroundColor: c.bg,
        border: "1px solid " + c.border,
        borderRadius: "999px",
        fontSize: "14px",
        fontWeight: 600,
        color: c.text,
        fontFamily: tokens.font,
      }}
    >
      {phrase}
    </span>
  );
}
