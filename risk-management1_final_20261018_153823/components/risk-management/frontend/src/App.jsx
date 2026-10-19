import { lazy, Suspense, useState } from 'react';
import { ThemeProvider } from '@risk/design/ThemeContext.jsx';
import Home from '@risk/pages/Home.jsx';
import DashboardChrome from './DashboardChrome';
import '@risk/index.css';
import '@risk/design/theme.css';
import './dashboard-chrome.css';

const Discover = lazy(() => import('@risk/pages/tourist/Discover.jsx'));
const DestinationDetail = lazy(() => import('@risk/pages/tourist/DestinationDetail.jsx'));

const embedded = new URLSearchParams(window.location.search).get('embed') === '1';

function LiveDataApp() {
  const [page, setPage] = useState(embedded ? 'discover' : 'home');
  const [selectedSite, setSelectedSite] = useState(null);

  const go = (target) => {
    setPage(target);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  let body = null;
  if (page === 'home') {
    body = <Home onGetStarted={() => go('discover')} />;
  } else if (page === 'discover') {
    body = (
      <Suspense fallback={<p style={{ padding: 32 }}>Loading destinations…</p>}>
        <Discover
          onSelectSite={(id, date) => {
            setSelectedSite({ id, date });
            setPage('destinationDetail');
            window.scrollTo({ top: 0, behavior: 'smooth' });
          }}
        />
      </Suspense>
    );
  } else {
    body = (
      <Suspense fallback={<p style={{ padding: 32 }}>Loading destination…</p>}>
        <DestinationDetail
          siteId={selectedSite ? selectedSite.id : null}
          date={selectedSite ? selectedSite.date : null}
          onSelectSite={(id, date) => {
            setSelectedSite({ id, date });
            window.scrollTo({ top: 0, behavior: 'smooth' });
          }}
          onBack={() => go('discover')}
        />
      </Suspense>
    );
  }

  return (
    <DashboardChrome>
      <div className="ld-app-shell">{body}</div>
    </DashboardChrome>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <LiveDataApp />
    </ThemeProvider>
  );
}
