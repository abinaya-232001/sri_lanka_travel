import SiteHeader from './SiteHeader';
import SiteFooter from './SiteFooter';
import SiteSosFab from './SiteSosFab';
import './site.css';

export default function SiteChrome({
  app,
  active,
  onSosClick,
  subnav,
  children,
  isAuthenticated,
  user,
  onLogout,
}) {
  return (
    <div className="tc-site">
      <SiteHeader
        app={app}
        active={active}
        onSosClick={onSosClick}
        subnav={subnav}
        isAuthenticated={isAuthenticated}
        user={user}
        onLogout={onLogout}
      />
      <div className="tc-site-body">{children}</div>
      <SiteFooter app={app} />
      {app === 'police' || app === 'immigration' ? null : <SiteSosFab app={app} />}
    </div>
  );
}
