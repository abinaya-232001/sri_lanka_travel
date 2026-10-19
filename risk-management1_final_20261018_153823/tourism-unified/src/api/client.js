import { applyCorrections } from "../data/siteCorrections";
const API_BASE = (import.meta.env.VITE_RISK_API_URL || "/api/risk").replace(/\/$/, "");
async function request(path, options = {}) {
  const { method = "GET", body, timeoutMs = 15000 } = options;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(API_BASE + path, {
      method,
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });
    if (!res.ok) {
      const text = await res.text().catch(() => "");
      throw new Error("API " + method + " " + path + " failed: " + res.status + " " + text);
    }
    return await res.json();
  } finally {
    clearTimeout(timer);
  }
}
export const api = {
  health: () => request("/health"),
  sites: () => request("/sites").then((res) => ({ sites: applyCorrections(res.sites || []) })),
  predict: (siteId, date) => request("/predict?site_id=" + siteId + "&date=" + date),
  explain: (siteId, date) => request("/explain?site_id=" + siteId + "&date=" + date),
  forecast: (siteId, date) => request("/forecast?site_id=" + siteId + "&date=" + date),
  uncertainty: (siteId, date) => request("/uncertainty?site_id=" + siteId + "&date=" + date),
  alert: (siteId, date) => request("/alert?site_id=" + siteId + "&date=" + date),
  greenSites: (date) => request("/green-sites?date=" + date),
  bestTimes: (siteId, month) => request("/best-times?site_id=" + siteId + "&month=" + month),
  itineraryCheck: (sites, date) =>
    request("/itinerary-check", { method: "POST", body: { sites, date } }),
  feedback: (payload) => request("/feedback", { method: "POST", body: payload }),
  getFeedback: () => request("/feedback"),
  retrain: () => request("/retrain", { method: "POST" }),
  modelMetrics: () => request("/model-metrics"),
  featureImportance: () => request("/feature-importance"),
  tourismPressure: () => request("/tourism-pressure"),
  personalizedRanking: (opts) => {
    opts = opts || {};
    const params = new URLSearchParams();
    if (opts.maxFee != null) params.set("max_fee", opts.maxFee);
    if (opts.riskTolerance) params.set("risk_tolerance", opts.riskTolerance);
    if (opts.date) params.set("date", opts.date);
    if (opts.limit != null) params.set("limit", opts.limit);
    return request("/personalized-ranking?" + params.toString()).then((res) => ({ ...res, ranking: applyCorrections(res.ranking || []) }));
  },
  surgePrediction: (siteId, date, days) =>
    request("/surge-prediction?site_id=" + siteId + "&date=" + date + "&days=" + (days || 7)),
  modelComparison: (siteId, date) =>
    request("/model-comparison?site_id=" + siteId + "&date=" + date),
  ablation: (siteId, date) => request("/ablation?site_id=" + siteId + "&date=" + date),
  errorAnalysis: () => request("/error-analysis"),
  pipelineStatus: () => request("/pipeline-status"),
};
export { API_BASE };
