import React from "react";
import { tokens } from "../design/tokens";
import CrowdChip from "./CrowdChip";
import { FALLBACK_IMAGE } from "../design/fallbackImage";

export default function DestinationCard({ site, onClick }) {
  const imageUrl = site.image || FALLBACK_IMAGE;

  return (
    <div
      onClick={onClick}
      style={{
        position: "relative",
        height: "260px",
        borderRadius: tokens.radiusLg,
        overflow: "hidden",
        cursor: "pointer",
        border: "1px solid " + tokens.border,
        backgroundColor: tokens.surface,
      }}
      onMouseEnter={(e) => {
        const img = e.currentTarget.querySelector("img");
        if (img) img.style.transform = "scale(1.06)";
      }}
      onMouseLeave={(e) => {
        const img = e.currentTarget.querySelector("img");
        if (img) img.style.transform = "scale(1)";
      }}
    >
      <img
        src={imageUrl}
        alt={site.name}
        style={{
          position: "absolute",
          inset: 0,
          width: "100%",
          height: "100%",
          objectFit: "cover",
          transition: "transform 0.6s cubic-bezier(0.16,1,0.3,1)",
        }}
        onError={(e) => {
          e.target.style.display = "none";
          e.target.parentElement.style.background =
            "linear-gradient(135deg, rgba(29,184,142,0.18) 0%, #0B0C0E 100%)";
        }}
      />
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "linear-gradient(to top, rgba(11,12,14,0.95) 0%, rgba(11,12,14,0.3) 55%, transparent 100%)",
        }}
      />
      <div
        style={{
          position: "absolute",
          bottom: 0,
          left: 0,
          right: 0,
          padding: "20px",
        }}
      >
        <div
          style={{
            fontSize: "14px",
            fontWeight: 600,
            color: tokens.accent,
            textTransform: "uppercase",
            letterSpacing: "0.08em",
            marginBottom: "6px",
          }}
        >
          {site.region || site.district}
        </div>
        <div
          style={{
            fontSize: "19px",
            fontWeight: 700,
            color: tokens.textPrimary,
            marginBottom: "10px",
          }}
        >
          {site.name}
        </div>
        <CrowdChip score={site.crowd_score} level={site.risk_level} />
      </div>
    </div>
  );
}
