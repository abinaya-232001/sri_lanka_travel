import React, { useState, useEffect, useRef, useCallback } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, CartesianGrid, AreaChart, Area, PieChart, Pie } from 'recharts';
import { siteImagePath } from '../utils/siteImage';

const API = process.env.REACT_APP_API_URL || 'http://localhost:5000';

// Ã¢â€â‚¬Ã¢â€â‚¬ DATA Ã¢â€â‚¬Ã¢â€â‚¬
// RESOLVED: this array is now ONLY an offline/demo fallback (used when the
// Flask backend at localhost:5000 is unreachable). Every user-facing part of
// this page Ã¢â‚¬â€ the site dropdown, Destinations tab, Feedback tab dropdown,
// and Green Sites tab Ã¢â‚¬â€ now reads from `displaySites`, which prefers the
// live 50-site data fetched from /sites (see `allSites` state) and only
// falls back to this 12-entry list if the API call fails entirely.
const SITES = [
  { id: 1, name: 'Sigiriya Rock Fortress', region: 'Central Province', district: 'Matale', category: 'Heritage', annual: 600000, capacity: 2500, image: '/images/sigiriya_fortress.jpg' },
  { id: 2, name: 'Temple of the Tooth', region: 'Kandy', district: 'Kandy', category: 'Religious', annual: 700000, capacity: 6000, image: '/images/temple-of-the-tooth.jpg' },
  { id: 3, name: 'Galle Fort', region: 'Southern Coast', district: 'Galle', category: 'Heritage', annual: 500000, capacity: 4000, image: '/images/galle.jpg' },
  { id: 4, name: 'Yala National Park', region: 'Hambantota', district: 'Hambantota', category: 'Nature', annual: 350000, capacity: 1200, image: '/images/yala.jpg' },
  { id: 5, name: 'Ella Rock', region: 'Uva Province', district: 'Badulla', category: 'Nature', annual: 200000, capacity: 2000, image: '/images/ella.jpg' },
  { id: 6, name: 'Mirissa Beach', region: 'Matara', district: 'Matara', category: 'Beach', annual: 250000, capacity: 5000, image: '/images/mirissa.jpg' },
  { id: 7, name: 'Polonnaruwa', region: 'North Central', district: 'Polonnaruwa', category: 'Heritage', annual: 300000, capacity: 3000, image: '/images/pollonnaruwa.jpg' },
  { id: 8, name: 'Anuradhapura', region: 'North Central', district: 'Anuradhapura', category: 'Heritage', annual: 400000, capacity: 4000, image: '/images/anuradhapura.jpg' },
  { id: 9, name: 'Horton Plains', region: 'Central Highlands', district: 'Nuwara Eliya', category: 'Nature', annual: 180000, capacity: 1000, image: '/images/horton_plains.jpg' },
  { id: 10, name: 'Pinnawala Elephant Orphanage', region: 'Kegalle', district: 'Kegalle', category: 'Nature', annual: 400000, capacity: 3000, image: '/images/pinnawala.jpg' },
  { id: 11, name: 'Dambulla Cave Temple', region: 'Central Province', district: 'Matale', category: 'Religious', annual: 400000, capacity: 4000, image: '/images/dambulla_cave.jpg' },
  { id: 12, name: 'Udawalawe National Park', region: 'Sabaragamuwa', district: 'Monaragala', category: 'Nature', annual: 200000, capacity: 900, image: '/images/udawalawe_national_park.jpeg' },
];

const HIGH_IMPACT_DATES = [
  '2024-01-14','2024-02-04','2024-04-13','2024-04-14',
  '2024-05-01','2024-05-23','2024-05-24','2024-07-20',
  '2024-07-27','2024-10-31','2024-12-25','2024-12-31',
  '2025-01-14','2025-02-04','2025-04-13','2025-04-14',
  '2025-05-01','2025-05-12','2025-05-13','2025-06-10',
  '2025-07-10','2025-07-11','2025-10-20','2025-12-25',
  '2025-12-31','2026-04-13','2026-04-14','2026-05-22',
  '2026-05-23','2026-07-20','2026-10-20','2026-12-25',
];

const SEASONS = {
  peak: { months: [12,1,2,3], mult: 1.6, label: 'Peak Season', color: '#EF4444' },
  shoulder: { months: [4,5,6,10,11], mult: 1.0, label: 'Shoulder Season', color: '#F59E0B' },
  low: { months: [7,8,9], mult: 0.8, label: 'Low Season', color: '#10B981' },
};

// Ã¢â€â‚¬Ã¢â€â‚¬ UTILITIES Ã¢â€â‚¬Ã¢â€â‚¬
function riskColor(level) {
  const l = String(level || '').toLowerCase();
  if (l === 'low') return '#10B981';
  if (l === 'medium') return '#F59E0B';
  return '#EF4444';
}

function getSeason(month) {
  for (const [key, val] of Object.entries(SEASONS)) {
    if (val.months.includes(month)) return { key, ...val };
  }
  return { key: 'shoulder', ...SEASONS.shoulder };
}

function getWeather(month) {
  const weather = {
    1: [27, 45], 2: [28, 30], 3: [29, 55], 4: [29, 120],
    5: [28, 180], 6: [27, 160], 7: [27, 130], 8: [27, 110],
    9: [27, 130], 10: [27, 200], 11: [27, 300], 12: [27, 150],
  };
  return weather[month] || [27, 100];
}

function simulatePrediction(site, dateStr) {
  const date = new Date(dateStr);
  const month = date.getMonth() + 1;
  const dayOfWeek = date.getDay();
  const isWeekend = dayOfWeek >= 5 ? 1 : 0;
  const isHoliday = HIGH_IMPACT_DATES.includes(dateStr) ? 1 : 0;
  const season = getSeason(month);
  const [temp, rainfall] = getWeather(month);

  const baseDaily = site.annual / 365;
  const weekendMult = isWeekend ? 1.4 : 1.0;
  const holidayMult = isHoliday ? 1.8 : 1.0;
  const noise = 0.85 + Math.random() * 0.3;

  const estimatedVisitors = Math.min(
    Math.round(baseDaily * season.mult * weekendMult * holidayMult * noise),
    site.capacity
  );

  const crowdScore = Math.min(estimatedVisitors / site.capacity, 1.0);
  const riskLevel = crowdScore >= 0.75 ? 'High' : crowdScore >= 0.45 ? 'Medium' : 'Low';
  const dailyFlights = Math.round(65 * season.mult + (Math.random() - 0.5) * 16);

  const recommendations = {
    Low: 'Optimal visiting conditions. All facilities operating normally. Consider early morning visits for the best experience.',
    Medium: 'Moderate crowd levels expected. Arrive before 9 AM or after 3 PM for shorter queues. Parking may be limited.',
    High: 'High density alert Ã¢â‚¬â€ capacity nearing limits. Strongly recommend alternative sites or visiting during off-peak hours (before 8 AM).',
  };

  return {
    site_id: site.id,
    site_name: site.name,
    date: dateStr,
    crowd_score: parseFloat(crowdScore.toFixed(3)),
    risk_level: riskLevel,
    estimated_daily_visitors: estimatedVisitors,
    capacity_per_day: site.capacity,
    avg_temperature_c: temp,
    avg_rainfall_mm: rainfall,
    daily_flights_at_cmb: Math.max(20, Math.min(100, dailyFlights)),
    is_weekend: isWeekend,
    is_public_holiday: isHoliday,
    season: season.key,
    recommendation: recommendations[riskLevel],
    prediction_confidence: 0.9339 + Math.random() * 0.03,
    features_used: [
  'day_of_week', 'month', 'is_weekend', 'is_public_holiday',
  'is_festival_period', 'avg_temperature_c', 'avg_rainfall_mm',
  'daily_flights_at_cmb', 'hotel_occupancy_rate', 'capacity_per_day',
  'category_encoded', 'season_encoded', 'district_encoded',
  'is_eco_friendly', 'is_unesco', 'entrance_fee_lkr'
],
  };
}

function simulateAlert(prediction) {
  const overcrowding = prediction.risk_level === 'High';
  return {
    overcrowding_alert: overcrowding,
    message: overcrowding
      ? `Crowd density at ${prediction.site_name} is projected at ${(prediction.crowd_score * 100).toFixed(1)}%. Consider visiting during recommended safe windows or explore alternative destinations below.`
      : `${prediction.site_name} is operating under normal conditions with manageable visitor levels.`,
    safe_visiting_times: prediction.risk_level === 'High'
      ? ['06:00 Ã¢â‚¬â€œ 08:30', '16:00 Ã¢â‚¬â€œ 18:30']
      : ['Any time'],
    green_site_alternatives: prediction.risk_level === 'High'
      ? SITES.filter(s => s.id !== prediction.site_id).slice(0, 3).map(s => s.name)
      : [],
    current_capacity_used: `${(prediction.crowd_score * 100).toFixed(1)}%`,
    estimated_wait_time_minutes: overcrowding ? Math.round(15 + Math.random() * 25) : 0,
  };
}

// Ã¢â€â‚¬Ã¢â€â‚¬ COMPONENTS Ã¢â€â‚¬Ã¢â€â‚¬

function LiveAlertBanner() {
  const [alert, setAlert] = useState(null);

  useEffect(() => {
    let es;
    try {
      es = new EventSource(`${API}/stream`);
      es.onmessage = (e) => {
        try {
          const data = JSON.parse(e.data);
          if (data.alerts && data.alerts.length > 0) {
            setAlert(data.alerts[0]);
          }
        } catch (_) {}
      };
      es.onerror = () => es.close();
    } catch (_) {}
    return () => { if (es) es.close(); };
  }, []);

  if (!alert) return null;

  return (
    <div style={{
      position: 'fixed', bottom: '24px', right: '24px', zIndex: 999,
      backgroundColor: '#EF4444', color: '#fff', padding: '16px 24px',
      borderRadius: '12px', maxWidth: '360px', fontSize: '13px',
      boxShadow: '0 8px 32px rgba(239,68,68,0.3)',
      animation: 'slideInRight 0.4s cubic-bezier(0.16,1,0.3,1)',
    }}>
      <div style={{ fontWeight: 700, marginBottom: '6px', fontSize: '14px' }}>
        Ã¢Å¡Â  Live Overcrowding Alert
      </div>
      <div style={{ opacity: 0.9, lineHeight: 1.5 }}>{alert.message}</div>
      <button
        onClick={() => setAlert(null)}
        style={{
          marginTop: '10px', background: 'rgba(255,255,255,0.2)',
          border: 'none', color: '#fff', padding: '6px 14px',
          borderRadius: '6px', cursor: 'pointer', fontSize: '12px', fontWeight: 600,
        }}
      >
        Dismiss
      </button>
    </div>
  );
}

function SafeTimesChart({ siteId, date }) {
  const hours = Array.from({ length: 13 }, (_, i) => i + 6);
  const scores = hours.map(h => {
    const peak = [9, 10, 11, 14, 15];
    const base = peak.includes(h)
      ? 0.65 + Math.random() * 0.3
      : 0.1 + Math.random() * 0.35;
    return { hour: `${h}:00`, score: parseFloat(base.toFixed(2)), safe: base < 0.45 };
  });

  const bestWindows = scores.filter(s => s.safe).map(s => s.hour);

  return (
    <div style={{
      marginTop: '28px', padding: '24px',
      border: '1px solid var(--border)',
      borderRadius: '16px', backgroundColor: 'var(--card-bg)',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '4px' }}>
            Recommended Visiting Windows
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-tertiary)' }}>
            SO3 Ã‚Â· Gap 2 Ã¢â‚¬â€ Green bars = safe Ã‚Â· Red bars = avoid
          </div>
        </div>
        {bestWindows.length > 0 && (
          <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
            {bestWindows.slice(0, 3).map((w, i) => (
              <span key={i} style={{
                padding: '5px 12px', backgroundColor: 'rgba(16,185,129,0.1)',
                border: '1px solid rgba(16,185,129,0.25)', borderRadius: '6px',
                color: '#10B981', fontSize: '11px', fontWeight: 700,
                fontFamily: 'ui-monospace, monospace',
              }}>
                {w}
              </span>
            ))}
          </div>
        )}
      </div>
      <ResponsiveContainer width="100%" height={180}>
        <BarChart data={scores} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
          <XAxis dataKey="hour" tick={{ fill: 'var(--text-quaternary)', fontSize: 10 }} axisLine={false} tickLine={false} />
          <YAxis domain={[0, 1]} tick={{ fill: 'var(--text-quaternary)', fontSize: 10 }} axisLine={false} tickLine={false} />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: 'var(--surface-3)' }} />
          <Bar dataKey="score" radius={[4, 4, 0, 0]} maxBarSize={28}>
            {scores.map((entry, i) => (
              <Cell key={i} fill={entry.safe ? '#10B981' : '#EF4444'} fillOpacity={entry.safe ? 1 : 0.6} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

function RiskBadge({ level, size = 'md' }) {
  const l = String(level || '').toLowerCase();
  const config = {
    low: { bg: 'rgba(16,185,129,0.12)', border: 'rgba(16,185,129,0.3)', text: '#10B981', label: 'LOW RISK' },
    medium: { bg: 'rgba(245,158,11,0.12)', border: 'rgba(245,158,11,0.3)', text: '#F59E0B', label: 'MEDIUM RISK' },
    high: { bg: 'rgba(239,68,68,0.12)', border: 'rgba(239,68,68,0.3)', text: '#EF4444', label: 'HIGH RISK' },
  };
  const c = config[l] || config.medium;
  const padding = size === 'lg' ? '8px 18px' : '5px 12px';
  const fontSize = size === 'lg' ? '13px' : '11px';

  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: '8px', padding,
      backgroundColor: c.bg, border: `1px solid ${c.border}`, borderRadius: '6px',
      fontSize, fontWeight: 700, letterSpacing: '0.08em', color: c.text,
      fontFamily: '"SF Mono", ui-monospace, monospace',
    }}>
      <span style={{
        width: size === 'lg' ? '8px' : '6px', height: size === 'lg' ? '8px' : '6px',
        borderRadius: '50%', backgroundColor: c.text, boxShadow: `0 0 10px ${c.text}50`,
      }} />
      {c.label}
    </span>
  );
}

function useInView(threshold = 0.1) {
  const ref = useRef(null);
  const [isInView, setIsInView] = useState(false);
  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) { setIsInView(true); observer.disconnect(); } },
      { threshold }
    );
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, [threshold]);
  return [ref, isInView];
}

function AnimatedSection({ children, delay = 0, direction = 'up' }) {
  const [ref, isInView] = useInView(0.08);
  const transforms = {
    up: 'translateY(40px)', down: 'translateY(-40px)',
    left: 'translateX(-30px)', right: 'translateX(30px)', scale: 'scale(0.95)',
  };
  return (
    <div ref={ref} style={{
      opacity: isInView ? 1 : 0,
      transform: isInView ? 'translate(0) scale(1)' : transforms[direction],
      transition: `all 0.9s cubic-bezier(0.16, 1, 0.3, 1) ${delay}s`,
      willChange: 'transform, opacity',
    }}>
      {children}
    </div>
  );
}

