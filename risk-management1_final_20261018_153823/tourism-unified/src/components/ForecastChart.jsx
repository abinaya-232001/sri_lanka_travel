import React from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from "recharts";
import { tokens, riskColors } from "../design/tokens";

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload || !payload.length) return null;
  const p = payload[0].payload;
  const c = riskColors(p.risk_level);
  return (
    <div style={{ background: "rgba(8,9,11,0.95)", border: "1px solid " + tokens.borderStrong, borderRadius: tokens.radiusSm, padding: "12px 16px", fontSize: "13px" }}>
      <div style={{ color: tokens.textTertiary, marginBottom: "4px" }}>{label}</div>
      <div style={{ color: c.text, fontWeight: 800, fontSize: "18px", fontFamily: tokens.mono }}>{(p.crowd_score * 100).toFixed(1)}%</div>
      <div style={{ color: tokens.textTertiary, fontSize: "14px" }}>{p.risk_level} risk</div>
    </div>
  );
}

export default function ForecastChart({ forecast }) {
  if (!forecast || !forecast.length) return null;
  const chartData = forecast.map((f) => ({ date: f.date.slice(5), crowd_score: f.crowd_score, risk_level: f.risk_level }));

  return (
    <div style={{ backgroundColor: tokens.surface, border: "1px solid " + tokens.border, borderRadius: tokens.radiusLg, padding: "22px", boxShadow: tokens.shadowSm }}>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={tokens.border} vertical={false} />
          <XAxis dataKey="date" tick={{ fill: tokens.textTertiary, fontSize: 11 }} axisLine={false} tickLine={false} />
          <YAxis domain={[0, 1]} tickFormatter={(v) => Math.round(v * 100) + "%"} tick={{ fill: tokens.textTertiary, fontSize: 11 }} axisLine={false} tickLine={false} />
          <Tooltip content={<CustomTooltip />} />
          <ReferenceLine y={0.75} stroke={tokens.danger} strokeDasharray="4 4" strokeOpacity={0.4} />
          <ReferenceLine y={0.45} stroke={tokens.warm} strokeDasharray="4 4" strokeOpacity={0.4} />
          <Line type="monotone" dataKey="crowd_score" stroke={tokens.accentBright} strokeWidth={2.5} dot={{ r: 4, fill: tokens.accentBright }} activeDot={{ r: 6 }} />
        </LineChart>
      </ResponsiveContainer>
      <div style={{ display: "flex", gap: "16px", marginTop: "8px", fontSize: "14px", color: tokens.textFaint }}>
        <span>- - - High risk threshold (75%)</span>
        <span>- - - Medium risk threshold (45%)</span>
      </div>
      <div style={{ marginTop: "6px", fontSize: "14px", color: tokens.textFaint }}>
        Crowd levels for this site stay fairly steady through the week &mdash; small changes are still meaningful.
      </div>
    </div>
  );
}