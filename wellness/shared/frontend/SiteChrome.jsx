import SiteHeader from './SiteHeader';
import SiteFooter from './SiteFooter';
import './site.css';

export default function SiteChrome({ app, active, onSosClick, subnav, children }) {
  return (
    <div className="tc-site">
      <SiteHeader app={app} active={active} onSosClick={onSosClick} subnav={subnav} />
      <div className="tc-site-body">{children}</div>
      <SiteFooter app={app} />
    </div>
  );
}
