import { useState } from "react";

const APP = "http://127.0.0.1:5000";

function readWho() {
  const fromUrl = (new URLSearchParams(window.location.search).get("who") || "")
    .replace(/[^A-Za-z]/g, "")
    .slice(0, 2)
    .toUpperCase();
  if (fromUrl) sessionStorage.setItem("tc-who", fromUrl);
  return fromUrl || sessionStorage.getItem("tc-who") || "";
}

const NAV = [
  { href: `${APP}/#/home`, label: "Home" },
  { href: `${APP}/#/itinerary/plan`, label: "Itinerary" },
  { href: "http://localhost:5003/", label: "Wellness" },
  { href: "http://localhost:5182/", label: "Risk analyst", current: true },
  { href: `${APP}/#/sos`, label: "SOS" },
];

export default function DashboardChrome({ children }) {
  const [menu, setMenu] = useState(false);
  const [who] = useState(readWho);
  const withWho = (href) => {
    if (!who) return href;
    const url = new URL(href);
    url.searchParams.set("who", who);
    return url.toString();
  };
  return (
    <div className="tc-dash">
      <header className="tc-dash-top">
        <div className="tc-dash-wrap tc-dash-bar">
          <a className="tc-dash-brand" href={`${APP}/#/home`}>
            <img src="/logo.png" alt="" />
            TourCeylon
          </a>
          <button type="button" className="nav-toggle" aria-label="Menu" aria-expanded={menu} onClick={() => setMenu((v) => !v)}>
            <span /><span /><span />
          </button>
          <nav className={`tc-dash-tabs${menu ? " is-open" : ""}`} aria-label="Main">
            {NAV.map((item) => (
              <a key={item.label} href={item.label === "Wellness" || item.current ? withWho(item.href) : item.href} aria-current={item.current ? "page" : undefined} onClick={() => setMenu(false)}>
                {item.label}
              </a>
            ))}
          </nav>
          <div className="tc-dash-who">
            <a className={`tc-profile-btn${who ? " has-name" : ""}`} href={`${APP}/#/profile`} aria-label="Profile">
              {who || (
                <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="8" r="3.2" fill="none" stroke="currentColor" strokeWidth="1.8" /><path d="M5 19.2c1.4-3 3.8-4.4 7-4.4s5.6 1.4 7 4.4" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" /></svg>
              )}
            </a>
          </div>
        </div>
      </header>
      <main className="tc-dash-main">{children}</main>
      <footer className="tc-dash-foot">
        <div className="tc-dash-wrap tc-dash-grid">
          <div className="tc-dash-brand-col">
            <a className="tc-dash-brand" href={`${APP}/#/home`}>
              <img src="/logo.png" alt="" />
              TourCeylon
            </a>
            <p>Explore Sri Lanka's cultural and natural heritage with our curated journeys.</p>
          </div>
          <div className="tc-dash-col">
            <h3>Experience Lanka</h3>
            <a href={`${APP}/#/home`}>Sigiriya Tours</a>
            <a href={`${APP}/#/itinerary/plan`}>Beach Stays</a>
            <a href={`${APP}/#/home`}>Cultural Festivals</a>
          </div>
          <div className="tc-dash-col">
            <h3>Stay Connected</h3>
            <div className="tc-dash-socials">
              <a href="https://facebook.com" target="_blank" rel="noopener noreferrer" aria-label="Facebook">
                <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M14 9h3V6h-3c-2.2 0-4 1.8-4 4v2H8v3h2v7h3v-7h2.6l.4-3H13v-2c0-.6.4-1 1-1z" /></svg>
              </a>
              <a href="https://instagram.com" target="_blank" rel="noopener noreferrer" aria-label="Instagram">
                <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 3h10a4 4 0 0 1 4 4v10a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4V7a4 4 0 0 1 4-4zm10 2H7a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2zm-5 3.2A3.8 3.8 0 1 1 8.2 12 3.8 3.8 0 0 1 12 8.2zm0 2A1.8 1.8 0 1 0 13.8 12 1.8 1.8 0 0 0 12 10.2zM17.2 6.6a1 1 0 1 1-1 1 1 1 0 0 1 1-1z" /></svg>
              </a>
              <a href="https://youtube.com" target="_blank" rel="noopener noreferrer" aria-label="YouTube">
                <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M23 12.2s0-3.2-.4-4.6a3 3 0 0 0-2.1-2.1C18.9 5 12 5 12 5s-6.9 0-8.5.5a3 3 0 0 0-2.1 2.1C1 9 1 12.2 1 12.2s0 3.2.4 4.6a3 3 0 0 0 2.1 2.1C5.1 19.4 12 19.4 12 19.4s6.9 0 8.5-.5a3 3 0 0 0 2.1-2.1c.4-1.4.4-4.6.4-4.6zM9.8 15.5v-6.6l6.2 3.3z" /></svg>
              </a>
              <a href="https://x.com" target="_blank" rel="noopener noreferrer" aria-label="X">
                <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 4h4.2l3.3 4.6L15.6 4H20l-6.2 7.4L20.4 20h-4.2l-3.6-5L8.2 20H4l6.6-7.8z" /></svg>
              </a>
            </div>
            <div className="tc-dash-contact">
              Email: <a href="mailto:info@tourceylon.com">info@tourceylon.com</a><br />
              Phone: <a href="tel:+9411234567">+94 112 34567</a>
            </div>
          </div>
        </div>
        <div className="tc-dash-bar-bottom">© 2024 TourCeylon · Plan with Purpose. Explore with Peace.</div>
      </footer>
      <a className="tc-dash-sos" href={`${APP}/#/sos`} aria-label="Open SOS"><span>SOS</span></a>
    </div>
  );
}
