import React from "react";
import { tokens } from "./design/tokens";
import { useTheme } from "./design/ThemeContext";

const TABS = [
  { id: "home", label: "Home" },
  { id: "discover", label: "Discover" },
];

function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === "dark";
  return (
    <button
      onClick={toggleTheme}
      aria-label="Toggle dark mode"
      style={{
        width: "38px",
        height: "38px",
        borderRadius: "10px",
        border: "1px solid " + tokens.border,
        backgroundColor: tokens.surfaceAlt,
        color: tokens.textSecondary,
        cursor: "pointer",
        fontSize: "16px",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        transition: "all 0.2s " + tokens.easeOut,
      }}
    >
      {isDark ? "\u2600" : "\u263D"}
    </button>
  );
}

export default function Navbar({ active, onNavigate }) {
  return (
    <div
      className="navbar-container"
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "16px 32px",
        backgroundColor: tokens.surface,
        borderBottom: "1px solid " + tokens.border,
        position: "sticky",
        top: 0,
        zIndex: 100,
      }}
    >
      <div
        onClick={() => onNavigate("home")}
        style={{ display: "flex", alignItems: "center", gap: "12px", cursor: "pointer" }}
      >
        <div
          style={{
            width: 32,
            height: 32,
            borderRadius: "8px",
            backgroundColor: tokens.accent,
          }}
        />
        <span className="navbar-brand-text" style={{ fontSize: "16px", fontWeight: 800, color: tokens.textPrimary, fontFamily: tokens.font }}>
          SafeJourney AI
        </span>
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
        <div style={{ display: "flex", gap: "6px" }}>
          {TABS.map((tab) => {
            const isActive = active === tab.id || (tab.id === "discover" && active === "destinationDetail");
            return (
              <button
                key={tab.id}
                onClick={() => onNavigate(tab.id)}
                style={{
                  padding: "9px 18px",
                  borderRadius: "8px",
                  border: "1px solid " + (isActive ? tokens.accentBorder : "transparent"),
                  backgroundColor: isActive ? tokens.accentSoft : "transparent",
                  color: isActive ? tokens.accent : tokens.textSecondary,
                  fontSize: "13px",
                  fontWeight: 600,
                  cursor: "pointer",
                  fontFamily: tokens.font,
                }}
              >
                {tab.label}
              </button>
            );
          })}
        </div>
        <ThemeToggle />
      </div>
    </div>
  );
}
