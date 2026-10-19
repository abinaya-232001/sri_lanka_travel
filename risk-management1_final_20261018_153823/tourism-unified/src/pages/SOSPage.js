import React, { useState } from 'react';

const ZONES = [
  { zone: 'Colombo Fort',      risk: 'HIGH',   incidents: 23, type: 'Harassment · Theft',          lat: 6.9271, lng: 79.8612 },
  { zone: 'Negombo Beach',     risk: 'MEDIUM', incidents: 11, type: 'Harassment',                  lat: 7.2106, lng: 79.8358 },
  { zone: 'Galle Road Night',  risk: 'HIGH',   incidents: 17, type: 'Road Accident · Theft',       lat: 6.8753, lng: 79.8614 },
  { zone: 'Sigiriya Approach', risk: 'LOW',    incidents: 4,  type: 'Minor Incidents',             lat: 7.9570, lng: 80.7603 },
  { zone: 'Kandy City Centre', risk: 'MEDIUM', incidents: 9,  type: 'Theft · Scams',               lat: 7.2906, lng: 80.6337 },
  { zone: 'Mirissa Night',     risk: 'HIGH',   incidents: 19, type: 'Harassment · Assault',        lat: 5.9483, lng: 80.4706 },
];

const LANGS = ['English','Sinhala','Tamil','German','French','Russian','Chinese','Japanese','Korean','Hindi'];

const ZONE_COLORS = { HIGH: '#C84B31', MEDIUM: '#E8A020', LOW: '#1A9E7A' };

