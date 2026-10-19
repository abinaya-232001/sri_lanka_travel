import React, { useState } from 'react';

const MOODS = [
  { emoji: '😊', label: 'Happy',       color: '#E8A020', spots: ['Sigiriya Rock Fortress', 'Mirissa Whale Watching', 'Kandy Cultural Show'] },
  { emoji: '😌', label: 'Relaxed',     color: '#1A9E7A', spots: ['Bentota Beach Resort', 'Nuwara Eliya Tea Estates', 'Peradeniya Gardens'] },
  { emoji: '😰', label: 'Anxious',     color: '#2A7AE8', spots: ['Temple of the Tooth', 'Botanical Gardens', 'Galle Fort (safe zone)'] },
  { emoji: '🤩', label: 'Excited',     color: '#C84B31', spots: ['White Water Rafting Kitulgala', 'Surfing Arugam Bay', 'Pinnawala Safari'] },
  { emoji: '😢', label: 'Melancholic', color: '#7A5CF0', spots: ['Sunset at Galle Fort', 'Tea Plantation Walk', 'Colombo Street Food Tour'] },
  { emoji: '💪', label: 'Adventurous', color: '#1A9E7A', spots: ['Horton Plains Hike', 'Knuckles Mountain Range', 'Yala Night Safari'] },
];

const ITINERARY = [
  { day: 1, title: 'Arrival & Colombo',   sites: ['Colombo Fort', 'Galle Face Green', 'Pettah Market'],             risk: 'MEDIUM' },
  { day: 2, title: 'Cultural Triangle',   sites: ['Sigiriya Rock', 'Dambulla Caves', 'Polonnaruwa'],                risk: 'LOW' },
  { day: 3, title: 'Hill Country',        sites: ['Kandy Temple', 'Peradeniya Gardens', 'Nuwara Eliya'],            risk: 'LOW' },
  { day: 4, title: 'Southern Coast',      sites: ['Galle Fort', 'Mirissa Beach', 'Whale Watching'],                 risk: 'LOW' },
  { day: 5, title: 'Wildlife & Nature',   sites: ['Yala National Park', 'Udawalawe', 'Tissamaharama'],             risk: 'LOW' },
];

const STARTERS = [
  'Plan a 5-day safe route from Colombo',
  'Best spots for solo female travelers',
  'Budget trip under $500',
  'Family-friendly with young children',
];

