import { useState } from 'react';

import { Link, useLocation } from 'react-router-dom';

import { CONTACT, SITES, TABS } from './config';

import { useSiteI18n } from './i18n/react.js';

import { useSiteAuth } from './useSiteAuth';

import ProfileGlyph from './ProfileGlyph';



const TAB_KEYS = {

  home: 'tab_home',

  itinerary: 'tab_itinerary',

  wellness: 'tab_wellness',

  livedata: 'tab_livedata',

  sos: 'tab_sos',

};



export default function SiteHeader({

  app = 'travel',

  active = 'home',

  onSosClick,

  subnav,

  isAuthenticated,

  user,

  onLogout,

}) {

  const [open, setOpen] = useState(false);

  const { t } = useSiteI18n();

  const location = useLocation();

  const { loggedIn, label, logout, loginUrl } = useSiteAuth(app, {

    isAuthenticated,

    user,

    onLogout,

  });

  const profilePath = '/profile';

  const profileHref = `${String(SITES.home || 'http://localhost:5180').replace(/\/$/, '')}${profilePath}`;

  const internalProfile = app === 'travel';

  const onProfile = internalProfile && location.pathname === profilePath;



  const loginControl =

    app === 'travel' ? (

      <Link className="tc-site-auth-btn" to="/login" onClick={() => setOpen(false)}>

        {t('logIn')}

      </Link>

    ) : (

      <a className="tc-site-auth-btn" href={loginUrl}>

        {t('logIn')}

      </a>

    );



  return (

    <header className={`tc-site-header${subnav ? ' has-subnav' : ''}`}>

      <div className="tc-site-top">

        <div className="tc-site-wrap tc-site-top-inner">

            <a className="tc-site-logo" href={TABS[0].href}>

            <img className="tc-site-logo-img" src="/tour-ceylon-logo.png" alt="" />
            <span className="tc-site-logo-text">Tour Ceylon</span>

          </a>

          <div className="tc-site-meta">

            <span className="tc-hide-sm">{CONTACT.hours}</span>

            <a className="tc-hide-sm" href={CONTACT.phoneHref}>{CONTACT.phone}</a>

            <a className="tc-site-quote tc-hide-sm" href={TABS[1].href}>{t('planTrip')}</a>

            <div className="tc-site-auth">

              {loggedIn ? (

                <>

                  {internalProfile ? (

                    <Link

                      className={`tc-site-profile${onProfile ? ' is-active' : ''}`}

                      to={profilePath}

                      onClick={() => setOpen(false)}

                      aria-label={t('nav_profile')}

                      title={label || t('nav_profile')}

                    >

                      <ProfileGlyph />

                    </Link>

                  ) : (

                    <a

                      className="tc-site-profile"

                      href={profileHref}

                      aria-label={t('nav_profile')}

                      title={label || t('nav_profile')}

                    >

                      <ProfileGlyph />

                    </a>

                  )}

                  <button type="button" className="tc-site-auth-btn is-logout" onClick={logout}>

                    {t('logOut')}

                  </button>

                </>

              ) : (

                loginControl

              )}

            </div>

          </div>

        </div>

      </div>



      <nav className={`tc-site-bar${open ? ' is-open' : ''}`}>

        <div className="tc-site-wrap tc-site-bar-inner">

          <button

            type="button"

            className="tc-site-menu"

            aria-label={t('openMenu')}

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

              const tabLabel = t(TAB_KEYS[tab.id] || 'tab_home');

              const internal = tab.internal?.[app];

              if (tab.idle) {

                return (

                  <span key={tab.id} className={className}>{tabLabel}</span>

                );

              }

              if (tab.id === 'sos' && onSosClick) {

                return (

                  <a key={tab.id} className={className} href={tab.href} onClick={onSosClick}>

                    {tabLabel}

                  </a>

                );

              }

              if (internal) {

                return (

                  <Link key={tab.id} className={className} to={internal} onClick={() => setOpen(false)}>

                    {tabLabel}

                  </Link>

                );

              }

              return (

                <a
                  key={tab.id}
                  className={className}
                  href={tab.href}
                  onMouseEnter={tab.id === 'wellness' ? () => {
                    if (document.querySelector('link[data-prefetch-wellness]')) return;
                    const base = tab.href.replace(/\/$/, '');
                    [
                      tab.href,
                      `${base}/css/style.css`,
                      `${base}/js/boot.js`,
                      `${base}/js/app.js`,
                      `${base}/data/pool.json`,
                    ].forEach((href) => {
                      const link = document.createElement('link');
                      link.rel = 'prefetch';
                      link.href = href;
                      link.dataset.prefetchWellness = '1';
                      document.head.appendChild(link);
                    });
                  } : undefined}
                >

                  {tabLabel}

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