export default function SOSPage() {
  const [lang, setLang]           = useState('English');
  const [stage, setStage]         = useState(0);
  const [voiceText, setVoiceText] = useState('');
  const [analysing, setAnalysing] = useState(false);
  const [nlpResult, setNlpResult] = useState(null);

  const triggerSOS = () => {
    setStage(1);
    setTimeout(() => setStage(2), 1500);
    setTimeout(() => setStage(3), 3200);
    setTimeout(() => setStage(4), 5200);
  };

  const analyse = () => {
    if (!voiceText.trim()) return;
    setAnalysing(true); setNlpResult(null);
    setTimeout(() => {
      const distress = /help|danger|follow|harass|attack|scared|emergency|police/i.test(voiceText);
      setNlpResult({
        confidence: distress ? 0.91 : 0.18,
        distress,
        entities: distress
          ? ['incident_type: harassment', 'urgency: HIGH', 'action: dispatch_required']
          : ['signal: no_distress_detected'],
        language: lang,
      });
      setAnalysing(false);
    }, 2000);
  };

  return (
    <div className="page-wrap">

      <div className="page-header">
        <div className="page-header-inner">
          <div>
            <div className="accent-line" style={{ background: '#C84B31' }} />
            <h1 className="page-title">SOS Emergency Safety System</h1>
            <p className="page-subtitle">De Silva D.S.K · IT22108654 · Whisper STT + NER + Random Forest · 10 Languages</p>
          </div>
          <span className="badge badge-demo" style={{ alignSelf: 'flex-start', marginTop: '0.5rem' }}>
            ◎ Prototype Demo
          </span>
        </div>
      </div>

      {/* Stats */}
      <div className="grid-4" style={{ marginBottom: '2rem' }}>
        {[
          { val: '<90s',  label: 'Response Target',   accent: '#C84B31' },
          { val: '≥0.80', label: 'F1 Score Target',   accent: '#C84B31' },
          { val: '10',    label: 'Languages',          accent: '#C84B31' },
          { val: '100K',  label: 'Training Posts',     accent: '#C84B31' },
        ].map(s => (
          <div key={s.label} className="stat-card">
            <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 2, background: `linear-gradient(90deg, transparent, ${s.accent}60, transparent)` }} />
            <div className="stat-value" style={{ color: s.accent, fontSize: '1.7rem' }}>{s.val}</div>
            <div className="stat-label">{s.label}</div>
          </div>
        ))}
      </div>

      <div className="grid-2" style={{ marginBottom: '1.5rem' }}>

        {/* SOS trigger */}
        <div className="card">
          <div style={{ marginBottom: '1.25rem' }}>
            <div className="accent-line" style={{ background: '#C84B31' }} />
            <h3 style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: '1.15rem', fontWeight: 600 }}>
              Emergency Dispatch
            </h3>
            <p style={{ fontSize: '0.78rem', color: '#6B6560', marginTop: '0.2rem' }}>
              Voice-activated · Anonymous GPS · Sub-90s response
            </p>
          </div>

          <div style={{ marginBottom: '1.25rem' }}>
            <label>Tourist Language</label>
            <select value={lang} onChange={e => setLang(e.target.value)}>
              {LANGS.map(l => <option key={l}>{l}</option>)}
            </select>
          </div>

          {stage === 0 ? (
            <button className="btn btn-danger" onClick={triggerSOS}>
              🆘 Activate SOS
            </button>
          ) : (
            <div>
              {[
                { s: 1, icon: '🎙', label: `Capturing voice in ${lang}` },
                { s: 2, icon: '⚙',  label: 'Whisper STT → NER analysis' },
                { s: 3, icon: '⚡', label: 'Distress confirmed — preparing dispatch' },
                { s: 4, icon: '✓',  label: 'Anonymous GPS dispatched to police' },
              ].map(step => (
                <div key={step.s} style={{
                  display: 'flex', alignItems: 'center', gap: '0.85rem',
                  padding: '0.75rem 0.9rem',
                  borderRadius: '9px', marginBottom: '0.5rem',
                  background: stage >= step.s ? 'rgba(200,75,49,0.08)' : 'transparent',
                  border: `1px solid ${stage >= step.s ? 'rgba(200,75,49,0.25)' : '#1E3D2F'}`,
                  transition: 'all 0.35s ease',
                  opacity: stage >= step.s ? 1 : 0.3,
                }}>
                  <div style={{
                    width: 30, height: 30, borderRadius: '8px', flexShrink: 0,
                    background: stage >= step.s ? 'rgba(200,75,49,0.2)' : 'rgba(255,255,255,0.03)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: '0.9rem',
                  }}>{step.icon}</div>
                  <span style={{ fontSize: '0.83rem', color: stage >= step.s ? '#F5F0E8' : '#4A5248' }}>
                    {step.label}
                  </span>
                  {stage === step.s && step.s < 4 && (
                    <div style={{
                      marginLeft: 'auto', width: 14, height: 14, flexShrink: 0,
                      border: '2px solid #C84B31', borderTopColor: 'transparent',
                      borderRadius: '50%', animation: 'spin 0.75s linear infinite',
                    }} />
                  )}
                </div>
              ))}

              {stage === 4 && (
                <div className="box-success" style={{ marginTop: '1rem' }}>
                  <div style={{ fontWeight: 600, marginBottom: '0.4rem' }}>Dispatch Confirmed</div>
                  → Nearest police station notified<br />
                  → Verified hotel alerted<br />
                  → Tourist identity fully anonymised
                </div>
              )}

              <button
                className="btn btn-secondary"
                onClick={() => setStage(0)}
                style={{ marginTop: '1rem' }}
              >
                Reset Demo
              </button>
            </div>
          )}
        </div>

        {/* NER analyser */}
        <div className="card">
          <div style={{ marginBottom: '1.25rem' }}>
            <div className="accent-line" style={{ background: '#2A7AE8' }} />
            <h3 style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: '1.15rem', fontWeight: 600 }}>
              Whisper STT + NER Analyser
            </h3>
            <p style={{ fontSize: '0.78rem', color: '#6B6560', marginTop: '0.2rem' }}>
              Simulates distress detection pipeline
            </p>
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label>Simulate tourist speech input</label>
            <textarea
              rows={4}
              placeholder="e.g. Help me! Someone is following me near Colombo Fort, I need police now..."
              value={voiceText}
              onChange={e => setVoiceText(e.target.value)}
            />
          </div>

          <button className="btn btn-teal" onClick={analyse} disabled={analysing || !voiceText.trim()}>
            {analysing ? 'Running Whisper + NER...' : 'Analyse Distress Signal'}
          </button>

          {analysing && <div className="spinner" />}

          {nlpResult && !analysing && (
            <div className={`fade-up ${nlpResult.distress ? 'box-error' : 'box-success'}`}
              style={{ marginTop: '1rem' }}>
              <div style={{ fontWeight: 700, marginBottom: '0.5rem', fontFamily: 'Cormorant Garamond, serif', fontSize: '1.1rem' }}>
                {nlpResult.distress ? '⚠ Distress Detected' : '✓ No Distress Signal'}
              </div>
              <div style={{ fontSize: '0.8rem', opacity: 0.85, marginBottom: '0.5rem' }}>
                Confidence: <strong>{(nlpResult.confidence*100).toFixed(0)}%</strong>
                &nbsp;·&nbsp;Language: <strong>{nlpResult.language}</strong>
              </div>
              <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '0.75rem', opacity: 0.75 }}>
                {nlpResult.entities.map((e, i) => <div key={i}>{e}</div>)}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Danger zones */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem' }}>
          <div>
            <h3 style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: '1.15rem', fontWeight: 600, marginBottom: '0.2rem' }}>
              Predictive Danger Zone Intelligence
            </h3>
            <p style={{ fontSize: '0.77rem', color: '#6B6560' }}>
              Updated every 30 minutes · Random Forest trained on 100K geo-tagged incident posts
            </p>
          </div>
          <div style={{
            fontSize: '0.68rem', fontFamily: 'JetBrains Mono, monospace',
            color: '#1A9E7A', background: 'rgba(26,158,122,0.1)',
            border: '1px solid rgba(26,158,122,0.2)',
            padding: '0.3rem 0.65rem', borderRadius: '6px',
          }}>
            ● Live — {new Date().toLocaleTimeString()}
          </div>
        </div>

        <div className="grid-3">
          {ZONES.map(z => (
            <div key={z.zone} style={{
              background: '#112A20',
              border: `1px solid ${ZONE_COLORS[z.risk]}25`,
              borderRadius: '11px',
              padding: '1.1rem',
              position: 'relative',
              overflow: 'hidden',
            }}>
              <div style={{
                position: 'absolute', top: 0, left: 0, right: 0, height: 2,
                background: ZONE_COLORS[z.risk], opacity: 0.6,
              }} />
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.6rem' }}>
                <span style={{ fontSize: '0.88rem', fontWeight: 600, color: '#F5F0E8' }}>{z.zone}</span>
                <span className={`badge badge-${z.risk.toLowerCase()}`}>{z.risk}</span>
              </div>
              <div style={{ fontSize: '0.77rem', color: '#6B6560', lineHeight: 1.5 }}>
                <div>{z.type}</div>
                <div style={{ marginTop: '0.2rem' }}>{z.incidents} incidents logged</div>
                <div style={{
                  marginTop: '0.4rem',
                  fontFamily: 'JetBrains Mono, monospace',
                  fontSize: '0.68rem', color: '#2A3830',
                }}>
                  {z.lat}° N, {z.lng}° E
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}