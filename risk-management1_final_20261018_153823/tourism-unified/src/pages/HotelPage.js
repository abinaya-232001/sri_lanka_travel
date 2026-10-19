import React, { useState, useEffect } from 'react';

const API = 'http://localhost:5001';

export default function HotelPage() {
  const [apiStatus, setApiStatus]   = useState('checking');
  const [flights, setFlights]       = useState([]);
  const [drivers, setDrivers]       = useState([]);
  const [flightNum, setFlightNum]   = useState('');
  const [flightData, setFlightData] = useState(null);
  const [flightLoading, setFlightLoading] = useState(false);
  const [hotels, setHotels]         = useState([]);
  const [hotelLoading, setHotelLoading] = useState(false);
  const [selectedHotel, setSelectedHotel] = useState(null);
  const [driverData, setDriverData] = useState(null);
  const [driverLoading, setDriverLoading] = useState(false);
  const [verifyLicence, setVerifyLicence] = useState('');
  const [verifyResult, setVerifyResult]   = useState(null);
  const [verifying, setVerifying]         = useState(false);
  const [matchForm, setMatchForm]   = useState({ budget: '', location: '', flight_number: '' });
  const [error, setError]           = useState(null);
  const [activeTab, setActiveTab]   = useState('hotels');

  useEffect(() => {
    fetch(`${API}/health`)
      .then(r => r.json())
      .then(() => {
        setApiStatus('online');
        fetch(`${API}/drivers`).then(r => r.json()).then(setDrivers).catch(() => {});
      })
      .catch(() => setApiStatus('offline'));
  }, []);

  const searchFlight = async () => {
    if (!flightNum.trim()) return;
    setFlightLoading(true);
    setFlightData(null);
    setError(null);
    try {
      const res = await fetch(`${API}/flight-status/${flightNum.trim()}`);
      const data = await res.json();
      setFlightData(data);
    } catch {
      setError('Cannot reach backend at localhost:5001. Make sure it is running.');
    } finally {
      setFlightLoading(false);
    }
  };

  const matchHotels = async () => {
    setHotelLoading(true);
    setHotels([]);
    setSelectedHotel(null);
    setDriverData(null);
    setError(null);
    try {
      const res = await fetch(`${API}/match-hotels`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(matchForm),
      });
      const data = await res.json();
      setHotels(Array.isArray(data) ? data : data.hotels || []);
    } catch {
      setError('Cannot reach backend at localhost:5001. Make sure it is running.');
    } finally {
      setHotelLoading(false);
    }
  };

  const fetchDriver = async (licenceOrId) => {
    setDriverLoading(true);
    setDriverData(null);
    try {
      const res = await fetch(`${API}/verify-driver/${licenceOrId}`);
      const data = await res.json();
      setDriverData(data);
    } catch {
      setError('Driver verification failed.');
    } finally {
      setDriverLoading(false);
    }
  };

  const verifyDriver = async () => {
    if (!verifyLicence.trim()) return;
    setVerifying(true);
    setVerifyResult(null);
    try {
      const res = await fetch(`${API}/verify-driver/${verifyLicence.trim()}`);
      const data = await res.json();
      setVerifyResult(data);
    } catch {
      setVerifyResult({ error: 'Verification failed' });
    } finally {
      setVerifying(false);
    }
  };

  const bookHotel = (hotel) => {
    setSelectedHotel(hotel);
    if (drivers.length > 0) {
      const driver = drivers[Math.floor(Math.random() * drivers.length)];
      fetchDriver(driver.licence || driver.id || driver.licence_number || '1');
    }
  };

  const TABS = [
    { id: 'hotels',  label: '🏨 Hotel Matching' },
    { id: 'flights', label: '✈️ Flight Status' },
    { id: 'drivers', label: '🚗 Driver Verify' },
  ];

  return (
    <div className="page-wrap">
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '0.4rem' }}>
        <h1 className="page-title">Hotel, Flight & Driver Matcher</h1>
        <span style={{
          padding: '0.2rem 0.6rem', borderRadius: '100px', fontSize: '0.68rem', fontWeight: 700,
          background: apiStatus === 'online' ? 'rgba(56,161,105,0.2)' : 'rgba(229,62,62,0.2)',
          color: apiStatus === 'online' ? '#68D391' : '#FC8181',
          border: `1px solid ${apiStatus === 'online' ? 'rgba(56,161,105,0.3)' : 'rgba(229,62,62,0.3)'}`,
        }}>
          {apiStatus === 'online' ? '● API LIVE' : apiStatus === 'offline' ? '✕ OFFLINE' : '○ Checking'}
        </span>
      </div>
      <p className="page-subtitle">De Silva D.C.M · IT22108586 · Flask :5001 · SLTDA Driver Verification · CMB Flights</p>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '0.4rem', marginBottom: '1.5rem' }}>
        {TABS.map(t => (
          <button
            key={t.id}
            onClick={() => setActiveTab(t.id)}
            style={{
              padding: '0.55rem 1.1rem', borderRadius: '8px',
              border: `1px solid ${activeTab === t.id ? 'rgba(59,130,246,0.4)' : '#1E2A3A'}`,
              background: activeTab === t.id ? 'rgba(59,130,246,0.12)' : 'transparent',
              color: activeTab === t.id ? '#93C5FD' : '#8A9BB0',
              cursor: 'pointer', fontFamily: 'DM Sans, sans-serif',
              fontSize: '0.82rem', fontWeight: activeTab === t.id ? 600 : 400,
            }}
          >{t.label}</button>
        ))}
      </div>

      {error && <div className="box-error" style={{ marginBottom: '1rem' }}>{error}</div>}

      {/* Hotel Matching tab */}
      {activeTab === 'hotels' && (
        <div>
          <div className="card" style={{ marginBottom: '1.5rem' }}>
            <h3 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '1.25rem' }}>🔍 Match Hotels to Your Arrival</h3>
            <div className="grid-3" style={{ marginBottom: '1rem' }}>
              <div>
                <label>Flight Number</label>
                <input
                  placeholder="e.g. UL504"
                  value={matchForm.flight_number}
                  onChange={e => setMatchForm(f => ({ ...f, flight_number: e.target.value }))}
                />
              </div>
              <div>
                <label>Preferred Location</label>
                <input
                  placeholder="e.g. Colombo, Galle"
                  value={matchForm.location}
                  onChange={e => setMatchForm(f => ({ ...f, location: e.target.value }))}
                />
              </div>
              <div>
                <label>Budget (USD/night)</label>
                <input
                  type="number"
                  placeholder="e.g. 150"
                  value={matchForm.budget}
                  onChange={e => setMatchForm(f => ({ ...f, budget: e.target.value }))}
                />
              </div>
            </div>
            <button className="btn btn-primary" onClick={matchHotels} disabled={hotelLoading}>
              {hotelLoading ? 'Matching hotels...' : 'Find Matching Hotels'}
            </button>
            {hotelLoading && <div className="spinner" />}
          </div>

          {hotels.length > 0 && (
            <div className="fade-up">
              <div style={{ fontSize: '0.83rem', color: '#8A9BB0', marginBottom: '1rem' }}>
                {hotels.length} hotels matched from backend
              </div>
              <div className="grid-2">
                {hotels.map((h, i) => (
                  <div key={i} className="card" style={{ position: 'relative' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                      <span style={{ fontWeight: 600, fontSize: '0.95rem' }}>
                        {h.name || h.hotel_name || `Hotel ${i + 1}`}
                      </span>
                      <span className="badge-low">VERIFIED</span>
                    </div>
                    <div style={{ fontSize: '0.8rem', color: '#8A9BB0', marginBottom: '0.75rem' }}>
                      {h.stars && '⭐'.repeat(h.stars)} {h.location && `· 📍 ${h.location}`}
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontFamily: 'Playfair Display, serif', fontSize: '1.05rem', color: '#C9A84C' }}>
                        {h.price ? `$${h.price}/night` : 'Price on request'}
                      </span>
                      <button
                        onClick={() => bookHotel(h)}
                        style={{
                          background: 'rgba(201,168,76,0.15)', border: '1px solid rgba(201,168,76,0.3)',
                          color: '#C9A84C', padding: '0.4rem 1rem', borderRadius: '8px',
                          cursor: 'pointer', fontFamily: 'DM Sans, sans-serif',
                          fontSize: '0.8rem', fontWeight: 600,
                        }}
                      >
                        Book + Get Driver
                      </button>
                    </div>
                    {Object.entries(h).filter(([k]) => !['name','hotel_name','stars','location','price'].includes(k)).slice(0, 3).map(([k, v]) => (
                      <div key={k} style={{ fontSize: '0.75rem', color: '#4A5568', marginTop: '0.3rem' }}>
                        {k}: {String(v)}
                      </div>
                    ))}
                  </div>
                ))}
              </div>

              {selectedHotel && (
                <div className="card fade-up" style={{ marginTop: '1.5rem', borderColor: 'rgba(56,161,105,0.3)' }}>
                  <h3 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '1rem' }}>
                    🚗 Driver Assignment — {selectedHotel.name || selectedHotel.hotel_name}
                  </h3>
                  {driverLoading ? (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', color: '#8A9BB0' }}>
                      <div className="spinner" style={{ margin: 0 }} />
                      Assigning verified SLTDA driver...
                    </div>
                  ) : driverData ? (
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div>
                        <div style={{ fontWeight: 600, fontSize: '1rem', marginBottom: '0.3rem' }}>
                          {driverData.name || driverData.driver_name || 'Assigned Driver'} ✓ SLTDA Verified
                        </div>
                        {Object.entries(driverData).filter(([k]) => !['name','driver_name'].includes(k)).slice(0, 4).map(([k, v]) => (
                          <div key={k} style={{ fontSize: '0.8rem', color: '#8A9BB0' }}>
                            {k}: {String(v)}
                          </div>
                        ))}
                      </div>
                      <div style={{ textAlign: 'right' }}>
                        <div style={{ color: '#68D391', fontWeight: 700, fontSize: '1.1rem' }}>Ready</div>
                        <button className="btn btn-teal" style={{ marginTop: '0.5rem', width: 'auto', padding: '0.4rem 1rem', fontSize: '0.8rem' }}>
                          Confirm Booking
                        </button>
                      </div>
                    </div>
                  ) : null}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Flight Status tab */}
      {activeTab === 'flights' && (
        <div className="card">
          <h3 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '1.25rem' }}>✈️ CMB Flight Status</h3>
          <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1rem' }}>
            <input
              placeholder="Enter flight number e.g. UL504, EK348"
              value={flightNum}
              onChange={e => setFlightNum(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && searchFlight()}
            />
            <button className="btn btn-primary" onClick={searchFlight} disabled={flightLoading}
              style={{ width: 'auto', whiteSpace: 'nowrap', padding: '0.75rem 1.25rem' }}>
              {flightLoading ? 'Checking...' : 'Check Status'}
            </button>
          </div>
          {flightLoading && <div className="spinner" />}
          {flightData && (
            <div className="fade-up" style={{
              padding: '1.25rem', background: 'rgba(255,255,255,0.03)',
              border: '1px solid #1E2A3A', borderRadius: '12px',
            }}>
              <div style={{ fontSize: '0.72rem', color: '#3B82F6', fontWeight: 700, marginBottom: '0.75rem', letterSpacing: '0.06em' }}>
                FLIGHT STATUS FROM BACKEND
              </div>
              {Object.entries(flightData).map(([k, v]) => (
                <div key={k} style={{
                  display: 'flex', justifyContent: 'space-between',
                  padding: '0.4rem 0', borderBottom: '1px solid rgba(255,255,255,0.04)',
                  fontSize: '0.85rem',
                }}>
                  <span style={{ color: '#8A9BB0', textTransform: 'capitalize' }}>{k.replace(/_/g, ' ')}</span>
                  <span style={{ color: '#F0EDE8', fontWeight: 500 }}>{String(v)}</span>
                </div>
              ))}
            </div>
          )}
          {!flightData && !flightLoading && (
            <div style={{ textAlign: 'center', padding: '2rem', color: '#4A5568' }}>
              <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>✈️</div>
              <p style={{ fontSize: '0.83rem' }}>Enter a flight number to check CMB arrival status</p>
            </div>
          )}
        </div>
      )}

      {/* Driver Verify tab */}
      {activeTab === 'drivers' && (
        <div>
          <div className="card" style={{ marginBottom: '1.5rem' }}>
            <h3 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '1.25rem' }}>🔒 SLTDA Driver Verification</h3>
            <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1rem' }}>
              <input
                placeholder="Enter driver licence number"
                value={verifyLicence}
                onChange={e => setVerifyLicence(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && verifyDriver()}
              />
              <button className="btn btn-primary" onClick={verifyDriver} disabled={verifying}
                style={{ width: 'auto', whiteSpace: 'nowrap', padding: '0.75rem 1.25rem' }}>
                {verifying ? 'Verifying...' : 'Verify Driver'}
              </button>
            </div>
            {verifying && <div className="spinner" />}
            {verifyResult && (
              <div className={`fade-up ${verifyResult.error ? 'box-error' : 'box-success'}`}>
                {verifyResult.error ? `❌ ${verifyResult.error}` : (
                  <>
                    <div style={{ fontWeight: 700, marginBottom: '0.5rem' }}>✅ Driver Verified by SLTDA</div>
                    {Object.entries(verifyResult).map(([k, v]) => (
                      <div key={k} style={{ fontSize: '0.82rem', opacity: 0.9 }}>
                        {k.replace(/_/g, ' ')}: {String(v)}
                      </div>
                    ))}
                  </>
                )}
              </div>
            )}
          </div>

          {/* Available drivers */}
          {drivers.length > 0 && (
            <div className="card">
              <h3 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '1.25rem' }}>🚗 Available Verified Drivers</h3>
              <div className="grid-2">
                {drivers.map((d, i) => (
                  <div key={i} style={{
                    background: 'rgba(255,255,255,0.02)', border: '1px solid #1E2A3A',
                    borderRadius: '10px', padding: '1rem',
                  }}>
                    <div style={{ fontWeight: 600, fontSize: '0.9rem', marginBottom: '0.4rem' }}>
                      {d.name || d.driver_name || `Driver ${i + 1}`} ✓
                    </div>
                    {Object.entries(d).filter(([k]) => !['name','driver_name'].includes(k)).slice(0, 4).map(([k, v]) => (
                      <div key={k} style={{ fontSize: '0.78rem', color: '#8A9BB0' }}>
                        {k.replace(/_/g, ' ')}: {String(v)}
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            </div>
          )}

          {drivers.length === 0 && apiStatus === 'offline' && (
            <div className="box-info">
              Backend offline. Start De Silva D.C.M's Flask server at port 5001 to see live driver data.
            </div>
          )}
        </div>
      )}
    </div>
  );
}