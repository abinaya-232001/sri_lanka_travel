import { getLoginUrl, getUserLabel, isLoggedIn, logout } from './authHeader.js';
import { SITES } from './config.js';

const PROFILE_SVG = `<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" fill="none">
  <circle cx="12" cy="8" r="3.4" stroke="currentColor" stroke-width="1.8" />
  <path d="M5.2 19.4c1.5-3.2 3.8-4.8 6.8-4.8s5.3 1.6 6.8 4.8" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
</svg>`;

/** Fill [data-tc-auth] on vanilla pages (wellness) so the header matches travel. */
export function mountSiteAuth(app = 'travel') {
  const slot = document.querySelector('[data-tc-auth]');
  if (!slot) return;

  const profileHref = `${String(SITES.home || 'http://localhost:5180').replace(/\/$/, '')}/profile`;
  if (isLoggedIn(app)) {
    const label = getUserLabel(app) || 'Profile';
    slot.innerHTML = `
      <a class="tc-site-profile" href="${profileHref}" aria-label="Profile" title="${label}">${PROFILE_SVG}</a>
      <button type="button" class="tc-site-auth-btn is-logout" data-tc-auth-logout>Log out</button>
    `;
    slot.querySelector('[data-tc-auth-logout]')?.addEventListener('click', () => logout(app));
    return;
  }

  slot.innerHTML = `<a class="tc-site-auth-btn" data-tc-auth-login href="${getLoginUrl(app)}">Log in</a>`;
}
