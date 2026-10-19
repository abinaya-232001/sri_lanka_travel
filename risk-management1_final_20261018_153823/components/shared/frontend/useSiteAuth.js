import { useCallback, useEffect, useState } from 'react';
import { getLoginUrl, getUserLabel, isLoggedIn, logout as defaultLogout } from './authHeader';

export function useSiteAuth(app, { isAuthenticated, user, onLogout } = {}) {
  const readState = useCallback(
    () => ({
      loggedIn: isAuthenticated ?? isLoggedIn(app),
      label: user?.name || user?.email || getUserLabel(app),
    }),
    [app, isAuthenticated, user],
  );

  const [state, setState] = useState(readState);

  useEffect(() => {
    setState(readState());
  }, [readState]);

  useEffect(() => {
    const sync = () => setState(readState());
    window.addEventListener('storage', sync);
    return () => window.removeEventListener('storage', sync);
  }, [readState]);

  const login = useCallback(() => {
    window.location.assign(getLoginUrl(app));
  }, [app]);

  const logout = useCallback(() => {
    if (onLogout) {
      onLogout();
      return;
    }
    defaultLogout(app);
  }, [app, onLogout]);

  return { ...state, login, logout, loginUrl: getLoginUrl(app) };
}
