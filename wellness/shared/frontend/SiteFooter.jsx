import { Link } from 'react-router-dom';
import { CONTACT, TABS } from './config';

export default function SiteFooter({ app = 'travel' }) {
  return (
    <footer className="tc-site-footer">
      <div className="tc-site-wrap">
        <div className="tc-site-footer-grid">
          <div>
            <a className="tc-site-logo" href={TABS[0].href} style={{ color: '#fff' }}>
              <img className="tc-site-logo-img" src="/tour-ceylon-logo.png" alt="Tour Ceylon" />
              Tour Ceylon
            </a>
            <p style={{ marginTop: 12, maxWidth: 340 }}>
              Beach-to-highlands travel for Sri Lanka — itineraries, wellness matching,
              live safety data, and one-tap SOS.
            </p>
          </div>
          <div>
            <h3>Explore</h3>
            <div className="tc-site-footer-links">
              {TABS.map((tab) => {
                const internal = tab.internal?.[app];
                const className = tab.id === 'sos' ? 'is-sos' : undefined;
                if (tab.idle) {
                  return (
                    <span key={tab.id} className={className} style={{ cursor: 'default', opacity: 0.85 }}>
                      {tab.label}
                    </span>
                  );
                }
                if (internal) {
                  return (
                    <Link key={tab.id} className={className} to={internal}>
                      {tab.label}
                    </Link>
                  );
                }
                return (
                  <a key={tab.id} className={className} href={tab.href}>
                    {tab.label}
                  </a>
                );
              })}
            </div>
          </div>
          <div>
            <h3>Contact</h3>
            <p>
              {CONTACT.address}<br />
              Hours: {CONTACT.hours}<br />
              <a href={CONTACT.phoneHref}>{CONTACT.phone}</a><br />
              <a href={CONTACT.mobileHref}>{CONTACT.mobile}</a><br />
              <a href={CONTACT.emailHref}>{CONTACT.email}</a>
            </p>
          </div>
        </div>
        <div className="tc-site-copy">
          <span>© {new Date().getFullYear()} Tour Ceylon. All rights reserved.</span>
          <span>Sri Lanka tourism · wellness · safety</span>
        </div>
      </div>
    </footer>
  );
}
