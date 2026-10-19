import React from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

// Archetypal hourly shapes (relative weights, 0-1) for common site categories.
// These are NOT model output -- they encode typical visitor behavior patterns
// per category, then get scaled by the real prediction.crowd_score for the day.
const HOURLY_SHAPES = {
  temple: [0.3, 0.5, 0.7, 0.6, 0.4, 0.3, 0.4, 0.6, 0.8, 0.9, 0.7, 0.5, 0.4, 0.3],
  beach: [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 0.9, 0.7, 0.5, 0.3],
  market: [0.2, 0.4, 0.6, 0.8, 0.9, 1.0, 0.9, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1],
  wildlife: [0.6, 0.9, 1.0, 0.8, 0.5, 0.3, 0.2, 0.2, 0.3, 0.5, 0.7, 0.9, 0.6, 0.3],
  waterfall: [0.2, 0.3, 0.5, 0.7, 0.8, 0.9, 1.0, 0.9, 0.7, 0.5, 0.4, 0.3, 0.2, 0.1],
  museum: [0.0, 0.0, 0.3, 0.5, 0.7, 0.8, 0.9, 0.7, 0.6, 0.5, 0.4, 0.2, 0.0, 0.0],
  historical: [0.2, 0.4, 0.6, 0.7, 0.6, 0.5, 0.5, 0.6, 0.8, 0.9, 0.7, 0.5, 0.3, 0.2],
  mountain: [0.5, 1.0, 0.9, 0.6, 0.4, 0.3, 0.2, 0.2, 0.3, 0.4, 0.5, 0.5, 0.4, 0.2],
  city: [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 0.9, 0.8, 0.7, 0.6, 0.5],
  default: [0.2, 0.4, 0.6, 0.7, 0.8, 0.9, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2],
};

const HOURS = [
  "6am", "7am", "8am", "9am", "10am", "11am", "12pm",
  "1pm", "2pm", "3pm", "4pm", "5pm", "6pm", "7pm",
];

function normalizeCategory(category) {
  if (!category) return "default";
  const c = category.toLowerCase();
  if (c.includes("temple") || c.includes("religious") || c.includes("shrine")) return "temple";
  if (c.includes("beach") || c.includes("coast")) return "beach";
  if (c.includes("market") || c.includes("bazaar")) return "market";
  if (c.includes("wildlife") || c.includes("safari") || c.includes("national park")) return "wildlife";
  if (c.includes("waterfall")) return "waterfall";
  if (c.includes("museum")) return "museum";
  if (c.includes("historical") || c.includes("heritage") || c.includes("ruins") || c.includes("fort")) return "historical";
  if (c.includes("mountain") || c.includes("hik") || c.includes("trek") || c.includes("peak")) return "mountain";
  if (c.includes("city") || c.includes("urban") || c.includes("town")) return "city";
  return "default";
}

// crowdScore expected as 0-1 float (matches model output range). If the real
// field uses a different scale, adjust the clamp below -- verify against
// prediction.crowd_score before relying on this in production.
export default function HourlyPatternChart({ category, crowdScore }) {
  const shapeKey = normalizeCategory(category);
  const shape = HOURLY_SHAPES[shapeKey] || HOURLY_SHAPES.default;
  const score = Math.max(0, Math.min(1, typeof crowdScore === "number" ? crowdScore : 0.5));

  const data = HOURS.map((hour, i) => ({
    hour,
    crowd: Math.round(shape[i] * score * 100),
  }));

  return (
    <div style={{ marginTop: "16px" }}>
      <ResponsiveContainer width="100%" height={220}>
        <AreaChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="hourlyFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#f59e0b" stopOpacity={0.6} />
              <stop offset="100%" stopColor="#f59e0b" stopOpacity={0.05} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" opacity={0.15} />
          <XAxis dataKey="hour" tick={{ fontSize: 11 }} interval={1} />
          <YAxis tick={{ fontSize: 11 }} width={30} domain={[0, "dataMax + 5"]} />
          <Tooltip formatter={(v) => [v + " / 100", "Estimated crowd level"]} />
          <Area
            type="monotone"
            dataKey="crowd"
            stroke="#f59e0b"
            strokeWidth={2}
            fill="url(#hourlyFill)"
          />
        </AreaChart>
      </ResponsiveContainer>
      <p style={{ fontSize: "15px", opacity: 0.7, marginTop: "4px", lineHeight: 1.4 }}>
        Typical visiting pattern for this type of destination, scaled to
        today&#39;s predicted crowd level.
      </p>
    </div>
  );
}