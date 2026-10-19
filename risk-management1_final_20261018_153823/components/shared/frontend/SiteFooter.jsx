import { Link } from 'react-router-dom';
import { CONTACT, SITES, TABS } from './config';
import { useSiteI18n } from './i18n/react.js';

const TAB_KEYS = {
  home: 'tab_home',
  itinerary: 'tab_itinerary',
  wellness: 'tab_wellness',
  livedata: 'tab_livedata',
  sos: 'tab_sos',
};

export default function SiteFooter({ app = 'travel' }) {
  const { t } = useSiteI18n();

  return (
    <footer className="tc-site-footer">
      <div className="tc-site-wrap">
        <div className="tc-site-footer-grid tc-site-footer-grid--staff">
          <div>
            <a className="tc-site-logo" href={TABS[0].href} style={{ color: '#fff' }}>
              <img className="tc-site-logo-img" src="/tour-ceylon-logo.png" alt="Tour Ceylon" />
              Tour Ceylon
            </a>
            <p style={{ marginTop: 12, maxWidth: 340 }}>
              {t('footer_tagline')}
            </p>
          </div>
          <div>
            <h3>{t('footer_explore')}</h3>
            <div className="tc-site-footer-links">
              {TABS.map((tab) => {
                const internal = tab.internal?.[app];
                const className = tab.id === 'sos' ? 'is-sos' : undefined;
                const tabLabel = t(TAB_KEYS[tab.id] || 'tab_home');
                if (tab.idle) {
                  return (
                    <span key={tab.id} className={className} style={{ cursor: 'default', opacity: 0.85 }}>
                      {tabLabel}
                    </span>
                  );
                }
                if (internal) {
                  return (
                    <Link key={tab.id} className={className} to={internal}>
                      {tabLabel}
                    </Link>
                  );
                }
                return (
                  <a key={tab.id} className={className} href={tab.href}>
                    {tabLabel}
                  </a>
                );
              })}
            </div>
          </div>
          <div>
            <h3>{t('footer_contact')}</h3>
            <p>
              {CONTACT.address}<br />
              {t('footer_hours')}: {CONTACT.hours}<br />
              <a href={CONTACT.phoneHref}>{CONTACT.phone}</a><br />
              <a href={CONTACT.mobileHref}>{CONTACT.mobile}</a><br />
              <a href={CONTACT.emailHref}>{CONTACT.email}</a>
            </p>
          </div>
          <div>
            <h3>{t('footerStaffAccess')}</h3>
            <div className="tc-site-footer-links">
              <a href={SITES.police} target="_blank" rel="noopener noreferrer">
                {t('emergencyInstructionsLink')}
              </a>
              <a href={`${SITES.immigration}login`} target="_blank" rel="noopener noreferrer">
                {t('immigrationDashboardLogin')}
              </a>
              <a href={SITES.wellnessAdmin} target="_blank" rel="noopener noreferrer">
                {t('wellnessAdminLogin')}
              </a>
            </div>
          </div>
        </div>
        <div className="tc-site-copy">
          <span>© {new Date().getFullYear()} Tour Ceylon. {t('footer_copyright')}</span>
          <span>{t('footer_tagline2')}</span>
        </div>
      </div>
    </footer>
  );
}