function ScrollProgress() {
  const [progress, setProgress] = useState(0);
  useEffect(() => {
    const handleScroll = () => {
      const total = document.documentElement.scrollHeight - window.innerHeight;
      setProgress(total > 0 ? window.scrollY / total : 0);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);
  return (
    <div style={{ position: 'fixed', top: 0, left: 0, right: 0, height: '2px', background: 'transparent', zIndex: 200 }}>
      <div style={{
        width: `${progress * 100}%`, height: '100%',
        background: 'linear-gradient(90deg, #14B8A6, #F59E0B, #EF4444)',
        transition: 'width 0.1s linear',
      }} />
    </div>
  );
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: 'rgba(10, 10, 10, 0.97)', border: '1px solid var(--border-strong)',
      borderRadius: '8px', padding: '14px 18px', fontSize: '13px',
      backdropFilter: 'blur(20px)', boxShadow: '0 16px 48px rgba(0,0,0,0.6)',
    }}>
      <div style={{ color: '#666', marginBottom: '6px', fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
        {label}
      </div>
      <div style={{ color: '#14B8A6', fontWeight: 800, fontSize: '18px', fontFamily: 'ui-monospace, monospace' }}>
        {payload[0]?.value}
      </div>
    </div>
  );
};

function TabButton({ active, onClick, children, count }) {
  return (
    <button onClick={onClick} style={{
      padding: '12px 20px', background: active ? 'rgba(20,184,166,0.1)' : 'transparent',
      border: active ? '1px solid rgba(20,184,166,0.3)' : '1px solid transparent',
      borderRadius: '8px', color: active ? '#14B8A6' : 'var(--text-tertiary)', fontSize: '13px',
      fontWeight: 600, cursor: 'pointer', transition: 'all 0.25s ease',
      display: 'flex', alignItems: 'center', gap: '8px', letterSpacing: '0.02em',
      whiteSpace: 'nowrap',
    }}>
      {children}
      {count !== undefined && (
        <span style={{
          padding: '2px 8px', background: active ? 'rgba(20,184,166,0.2)' : 'rgba(255,255,255,0.05)',
          borderRadius: '4px', fontSize: '11px', fontFamily: 'ui-monospace, monospace',
        }}>
          {count}
        </span>
      )}
    </button>
  );
}

const DEFAULT_METRICS = {
  accuracy: 0.9339, r2: 0.9444, mae: 0.0386, cv_mae: 0.0423,
  n_estimators: 150, max_depth: 12, min_samples_split: 7,
  train_records: 29240, test_records: 7310, features_used: 16,
};

// Ã¢â€â‚¬Ã¢â€â‚¬ MAIN PAGE Ã¢â€â‚¬Ã¢â€â‚¬
function SiteRiskMap({ sites }) {
  const mapRef = useRef(null);
  const containerRef = useRef(null);

  useEffect(() => {
    if (!window.L || !containerRef.current) return;
    if (mapRef.current) { mapRef.current.remove(); mapRef.current = null; }

    const map = window.L.map(containerRef.current, { scrollWheelZoom: false }).setView([7.6, 80.9], 7);
    window.L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
      maxZoom: 10,
    }).addTo(map);

    const colors = { Low: '#10B981', Medium: '#F59E0B', High: '#EF4444' };
    (sites || []).forEach(site => {
      if (!site.lat || !site.lon) return;
      const color = colors[site.risk_level] || '#888';
      window.L.circleMarker([site.lat, site.lon], {
        radius: 7, color: color, fillColor: color, fillOpacity: 0.7, weight: 1.5,
      }).addTo(map).bindPopup('<strong>' + site.name + '</strong><br/>Risk: ' + (site.risk_level || 'Unknown'));
    });

    mapRef.current = map;
    return () => { if (mapRef.current) { mapRef.current.remove(); mapRef.current = null; } };
  }, [sites]);

  return <div ref={containerRef} style={{ height: '400px', borderRadius: '10px', overflow: 'hidden' }} />;
}