export default function ItineraryPage() {
  const [mood, setMood]             = useState(null);
  const [detecting, setDetecting]   = useState(false);
  const [days, setDays]             = useState(4);
  const [budget, setBudget]         = useState('medium');
  const [touristType, setTouristType] = useState('general');
  const [generating, setGenerating] = useState(false);
  const [itinerary, setItinerary]   = useState(null);
  const [messages, setMessages]     = useState([
    { role: 'ai', text: "Welcome. I'm the SafeJourney AI Planner — I create safety-aware itineraries for Sri Lanka using A* danger-zone routing. How can I help plan your journey?" }
  ]);
  const [input, setInput]           = useState('');
  const [chatLoading, setChatLoading] = useState(false);

  const detectEmotion = () => {
    setDetecting(true);
    setTimeout(() => {
      setMood(MOODS[Math.floor(Math.random() * MOODS.length)]);
      setDetecting(false);
    }, 2500);
  };

  const generate = () => {
    setGenerating(true);
    setTimeout(() => {
      setItinerary(ITINERARY.slice(0, Math.min(days, 5)));
      setGenerating(false);
    }, 2000);
  };

  const sendMsg = (text) => {
    const msg = text || input;
    if (!msg.trim()) return;
    setInput('');
    setMessages(p => [...p, { role: 'user', text: msg }]);
    setChatLoading(true);
    setTimeout(() => {
      let reply = `I've analysed your request using our ML risk model across 30 Sri Lankan sites. For a ${days}-day journey, I recommend A*-optimised routes bypassing all HIGH-risk zones. Shall I generate the full day-by-day itinerary?`;
      if (/solo|female/i.test(msg)) reply = 'For solo female travelers: The Cultural Triangle (Sigiriya, Dambulla) and Hill Country are consistently LOW risk with strong tourist infrastructure. Galle Fort is well-patrolled. Avoid Colombo Fort and Negombo Beach after dark — our danger zone model flags both as HIGH risk during evening hours.';
      if (/budget|cheap|500/i.test(msg)) reply = 'Budget optimisation: Colombo guesthouse $25/night · Cultural Triangle budget stay $20/night · Hill Country $25/night. Estimated total for 4 days: $170 accommodation + $80 transport + $60 food + $50 entry fees = $360 — comfortably under $500.';
      if (/family|kid|child/i.test(msg)) reply = 'Top family picks from our ML model: Pinnawala Elephant Orphanage (LOW risk, kid-friendly ✓) · Peradeniya Botanical Gardens (LOW risk, relaxed pace ✓) · Kandy Lake Walk (LOW risk ✓). All show LOW crowd scores on weekdays in our prediction system.';
      setMessages(p => [...p, { role: 'ai', text: reply }]);
      setChatLoading(false);
    }, 1600);
  };

  return (
    <div className="page-wrap">

      <div className="page-header">
        <div className="page-header-inner">
          <div>
            <div className="accent-line" style={{ background: '#1A9E7A' }} />
            <h1 className="page-title">AI Itinerary Generator + Emotion Chatbot</h1>
            <p className="page-subtitle">Wanniarachchi P.M.R · IT22225092 · A* Safety Routing · Facial Emotion AI</p>
          </div>
          <span className="badge badge-demo" style={{ alignSelf: 'flex-start', marginTop: '0.5rem' }}>
            ◎ Prototype Demo
          </span>
        </div>
      </div>

      <div className="grid-4" style={{ marginBottom: '2rem' }}>
        {[
          { val: '10K+', label: 'Hotels in Database',    accent: '#1A9E7A' },
          { val: '500',  label: 'Tourist Sites',         accent: '#1A9E7A' },
          { val: '70%',  label: 'Planning Time Saved',   accent: '#1A9E7A' },
          { val: '85%',  label: 'Safety Satisfaction',   accent: '#1A9E7A' },
        ].map(s => (
          <div key={s.label} className="stat-card">
            <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 2, background: `linear-gradient(90deg, transparent, ${s.accent}60, transparent)` }} />
            <div className="stat-value" style={{ color: s.accent, fontSize: '1.7rem' }}>{s.val}</div>
            <div className="stat-label">{s.label}</div>
          </div>
        ))}
      </div>

      <div className="grid-2" style={{ marginBottom: '1.5rem' }}>

        {/* Emotion detection */}
        <div className="card">
          <div style={{ marginBottom: '1.25rem' }}>
            <div className="accent-line" style={{ background: '#1A9E7A' }} />
            <h3 style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: '1.15rem', fontWeight: 600 }}>
              Facial Emotion Detection
            </h3>
            <p style={{ fontSize: '0.78rem', color: '#6B6560', marginTop: '0.2rem' }}>
              Webcam analysis recommends activities matching your mood
            </p>
          </div>

          {/* Camera area */}
          <div style={{
            height: 175, borderRadius: '10px', marginBottom: '1rem',
            background: detecting ? '#060E0A' : 'rgba(255,255,255,0.02)',
            border: `1px solid ${detecting ? 'rgba(26,158,122,0.5)' : '#1E3D2F'}`,
            display: 'flex', flexDirection: 'column',
            alignItems: 'center', justifyContent: 'center',
            position: 'relative', overflow: 'hidden', transition: 'all 0.3s',
          }}>
            {detecting ? (
              <>
                <div style={{
                  position: 'absolute', inset: 0,
                  backgroundImage: 'repeating-linear-gradient(0deg, rgba(26,158,122,0.05) 0, rgba(26,158,122,0.05) 1px, transparent 1px, transparent 18px)',
                }} />
                <div style={{ fontSize: '2.5rem', animation: 'spin 4s linear infinite', opacity: 0.6 }}>👤</div>
                <div style={{ fontSize: '0.75rem', color: '#1A9E7A', marginTop: '0.6rem', fontFamily: 'JetBrains Mono, monospace' }}>
                  analysing landmarks...
                </div>
              </>
            ) : mood ? (
              <>
                <div style={{ fontSize: '3.2rem' }}>{mood.emoji}</div>
                <div style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: '1.2rem', fontWeight: 600, color: mood.color, marginTop: '0.3rem' }}>
                  {mood.label}
                </div>
                <div style={{ fontSize: '0.7rem', color: '#6B6560', marginTop: '0.2rem' }}>91% confidence</div>
              </>
            ) : (
              <>
                <div style={{ fontSize: '2rem', opacity: 0.2 }}>📷</div>
                <div style={{ fontSize: '0.78rem', color: '#4A5248', marginTop: '0.4rem' }}>Camera activates here</div>
              </>
            )}
          </div>

          <button className="btn btn-teal" onClick={detectEmotion} disabled={detecting} style={{ marginBottom: '1.1rem' }}>
            {detecting ? 'Detecting emotion...' : '📷  Detect My Emotion'}
          </button>

          <div className="label-caps" style={{ marginBottom: '0.6rem' }}>Or select mood</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.4rem', marginBottom: '1rem' }}>
            {MOODS.map(m => (
              <button key={m.label} onClick={() => setMood(m)} style={{
                background: mood?.label === m.label ? m.color + '18' : 'rgba(255,255,255,0.02)',
                border: `1px solid ${mood?.label === m.label ? m.color + '55' : '#1E3D2F'}`,
                borderRadius: '9px', padding: '0.55rem 0.25rem',
                cursor: 'pointer', display: 'flex', flexDirection: 'column',
                alignItems: 'center', gap: '0.2rem', transition: 'all 0.15s',
              }}>
                <span style={{ fontSize: '1.3rem' }}>{m.emoji}</span>
                <span style={{ fontSize: '0.65rem', color: '#6B6560', fontFamily: 'Figtree, sans-serif' }}>{m.label}</span>
              </button>
            ))}
          </div>

          {mood && (
            <div className="fade-up" style={{
              padding: '1rem 1.1rem',
              background: mood.color + '0D',
              border: `1px solid ${mood.color}28`,
              borderRadius: '10px',
            }}>
              <div className="label-caps" style={{ color: mood.color, marginBottom: '0.6rem' }}>
                Recommended for {mood.label} mood
              </div>
              {mood.spots.map((s, i) => (
                <div key={i} style={{
                  fontSize: '0.84rem', color: '#B8B0A0',
                  padding: '0.3rem 0',
                  borderBottom: i < mood.spots.length-1 ? '1px solid rgba(255,255,255,0.04)' : 'none',
                  display: 'flex', alignItems: 'center', gap: '0.5rem',
                }}>
                  <span style={{ color: mood.color, fontSize: '0.7rem' }}>▸</span> {s}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Itinerary generator */}
        <div className="card">
          <div style={{ marginBottom: '1.25rem' }}>
            <div className="accent-line" style={{ background: '#E8A020' }} />
            <h3 style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: '1.15rem', fontWeight: 600 }}>
              AI Itinerary Generator
            </h3>
            <p style={{ fontSize: '0.78rem', color: '#6B6560', marginTop: '0.2rem' }}>
              A* danger-zone routing · Risk-verified stops
            </p>
          </div>

          <div className="grid-2" style={{ marginBottom: '1rem' }}>
            <div>
              <label>Trip Duration</label>
              <select value={days} onChange={e => setDays(Number(e.target.value))}>
                {[2,3,4,5].map(d => <option key={d} value={d}>{d} Days</option>)}
              </select>
            </div>
            <div>
              <label>Tourist Type</label>
              <select value={touristType} onChange={e => setTouristType(e.target.value)}>
                {['general','family','solo','couple','adventure'].map(t => (
                  <option key={t} value={t}>{t.charAt(0).toUpperCase()+t.slice(1)}</option>
                ))}
              </select>
            </div>
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <label>Budget Level</label>
            <select value={budget} onChange={e => setBudget(e.target.value)}>
              <option value="budget">Budget — under $300</option>
              <option value="medium">Mid-range — $300–$600</option>
              <option value="luxury">Luxury — $600+</option>
            </select>
          </div>

          <button className="btn btn-primary" onClick={generate} disabled={generating}>
            {generating ? 'Optimising with A* routing...' : 'Generate Safe Itinerary'}
          </button>

          {generating && <div className="spinner" />}

          {itinerary && !generating && (
            <div className="fade-up" style={{ marginTop: '1.5rem' }}>
              <div className="divider" />
              {itinerary.map((day, i) => (
                <div key={i} style={{
                  background: '#0F2419',
                  border: '1px solid #1E3D2F',
                  borderRadius: '10px', padding: '1rem',
                  marginBottom: '0.6rem',
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.6rem' }}>
                    <span style={{
                      fontFamily: 'Cormorant Garamond, serif',
                      fontSize: '0.95rem', fontWeight: 600,
                      color: '#1A9E7A',
                    }}>
                      Day {day.day} — {day.title}
                    </span>
                    <span className={`badge badge-${day.risk.toLowerCase()}`}>{day.risk}</span>
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.3rem' }}>
                    {day.sites.map((s, j) => (
                      <span key={j} style={{
                        background: 'rgba(26,158,122,0.08)',
                        border: '1px solid rgba(26,158,122,0.2)',
                        borderRadius: '6px', padding: '0.18rem 0.55rem',
                        fontSize: '0.72rem', color: '#4DD9A8',
                        fontFamily: 'Figtree, sans-serif',
                      }}>{s}</span>
                    ))}
                  </div>
                </div>
              ))}
              <div className="box-info" style={{ marginTop: '0.5rem' }}>
                ✓ Route generated using A* pathfinding with danger-zone risk weights.
                All stops verified LOW or MEDIUM risk.
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Chat */}
      <div className="card">
        <div style={{ marginBottom: '1.25rem' }}>
          <h3 style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: '1.15rem', fontWeight: 600 }}>
            AI Trip Planner Chat
          </h3>
          <p style={{ fontSize: '0.78rem', color: '#6B6560', marginTop: '0.2rem' }}>
            Powered by safety-aware route intelligence
          </p>
        </div>

        <div style={{
          height: 280, overflowY: 'auto',
          display: 'flex', flexDirection: 'column', gap: '0.75rem',
          marginBottom: '1rem', paddingRight: '0.25rem',
        }}>
          {messages.map((m, i) => (
            <div key={i} style={{
              display: 'flex',
              justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start',
            }}>
              <div style={{
                maxWidth: '75%',
                padding: '0.75rem 1rem',
                fontSize: '0.84rem', lineHeight: 1.55,
                borderRadius: m.role === 'user' ? '12px 12px 3px 12px' : '12px 12px 12px 3px',
                background: m.role === 'user' ? 'rgba(26,158,122,0.15)' : '#112A20',
                border: `1px solid ${m.role === 'user' ? 'rgba(26,158,122,0.3)' : '#1E3D2F'}`,
              }}>
                {m.role === 'ai' && (
                  <div style={{
                    fontSize: '0.65rem', color: '#1A9E7A',
                    fontWeight: 700, marginBottom: '0.35rem',
                    letterSpacing: '0.06em', textTransform: 'uppercase',
                  }}>SafeJourney AI</div>
                )}
                {m.text}
              </div>
            </div>
          ))}
          {chatLoading && (
            <div style={{ display: 'flex', gap: '5px', paddingLeft: '0.5rem', alignItems: 'center' }}>
              {[0,1,2].map(i => (
                <div key={i} style={{
                  width: 6, height: 6, borderRadius: '50%', background: '#1A9E7A',
                  animation: `pulse 1.4s ease-in-out ${i*0.2}s infinite`,
                }} />
              ))}
            </div>
          )}
        </div>

        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem', marginBottom: '0.75rem' }}>
          {STARTERS.map(s => (
            <button key={s} onClick={() => sendMsg(s)} style={{
              background: 'rgba(26,158,122,0.06)',
              border: '1px solid rgba(26,158,122,0.2)',
              borderRadius: '100px', padding: '0.28rem 0.8rem',
              fontSize: '0.72rem', color: '#4DD9A8',
              cursor: 'pointer', fontFamily: 'Figtree, sans-serif',
              transition: 'all 0.15s',
            }}>
              {s}
            </button>
          ))}
        </div>

        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <input
            placeholder="Ask about safe routes, itineraries, budget..."
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && sendMsg()}
          />
          <button className="btn btn-teal" onClick={() => sendMsg()}
            style={{ width: 'auto', padding: '0.72rem 1.25rem', whiteSpace: 'nowrap' }}>
            Send
          </button>
        </div>
      </div>
    </div>
  );
}