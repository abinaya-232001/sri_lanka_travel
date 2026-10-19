export const tokens = {
  bg: "var(--bg)",
  bgGradient: "var(--bg-gradient)",
  surface: "var(--surface)",
  surfaceAlt: "var(--surface-alt)",
  cardBg: "var(--card-bg)",
  cardBgHover: "var(--card-bg-hover)",
  glass: "var(--glass)",
  border: "var(--border)",
  borderStrong: "var(--border-strong)",
  textPrimary: "var(--text-primary)",
  textSecondary: "var(--text-secondary)",
  textTertiary: "var(--text-tertiary)",
  textFaint: "var(--text-faint)",
  accent: "var(--accent)",
  accentBright: "var(--accent-bright)",
  accentSoft: "var(--accent-soft)",
  accentBorder: "var(--accent-border)",
  accentGlow: "var(--accent-glow)",
  warm: "var(--warm)",
  warmSoft: "var(--warm-soft)",
  warmBorder: "var(--warm-border)",
  danger: "var(--danger)",
  dangerSoft: "var(--danger-soft)",
  dangerBorder: "var(--danger-border)",
  radiusXl: "28px",
  radiusLg: "22px",
  radiusMd: "16px",
  radiusSm: "10px",
  shadowSm: "var(--shadow-sm)",
  shadowMd: "var(--shadow-md)",
  shadowLg: "var(--shadow-lg)",
  easeOut: "cubic-bezier(0.16, 1, 0.3, 1)",
  easeInOut: "cubic-bezier(0.65, 0, 0.35, 1)",
  font: `Figtree, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif`,
  mono: `"SF Mono", "JetBrains Mono", ui-monospace, monospace`,
};
export function riskColors(level) {
  const l = String(level || "").toLowerCase();
  if (l === "low") {
    return { text: tokens.accentBright, bg: tokens.accentSoft, border: tokens.accentBorder, glow: tokens.accentGlow };
  }
  if (l === "medium") {
    return { text: tokens.warm, bg: tokens.warmSoft, border: tokens.warmBorder, glow: "0 0 40px rgba(217,119,6,0.18)" };
  }
  return { text: tokens.danger, bg: tokens.dangerSoft, border: tokens.dangerBorder, glow: "0 0 40px rgba(220,38,38,0.20)" };
}
export function crowdPhrase(score) {
  const s = typeof score === "number" ? score : parseFloat(score);
  if (Number.isNaN(s)) return "Unknown";
  if (s >= 0.75) return "Very crowded";
  if (s >= 0.45) return "Filling up";
  if (s >= 0.2) return "Fairly quiet";
  return "Quiet now";
}
export function crowdEmoji(score) {
  const s = typeof score === "number" ? score : parseFloat(score);
  if (Number.isNaN(s)) return "○";
  if (s >= 0.75) return "●";
  if (s >= 0.45) return "◐";
  return "○";
}
