import { useState } from 'react';
import { Link } from 'react-router-dom';
import { CONTACT, TABS } from './config';

export default function SiteHeader({ app = 'travel', active = 'home', onSosClick, subnav }) {
  const [open, setOpen] = useState(false);

  return (
    <header className={`tc-site-header${subnav ? ' has-subnav' : ''}`}>
      <div className="tc-site-top">
        <div className="tc-site-wrap tc-site-top-inner">
            <a className="tc-site-logo" href={TABS[0].href}>
            <img className="tc-site-logo-img" src="/tour-ceylon-logo.png" alt="Tour Ceylon" />
            Tour Ceylon
          </a>
          <div className="tc-site-meta">
            <span className="tc-hide-sm">{CONTACT.hours}</span>
            <a href={CONTACT.phoneHref}>{CONTACT.phone}</a>
            <a className="tc-site-quote" href={TABS[1].href}>Plan a trip</a>
          </div>
        </div>
      </div>

      <nav className={`tc-site-bar${open ? ' is-open' : ''}`}>
        <div className="tc-site-wrap tc-site-bar-inner">
          <button
            type="button"
            className="tc-site-menu"
            aria-label="Open menu"
            aria-expanded={open}
            onClick={() => setOpen((v) => !v)}
          >
            <span />
            <span />
            <span />
          </button>
          <div className="tc-site-tabs">
            {TABS.map((tab) => {
              const className = `tc-site-tab${tab.id === 'sos' ? ' is-sos' : ''}${tab.idle ? ' is-idle' : ''}${active === tab.id ? ' is-active' : ''}`;
              const internal = tab.internal?.[app];
              if (tab.idle) {
                return (
                  <span key={tab.id} className={className}>{tab.label}</span>
                );
              }
              if (tab.id === 'sos' && onSosClick) {
                return (
                  <a key={tab.id} className={className} href={tab.href} onClick={onSosClick}>
                    {tab.label}
                  </a>
                );
              }
              if (internal) {
                return (
                  <Link key={tab.id} className={className} to={internal} onClick={() => setOpen(false)}>
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
      </nav>
      {subnav}
    </header>
  );
}
