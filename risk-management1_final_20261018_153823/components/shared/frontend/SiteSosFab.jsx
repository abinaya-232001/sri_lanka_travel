import { Link } from 'react-router-dom';
import { SITES } from './config';
import { useSiteI18n } from './i18n/react.js';

export function sosPageUrl(next = '/sos') {
  const base = String(SITES.sos || '').replace(/\/$/, '');
  const path = next.startsWith('/') ? next : `/${next}`;
  return `${base}/enter?next=${encodeURIComponent(path)}`;
}

export default function SiteSosFab({ app = 'travel' }) {
  const { t } = useSiteI18n();
  const label = t('sosFabAria');
  const inner = (
    <span className="tc-sos-fab-ring">
      <span className="tc-sos-fab-core">SOS</span>
    </span>
  );

  if (app === 'tourist') {
    return (
      <Link className="tc-sos-fab" to="/sos" aria-label={label} title={label}>
        {inner}
      </Link>
    );
  }

  return (
    <a className="tc-sos-fab" href={sosPageUrl()} aria-label={label} title={label}>
      {inner}
    </a>
  );
}
