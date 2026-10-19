const TOKEN_COOKIE = 'tc_access_token';
const USER_COOKIE = 'tc_user';
const WEEK = 60 * 60 * 24 * 7;

function readCookie(name) {
  const prefix = `${name}=`;
  const row = document.cookie.split('; ').find((part) => part.startsWith(prefix));
  if (!row) return null;
  try {
    return decodeURIComponent(row.slice(prefix.length));
  } catch {
    return null;
  }
}

function writeCookie(name, value, maxAge) {
  document.cookie = `${name}=${encodeURIComponent(value)}; path=/; max-age=${maxAge}; SameSite=Lax`;
}

function cookieSafeUser(user) {
  if (!user || typeof user !== 'object') return null;
  const { picture, ...rest } = user;
  const slim = { ...rest };
  if (picture && String(picture).length < 240) slim.picture = picture;
  return slim;
}

/** Cookies are shared across localhost ports; localStorage is not. */
export function writeTravelSessionCookie(token, user) {
  if (!token) return;
  writeCookie(TOKEN_COOKIE, token, WEEK);
  const slim = cookieSafeUser(user);
  if (slim) writeCookie(USER_COOKIE, JSON.stringify(slim), WEEK);
}

export function clearTravelSessionCookie() {
  writeCookie(TOKEN_COOKIE, '', 0);
  writeCookie(USER_COOKIE, '', 0);
}

export function hydrateTravelSessionFromCookie() {
  try {
    const token = readCookie(TOKEN_COOKIE);
    if (token && !localStorage.getItem('access_token')) {
      localStorage.setItem('access_token', token);
    }
    const userRaw = readCookie(USER_COOKIE);
    if (userRaw && !localStorage.getItem('user')) {
      JSON.parse(userRaw);
      localStorage.setItem('user', userRaw);
    }
  } catch {
    /* ignore */
  }
}