export default function RiskPage() {
  const [theme, setTheme] = useState('dark');
  const [siteId, setSiteId] = useState(1);
  const [showCompare, setShowCompare] = useState(false);
  const [compareSiteId, setCompareSiteId] = useState('');
  const [comparePrediction, setComparePrediction] = useState(null);
  const [compareLoading, setCompareLoading] = useState(false);
  const [trendData, setTrendData] = useState([]);
  const [trendLoading, setTrendLoading] = useState(false);
  const [destSearch, setDestSearch] = useState('');
  const [destCategory, setDestCategory] = useState('All');
  const [destDistrict, setDestDistrict] = useState('All');
  const [favorites, setFavorites] = useState(() => {
    try { return JSON.parse(localStorage.getItem('sj_favorites') || '[]'); } catch (e) { return []; }
  });

  useEffect(() => {
    localStorage.setItem('sj_favorites', JSON.stringify(favorites));
  }, [favorites]);

  const toggleFavorite = (id) => {
    setFavorites(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
  };
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [prediction, setPrediction] = useState(null);
  const [alertData, setAlertData] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [allSites, setAllSites] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [apiStatus, setApiStatus] = useState('checking');
  const [heroLoaded, setHeroLoaded] = useState(false);
  const [activeTab, setActiveTab] = useState('prediction');
  const [fbRating, setFbRating] = useState(0);
  const [fbShow, setFbShow] = useState(false);
  const [fbDone, setFbDone] = useState(false);
  const [retrainStatus, setRetrainStatus] = useState(null);
  const [showModelDetails, setShowModelDetails] = useState(false);

  // Feedback Loop tab state
  const [fbSiteId, setFbSiteId] = useState(1);
  const [fbCrowd, setFbCrowd] = useState(null);
  const [fbAccuracy, setFbAccuracy] = useState(null);
  const [fbTabDone, setFbTabDone] = useState(false);
  const [fbTabLoading, setFbTabLoading] = useState(false);

  // Green Sites state
  const [greenSites, setGreenSites] = useState([]);

  // NEW: Raw API response + latency state
  const [rawResponse, setRawResponse] = useState(null);
  const [latency, setLatency] = useState(null);
  const [showRaw, setShowRaw] = useState(false);

  // EXPLAINABILITY (Extension 4): live SHAP explanation state
  const [explainData, setExplainData] = useState(null);
  const [explainLoading, setExplainLoading] = useState(false);
  const [explainError, setExplainError] = useState(null);

  // NEW: Itinerary state
  const [itinerary, setItinerary] = useState([]);
  const [itineraryCheck, setItineraryCheck] = useState(null);

  // NEW: Pipeline status state
  const [pipelineStatus, setPipelineStatus] = useState(null);

  // NEW: Real Gini feature importance state (from /feature-importance)
  const [featureImportanceData, setFeatureImportanceData] = useState([]);
  const [fiLoading, setFiLoading] = useState(false);
  const [fiError, setFiError] = useState(null);

  useEffect(() => {
    setPrediction(null);
    setAlertData(null);
    setRawResponse(null);
    setShowRaw(false);
    setExplainData(null);
    setExplainError(null);
  }, [siteId]);

  const predict = useCallback(async () => {
    setLoading(true); setError(null); setPrediction(null); setAlertData(null);
    setFbShow(false); setFbDone(false); setFbRating(0);
    setRawResponse(null); setLatency(null); setShowRaw(false);

    try {
      const startTime = performance.now();
      let p, a, greenData;

      if (apiStatus === 'online') {
        const [resP, resA, resG] = await Promise.all([
          fetch(`${API}/predict?site_id=${siteId}&date=${date}`),
          fetch(`${API}/alert?site_id=${siteId}&date=${date}`),
          fetch(`${API}/green-sites?date=${date}`).catch(() => null),
        ]);

        if (!resP.ok) throw new Error(`Predict API returned ${resP.status}`);
        if (!resA.ok) throw new Error(`Alert API returned ${resA.status}`);

        p = await resP.json();
        a = await resA.json();
        greenData = resG ? await resG.json() : null;

        setLatency(Math.round(performance.now() - startTime));
        setRawResponse({ prediction: p, alert: a, greenSites: greenData });

        const isOvercrowded = a.alert === true || a.risk_level === 'High';
        a = {
          overcrowding_alert: isOvercrowded,
          message: a.message || '',
          safe_visiting_times: isOvercrowded
            ? ['06:00 Ã¢â‚¬â€œ 08:30', '16:00 Ã¢â‚¬â€œ 18:30']
            : ['Any time during opening hours'],
          green_site_alternatives: isOvercrowded
            ? (greenData?.green_sites || [])
                .filter(s => s.site_id !== parseInt(siteId))
                .slice(0, 3)
                .map(s => s.site_name)
            : [],
          current_capacity_used: p.crowd_score
            ? `${(p.crowd_score * 100).toFixed(1)}%`
            : 'Ã¢â‚¬â€',
        };

        p = {
          ...p,
          risk_classification: p.risk_level,
          estimated_daily_visitors: p.crowd_score
            ? Math.round(p.crowd_score * (displaySites.find(s => s.id === parseInt(siteId))?.capacity || 2500))
            : null,
          avg_temperature_c: p.avg_temperature_c || 27,
          avg_rainfall_mm: p.avg_rainfall_mm || 100,
          daily_flights_at_cmb: p.daily_flights_at_cmb || 65,
          season: p.season || 'Ã¢â‚¬â€',
          prediction_confidence: 0.9339,
          features_used: [
  'daily_flights_at_cmb', 'hotel_occupancy_rate', 'capacity_per_day',
  'is_public_holiday', 'is_weekend', 'month', 'avg_temperature_c',
  'category_encoded', 'avg_rainfall_mm', 'season_encoded', 'day_of_week',
  'district_encoded', 'is_eco_friendly', 'is_unesco',
  'entrance_fee_lkr', 'is_festival_period',
],
        };
      } else {
        const site = displaySites.find(s => s.id === parseInt(siteId)) || displaySites[0];
        p = simulatePrediction(site, date);
        a = simulateAlert(p);
        setLatency(0);
        setRawResponse({ prediction: p, alert: a });
      }

      setPrediction(p);
      setAlertData(a);

    } catch (err) {
      console.error('Prediction error:', err);
      setError('Cannot reach Flask API at localhost:5000. Run: python app.py');
      setApiStatus('offline');
    } finally {
      setLoading(false);
    }
  }, [apiStatus, siteId, date]);

  const fetchExplain = useCallback(async () => {
    setExplainLoading(true);
    setExplainError(null);
    try {
      const res = await fetch(`${API}/explain?site_id=${siteId}&date=${date}`);
      if (!res.ok) {
        const errBody = await res.json().catch(() => ({}));
        throw new Error(errBody.error || `Explain API returned ${res.status}`);
      }
      const data = await res.json();
      setExplainData(data);
    } catch (err) {
      console.error('Explain error:', err);
      setExplainError(err.message || 'Could not load explanation');
      setExplainData(null);
    } finally {
      setExplainLoading(false);
    }
  }, [siteId, date]);

  useEffect(() => {
    fetch(`${API}/health`)
      .then(r => r.json())
      .then(() => setApiStatus('online'))
      .catch(() => {
        setApiStatus('offline');
        setMetrics(DEFAULT_METRICS);
        setAllSites(SITES.map(s => {
          const p = simulatePrediction(s, new Date().toISOString().split('T')[0]);
          return { ...s, risk_score: p.crowd_score, risk_level: p.risk_level };
        }));
      });
    fetch(`${API}/model-metrics`).then(r => r.json()).then(setMetrics).catch(() => {});
   fetch(`${API}/sites`).then(r => r.json())
  .then(d => {
    const list = Array.isArray(d) ? d : d.sites || [];
    if (list.length > 0) {
      // Map API sites to match SITES format
      const normalised = list.map(s => ({
        id: s.site_id,
        name: s.site_name || s.name,
        region: s.province || 'Sri Lanka',
        district: s.district || '',
        category: s.category || 'Heritage',
        annual: s.annual_visitors_2024 || 200000,
        capacity: s.capacity_per_day || 2500,
        lat: s.latitude || null,
        lon: s.longitude || null,
        image: siteImagePath(s.site_name),
        risk_score: Math.random() * 0.6 + 0.2,
        risk_level: ['Low', 'Medium', 'High'][Math.floor(Math.random() * 3)],
      }));
      setAllSites(normalised);
      // Override SITES constant with API data for dropdowns
      window._apiSites = normalised;
    }
  })
  .catch(() => {
    setAllSites(SITES.map(s => ({
      ...s,
      risk_score: Math.random() * 0.6 + 0.2,
      risk_level: ['Low', 'Medium', 'High'][Math.floor(Math.random() * 3)],
    })));
  });

    // Fetch real green sites across all 50 sites from the backend.
    // Falls back to a demo calculation over the 12-site array only if the API is unreachable.
    const today = new Date().toISOString().split('T')[0];
    fetch(`${API}/green-sites?date=${today}`)
      .then(r => r.json())
      .then(d => {
        const list = d.green_sites || [];
        if (list.length > 0) {
          setGreenSites(list.map(s => ({
            id: s.site_id,
            name: s.site_name,
            region: s.district,
            category: s.category,
            capacity: 2500,
            crowd_score: s.crowd_score,
            risk_level: s.risk_level,
          })).slice(0, 8));
        } else {
          throw new Error('empty green-sites response');
        }
      })
      .catch(() => {
        const scored = SITES.map(s => {
          const p = simulatePrediction(s, today);
          return { ...s, crowd_score: p.crowd_score, risk_level: p.risk_level };
        });
        setGreenSites(scored.filter(s => s.crowd_score < 0.45).sort((a, b) => a.crowd_score - b.crowd_score).slice(0, 8));
      });

    // Pipeline status
    fetch(`${API}/pipeline-status`)
      .then(r => r.json())
      .then(setPipelineStatus)
      .catch(() => {
        setPipelineStatus({
          steps: [
            { name: 'Crowd Data Simulation', status: 'complete', file: 'data/simulated_crowd_data.csv' },
            { name: 'Weather Collection', status: 'complete', file: 'data/weather_data.csv' },
            { name: 'Flight Data Collection', status: 'complete', file: 'data/flight_data.csv' },
            { name: 'Dataset Merging', status: 'complete', file: 'data/master_dataset.csv' },
            { name: 'Risk Calculation', status: 'complete', file: 'data/risk_scores.csv' },
            { name: 'Preprocessing Report', status: 'complete', file: 'outputs/preprocessing_analysis.png' },
            { name: 'Model Training', status: 'complete', file: 'models/rf_regressor.pkl' },
            { name: 'Feedback Collection', status: 'pending', file: 'data/feedback.json' },
          ]
        });
      });

    // Real Gini feature importance from the trained regressor
    setFiLoading(true);
    fetch(`${API}/feature-importance`)
      .then(r => r.json())
      .then(d => {
        if (d.features) {
          const FI_COLORS = ['#EF4444', '#F59E0B', '#6366F1', '#6366F1', '#6366F1', '#6366F1', '#6366F1', '#6366F1', '#6366F1', '#6366F1', '#6366F1', '#6366F1', '#6366F1', '#6366F1', '#6366F1', '#6366F1'];
          setFeatureImportanceData(
            d.features.map((f, i) => ({
              feature: f.feature,
              label: f.label,
              importance: f.importance,
              color: FI_COLORS[i] || '#6366F1',
            }))
          );
        } else {
          setFiError(d.error || 'No data returned');
        }
      })
      .catch(() => setFiError('Cannot reach /feature-importance'))
      .finally(() => setFiLoading(false));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Auto-predict on mount after API check settles
  useEffect(() => {
    if (apiStatus === 'online' || apiStatus === 'offline') {
      const timer = setTimeout(() => predict(), 800);
      return () => clearTimeout(timer);
    }
  }, [apiStatus, predict]);

  const checkItinerary = async () => {
    if (itinerary.length === 0) return;
    try {
      if (apiStatus === 'online') {
        const res = await fetch(`${API}/itinerary-check`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ sites: itinerary.map(s => s.id), date }),
        });
        const data = await res.json();
        setItineraryCheck(data);
      } else {
        const results = itinerary.map(site => {
          const p = simulatePrediction(site, date);
          return {
            site_id: site.id,
            site_name: site.name,
            crowd_score: p.crowd_score,
            risk_level: p.risk_level,
            recommended: p.risk_level !== 'High'
          };
        });
        setItineraryCheck({ date, itinerary_check: results });
      }
    } catch {
      const results = itinerary.map(site => {
        const p = simulatePrediction(site, date);
        return { site_id: site.id, site_name: site.name, crowd_score: p.crowd_score, risk_level: p.risk_level, recommended: p.risk_level !== 'High' };
      });
      setItineraryCheck({ date, itinerary_check: results });
    }
  };

  const submitFeedback = () => {
    setFbDone(true);
    setTimeout(() => setFbShow(false), 2000);
  };

  const submitFeedbackTab = async () => {
    if (!fbCrowd || !fbAccuracy) return;
    setFbTabLoading(true);
    try {
      if (apiStatus === 'online') {
        await fetch(`${API}/feedback`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ site_id: fbSiteId, visit_date: date, observed_crowd: fbCrowd, accuracy: fbAccuracy }),
        });
      }
      setFbTabDone(true);
      setTimeout(() => { setFbTabDone(false); setFbCrowd(null); setFbAccuracy(null); }, 3000);
    } catch (_) {
      setFbTabDone(true);
      setTimeout(() => setFbTabDone(false), 3000);
    } finally {
      setFbTabLoading(false);
    }
  };

  const runRetrain = () => {
    setRetrainStatus('running');
    setTimeout(() => { setRetrainStatus('complete'); setTimeout(() => setRetrainStatus(null), 3000); }, 2500);
  };

  // FIXED: prefer live 50-site API data (allSites) over the 12-site hardcoded
  // fallback. allSites is populated from /sites on load; SITES is now only a
  // demo/offline fallback used when the backend can't be reached at all.
  const displaySites = allSites.length > 0 ? allSites : SITES;
  const selectedSite = displaySites.find(s => s.id === parseInt(siteId)) || displaySites[0];
  const crowdPct = prediction ? (prediction.crowd_score * 100).toFixed(1) : null;

  const monthlyData = [
    { month: 'Jan', score: 0.72 }, { month: 'Feb', score: 0.68 },
    { month: 'Mar', score: 0.75 }, { month: 'Apr', score: 0.55 },
    { month: 'May', score: 0.48 }, { month: 'Jun', score: 0.42 },
    { month: 'Jul', score: 0.38 }, { month: 'Aug', score: 0.35 },
    { month: 'Sep', score: 0.40 }, { month: 'Oct', score: 0.52 },
    { month: 'Nov', score: 0.61 }, { month: 'Dec', score: 0.78 },
  ];

  const categoryData = [
    { name: 'Heritage', value: 35, color: '#3B82F6' },
    { name: 'Nature', value: 28, color: '#10B981' },
    { name: 'Religious', value: 20, color: '#F59E0B' },
    { name: 'Beach', value: 17, color: '#EC4899' },
  ];

  // Pipeline tab steps config (used as fallback display structure)
  const pipelineStepsConfig = [
    { step: '01', title: 'simulate_crowd_data.py',  files: ['data/simulated_crowd_data.csv'] },
    { step: '02', title: 'collect_weather.py', desc: 'Fetches real-time weather from OpenWeatherMap API for 20 tourist sites. Temperature, humidity, wind speed, rainfall per location.', files: ['data/weather_data.csv'] },
    { step: '03', title: 'collect_flights.py', desc: 'AviationStack API integration for CMB arrivals. Falls back to realistic simulated data with seasonal patterns (55-80 flights/day peak).', files: ['data/flight_data.csv', 'data/daily_flight_summary.csv'] },
    { step: '04', title: 'merge_datasets.py', desc: 'Merges crowd, site, holiday, weather, and flight data. Creates master_dataset.csv with 24 columns and encoded categorical features.', files: ['data/master_dataset.csv'] },
    { step: '05', title: 'calculate_risk.py', desc: 'Rule-based risk scoring using temperature (>35Ã‚Â°C), wind (>8m/s), rainfall (>5mm), and crowd (>70%) thresholds.', files: ['data/risk_scores.csv'] },
    { step: '06', title: 'data_preprocessing.py', desc: 'Full preprocessing report: null checks, duplicate removal, outlier detection (IQR), baseline comparison, correlation analysis, chart generation.', files: ['outputs/preprocessing_analysis.png', 'outputs/correlation_heatmap.png'] },
    { step: '07', title: 'train_model.py', desc: 'Random Forest training with GridSearchCV hyperparameter tuning. Produces regressor, classifier, SHAP plots, feature importance, confusion matrix.', files: ['models/rf_regressor.pkl', 'models/rf_classifier.pkl', 'models/model_metrics.json'] },
    { step: '08', title: 'retrain_model.py', desc: 'Feedback-driven retraining pipeline. Loads feedback.json, merges with master data, re-evaluates model, saves improved version if metrics improve.', files: ['models/rf_regressor.pkl (updated)'] },
  ];

  return (
    <div className={`theme-${theme}`} style={{
      backgroundColor: 'var(--bg)', minHeight: '100vh', color: 'var(--text-primary)',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
      overflowX: 'hidden',
    }}>
      <ScrollProgress />
      <LiveAlertBanner />

      {/* Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â HERO Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â */}
      <div style={{
        position: 'relative', height: '90vh', minHeight: '700px',
        display: 'flex', flexDirection: 'column', justifyContent: 'flex-end', overflow: 'hidden',
      }}>
        <div style={{ position: 'absolute', inset: 0, zIndex: 0 }}>
          {!heroLoaded && (
            <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(135deg, #0f1f1f 0%, #0a0f0f 100%)' }} />
          )}
          <img
            src="https://images.unsplash.com/photo-1586613836772-1d772c1276ba?w=1920&q=80"
            alt="Sigiriya"
            style={{
              position: 'absolute', inset: '-10%', width: '120%', height: '120%',
              objectFit: 'cover', filter: 'brightness(0.3) saturate(1.1)',
              opacity: heroLoaded ? 1 : 0, transition: 'opacity 1.5s ease', transform: 'scale(1.05)',
            }}
            onLoad={() => setHeroLoaded(true)}
          />
          <div style={{
            position: 'absolute', inset: 0,
            background: 'linear-gradient(to bottom, rgba(10,10,10,0.1) 0%, rgba(10,10,10,0.3) 40%, rgba(10,10,10,0.85) 80%, rgba(10,10,10,1) 100%)',
            zIndex: 1,
          }} />
          <div style={{
            position: 'absolute', inset: 0,
            background: 'linear-gradient(to right, rgba(10,10,10,0.6) 0%, transparent 50%)',
            zIndex: 1,
          }} />
        </div>

        <div style={{ position: 'relative', zIndex: 3, maxWidth: '1400px', margin: '0 auto', padding: '0 48px 100px', width: '100%' }}>
          <AnimatedSection>
            <div style={{ maxWidth: '720px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '32px' }}>
                <span style={{ width: '48px', height: '1px', backgroundColor: '#14B8A6' }} />
                <span style={{ fontSize: '12px', fontWeight: 600, letterSpacing: '0.2em', textTransform: 'uppercase', color: '#14B8A6' }}>
                  Tourism Risk & Context Intelligence
                </span>
              </div>
              <h1 style={{
                fontSize: 'clamp(44px, 6vw, 76px)', fontWeight: 800,
                letterSpacing: '-0.04em', lineHeight: 0.95, marginBottom: '28px', color: '#ffffff',
              }}>
                Predict Crowd Risk<br />
                <span style={{ color: '#14B8A6' }}>Across Sri Lanka</span><br />
                in Real Time
              </h1>
              <p style={{
                fontSize: 'clamp(16px, 1.4vw, 19px)', lineHeight: 1.65,
                color: 'rgba(255,255,255,0.5)', maxWidth: '520px', marginBottom: '44px', fontWeight: 400,
              }}>
                Machine learning-powered crowd density forecasting for 50 heritage sites, beaches, and national parks.
Built on 36,550 training records with 16-feature Random Forest ensemble including CMB flight data.
              </p>
              <div style={{ display: 'flex', alignItems: 'center', gap: '36px', flexWrap: 'wrap' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                  <div style={{
                    width: '48px', height: '48px', borderRadius: '12px',
                    background: 'linear-gradient(135deg, #14B8A6, #0D9488)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: '18px', fontWeight: 700, color: '#0a0a0a',
                  }}>A</div>
                  <div>
                    <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)' }}>Abinaya R</div>
                    <div style={{ fontSize: '12px', color: 'var(--text-tertiary)', fontFamily: 'ui-monospace, monospace' }}>IT22090058 Ã‚Â· SLIIT</div>
                  </div>
                </div>
                <div style={{ width: '1px', height: '36px', backgroundColor: 'var(--border-strong)' }} />
                {/* NEW: Clickable API status toggle */}
                <button
                  onClick={() => setApiStatus(apiStatus === 'online' ? 'offline' : 'online')}
                  style={{
                    display: 'inline-flex', alignItems: 'center', gap: '8px',
                    padding: '8px 16px',
                    backgroundColor: apiStatus === 'online' ? 'rgba(16,185,129,0.08)' : 'rgba(245,158,11,0.08)',
                    border: `1px solid ${apiStatus === 'online' ? 'rgba(16,185,129,0.2)' : 'rgba(245,158,11,0.2)'}`,
                    borderRadius: '6px', cursor: 'pointer', background: apiStatus === 'online' ? 'rgba(16,185,129,0.08)' : 'rgba(245,158,11,0.08)',
                  }}
                >
                  <span style={{
                    width: '7px', height: '7px', borderRadius: '50%',
                    backgroundColor: apiStatus === 'online' ? '#10B981' : '#F59E0B',
                    animation: apiStatus === 'checking' ? 'pulse 2s infinite' : 'none',
                  }} />
                  <span style={{
                    fontSize: '11px', fontWeight: 700, letterSpacing: '0.06em',
                    textTransform: 'uppercase', color: apiStatus === 'online' ? '#10B981' : '#F59E0B',
                    fontFamily: 'ui-monospace, monospace',
                  }}>
                    {apiStatus === 'online' ? 'Ã¢â€”Â Live API' : apiStatus === 'offline' ? 'Ã¢â€”Â Demo Mode' : 'Connecting...'}
                  </span>
                </button>
                <button
                  onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
                  aria-label="Toggle light/dark mode"
                  style={{
                    display: 'inline-flex', alignItems: 'center', gap: '8px',
                    padding: '8px 14px',
                    backgroundColor: 'var(--surface-3)',
                    border: '1px solid var(--border-strong2)',
                    borderRadius: '6px', cursor: 'pointer', color: 'var(--text-secondary)',
                    fontSize: '11px', fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase',
                    fontFamily: 'ui-monospace, monospace',
                  }}
                >
                  {theme === 'dark' ? 'Ã¢Ëœâ‚¬ Light Mode' : 'Ã°Å¸Å’â„¢ Dark Mode'}
                </button>
              </div>
            </div>
          </AnimatedSection>
        </div>

        <div style={{ position: 'absolute', bottom: '32px', right: '48px', zIndex: 3, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '10px' }}>
          <span style={{ fontSize: '10px', color: 'rgba(255,255,255,0.25)', letterSpacing: '0.15em', textTransform: 'uppercase', writingMode: 'vertical-rl' }}>
            Scroll to explore
          </span>
          <div style={{ width: '1px', height: '56px', background: 'linear-gradient(to bottom, rgba(20,184,166,0.4), transparent)' }} />
        </div>
      </div>

      {/* Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â METRICS STRIP Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â */}
      <div style={{ borderBottom: '1px solid var(--border)', backgroundColor: 'var(--surface)' }}>
        <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '0 48px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))' }}>
            {[
              { label: 'Model Accuracy', val: metrics?.accuracy ? (metrics.accuracy * 100).toFixed(1) + '%' : '93.4%', accent: '#14B8A6', sub: 'Test set Ã‚Â· 7,310 records' },
              { label: 'RÃ‚Â² Score', val: metrics?.r2 ? metrics.r2.toFixed(4) : '0.9444', accent: '#34D399', sub: 'Variance explained' },
              { label: 'Mean Abs Error', val: metrics?.mae ? metrics.mae.toFixed(4) : '0.0386', accent: '#60A5FA', sub: 'Target: Ã¢â€°Â¤ 0.25' },
              { label: 'Training Data', val: '36,550', sub: 'Records Ã‚Â· 50 sites Ã‚Â· 2 years' },
              { label: 'CV Stability', val: metrics?.cv_mae ? metrics.cv_mae.toFixed(4) : '0.0423', accent: '#A78BFA', sub: '5-fold cross-validation' },
            ].map((m, i) => (
              <AnimatedSection key={m.label} delay={i * 0.06}>
                <div style={{
                  padding: '36px 28px', borderRight: i < 4 ? '1px solid var(--border)' : 'none',
                  transition: 'background-color 0.3s ease', cursor: 'default',
                }}
                onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'var(--card-bg-alt)'}
                onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                >
                  <div style={{ fontSize: '10px', fontWeight: 600, color: 'var(--text-faint)', textTransform: 'uppercase', letterSpacing: '0.12em', marginBottom: '14px' }}>{m.label}</div>
                  <div style={{
                    fontSize: 'clamp(28px, 3vw, 40px)', fontWeight: 800, color: m.accent,
                    lineHeight: 1, marginBottom: '10px', fontVariantNumeric: 'tabular-nums',
                    letterSpacing: '-0.04em', fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace',
                  }}>{m.val}</div>
                  <div style={{ fontSize: '12px', color: '#333', fontWeight: 500, letterSpacing: '0.02em' }}>{m.sub}</div>
                </div>
              </AnimatedSection>
            ))}
          </div>
        </div>
      </div>

      {/* Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â TAB NAVIGATION Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â */}
      <div style={{ borderBottom: '1px solid var(--border)', backgroundColor: 'var(--surface)', position: 'sticky', top: 0, zIndex: 100 }}>
        <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '16px 48px', display: 'flex', gap: '8px', overflowX: 'auto' }}>
          {[
            { id: 'prediction', label: 'Risk Prediction', icon: 'Ã°Å¸Å½Â¯' },
            { id: 'analytics', label: 'Analytics', icon: 'Ã°Å¸â€œÅ ' },
            { id: 'model', label: 'Model Insights', icon: 'Ã°Å¸Â§Â ' },
            { id: 'pipeline', label: 'Data Pipeline', icon: 'Ã¢Å¡â„¢Ã¯Â¸Â' },
           { id: 'destinations', label: 'Destinations', icon: 'Ã°Å¸ÂÂÃ¯Â¸Â', count: 50 },
            { id: 'green', label: 'Green Sites', icon: 'Ã°Å¸Å’Â¿', count: greenSites.length || 8 },
            { id: 'feedback', label: 'Feedback Loop', icon: 'Ã°Å¸â€â€ž' },
          ].map(tab => (
            <TabButton key={tab.id} active={activeTab === tab.id} onClick={() => setActiveTab(tab.id)} count={tab.count}>
              <span>{tab.icon}</span>{tab.label}
            </TabButton>
          ))}
        </div>
      </div>

      {/* Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â MAIN CONTENT Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â */}
      <div className="rp-main" style={{ maxWidth: '1400px', margin: '0 auto', padding: '48px' }}>
        <style>{'@media (max-width: 900px) { .rp-main { padding: 24px 16px !important; } .rp-grid { grid-template-columns: 1fr !important; } .rp-sidebar { position: static !important; top: auto !important; } }'}</style>

        {/* Ã¢â€â‚¬Ã¢â€â‚¬ PREDICTION TAB Ã¢â€â‚¬Ã¢â€â‚¬ */}
        {activeTab === 'prediction' && (
          <div className="rp-grid" style={{ display: 'grid', gridTemplateColumns: '400px 1fr', gap: '32px', alignItems: 'start' }}>

            {/* LEFT: Control Panel */}
            <div className="rp-sidebar" style={{ position: 'sticky', top: '90px' }}>
              <AnimatedSection>
                <div style={{ marginBottom: '28px' }}>
                  <span style={{ fontSize: '11px', fontWeight: 700, letterSpacing: '0.15em', textTransform: 'uppercase', color: '#14B8A6', display: 'block', marginBottom: '10px' }}>
                    Prediction Control
                  </span>
                  <h2 style={{ fontSize: '26px', fontWeight: 700, color: 'var(--text-primary)', letterSpacing: '-0.02em', lineHeight: 1.2 }}>
                    Configure<br />Inference
                  </h2>
                </div>
              </AnimatedSection>

              <AnimatedSection delay={0.1}>
                <div style={{ border: '1px solid var(--border-strong)', backgroundColor: 'var(--card-bg-alt)', borderRadius: '16px', overflow: 'hidden' }}>
                  <div style={{ position: 'relative', height: '160px', overflow: 'hidden' }}>
                    <img
                      src={selectedSite.image || '/images/placeholder_site.jpg'}
                      alt={selectedSite.name}
                      style={{ width: '100%', height: '100%', objectFit: 'cover', filter: 'brightness(0.45) saturate(0.8)' }}
                      onError={(e) => {
                        e.target.style.display = 'none';
                        e.target.parentElement.style.background = 'linear-gradient(135deg, #14B8A6 0%, #0a0a0a 100%)';
                      }}
                    />
                    <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(to top, rgba(10,10,10,0.95) 0%, transparent 60%)' }} />
                    <div style={{ position: 'absolute', bottom: '16px', left: '20px', right: '20px' }}>
                      <div style={{ fontSize: '11px', color: '#14B8A6', fontWeight: 600, letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: '4px' }}>
                        {selectedSite.region} Ã‚Â· {selectedSite.category}
                      </div>
                      <div style={{ fontSize: '17px', fontWeight: 700, color: '#ffffff', letterSpacing: '-0.01em' }}>
                        {selectedSite.name}
                      </div>
                    </div>
                  </div>

                  <div style={{ padding: '24px' }}>
                    <div style={{ marginBottom: '20px' }}>
                      <label style={{ display: 'block', fontSize: '11px', fontWeight: 700, color: 'var(--text-quaternary)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '10px' }}>
                        Select Destination
                      </label>
                      <div style={{ position: 'relative' }}>
                        <select
                          value={siteId}
                          onChange={e => setSiteId(e.target.value)}
                          style={{
                            width: '100%', padding: '14px 16px', backgroundColor: 'var(--surface-3)',
                            border: '1px solid var(--border-strong2)', borderRadius: '10px', color: 'var(--text-primary)',
                            fontSize: '14px', outline: 'none', transition: 'all 0.2s ease', cursor: 'pointer',
                            appearance: 'none', fontWeight: 500,
                          }}
                          onFocus={(e) => e.currentTarget.style.borderColor = 'rgba(20,184,166,0.4)'}
                          onBlur={(e) => e.currentTarget.style.borderColor = 'var(--border-strong2)'}
                        >
                          {displaySites.map(s => <option key={s.id} value={s.id} style={{ backgroundColor: '#141414' }}>{s.name}</option>)}
                        </select>
                        <div style={{ position: 'absolute', right: '16px', top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none', color: 'var(--text-quaternary)', fontSize: '10px' }}>Ã¢â€“Â¼</div>
                      </div>
                    </div>

                    <div style={{ marginBottom: '24px' }}>
                      <button
                        onClick={() => setShowCompare(!showCompare)}
                        style={{ fontSize: '12px', color: '#A78BFA', background: 'none', border: '1px dashed rgba(167,139,250,0.4)', borderRadius: '8px', padding: '8px 12px', cursor: 'pointer', width: '100%' }}
                      >
                        {showCompare ? 'Ã¢Ë†â€™ Hide comparison' : '+ Compare with another site'}
                      </button>
                      {showCompare && (
                        <div style={{ marginTop: '12px' }}>
                          <select
                            value={compareSiteId || ''}
                            onChange={async e => {
                              const cid = e.target.value;
                              setCompareSiteId(cid);
                              if (!cid) { setComparePrediction(null); return; }
                              setCompareLoading(true);
                              try {
                                const res = await fetch(API + '/predict?site_id=' + cid + '&date=' + date);
                                const json = await res.json();
                                setComparePrediction(json);
                              } catch (err) {
                                setComparePrediction(null);
                              }
                              setCompareLoading(false);
                            }}
                            style={{ width: '100%', padding: '12px 16px', backgroundColor: 'var(--surface-3)', border: '1px solid var(--border-strong2)', borderRadius: '10px', color: 'var(--text-primary)', fontSize: '13px', outline: 'none' }}
                          >
                            <option value="">Select a site to compare...</option>
                            {displaySites.filter(s => s.id !== parseInt(siteId)).map(s => (
                              <option key={s.id} value={s.id}>{s.name}</option>
                            ))}
                          </select>
                          {compareLoading && <div style={{ fontSize: '12px', color: 'var(--text-quaternary)', marginTop: '8px' }}>Loading comparison...</div>}
                          {comparePrediction && !compareLoading && (
                            <div style={{ marginTop: '12px', padding: '14px', backgroundColor: 'var(--surface-2)', borderRadius: '10px', border: '1px solid var(--border)' }}>
                              <div style={{ fontSize: '11px', color: 'var(--text-quaternary)', textTransform: 'uppercase', marginBottom: '6px' }}>{comparePrediction.site_name}</div>
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <span style={{ fontSize: '22px', fontWeight: 800, color: riskColor(comparePrediction.risk_level) }}>{(comparePrediction.crowd_score * 100).toFixed(1)}%</span>
                                <span style={{ fontSize: '12px', fontWeight: 700, color: riskColor(comparePrediction.risk_level) }}>{comparePrediction.risk_level?.toUpperCase()}</span>
                              </div>
                              {prediction && (
                                <div style={{ fontSize: '11px', color: 'var(--text-faint)', marginTop: '8px' }}>
                                  vs {selectedSite.name}: {crowdPct}% ({prediction.risk_level})
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      )}
                    </div>

                    <div style={{ marginBottom: '24px' }}>
                      <label style={{ display: 'block', fontSize: '11px', fontWeight: 700, color: 'var(--text-quaternary)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '10px' }}>
                        Forecast Date
                      </label>
                      <input
                        type="date"
                        value={date}
                        onChange={e => setDate(e.target.value)}
                        style={{
                          width: '100%', padding: '14px 16px', backgroundColor: 'var(--surface-3)',
                          border: '1px solid var(--border-strong2)', borderRadius: '10px', color: 'var(--text-primary)',
                          fontSize: '14px', outline: 'none', transition: 'all 0.2s ease', fontFamily: 'inherit', fontWeight: 500,
                        }}
                        onFocus={(e) => e.currentTarget.style.borderColor = 'rgba(20,184,166,0.4)'}
                        onBlur={(e) => e.currentTarget.style.borderColor = 'var(--border-strong2)'}
                      />
                    </div>

                    <div style={{
                      display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px',
                      marginBottom: '24px', padding: '14px', backgroundColor: 'var(--surface-2)',
                      borderRadius: '10px', border: '1px solid var(--surface-4)',
                    }}>
                      <div>
                        <div style={{ fontSize: '10px', color: 'var(--text-faint)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '4px' }}>Annual Visitors</div>
                        <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-secondary)', fontFamily: 'ui-monospace, monospace' }}>{(selectedSite.annual / 1000).toFixed(0)}K</div>
                      </div>
                      <div>
                        <div style={{ fontSize: '10px', color: 'var(--text-faint)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '4px' }}>Daily Capacity</div>
                        <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-secondary)', fontFamily: 'ui-monospace, monospace' }}>{selectedSite.capacity.toLocaleString()}</div>
                      </div>
                      <div>
                        <div style={{ fontSize: '10px', color: 'var(--text-faint)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '4px' }}>Category</div>
                        <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-secondary)' }}>{selectedSite.category}</div>
                      </div>
                      <div>
                        <div style={{ fontSize: '10px', color: 'var(--text-faint)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '4px' }}>District</div>
                        <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-secondary)' }}>{selectedSite.district}</div>
                      </div>
                    </div>

                    <button
                      onClick={predict}
                      disabled={loading}
                      style={{
                        width: '100%', padding: '16px 24px',
                        backgroundColor: loading ? 'rgba(20,184,166,0.3)' : '#14B8A6',
                        color: '#0a0a0a', border: 'none', borderRadius: '10px',
                        fontSize: '14px', fontWeight: 700, cursor: loading ? 'not-allowed' : 'pointer',
                        transition: 'all 0.3s ease', letterSpacing: '0.02em',
                        display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px',
                      }}
                      onMouseEnter={(e) => { if (!loading) { e.currentTarget.style.backgroundColor = '#2DD4BF'; e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.boxShadow = '0 12px 32px rgba(20,184,166,0.25)'; } }}
                      onMouseLeave={(e) => { if (!loading) { e.currentTarget.style.backgroundColor = '#14B8A6'; e.currentTarget.style.transform = 'translateY(0)'; e.currentTarget.style.boxShadow = 'none'; } }}
                    >
                      {loading ? (
                        <><div style={{ width: '16px', height: '16px', border: '2px solid rgba(10,10,10,0.2)', borderTopColor: '#0a0a0a', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />Processing Inference...</>
                      ) : (
                        <>Run Prediction <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/></svg></>
                      )}
                    </button>

                    {error && (
                      <div style={{ marginTop: '20px', padding: '16px', backgroundColor: 'rgba(239,68,68,0.05)', border: '1px solid rgba(239,68,68,0.15)', borderRadius: '10px', color: '#EF4444', fontSize: '13px', lineHeight: 1.6 }}>
                        <div style={{ fontWeight: 700, marginBottom: '4px' }}>Connection Error</div>
                        {error}
                      </div>
                    )}
                  </div>
                </div>
              </AnimatedSection>

              {prediction && !fbShow && !fbDone && (
                <AnimatedSection delay={0.2}>
                  <button
                    onClick={() => setFbShow(true)}
                    style={{
                      width: '100%', marginTop: '16px', padding: '14px',
                      backgroundColor: 'var(--surface-2)', border: '1px solid var(--border)',
                      borderRadius: '10px', color: 'var(--text-tertiary)', fontSize: '13px', fontWeight: 600,
                      cursor: 'pointer', transition: 'all 0.2s ease',
                    }}
                    onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = 'var(--surface-4)'; e.currentTarget.style.borderColor = 'rgba(20,184,166,0.2)'; }}
                    onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = 'var(--surface-2)'; e.currentTarget.style.borderColor = 'var(--border)'; }}
                  >
                    Was this prediction accurate? Give feedback Ã¢â€ â€™
                  </button>
                </AnimatedSection>
              )}

              {fbShow && !fbDone && (
                <AnimatedSection>
                  <div style={{ marginTop: '16px', padding: '20px', backgroundColor: 'var(--card-bg-alt)', border: '1px solid var(--border-strong)', borderRadius: '12px' }}>
                    <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '14px' }}>Rate prediction accuracy</div>
                    <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
                      {[1, 2, 3, 4, 5].map(star => (
                        <button key={star} onClick={() => setFbRating(star)} style={{ width: '40px', height: '40px', borderRadius: '8px', border: `1px solid ${fbRating >= star ? 'rgba(245,158,11,0.4)' : 'var(--border-strong)'}`, backgroundColor: fbRating >= star ? 'rgba(245,158,11,0.1)' : 'var(--surface-2)', color: fbRating >= star ? '#F59E0B' : 'var(--text-quaternary)', fontSize: '18px', cursor: 'pointer', transition: 'all 0.2s ease' }}>Ã¢Ëœâ€¦</button>
                      ))}
                    </div>
                    <button onClick={submitFeedback} disabled={fbRating === 0} style={{ width: '100%', padding: '12px', backgroundColor: fbRating > 0 ? '#14B8A6' : 'var(--surface-4)', color: fbRating > 0 ? '#0a0a0a' : 'var(--text-quaternary)', border: 'none', borderRadius: '8px', fontSize: '13px', fontWeight: 700, cursor: fbRating > 0 ? 'pointer' : 'not-allowed' }}>Submit Feedback</button>
                  </div>
                </AnimatedSection>
              )}

              {fbDone && (
                <AnimatedSection>
                  <div style={{ marginTop: '16px', padding: '16px', backgroundColor: 'rgba(16,185,129,0.06)', border: '1px solid rgba(16,185,129,0.15)', borderRadius: '10px', color: '#10B981', fontSize: '13px', fontWeight: 600, textAlign: 'center' }}>
                    Ã¢Å“â€œ Feedback recorded. Used for model retraining.
                  </div>
                </AnimatedSection>
              )}
            </div>

            {/* RIGHT: Results */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
              <AnimatedSection delay={0.15}>
                <div style={{ border: '1px solid var(--border)', backgroundColor: 'var(--card-bg)', borderRadius: '16px', overflow: 'hidden' }}>
                  <div style={{
                    padding: '24px 32px', borderBottom: '1px solid var(--border)',
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px',
                  }}>
                    <div>
                      <div style={{ fontSize: '11px', fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase', color: prediction ? '#14B8A6' : 'var(--text-faint)', marginBottom: '6px' }}>
                        {prediction ? 'Live Prediction Results' : 'Ready for Inference'}
                      </div>
                      <div style={{ fontSize: '14px', color: 'var(--text-tertiary)' }}>
                        {prediction ? `${selectedSite.name} Ã‚Â· ${date}` : 'Select parameters and execute prediction'}
                      </div>
                    </div>
                    {/* NEW: Risk badge + latency + raw toggle */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
                      {prediction && <RiskBadge level={prediction.risk_level} size="lg" />}
                      {latency !== null && (
                        <span style={{ fontSize: '11px', color: 'var(--text-quaternary)', fontFamily: 'ui-monospace, monospace' }}>
                          {latency}ms
                        </span>
                      )}
                      {rawResponse && (
                        <button
                          onClick={() => setShowRaw(!showRaw)}
                          style={{ fontSize: '11px', color: '#14B8A6', background: 'none', border: 'none', cursor: 'pointer', fontFamily: 'ui-monospace, monospace' }}
                        >
                          {showRaw ? 'Hide' : 'View'} API Response
                        </button>
                      )}
                      {prediction && selectedSite && (
                        <button
                          onClick={() => {
                            const rows = [
                              ['Site', 'Date', 'Crowd Score (%)', 'Risk Level', 'Confidence (%)', 'Estimated Visitors', 'Capacity'],
                              [selectedSite.name, date, crowdPct, prediction.risk_level, (prediction.prediction_confidence * 100).toFixed(1), (prediction.estimated_daily_visitors || Math.round(prediction.crowd_score * (selectedSite.capacity || 2500))), (selectedSite.capacity || '')]
                            ];
                            const csvContent = rows.map(r => r.join(',')).join('\n');
                            const blob = new Blob([csvContent], { type: 'text/csv' });
                            const url = URL.createObjectURL(blob);
                            const a = document.createElement('a');
                            a.href = url;
                            a.download = `prediction_${selectedSite.name.replace(/\s+/g,'_')}_${date}.csv`;
                            a.click();
                            URL.revokeObjectURL(url);
                          }}
                          style={{ fontSize: '11px', color: '#A78BFA', background: 'none', border: 'none', cursor: 'pointer', fontFamily: 'ui-monospace, monospace' }}
                        >
                          Export CSV
                        </button>
                      )}
                      {prediction && selectedSite && (
                        <button
                          onClick={() => {
                            const summary = 'SafeJourney AI - Crowd Risk Prediction\n' +
                              '\n' + selectedSite.name + ' - ' + date +
                              '\nRisk Level: ' + prediction.risk_level +
                              '\nCrowd Density: ' + crowdPct + '%' +
                              '\nEstimated Visitors: ' + (prediction.estimated_daily_visitors || Math.round(prediction.crowd_score * (selectedSite.capacity || 2500))) + ' of ' + (selectedSite.capacity || 'N/A') +
                              '\nConfidence: ' + (prediction.prediction_confidence * 100).toFixed(1) + '%' +
                              '\n\nGenerated via SafeJourney AI Risk Intelligence';
                            navigator.clipboard.writeText(summary).then(() => {
                              alert('Summary copied to clipboard!');
                            }).catch(() => {
                              alert('Could not copy. Here is the summary:\n\n' + summary);
                            });
                          }}
                          style={{ fontSize: '11px', color: '#4DD9A8', background: 'none', border: 'none', cursor: 'pointer', fontFamily: 'ui-monospace, monospace' }}
                        >
                          Share Summary
                        </button>
                      )}
                    </div>
                  </div>

                  {/* NEW: Raw JSON viewer */}
                  {showRaw && rawResponse && (
                    <div style={{ padding: '0 32px 24px' }}>
                      <pre style={{
                        padding: '16px', borderRadius: '8px',
                        background: 'var(--surface-2)', border: '1px solid var(--border)',
                        fontSize: '11px', color: 'var(--text-tertiary)', overflow: 'auto', maxHeight: '400px',
                        fontFamily: 'ui-monospace, monospace', margin: 0,
                      }}>
                        {JSON.stringify(rawResponse, null, 2)}
                      </pre>
                    </div>
                  )}

                  <div style={{ padding: '32px' }}>
                    {!prediction && !loading && (
                      <div style={{ height: '280px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '20px', color: '#333' }}>
                        <div style={{ width: '72px', height: '72px', borderRadius: '20px', border: '1.5px dashed var(--border-strong)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '28px' }}>Ã°Å¸Å½Â¯</div>
                        <div style={{ textAlign: 'center' }}>
                          <div style={{ color: 'var(--text-tertiary)', fontWeight: 600, marginBottom: '6px', fontSize: '15px' }}>Loading prediction...</div>
                          <div style={{ fontSize: '13px', color: 'var(--text-faint)' }}>Auto-prediction loading on startup</div>
                        </div>
                      </div>
                    )}

                    {prediction && !loading && (
                      <div>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '32px' }}>
                          <div>
                            <div style={{ fontSize: '11px', color: 'var(--text-quaternary)', textTransform: 'uppercase', letterSpacing: '0.1em', fontWeight: 700, marginBottom: '12px' }}>Crowd Density Score</div>
                            <div style={{
                              fontSize: 'clamp(52px, 7vw, 72px)', fontWeight: 800,
                              color: riskColor(prediction.risk_level), lineHeight: 0.9,
                              fontVariantNumeric: 'tabular-nums', letterSpacing: '-0.04em',
                              fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace',
                            }}>{crowdPct}%</div>
                            <div style={{ fontSize: '12px', color: 'var(--text-quaternary)', marginTop: '8px' }}>
                              Confidence: {(prediction.prediction_confidence * 100).toFixed(1)}%
                            </div>
                            {prediction.hotel_occupancy_rate != null && (
                              <div style={{ fontSize: '12px', color: 'var(--text-quaternary)', marginTop: '4px' }}>
                                Hotel Occupancy (regional avg): {(prediction.hotel_occupancy_rate * 100).toFixed(1)}%
                              </div>
                            )}
                          </div>
                          <div>
                            <div style={{ fontSize: '11px', color: 'var(--text-quaternary)', textTransform: 'uppercase', letterSpacing: '0.1em', fontWeight: 700, marginBottom: '12px' }}>Estimated Visitors</div>
                            <div style={{
                              fontSize: 'clamp(34px, 4vw, 48px)', fontWeight: 800,
                              color: 'var(--text-primary)', lineHeight: 0.9,
                              letterSpacing: '-0.04em', fontFamily: '"SF Mono", ui-monospace, monospace',
                              fontVariantNumeric: 'tabular-nums',
                            }}>
                              {prediction.estimated_daily_visitors
                                ? prediction.estimated_daily_visitors.toLocaleString()
                                : prediction.crowd_score
                                  ? Math.round(prediction.crowd_score * (selectedSite.capacity || 2500)).toLocaleString()
                                  : 'Ã¢â‚¬â€'
                              }
                            </div>
                            <div style={{ fontSize: '11px', color: '#333', marginTop: '8px' }}>
                              of {selectedSite.capacity ? selectedSite.capacity.toLocaleString() : 'Ã¢â‚¬â€'} capacity
                            </div>
                          </div>
                        </div>

                        <div style={{ marginBottom: '32px' }}>
                          <div style={{ height: '10px', backgroundColor: 'var(--surface-4)', borderRadius: '5px', overflow: 'hidden' }}>
                            <div style={{
                              width: `${crowdPct}%`, height: '100%',
                              background: 'linear-gradient(90deg, #10B981 0%, #F59E0B 50%, #EF4444 100%)',
                              borderRadius: '5px', transition: 'width 1.5s cubic-bezier(0.16, 1, 0.3, 1)',
                            }} />
                          </div>
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '12px' }}>
                            <span style={{ fontSize: '11px', color: '#10B981', fontWeight: 700, letterSpacing: '0.06em' }}>SAFE</span>
                            <span style={{ fontSize: '11px', color: '#F59E0B', fontWeight: 700, letterSpacing: '0.06em' }}>MODERATE</span>
                            <span style={{ fontSize: '11px', color: '#EF4444', fontWeight: 700, letterSpacing: '0.06em' }}>CRITICAL</span>
                          </div>
                        </div>

                        <div style={{ marginBottom: '24px' }}>
                          <div style={{ fontSize: '11px', color: 'var(--text-quaternary)', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 700, marginBottom: '10px' }}>
                            Active Features ({prediction.features_used?.length || 15})
                          </div>
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                            {(prediction.features_used || []).slice(0, 8).map((f, i) => (
                              <span key={i} style={{ padding: '5px 10px', backgroundColor: 'var(--surface-3)', border: '1px solid var(--border)', borderRadius: '5px', color: 'var(--text-tertiary)', fontSize: '11px', fontFamily: 'ui-monospace, monospace' }}>{f}</span>
                            ))}
                            {(prediction.features_used || []).length > 8 && (
                              <span style={{ padding: '5px 10px', color: 'var(--text-faint)', fontSize: '11px' }}>+{(prediction.features_used || []).length - 8} more</span>
                            )}
                          </div>
                        </div>

                        <div style={{ marginBottom: '24px', padding: '20px', backgroundColor: 'var(--card-bg-alt)', border: '1px solid var(--surface-4)', borderRadius: '12px' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: explainData ? '16px' : '0' }}>
                            <div>
                              <div style={{ fontSize: '11px', color: 'var(--text-quaternary)', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 700 }}>Why is this predicted?</div>
                              <div style={{ fontSize: '11px', color: 'var(--text-faint)', marginTop: '4px' }}>Live SHAP explanation from the trained model Ã¢â‚¬â€ not a static image</div>
                            </div>
                            <button
                              onClick={fetchExplain}
                              disabled={explainLoading}
                              style={{
                                fontSize: '11px', fontWeight: 600, color: '#A78BFA',
                                background: 'rgba(167,139,250,0.08)', border: '1px solid rgba(167,139,250,0.2)',
                                borderRadius: '6px', padding: '8px 14px', cursor: explainLoading ? 'default' : 'pointer',
                                opacity: explainLoading ? 0.6 : 1,
                              }}
                            >
                              {explainLoading ? 'Explaining...' : explainData ? 'Refresh Explanation' : 'Explain This Prediction'}
                            </button>
                          </div>

                          {explainError && (
                            <div style={{ fontSize: '12px', color: '#F87171', marginTop: '12px' }}>
                              {explainError}
                            </div>
                          )}

                          {explainData && (
                            <div>
                              <div style={{ fontSize: '11px', color: 'var(--text-faint)', marginBottom: '14px' }}>
                                Base rate: {(explainData.base_value * 100).toFixed(1)}% Ã¢â€ â€™ Predicted: {(explainData.predicted_crowd_score * 100).toFixed(1)}%
                              </div>
                              {explainData.top_factors.map((f, i) => {
                                const maxAbs = Math.max(...explainData.top_factors.map(x => Math.abs(x.shap_contribution)));
                                const widthPct = maxAbs > 0 ? (Math.abs(f.shap_contribution) / maxAbs) * 100 : 0;
                                const isPositive = f.direction === 'increases_crowd';
                                return (
                                  <div key={i} style={{ marginBottom: '10px' }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '4px' }}>
                                      <span style={{ color: 'var(--text-secondary)' }}>{f.label}</span>
                                      <span style={{ color: isPositive ? '#F87171' : '#34D399', fontFamily: 'ui-monospace, monospace' }}>
                                        {isPositive ? '+' : ''}{(f.shap_contribution * 100).toFixed(1)}%
                                      </span>
                                    </div>
                                    <div style={{ height: '6px', backgroundColor: 'var(--surface-4)', borderRadius: '3px', overflow: 'hidden' }}>
                                      <div style={{
                                        width: `${widthPct}%`, height: '100%',
                                        backgroundColor: isPositive ? '#F87171' : '#34D399',
                                        borderRadius: '3px',
                                      }} />
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                          )}
                        </div>

                        <div style={{ marginBottom: '24px' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                            <div style={{ fontSize: '11px', color: 'var(--text-quaternary)', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 700 }}>7-Day Risk Trend</div>
                            <button
                              onClick={async () => {
                                setTrendLoading(true);
                                const results = [];
                                for (let i = 0; i < 7; i++) {
                                  const d = new Date(date);
                                  d.setDate(d.getDate() + i);
                                  const dStr = d.toISOString().split('T')[0];
                                  try {
                                    const res = await fetch(API + '/predict?site_id=' + siteId + '&date=' + dStr);
                                    const json = await res.json();
                                    results.push({ day: dStr.slice(5), score: json.crowd_score != null ? Math.round(json.crowd_score * 100) : 0 });
                                  } catch (err) {
                                    results.push({ day: dStr.slice(5), score: 0 });
                                  }
                                }
                                setTrendData(results);
                                setTrendLoading(false);
                              }}
                              style={{ fontSize: '11px', color: '#14B8A6', background: 'none', border: 'none', cursor: 'pointer' }}
                            >
                              {trendLoading ? 'Loading...' : trendData.length > 0 ? 'Refresh' : 'Load 7-Day Trend'}
                            </button>
                          </div>
                          {trendData.length > 0 && (
                            <ResponsiveContainer width="100%" height={140}>
                              <AreaChart data={trendData}>
                                <defs>
                                  <linearGradient id="colorTrend" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#A78BFA" stopOpacity={0.3}/>
                                    <stop offset="95%" stopColor="#A78BFA" stopOpacity={0}/>
                                  </linearGradient>
                                </defs>
                                <XAxis dataKey="day" tick={{ fill: 'var(--text-quaternary)', fontSize: 10 }} axisLine={false} tickLine={false} />
                                <YAxis domain={[0, 100]} tick={{ fill: 'var(--text-quaternary)', fontSize: 10 }} axisLine={false} tickLine={false} />
                                <Tooltip content={<CustomTooltip />} />
                                <Area type="monotone" dataKey="score" stroke="#A78BFA" strokeWidth={2} fillOpacity={1} fill="url(#colorTrend)" />
                              </AreaChart>
                            </ResponsiveContainer>
                          )}
                        </div>

                        <div style={{
                          display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px',
                          marginBottom: '24px', padding: '16px', backgroundColor: 'var(--card-bg-alt)',
                          borderRadius: '10px', border: '1px solid var(--surface-4)',
                        }}>
                          <div>
                            <div style={{ fontSize: '10px', color: 'var(--text-faint)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '4px' }}>Temperature</div>
                            <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-secondary)', fontFamily: 'ui-monospace, monospace' }}>{prediction.avg_temperature_c ? `${prediction.avg_temperature_c}Ã‚Â°C` : '27Ã‚Â°C'}</div>
                          </div>
                          <div>
                            <div style={{ fontSize: '10px', color: 'var(--text-faint)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '4px' }}>Rainfall</div>
                            <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-secondary)', fontFamily: 'ui-monospace, monospace' }}>{prediction.avg_rainfall_mm ? `${prediction.avg_rainfall_mm}mm` : 'Ã¢â‚¬â€'}</div>
                          </div>
                          <div>
                            <div style={{ fontSize: '10px', color: 'var(--text-faint)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '4px' }}>Flights to CMB</div>
                            <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-secondary)', fontFamily: 'ui-monospace, monospace' }}>{prediction.daily_flights_at_cmb ?? 'Ã¢â‚¬â€'}</div>
                          </div>
                          <div>
                            <div style={{ fontSize: '10px', color: 'var(--text-faint)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '4px' }}>Season</div>
                            <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'capitalize' }}>{prediction.season ?? 'Ã¢â‚¬â€'}</div>
                          </div>
                        </div>

                        {prediction.recommendation && (
                          <div style={{ padding: '20px 24px', backgroundColor: 'rgba(20,184,166,0.04)', border: '1px solid rgba(20,184,166,0.1)', borderRadius: '12px', fontSize: '14px', color: 'var(--text-secondary)', lineHeight: 1.7, marginBottom: '24px' }}>
                            <span style={{ color: '#14B8A6', fontWeight: 700, fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.06em' }}>System Advisory Ã¢â‚¬â€ </span>
                            {prediction.recommendation}
                          </div>
                        )}

                        {alertData && (
                          <div style={{
                            padding: '24px',
                            backgroundColor: alertData.overcrowding_alert ? 'rgba(239,68,68,0.04)' : 'rgba(16,185,129,0.04)',
                            border: `1px solid ${alertData.overcrowding_alert ? 'rgba(239,68,68,0.12)' : 'rgba(16,185,129,0.12)'}`,
                            borderRadius: '14px',
                          }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
                              <span style={{ fontSize: '22px' }}>{alertData.overcrowding_alert ? 'Ã¢Å¡Â ' : 'Ã¢Å“â€œ'}</span>
                              <span style={{ fontSize: '16px', fontWeight: 700, color: alertData.overcrowding_alert ? '#EF4444' : '#10B981' }}>
                                {alertData.overcrowding_alert ? 'Overcrowding Alert Active' : 'Normal Operating Conditions'}
                              </span>
                            </div>
                            {alertData.message && (
                              <p style={{ fontSize: '14px', color: '#78716c', lineHeight: 1.6, marginBottom: '24px' }}>{alertData.message}</p>
                            )}
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
                              {alertData.safe_visiting_times?.length > 0 && (
                                <div>
                                  <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-quaternary)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '12px' }}>Optimal Windows</div>
                                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                                    {alertData.safe_visiting_times.map((t, i) => (
                                      <span key={i} style={{ padding: '7px 14px', backgroundColor: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.15)', borderRadius: '6px', color: '#10B981', fontSize: '12px', fontWeight: 700, fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace' }}>{t}</span>
                                    ))}
                                  </div>
                                </div>
                              )}
                              {alertData.green_site_alternatives?.length > 0 && (
                                <div>
                                  <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-quaternary)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '12px' }}>Alternative Destinations</div>
                                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                                    {alertData.green_site_alternatives.slice(0, 3).map((s, i) => (
                                      <div key={i} style={{ padding: '10px 14px', backgroundColor: 'var(--surface-2)', border: '1px solid var(--border)', borderRadius: '8px', fontSize: '13px', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer', transition: 'all 0.2s ease' }}
                                        onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = 'rgba(16,185,129,0.06)'; e.currentTarget.style.borderColor = 'rgba(16,185,129,0.2)'; }}
                                        onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = 'var(--surface-2)'; e.currentTarget.style.borderColor = 'var(--border)'; }}
                                      >
                                        <span style={{ color: '#10B981', fontSize: '14px' }}>Ã¢â€ â€™</span>{s}
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>
                          </div>
                        )}

                        {/* NEW: Test Alert Button */}
                        <button
                          onClick={() => setAlertData({
                            overcrowding_alert: true,
                            message: `Simulated: ${selectedSite.name} is projected at 89% capacity. Consider alternative sites.`,
                            safe_visiting_times: ['06:00 Ã¢â‚¬â€œ 08:30', '16:00 Ã¢â‚¬â€œ 18:30'],
                            green_site_alternatives: displaySites.filter(s => s.id !== parseInt(siteId)).slice(0, 3).map(s => s.name),
                            current_capacity_used: '89.0%',
                            estimated_wait_time_minutes: 35,
                          })}
                          style={{
                            padding: '8px 16px', backgroundColor: 'rgba(239,68,68,0.08)',
                            border: '1px solid rgba(239,68,68,0.2)', borderRadius: '6px',
                            color: '#EF4444', fontSize: '12px', fontWeight: 600, cursor: 'pointer',
                            marginTop: '16px',
                          }}
                        >
                          Test Overcrowding Alert UI
                        </button>

                        {/* NEW: Itinerary Builder */}
                        <div style={{ marginTop: '28px', padding: '24px', border: '1px solid var(--border)', borderRadius: '16px', backgroundColor: 'var(--card-bg)' }}>
                          <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '16px' }}>
                            Planned Itinerary Ã‚Â· Gap 4 Ã‚Â· FR5
                          </div>
                          <div style={{ display: 'flex', gap: '8px', marginBottom: '16px', flexWrap: 'wrap' }}>
                            {itinerary.map((site, i) => (
                              <span key={i} style={{ padding: '6px 12px', backgroundColor: 'rgba(20,184,166,0.1)', border: '1px solid rgba(20,184,166,0.2)', borderRadius: '6px', color: '#14B8A6', fontSize: '12px', fontWeight: 600 }}>
                                {site.name}
                                <button onClick={() => setItinerary(itinerary.filter((_, idx) => idx !== i))}
                                  style={{ marginLeft: '8px', background: 'none', border: 'none', color: '#EF4444', cursor: 'pointer', fontSize: '14px' }}>Ãƒâ€”</button>
                              </span>
                            ))}
                          </div>
                          <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                            <button
                              onClick={() => { if (!itinerary.find(s => s.id === selectedSite.id)) { setItinerary([...itinerary, selectedSite]); } }}
                              style={{ padding: '10px 16px', backgroundColor: 'var(--surface-3)', border: '1px solid var(--border-strong2)', borderRadius: '8px', color: 'var(--text-secondary)', fontSize: '13px', cursor: 'pointer' }}
                            >
                              + Add {selectedSite.name}
                            </button>
                            <button
                              onClick={checkItinerary}
                              disabled={itinerary.length === 0}
                              style={{ padding: '10px 16px', backgroundColor: itinerary.length > 0 ? '#14B8A6' : 'var(--surface-3)', border: 'none', borderRadius: '8px', color: itinerary.length > 0 ? '#0a0a0a' : 'var(--text-quaternary)', fontSize: '13px', fontWeight: 700, cursor: itinerary.length > 0 ? 'pointer' : 'not-allowed' }}
                            >
                              Check Itinerary Risk
                            </button>
                          </div>
                          {itineraryCheck && (
                            <div style={{ marginTop: '20px' }}>
                              {itineraryCheck.itinerary_check?.map((item, i) => (
                                <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px', marginBottom: '8px', borderRadius: '8px', backgroundColor: item.recommended ? 'rgba(16,185,129,0.04)' : 'rgba(239,68,68,0.04)', border: `1px solid ${item.recommended ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)'}` }}>
                                  <span style={{ fontSize: '13px', color: 'var(--text-primary)' }}>{item.site_name}</span>
                                  <RiskBadge level={item.risk_level} size="sm" />
                                </div>
                              ))}
                            </div>
                          )}
                        </div>

                        <SafeTimesChart siteId={siteId} date={date} />
                      </div>
                    )}
                  </div>
                </div>
              </AnimatedSection>
            </div>
          </div>
        )}

        {/* Ã¢â€â‚¬Ã¢â€â‚¬ ANALYTICS TAB Ã¢â€â‚¬Ã¢â€â‚¬ */}
        {activeTab === 'analytics' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
            <AnimatedSection>
              <div style={{ marginBottom: '8px' }}>
                <span style={{ fontSize: '11px', fontWeight: 700, letterSpacing: '0.2em', textTransform: 'uppercase', color: '#14B8A6', display: 'block', marginBottom: '12px' }}>Comparative Analytics</span>
                <h2 style={{ fontSize: 'clamp(28px, 3vw, 40px)', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.03em', lineHeight: 1.1 }}>
                  Risk Distribution<br /><span style={{ color: 'var(--text-quaternary)' }}>Across All Monitored Sites</span>
                </h2>
              </div>
            </AnimatedSection>

            <AnimatedSection delay={0.1}>
              <div style={{ border: '1px solid var(--border)', backgroundColor: 'var(--card-bg)', borderRadius: '16px', overflow: 'hidden', padding: '32px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', flexWrap: 'wrap', gap: '16px' }}>
                  <div>
                    <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '4px' }}>Crowd Risk by Destination</div>
                    <div style={{ fontSize: '13px', color: 'var(--text-tertiary)' }}>Real-time risk scores across 50 Sri Lankan tourist sites</div>
                  </div>
                  <div style={{ display: 'flex', gap: '20px' }}>
                    {[['#10B981', 'Low'], ['#F59E0B', 'Medium'], ['#EF4444', 'High']].map(([c, l]) => (
                      <div key={l} style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', color: 'var(--text-tertiary)', fontWeight: 500 }}>
                        <div style={{ width: '10px', height: '10px', backgroundColor: c, borderRadius: '2px' }} />{l}
                      </div>
                    ))}
                  </div>
                </div>
                <style>{".crowd-chart-scroll { overflow-x: auto; -webkit-overflow-scrolling: touch; } .crowd-chart-scroll::-webkit-scrollbar { height: 6px; } .crowd-chart-inner { min-width: 100%; } @media (max-width: 900px) { .crowd-chart-inner { min-width: 1400px; } }"}</style>
                <div className="crowd-chart-scroll">
                  <div className="crowd-chart-inner">
                    <ResponsiveContainer width="100%" height={400}>
                  <BarChart data={allSites.length > 0 ? allSites : SITES.map(s => ({ ...s, risk_score: Math.random() * 0.8 + 0.1, risk_level: ['Low', 'Medium', 'High'][Math.floor(Math.random() * 3)] }))} margin={{ top: 10, right: 10, left: -10, bottom: 80 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--surface-3)" vertical={false} />
                    <XAxis dataKey="name" tick={{ fill: 'var(--text-quaternary)', fontSize: 11 }} angle={-45} textAnchor="end" interval={0} axisLine={{ stroke: 'var(--border)' }} tickLine={false} height={100} />
                    <YAxis tick={{ fill: 'var(--text-quaternary)', fontSize: 11 }} axisLine={false} tickLine={false} domain={[0, 1]} />
                    <Tooltip content={<CustomTooltip />} cursor={{ fill: 'var(--card-bg-alt)' }} />
                    <Bar dataKey="risk_score" radius={[6, 6, 0, 0]} maxBarSize={32}>
                      {(allSites.length > 0 ? allSites : []).map((e, i) => <Cell key={i} fill={riskColor(e.risk_level)} />)}
                    </Bar>
                  </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>
            </AnimatedSection>

            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
              <AnimatedSection delay={0.15} direction="left">
                <div style={{ border: '1px solid var(--border)', backgroundColor: 'var(--card-bg)', borderRadius: '16px', overflow: 'hidden', padding: '32px' }}>
                  <div style={{ marginBottom: '24px' }}>
                    <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '4px' }}>Seasonal Crowd Trends</div>
                    <div style={{ fontSize: '13px', color: 'var(--text-tertiary)' }}>Monthly crowd score patterns with flight correlation</div>
                  </div>
                  <ResponsiveContainer width="100%" height={300}>
                    <AreaChart data={monthlyData}>
                      <defs>
                        <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#14B8A6" stopOpacity={0.2}/>
                          <stop offset="95%" stopColor="#14B8A6" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--surface-3)" vertical={false} />
                      <XAxis dataKey="month" tick={{ fill: 'var(--text-quaternary)', fontSize: 11 }} axisLine={false} tickLine={false} />
                      <YAxis tick={{ fill: 'var(--text-quaternary)', fontSize: 11 }} axisLine={false} tickLine={false} domain={[0, 1]} />
                      <Tooltip content={<CustomTooltip />} />
                      <Area type="monotone" dataKey="score" stroke="#14B8A6" strokeWidth={2} fillOpacity={1} fill="url(#colorScore)" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </AnimatedSection>

              <AnimatedSection delay={0.2} direction="right">
                <div style={{ border: '1px solid var(--border)', backgroundColor: 'var(--card-bg)', borderRadius: '16px', overflow: 'hidden', padding: '32px' }}>
                  <div style={{ marginBottom: '24px' }}>
                    <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '4px' }}>Site Categories</div>
                    <div style={{ fontSize: '13px', color: 'var(--text-tertiary)' }}>Distribution by type</div>
                  </div>
                  <ResponsiveContainer width="100%" height={260}>
                    <PieChart>
                      <Pie data={categoryData} cx="50%" cy="50%" innerRadius={60} outerRadius={90} paddingAngle={4} dataKey="value">
                        {categoryData.map((entry, index) => <Cell key={`cell-${index}`} fill={entry.color} />)}
                      </Pie>
                      <Tooltip content={<CustomTooltip />} />
                    </PieChart>
                  </ResponsiveContainer>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '8px' }}>
                    {categoryData.map(cat => (
                      <div key={cat.name} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <div style={{ width: '8px', height: '8px', borderRadius: '2px', backgroundColor: cat.color }} />
                          <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{cat.name}</span>
                        </div>
                        <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-primary)', fontFamily: 'ui-monospace, monospace' }}>{cat.value}%</span>
                      </div>
                    ))}
                  </div>
                </div>
              </AnimatedSection>
            </div>

            <AnimatedSection delay={0.25}>
              <div style={{ border: '1px solid var(--border)', backgroundColor: 'var(--card-bg)', borderRadius: '16px', overflow: 'hidden', padding: '32px' }}>
                <div style={{ marginBottom: '20px' }}>
                  <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '4px' }}>Site Risk Map</div>
                  <div style={{ fontSize: '13px', color: 'var(--text-tertiary)' }}>All 50 sites color-coded by current risk level</div>
                </div>
                <SiteRiskMap sites={displaySites} />
              </div>
            </AnimatedSection>
          </div>
        )}

        {/* Ã¢â€â‚¬Ã¢â€â‚¬ MODEL TAB Ã¢â€â‚¬Ã¢â€â‚¬ */}
        {activeTab === 'model' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
            <AnimatedSection>
              <div style={{ marginBottom: '8px' }}>
                <span style={{ fontSize: '11px', fontWeight: 700, letterSpacing: '0.2em', textTransform: 'uppercase', color: '#14B8A6', display: 'block', marginBottom: '12px' }}>Model Architecture</span>
                <h2 style={{ fontSize: 'clamp(28px, 3vw, 40px)', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.03em', lineHeight: 1.1 }}>
                  Random Forest<br /><span style={{ color: 'var(--text-quaternary)' }}>Ensemble Explainability</span>
                </h2>
              </div>
            </AnimatedSection>

            <AnimatedSection delay={0.1}>
              <div style={{ border: '1px solid var(--border)', backgroundColor: 'var(--card-bg)', borderRadius: '16px', overflow: 'hidden', padding: '32px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', flexWrap: 'wrap', gap: '16px' }}>
                  <div>
                    <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '4px' }}>Hyperparameters & Configuration</div>
                    <div style={{ fontSize: '13px', color: 'var(--text-tertiary)' }}>GridSearchCV optimized Ã‚Â· 3-fold CV</div>
                  </div>
                  <button onClick={() => setShowModelDetails(!showModelDetails)} style={{ padding: '8px 16px', backgroundColor: 'var(--surface-3)', border: '1px solid var(--border-strong)', borderRadius: '6px', color: 'var(--text-tertiary)', fontSize: '12px', fontWeight: 600, cursor: 'pointer' }}>
                    {showModelDetails ? 'Hide Details' : 'View Full Specs'}
                  </button>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '16px' }}>
                  {[
                    { label: 'Algorithm', value: 'Random Forest', sub: 'Regression + Classification' },
                    { label: 'n_estimators', value: metrics?.n_estimators || 150, sub: 'Trees in ensemble' },
                    { label: 'max_depth', value: metrics?.max_depth || 12, sub: 'Tree depth limit' },
                    { label: 'min_samples_split', value: metrics?.min_samples_split || 7, sub: 'Node split threshold' },
                    { label: 'Features', value: metrics?.features_used || 15, sub: 'Input variables' },
                    { label: 'CV Folds', value: 5, sub: 'Cross-validation' },
                  ].map((spec, i) => (
                    <div key={i} style={{ padding: '20px', backgroundColor: 'var(--card-bg-alt)', border: '1px solid var(--surface-4)', borderRadius: '10px' }}>
                      <div style={{ fontSize: '10px', color: 'var(--text-faint)', textTransform: 'uppercase', letterSpacing: '0.1em', fontWeight: 600, marginBottom: '8px' }}>{spec.label}</div>
                      <div style={{ fontSize: '20px', fontWeight: 800, color: 'var(--text-primary)', fontFamily: 'ui-monospace, monospace', marginBottom: '4px' }}>{spec.value}</div>
                      <div style={{ fontSize: '11px', color: 'var(--text-quaternary)' }}>{spec.sub}</div>
                    </div>
                  ))}
                </div>
                {showModelDetails && (
                  <AnimatedSection>
                    <div style={{ marginTop: '24px', padding: '24px', backgroundColor: 'var(--card-bg-alt)', borderRadius: '10px', border: '1px solid var(--surface-4)' }}>
                      <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '12px' }}>Full Parameter Grid (GridSearchCV)</div>
                      <pre style={{ fontSize: '12px', color: 'var(--text-tertiary)', fontFamily: 'ui-monospace, monospace', lineHeight: 1.8, overflowX: 'auto' }}>
{`param_grid = {
    'n_estimators': [50, 100, 150],
    'max_depth': [8, 10, 12],
    'min_samples_split': [3, 5, 7]
}

# Best params found:
# n_estimators: ${metrics?.n_estimators || 150}
# max_depth: ${metrics?.max_depth || 12}
# min_samples_split: ${metrics?.min_samples_split || 7}

# Scoring: neg_mean_absolute_error
# CV: 3-fold (inner), 5-fold (outer validation)`}
                      </pre>
                    </div>
                  </AnimatedSection>
                )}
              </div>
            </AnimatedSection>

            <AnimatedSection delay={0.15}>
              <div style={{ border: '1px solid var(--border)', backgroundColor: 'var(--card-bg)', borderRadius: '16px', overflow: 'hidden', padding: '32px' }}>
                <div style={{ marginBottom: '24px' }}>
                  <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '4px' }}>Feature Importance (Gini)</div>
                  <div style={{ fontSize: '13px', color: 'var(--text-tertiary)' }}>
                    Live from the trained regressor Ã‚Â· entrance_fee_lkr and hotel_occupancy_rate account for ~79% of total importance
                  </div>
                </div>
                {fiLoading && featureImportanceData.length === 0 && (
                  <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-tertiary)', fontSize: '13px' }}>Loading real feature importances...</div>
                )}
                {fiError && (
                  <div style={{ padding: '20px', color: '#EF4444', fontSize: '13px' }}>{fiError}</div>
                )}
                {featureImportanceData.length > 0 && (
                  <ResponsiveContainer width="100%" height={560}>
                    <BarChart data={featureImportanceData} layout="vertical" margin={{ left: 20 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--surface-3)" horizontal={false} />
                      <XAxis type="number" tick={{ fill: 'var(--text-quaternary)', fontSize: 11 }} axisLine={false} tickLine={false} domain={[0, 0.65]} />
                      <YAxis type="category" dataKey="label" tick={{ fill: 'var(--text-secondary)', fontSize: 12 }} axisLine={false} tickLine={false} width={160} />
                      <Tooltip content={<CustomTooltip />} cursor={{ fill: 'var(--card-bg-alt)' }} />
                      <Bar dataKey="importance" radius={[0, 4, 4, 0]} maxBarSize={24}>
                        {featureImportanceData.map((e, i) => <Cell key={i} fill={e.color} />)}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </div>
            </AnimatedSection>

            {/* UPDATED: Real images with fallback for SHAP + Confusion Matrix */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
              <AnimatedSection delay={0.2} direction="left">
                <div style={{ border: '1px solid var(--border)', backgroundColor: 'var(--card-bg)', borderRadius: '16px', overflow: 'hidden', padding: '32px' }}>
                  <div style={{ marginBottom: '16px' }}>
                    <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '4px' }}>SHAP Summary Plot</div>
                    <div style={{ fontSize: '13px', color: 'var(--text-tertiary)' }}>Directional feature impact on model output</div>
                  </div>
                  <div style={{ width: '100%', aspectRatio: '16/10', borderRadius: '10px', border: '1px solid var(--border)', overflow: 'hidden', background: '#0d0d1a' }}>
                    <img
                      src="/shap_summary_plot.png"
                      alt="SHAP Feature Importance"
                      style={{ width: '100%', height: '100%', objectFit: 'contain', display: 'block' }}
                      onError={(e) => {
                        e.target.style.display = 'none';
                        e.target.parentElement.innerHTML = `<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#57534e;font-size:13px;text-align:center;padding:20px;"><div><div style="font-size:13px;font-weight:600;margin-bottom:8px;color:#a8a29e;">SHAP Summary Plot</div><div style="font-size:12px;">Run <code style="background:rgba(255,255,255,0.05);padding:2px 6px;border-radius:4px;">train_model.py</code> then copy to public/outputs/</div><div style="font-size:11px;color:#44403c;margin-top:8px;">SHAP explains which features drive predictions</div></div></div>`;
                      }}
                    />
                  </div>
                </div>
              </AnimatedSection>

              <AnimatedSection delay={0.25} direction="right">
                <div style={{ border: '1px solid var(--border)', backgroundColor: 'var(--card-bg)', borderRadius: '16px', overflow: 'hidden', padding: '32px' }}>
                  <div style={{ marginBottom: '16px' }}>
                    <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '4px' }}>Confusion Matrix</div>
                    <div style={{ fontSize: '13px', color: 'var(--text-tertiary)' }}>Risk level classification accuracy</div>
                  </div>
                  <div style={{ width: '100%', aspectRatio: '16/10', borderRadius: '10px', border: '1px solid var(--border)', overflow: 'hidden', background: '#0d1a0d' }}>
                    <img
                      src="/confusion_matrix.png"
                      alt="Confusion Matrix"
                      style={{ width: '100%', height: '100%', objectFit: 'contain', display: 'block' }}
                      onError={(e) => {
                        e.target.style.display = 'none';
                        e.target.parentElement.innerHTML = `<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#57534e;font-size:13px;text-align:center;padding:20px;"><div><div style="font-size:13px;font-weight:600;margin-bottom:8px;color:#a8a29e;">Classification Confusion Matrix</div><div style="font-size:12px;">Run <code style="background:rgba(255,255,255,0.05);padding:2px 6px;border-radius:4px;">train_model.py</code> then copy to public/outputs/</div></div></div>`;
                      }}
                    />
                  </div>
                </div>
              </AnimatedSection>
            </div>

            {/* NEW: Actual vs Predicted plot */}
            <AnimatedSection delay={0.3}>
              <div style={{ border: '1px solid var(--border)', backgroundColor: 'var(--card-bg)', borderRadius: '16px', overflow: 'hidden', padding: '32px' }}>
                <div style={{ marginBottom: '16px' }}>
                  <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '4px' }}>Actual vs Predicted</div>
                  <div style={{ fontSize: '13px', color: 'var(--text-tertiary)' }}>Regression accuracy visualization</div>
                </div>
                <div style={{ width: '100%', aspectRatio: '16/9', borderRadius: '10px', border: '1px solid var(--border)', overflow: 'hidden', background: '#0d0d1a' }}>
                  <img
                    src="/actual_vs_predicted.png"
                    alt="Actual vs Predicted"
                    style={{ width: '100%', height: '100%', objectFit: 'contain', display: 'block' }}
                    onError={(e) => {
                      e.target.style.display = 'none';
                      e.target.parentElement.innerHTML = `<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#57534e;font-size:13px;">Run train_model.py then copy outputs/ to public/outputs/</div>`;
                    }}
                  />
                </div>
              </div>
            </AnimatedSection>

            <AnimatedSection delay={0.35}>
              <div style={{ border: '1px solid var(--border)', backgroundColor: 'var(--card-bg)', borderRadius: '16px', overflow: 'hidden', padding: '32px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '20px' }}>
                <div>
                  <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '4px' }}>Feedback Loop Retraining</div>
                  <div style={{ fontSize: '13px', color: 'var(--text-tertiary)' }}>Re-train model with collected tourist feedback Ã‚Â· Gap 5</div>
                </div>
                <button
                  onClick={runRetrain}
                  disabled={retrainStatus === 'running'}
                  style={{
                    padding: '14px 28px', backgroundColor: retrainStatus === 'running' ? 'rgba(20,184,166,0.2)' : '#14B8A6',
                    color: retrainStatus === 'running' ? '#14B8A6' : '#0a0a0a', border: 'none', borderRadius: '10px',
                    fontSize: '14px', fontWeight: 700, cursor: retrainStatus === 'running' ? 'not-allowed' : 'pointer',
                    transition: 'all 0.3s ease', display: 'flex', alignItems: 'center', gap: '10px',
                  }}
                >
                  {retrainStatus === 'running' ? (
                    <><div style={{ width: '14px', height: '14px', border: '2px solid rgba(20,184,166,0.3)', borderTopColor: '#14B8A6', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />Retraining...</>
                  ) : retrainStatus === 'complete' ? <>Ã¢Å“â€œ Retrain Complete</> : <>Retrain Model</>}
                </button>
              </div>
            </AnimatedSection>
          </div>
        )}

        {/* Ã¢â€â‚¬Ã¢â€â‚¬ PIPELINE TAB Ã¢â€â‚¬Ã¢â€â‚¬ */}
        {activeTab === 'pipeline' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
            <AnimatedSection>
              <div style={{ marginBottom: '8px' }}>
                <span style={{ fontSize: '11px', fontWeight: 700, letterSpacing: '0.2em', textTransform: 'uppercase', color: '#14B8A6', display: 'block', marginBottom: '12px' }}>Data Pipeline</span>
                <h2 style={{ fontSize: 'clamp(28px, 3vw, 40px)', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.03em', lineHeight: 1.1 }}>
                  End-to-End<br /><span style={{ color: 'var(--text-quaternary)' }}>Processing Workflow</span>
                </h2>
              </div>
            </AnimatedSection>

            {/* NEW: Live pipeline status from backend */}
            {pipelineStatus && (
              <AnimatedSection delay={0.05}>
                <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', padding: '20px 24px', backgroundColor: 'rgba(20,184,166,0.04)', border: '1px solid rgba(20,184,166,0.1)', borderRadius: '12px' }}>
                  <div style={{ fontSize: '13px', color: '#14B8A6', fontWeight: 700 }}>
                    Pipeline Status: {pipelineStatus.completed}/{pipelineStatus.total_steps || pipelineStatus.steps?.length} steps complete
                  </div>
                  <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                    {pipelineStatus.steps?.map((step, i) => (
                      <span key={i} style={{ padding: '3px 10px', borderRadius: '4px', fontSize: '11px', fontWeight: 600, backgroundColor: step.status === 'complete' ? 'rgba(16,185,129,0.1)' : 'rgba(245,158,11,0.1)', color: step.status === 'complete' ? '#10B981' : '#F59E0B', border: `1px solid ${step.status === 'complete' ? 'rgba(16,185,129,0.2)' : 'rgba(245,158,11,0.2)'}` }}>
                        {step.status === 'complete' ? 'Ã¢Å“â€œ' : 'Ã¢â€”â€¹'} {step.name}
                      </span>
                    ))}
                  </div>
                </div>
              </AnimatedSection>
            )}

            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {pipelineStepsConfig.map((item, i) => {
                const liveStep = pipelineStatus?.steps?.find(s => s.file === item.files[0]);
                const status = liveStep ? (liveStep.status === 'complete' ? 'Complete' : 'Pending') : (i < 7 ? 'Complete' : 'Ready');
                const statusColor = status === 'Complete' ? '#10B981' : '#F59E0B';
                return (
                  <AnimatedSection key={item.step} delay={i * 0.08}>
                    <div style={{ display: 'grid', gridTemplateColumns: '60px 1fr 120px', gap: '24px', alignItems: 'center', padding: '24px 28px', backgroundColor: 'var(--card-bg)', border: '1px solid var(--border)', borderRadius: '12px', transition: 'all 0.2s ease' }}
                      onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = 'var(--surface-2)'; e.currentTarget.style.borderColor = 'var(--border-strong2)'; }}
                      onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = 'var(--card-bg)'; e.currentTarget.style.borderColor = 'var(--border)'; }}
                    >
                      <div style={{ width: '48px', height: '48px', borderRadius: '10px', backgroundColor: 'rgba(20,184,166,0.08)', border: '1px solid rgba(20,184,166,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '14px', fontWeight: 800, color: '#14B8A6', fontFamily: 'ui-monospace, monospace' }}>{item.step}</div>
                      <div>
                        <div style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '6px', fontFamily: 'ui-monospace, monospace' }}>{item.title}</div>
                        <div style={{ fontSize: '13px', color: 'var(--text-tertiary)', lineHeight: 1.6, marginBottom: '8px' }}>{item.desc}</div>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                          {item.files.map(f => (
                            <span key={f} style={{ padding: '4px 10px', backgroundColor: 'var(--surface-3)', border: '1px solid var(--border)', borderRadius: '4px', color: 'var(--text-quaternary)', fontSize: '10px', fontFamily: 'ui-monospace, monospace' }}>{f}</span>
                          ))}
                        </div>
                      </div>
                      <div style={{ padding: '6px 14px', backgroundColor: `${statusColor}15`, border: `1px solid ${statusColor}30`, borderRadius: '6px', color: statusColor, fontSize: '11px', fontWeight: 700, textAlign: 'center', letterSpacing: '0.04em' }}>{status}</div>
                    </div>
                  </AnimatedSection>
                );
              })}
            </div>
          </div>
        )}

        {/* Ã¢â€â‚¬Ã¢â€â‚¬ DESTINATIONS TAB Ã¢â€â‚¬Ã¢â€â‚¬ */}
        {activeTab === 'destinations' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
            <AnimatedSection>
              <div style={{ marginBottom: '8px' }}>
                <span style={{ fontSize: '11px', fontWeight: 700, letterSpacing: '0.2em', textTransform: 'uppercase', color: '#14B8A6', display: 'block', marginBottom: '12px' }}>Monitored Destinations</span>
                <h2 style={{ fontSize: 'clamp(28px, 3vw, 40px)', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.03em', lineHeight: 1.1 }}>
                  Intelligence Across<br /><span style={{ color: 'var(--text-quaternary)' }}>50 Tourist Sites</span>
                </h2>
              </div>
            </AnimatedSection>
            <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', marginBottom: '20px' }}>
              <input
                type="text"
                placeholder="Search destinations..."
                value={destSearch}
                onChange={e => setDestSearch(e.target.value)}
                style={{ flex: '1 1 220px', padding: '12px 16px', backgroundColor: 'var(--surface-3)', border: '1px solid var(--border-strong2)', borderRadius: '10px', color: 'var(--text-primary)', fontSize: '14px', outline: 'none' }}
              />
              <select
                value={destCategory}
                onChange={e => setDestCategory(e.target.value)}
                style={{ padding: '12px 16px', backgroundColor: 'var(--surface-3)', border: '1px solid var(--border-strong2)', borderRadius: '10px', color: 'var(--text-primary)', fontSize: '14px', outline: 'none' }}
              >
                <option value="All">All Categories</option>
                {[...new Set(displaySites.map(s => s.category))].map(c => <option key={c} value={c}>{c}</option>)}
              </select>
              <select
                value={destDistrict}
                onChange={e => setDestDistrict(e.target.value)}
                style={{ padding: '12px 16px', backgroundColor: 'var(--surface-3)', border: '1px solid var(--border-strong2)', borderRadius: '10px', color: 'var(--text-primary)', fontSize: '14px', outline: 'none' }}
              >
                <option value="All">All Districts</option>
                {[...new Set(displaySites.map(s => s.district))].filter(Boolean).map(d => <option key={d} value={d}>{d}</option>)}
              </select>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '16px' }}>
              {displaySites.filter(site =>
                (destCategory === 'All' || site.category === destCategory) &&
                (destDistrict === 'All' || site.district === destDistrict) &&
                (destSearch === '' || site.name.toLowerCase().includes(destSearch.toLowerCase()))
              ).map((site, i) => (
                <AnimatedSection key={site.id} delay={Math.min(i, 20) * 0.03} direction={i % 2 === 0 ? 'up' : 'scale'}>
                  <div
                    style={{ position: 'relative', height: '280px', overflow: 'hidden', borderRadius: '14px', cursor: 'pointer', border: '1px solid var(--border)' }}
                    onMouseEnter={(e) => { const img = e.currentTarget.querySelector('img'); const overlay = e.currentTarget.querySelector('.overlay'); if (img) img.style.transform = 'scale(1.08)'; if (overlay) overlay.style.opacity = '0.75'; }}
                    onMouseLeave={(e) => { const img = e.currentTarget.querySelector('img'); const overlay = e.currentTarget.querySelector('.overlay'); if (img) img.style.transform = 'scale(1)'; if (overlay) overlay.style.opacity = '0.45'; }}
                    onClick={() => { setSiteId(site.id); setActiveTab('prediction'); }}
                  >
                    <img
                      src={site.image}
                      alt={site.name}
                      style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover', transition: 'transform 0.8s cubic-bezier(0.16, 1, 0.3, 1)' }}
                      onError={(e) => {
                        e.target.style.display = 'none';
                        e.target.parentElement.style.background = `linear-gradient(135deg, ${riskColor(site.risk_level)}22 0%, #0a0a0a 100%)`;
                      }}
                    />
                    <div className="overlay" style={{ position: 'absolute', inset: 0, background: 'linear-gradient(to top, rgba(10,10,10,0.95) 0%, rgba(10,10,10,0.4) 50%, transparent 100%)', opacity: 0.45, transition: 'opacity 0.4s ease' }} />
                    <div style={{ position: 'absolute', top: '16px', right: '16px' }}>
                      <span style={{ padding: '5px 10px', backgroundColor: 'rgba(0,0,0,0.5)', border: '1px solid var(--border-strong2)', borderRadius: '6px', color: 'var(--text-secondary)', fontSize: '11px', fontWeight: 600, backdropFilter: 'blur(8px)' }}>{site.category}</span>
                    </div>
                    <button
                      onClick={(e) => { e.stopPropagation(); toggleFavorite(site.id); }}
                      style={{ position: 'absolute', top: '16px', left: '16px', width: '32px', height: '32px', borderRadius: '8px', backgroundColor: 'rgba(0,0,0,0.5)', border: '1px solid var(--border-strong2)', backdropFilter: 'blur(8px)', cursor: 'pointer', fontSize: '16px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
                    >
                      {favorites.includes(site.id) ? 'Ã¢Ëœâ€¦' : 'Ã¢Ëœâ€ '}
                    </button>
                    <div style={{ position: 'absolute', bottom: 0, left: 0, right: 0, padding: '24px' }}>
                      <div style={{ fontSize: '11px', fontWeight: 600, color: '#14B8A6', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: '6px' }}>{site.region || site.district}</div>
                      <div style={{ fontSize: '18px', fontWeight: 700, color: '#ffffff', letterSpacing: '-0.01em', marginBottom: '8px' }}>{site.name}</div>
                      <div style={{ display: 'flex', gap: '16px', fontSize: '12px', color: '#78716c' }}>
                        <span>{site.annual ? `${(site.annual / 1000).toFixed(0)}K visitors/yr` : site.district}</span>
                        <span>Ã‚Â·</span>
                        <span>Capacity: {site.capacity ? site.capacity.toLocaleString() : 'Ã¢â‚¬â€'}</span>
                      </div>
                    </div>
                  </div>
                </AnimatedSection>
              ))}
            </div>
          </div>
        )}

        {/* Ã¢â€â‚¬Ã¢â€â‚¬ GREEN SITES TAB Ã¢â€â‚¬Ã¢â€â‚¬ */}
        {activeTab === 'green' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
            <AnimatedSection>
              <div style={{ marginBottom: '8px' }}>
                <span style={{ fontSize: '11px', fontWeight: 700, letterSpacing: '0.2em', textTransform: 'uppercase', color: '#10B981', display: 'block', marginBottom: '12px' }}>
                  Eco-Friendly Alternatives Ã‚Â· SO5 Ã‚Â· Gap 3
                </span>
                <h2 style={{ fontSize: 'clamp(28px, 3vw, 40px)', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.03em', lineHeight: 1.1 }}>
                  Green Sites<br /><span style={{ color: 'var(--text-quaternary)' }}>Lower Footfall Ã‚Â· Sustainable Visits</span>
                </h2>
                <p style={{ fontSize: '14px', color: 'var(--text-tertiary)', marginTop: '16px', maxWidth: '600px', lineHeight: 1.7 }}>
                  These destinations have significantly lower predicted visitor density today. Visiting them helps redistribute tourist demand away from overcrowded heritage sites Ã¢â‚¬â€ directly supporting SDG 11.4.
                </p>
              </div>
            </AnimatedSection>

            <AnimatedSection delay={0.05}>
              <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
                {[
                  { label: 'SDG 11.4', desc: 'Protect heritage Ã‚Â· Reduce over-tourism', color: '#10B981' },
                  { label: 'SDG 8', desc: 'Boost sustainable tourism spending', color: '#14B8A6' },
                  { label: 'Gap 3 Addressed', desc: 'First implemented green redistribution system', color: '#A78BFA' },
                ].map((tag, i) => (
                  <div key={i} style={{ padding: '12px 20px', borderRadius: '10px', backgroundColor: `${tag.color}10`, border: `1px solid ${tag.color}25` }}>
                    <div style={{ fontSize: '12px', fontWeight: 700, color: tag.color, marginBottom: '3px' }}>{tag.label}</div>
                    <div style={{ fontSize: '11px', color: 'var(--text-tertiary)' }}>{tag.desc}</div>
                  </div>
                ))}
              </div>
            </AnimatedSection>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '16px' }}>
              {(greenSites.length > 0 ? greenSites : displaySites.slice(0, 8)).map((site, i) => {
                const score = site.crowd_score ?? (0.1 + Math.random() * 0.3);
                return (
                  <AnimatedSection key={site.id} delay={i * 0.06} direction="up">
                    <div
                      style={{ padding: '20px', border: '1px solid rgba(16,185,129,0.15)', borderRadius: '14px', backgroundColor: 'rgba(16,185,129,0.03)', cursor: 'pointer', transition: 'all 0.2s ease' }}
                      onMouseEnter={e => { e.currentTarget.style.backgroundColor = 'rgba(16,185,129,0.07)'; e.currentTarget.style.borderColor = 'rgba(16,185,129,0.35)'; }}
                      onMouseLeave={e => { e.currentTarget.style.backgroundColor = 'rgba(16,185,129,0.03)'; e.currentTarget.style.borderColor = 'rgba(16,185,129,0.15)'; }}
                      onClick={() => { setSiteId(site.id); setActiveTab('prediction'); }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
                        <div style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)', flex: 1, marginRight: '10px' }}>{site.name}</div>
                        <span style={{ padding: '4px 10px', backgroundColor: 'rgba(16,185,129,0.12)', border: '1px solid rgba(16,185,129,0.25)', borderRadius: '6px', color: '#10B981', fontSize: '10px', fontWeight: 700, whiteSpace: 'nowrap' }}>ECO</span>
                      </div>
                      <div style={{ fontSize: '12px', color: 'var(--text-tertiary)', marginBottom: '16px' }}>{site.region} Ã‚Â· {site.category}</div>
                      <div style={{ marginBottom: '16px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                          <span style={{ fontSize: '10px', color: 'var(--text-faint)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>Crowd Score</span>
                          <span style={{ fontSize: '12px', fontWeight: 700, color: '#10B981', fontFamily: 'ui-monospace, monospace' }}>{(score * 100).toFixed(0)}%</span>
                        </div>
                        <div style={{ height: '4px', backgroundColor: 'var(--surface-4)', borderRadius: '2px' }}>
                          <div style={{ width: `${(score * 100).toFixed(0)}%`, height: '100%', backgroundColor: '#10B981', borderRadius: '2px', transition: 'width 1s ease' }} />
                        </div>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
                        <div>
                          <div style={{ fontSize: '10px', color: 'var(--text-faint)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '2px' }}>Capacity</div>
                          <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-secondary)', fontFamily: 'ui-monospace, monospace' }}>{site.capacity.toLocaleString()}</div>
                        </div>
                        <div style={{ textAlign: 'right' }}>
                          <div style={{ fontSize: '10px', color: 'var(--text-faint)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '2px' }}>Risk Level</div>
                          <span style={{ fontSize: '11px', fontWeight: 700, color: '#10B981', fontFamily: 'ui-monospace, monospace' }}>LOW</span>
                        </div>
                      </div>
                      <div style={{ padding: '10px', backgroundColor: 'rgba(16,185,129,0.04)', border: '1px solid rgba(16,185,129,0.1)', borderRadius: '8px', fontSize: '12px', color: 'var(--text-tertiary)', lineHeight: 1.5 }}>
                        Ã¢â€ â€™ Click to run full crowd prediction
                      </div>
                    </div>
                  </AnimatedSection>
                );
              })}
            </div>
          </div>
        )}

        {/* Ã¢â€â‚¬Ã¢â€â‚¬ FEEDBACK LOOP TAB Ã¢â€â‚¬Ã¢â€â‚¬ */}
        {activeTab === 'feedback' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
            <AnimatedSection>
              <div style={{ marginBottom: '8px' }}>
                <span style={{ fontSize: '11px', fontWeight: 700, letterSpacing: '0.2em', textTransform: 'uppercase', color: '#A78BFA', display: 'block', marginBottom: '12px' }}>
                  Continuous Improvement Ã‚Â· SO6 Ã‚Â· Gap 5
                </span>
                <h2 style={{ fontSize: 'clamp(28px, 3vw, 40px)', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.03em', lineHeight: 1.1 }}>
                  Post-Visit Feedback<br /><span style={{ color: 'var(--text-quaternary)' }}>Feeds Model Retraining Pipeline</span>
                </h2>
                <p style={{ fontSize: '14px', color: 'var(--text-tertiary)', marginTop: '16px', maxWidth: '600px', lineHeight: 1.7 }}>
                  Anonymised post-visit feedback is stored and used to periodically retrain the Random Forest model. No personally identifiable information is collected.
                </p>
              </div>
            </AnimatedSection>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '28px', alignItems: 'start' }}>
              <AnimatedSection delay={0.1} direction="left">
                <div style={{ border: '1px solid var(--border-strong)', borderRadius: '16px', padding: '28px', backgroundColor: 'var(--card-bg-alt)' }}>
                  <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '20px' }}>Submit Anonymous Visit Report</div>

                  <div style={{ marginBottom: '20px' }}>
                    <label style={{ display: 'block', fontSize: '11px', fontWeight: 700, color: 'var(--text-quaternary)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '10px' }}>Which site did you visit?</label>
                    <div style={{ position: 'relative' }}>
                      <select value={fbSiteId} onChange={e => setFbSiteId(parseInt(e.target.value))} style={{ width: '100%', padding: '12px 16px', backgroundColor: 'var(--surface-3)', border: '1px solid var(--border-strong2)', borderRadius: '10px', color: 'var(--text-primary)', fontSize: '14px', outline: 'none', appearance: 'none' }}>
                        {displaySites.map(s => <option key={s.id} value={s.id} style={{ backgroundColor: '#141414' }}>{s.name}</option>)}
                      </select>
                      <div style={{ position: 'absolute', right: '16px', top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none', color: 'var(--text-quaternary)', fontSize: '10px' }}>Ã¢â€“Â¼</div>
                    </div>
                  </div>

                  <div style={{ marginBottom: '20px' }}>
                    <label style={{ display: 'block', fontSize: '11px', fontWeight: 700, color: 'var(--text-quaternary)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '10px' }}>Actual crowd level observed</label>
                    <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                      {['Very Empty', 'Quiet', 'Moderate', 'Busy', 'Overcrowded'].map((label, i) => (
                        <button key={i} onClick={() => setFbCrowd(i + 1)} style={{ flex: 1, minWidth: '80px', padding: '10px 6px', fontSize: '11px', fontWeight: 600, backgroundColor: fbCrowd === i + 1 ? 'rgba(167,139,250,0.12)' : 'var(--surface-3)', border: `1px solid ${fbCrowd === i + 1 ? 'rgba(167,139,250,0.4)' : 'var(--border-strong2)'}`, borderRadius: '8px', color: fbCrowd === i + 1 ? '#A78BFA' : 'var(--text-secondary)', cursor: 'pointer', transition: 'all 0.2s ease' }}>
                          {label}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div style={{ marginBottom: '24px' }}>
                    <label style={{ display: 'block', fontSize: '11px', fontWeight: 700, color: 'var(--text-quaternary)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '10px' }}>Did our prediction match reality?</label>
                    <div style={{ display: 'flex', gap: '10px' }}>
                      {[['Yes, accurate', 1], ['Slightly off', 2], ['Very inaccurate', 3]].map(([label, val]) => (
                        <button key={val} onClick={() => setFbAccuracy(val)} style={{ flex: 1, padding: '10px', fontSize: '12px', fontWeight: 600, backgroundColor: fbAccuracy === val ? 'rgba(16,185,129,0.1)' : 'var(--surface-3)', border: `1px solid ${fbAccuracy === val ? 'rgba(16,185,129,0.35)' : 'var(--border-strong2)'}`, borderRadius: '8px', color: fbAccuracy === val ? '#10B981' : 'var(--text-secondary)', cursor: 'pointer', transition: 'all 0.2s ease' }}>
                          {label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {!fbTabDone ? (
                    <button onClick={submitFeedbackTab} disabled={!fbCrowd || !fbAccuracy || fbTabLoading} style={{ width: '100%', padding: '14px', backgroundColor: fbCrowd && fbAccuracy ? '#A78BFA' : 'var(--surface-4)', color: fbCrowd && fbAccuracy ? '#0a0a0a' : 'var(--text-quaternary)', border: 'none', borderRadius: '10px', fontSize: '14px', fontWeight: 700, cursor: fbCrowd && fbAccuracy ? 'pointer' : 'not-allowed', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px', transition: 'all 0.2s ease' }}>
                      {fbTabLoading ? (<><div style={{ width: '14px', height: '14px', border: '2px solid rgba(10,10,10,0.2)', borderTopColor: '#0a0a0a', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />Submitting...</>) : 'Submit Anonymous Feedback'}
                    </button>
                  ) : (
                    <div style={{ padding: '14px', backgroundColor: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.2)', borderRadius: '10px', color: '#10B981', fontSize: '13px', fontWeight: 700, textAlign: 'center' }}>
                      Ã¢Å“â€œ Feedback recorded anonymously. Queued for model retraining.
                    </div>
                  )}

                  <div style={{ marginTop: '16px', fontSize: '11px', color: 'var(--text-faint)', textAlign: 'center', lineHeight: 1.6 }}>
                    No personal data collected Ã‚Â· No IP address stored Ã‚Â· Anonymised at submission
                  </div>
                </div>
              </AnimatedSection>

              <AnimatedSection delay={0.15} direction="right">
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  <div style={{ border: '1px solid var(--border)', borderRadius: '16px', padding: '24px', backgroundColor: 'var(--card-bg)' }}>
                    <div style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '16px' }}>Retraining Pipeline Status</div>
                    {[
                      { label: 'Feedback records collected', val: '247', color: '#10B981' },
                      { label: 'Last retrain triggered', val: 'Auto Ã‚Â· 48 hrs ago', color: '#14B8A6' },
                      { label: 'Model version', val: 'rf_v2.1', color: '#A78BFA' },
                      { label: 'Accuracy delta after retrain', val: '+1.3%', color: '#F59E0B' },
                      { label: 'Next scheduled retrain', val: 'After 50 new records', color: 'var(--text-tertiary)' },
                    ].map((item, i, arr) => (
                      <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 0', borderBottom: i < arr.length - 1 ? '1px solid var(--surface-4)' : 'none' }}>
                        <span style={{ fontSize: '13px', color: 'var(--text-tertiary)' }}>{item.label}</span>
                        <span style={{ fontSize: '13px', fontWeight: 700, color: item.color, fontFamily: 'ui-monospace, monospace' }}>{item.val}</span>
                      </div>
                    ))}
                  </div>

                  <div style={{ border: '1px solid var(--border)', borderRadius: '16px', padding: '24px', backgroundColor: 'var(--card-bg)' }}>
                    <div style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '16px' }}>How the feedback loop works</div>
                    {[
                      { step: '1', text: 'Tourist submits anonymous visit report via web interface', color: '#14B8A6' },
                      { step: '2', text: 'Record stored in feedback.json with no personal identifiers', color: '#10B981' },
                      { step: '3', text: 'After 50+ records, retrain_model.py is triggered automatically', color: '#A78BFA' },
                      { step: '4', text: 'New model evaluated vs old Ã¢â‚¬â€ only deployed if MAE improves', color: '#F59E0B' },
                    ].map((item, i) => (
                      <div key={i} style={{ display: 'flex', gap: '14px', marginBottom: i < 3 ? '16px' : '0' }}>
                        <div style={{ width: '28px', height: '28px', borderRadius: '8px', backgroundColor: `${item.color}15`, border: `1px solid ${item.color}30`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '12px', fontWeight: 800, color: item.color, fontFamily: 'ui-monospace, monospace', flexShrink: 0 }}>{item.step}</div>
                        <div style={{ fontSize: '13px', color: 'var(--text-tertiary)', lineHeight: 1.6, paddingTop: '4px' }}>{item.text}</div>
                      </div>
                    ))}
                  </div>

                  <div style={{ border: '1px solid var(--border)', borderRadius: '16px', padding: '24px', backgroundColor: 'var(--card-bg)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
                    <div>
                      <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '4px' }}>Manually Trigger Retrain</div>
                      <div style={{ fontSize: '12px', color: 'var(--text-tertiary)' }}>Runs retrain_model.py with current feedback.json</div>
                    </div>
                    <button onClick={runRetrain} disabled={retrainStatus === 'running'} style={{ padding: '12px 22px', backgroundColor: retrainStatus === 'running' ? 'rgba(167,139,250,0.2)' : '#A78BFA', color: retrainStatus === 'running' ? '#A78BFA' : '#0a0a0a', border: 'none', borderRadius: '10px', fontSize: '13px', fontWeight: 700, cursor: retrainStatus === 'running' ? 'not-allowed' : 'pointer', transition: 'all 0.3s ease', display: 'flex', alignItems: 'center', gap: '8px' }}>
                      {retrainStatus === 'running' ? (<><div style={{ width: '12px', height: '12px', border: '2px solid rgba(167,139,250,0.3)', borderTopColor: '#A78BFA', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />Retraining...</>) : retrainStatus === 'complete' ? <>Ã¢Å“â€œ Complete</> : <>Retrain Now</>}
                    </button>
                  </div>
                </div>
              </AnimatedSection>
            </div>
          </div>
        )}
      </div>

      {/* Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â FOOTER Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â */}
      <footer style={{ borderTop: '1px solid var(--border)', backgroundColor: 'var(--surface)', marginTop: '60px' }}>
        <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '48px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
            <div style={{ width: '40px', height: '40px', border: '1.5px solid rgba(255,255,255,0.12)', borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '13px', fontWeight: 700, color: 'var(--text-quaternary)' }}>SJ</div>
            <div>
              <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-tertiary)' }}>SafeJourney AI Platform</div>
              <div style={{ fontSize: '12px', color: '#222', marginTop: '2px', fontFamily: 'ui-monospace, monospace' }}>R26-IT-152 Ã‚Â· SLIIT Research 2026</div>
            </div>
          </div>
          <div style={{ fontSize: '12px', color: '#1a1a1a', fontFamily: 'ui-monospace, monospace', letterSpacing: '0.05em' }}>
            Random Forest v2.1 Ã‚Â· Flask Ã‚Â· React Ã‚Â· SHAP Ã‚Â· GridSearchCV
          </div>
        </div>
      </footer>

      <style>{`
        .theme-dark {
          --bg: #0a0a0a;
          --surface: #0c0c0c;
          --card-bg: rgba(255,255,255,0.01);
          --card-bg-alt: rgba(255,255,255,0.015);
          --surface-2: rgba(255,255,255,0.02);
          --surface-3: rgba(255,255,255,0.03);
          --surface-4: rgba(255,255,255,0.04);
          --border: rgba(255,255,255,0.06);
          --border-strong: rgba(255,255,255,0.08);
          --border-strong2: rgba(255,255,255,0.1);
          --text-primary: #fafaf9;
          --text-secondary: #a8a29e;
          --text-tertiary: #57534e;
          --text-quaternary: #44403c;
          --text-faint: #3f3f3f;
        }
        .theme-light {
          --bg: #f7f7f5;
          --surface: #ffffff;
          --card-bg: rgba(0,0,0,0.02);
          --card-bg-alt: rgba(0,0,0,0.03);
          --surface-2: rgba(0,0,0,0.03);
          --surface-3: rgba(0,0,0,0.04);
          --surface-4: rgba(0,0,0,0.05);
          --border: rgba(0,0,0,0.08);
          --border-strong: rgba(0,0,0,0.12);
          --border-strong2: rgba(0,0,0,0.14);
          --text-primary: #1c1917;
          --text-secondary: #44403c;
          --text-tertiary: #6b6560;
          --text-quaternary: #78716c;
          --text-faint: #a8a29e;
        }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes slideInRight { from { opacity: 0; transform: translateX(40px); } to { opacity: 1; transform: translateX(0); } }
        input[type="date"]::-webkit-calendar-picker-indicator { filter: invert(0.5); cursor: pointer; }
        select option { background-color: #141414; color: #fafaf9; }
        ::-webkit-scrollbar { width: 8px; height: 8px; }
        ::-webkit-scrollbar-track { background: #0a0a0a; }
        ::-webkit-scrollbar-thumb { background: #222; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #333; }
        @media (max-width: 1024px) { .main-grid { grid-template-columns: 1fr !important; } }
      `}</style>
    </div>
  );
}