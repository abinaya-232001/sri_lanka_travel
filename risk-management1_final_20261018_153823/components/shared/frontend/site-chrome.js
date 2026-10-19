import { SITE_LANGUAGES } from './i18n/languages.js';
import {
  getSiteLanguage,
  setSiteLanguage,
  SITE_LANGUAGE_EVENT,
  translate,
} from './i18n/core.js';
import { SITES } from './config.js';

const TAB_KEYS = {
  home: 'tab_home',
  itinerary: 'tab_itinerary',
  wellness: 'tab_wellness',
  livedata: 'tab_livedata',
  sos: 'tab_sos',
};

const CHROME_KEYS = {
  '[data-tc-plan-trip]': 'planTrip',
  '[data-tc-auth-login]': 'logIn',
  '[data-tc-auth-logout]': 'logOut',
  '[data-tc-auth-account]': 'myAccount',
  '[data-tc-footer-tagline]': 'footer_tagline',
  '[data-tc-footer-explore]': 'footer_explore',
  '[data-tc-footer-contact]': 'footer_contact',
  '[data-tc-footer-hours-label]': 'footer_hours',
  '[data-tc-footer-staff]': 'footerStaffAccess',
  '[data-tc-footer-police]': 'emergencyInstructionsLink',
  '[data-tc-footer-immigration]': 'immigrationDashboardLogin',
  '[data-tc-footer-wellness-admin]': 'wellnessAdminLogin',
  '#heroEyebrow': 'wellnessHeroEyebrow',
  '#heroHeading': 'wellnessHeroTitle',
  '#heroTagline': 'wellnessHeroTagline',
  '#heroBody': 'wellnessHeroBody',
  '#wellnessWhatLooking': 'wellnessWhatLooking',
  '#wellnessChooseStay': 'wellnessChooseStay',
  '#wellnessAyurvedaTitle': 'wellnessAyurvedaTitle',
  '#wellnessAyurvedaDesc': 'wellnessAyurvedaDesc',
  '#wellnessMeditationTitle': 'wellnessMeditationTitle',
  '#wellnessMeditationDesc': 'wellnessMeditationDesc',
};

const STAT_KEYS = ['wellnessStatCenters', 'wellnessStatMedical', 'wellnessStatWellness', 'wellnessStatSpiritual'];
const STEP_KEYS = ['wellnessStep1', 'wellnessStep2', 'wellnessStep3'];

function t(key, lang = getSiteLanguage()) {
  return translate(key, lang);
}

function applyStaticTranslations(lang = getSiteLanguage()) {
  document.documentElement.lang = lang === 'zh' ? 'zh-Hans' : lang;

  Object.entries(CHROME_KEYS).forEach(([selector, key]) => {
    document.querySelectorAll(selector).forEach((el) => {
      el.textContent = t(key, lang);
    });
  });

  document.querySelectorAll('[data-tc-tab]').forEach((el) => {
    const id = el.getAttribute('data-tc-tab');
    if (id && TAB_KEYS[id]) el.textContent = t(TAB_KEYS[id], lang);
  });

  document.querySelectorAll('[data-tc-stat-label]').forEach((el, index) => {
    const key = STAT_KEYS[index];
    if (key) el.textContent = t(key, lang);
  });

  document.querySelectorAll('[data-tc-step]').forEach((el, index) => {
    const key = STEP_KEYS[index];
    if (key) el.textContent = t(key, lang);
  });

  const browse = document.querySelector('[data-tc-browse-all]');
  if (browse) browse.textContent = t('wellnessBrowseAll', lang);

  const logoutBtn = document.querySelector('[data-tc-auth-logout]');
  if (logoutBtn) logoutBtn.textContent = t('logOut', lang);

  const loginLink = document.querySelector('[data-tc-auth-login]');
  if (loginLink) loginLink.textContent = t('logIn', lang);

  const account = document.querySelector('[data-tc-auth-account]');
  if (account) account.textContent = t('myAccount', lang);

  const fab = document.querySelector('.tc-sos-fab');
  if (fab) {
    const label = t('sosFabAria', lang);
    fab.setAttribute('aria-label', label);
    fab.setAttribute('title', label);
  }
}

function shouldHideSosFab() {
  if (document.body?.hasAttribute('data-tc-no-sos-fab')) return true;
  const path = window.location.pathname || '';
  return path === '/admin' || path.startsWith('/admin/');
}

function ensureSosFab() {
  if (shouldHideSosFab()) return;
  if (document.querySelector('.tc-sos-fab')) return;
  const href = `${String(SITES.sos || '').replace(/\/$/, '')}/sos`;
  const label = t('sosFabAria');
  const a = document.createElement('a');
  a.className = 'tc-sos-fab';
  a.href = href;
  a.setAttribute('aria-label', label);
  a.setAttribute('title', label);
  a.innerHTML = '<span class="tc-sos-fab-ring"><span class="tc-sos-fab-core">SOS</span></span>';
  document.body.appendChild(a);
}

export function initSiteChrome() {
  ensureSosFab();
  applyStaticTranslations();

  window.addEventListener(SITE_LANGUAGE_EVENT, (event) => {
    applyStaticTranslations(event.detail || getSiteLanguage());
  });

  window.addEventListener('storage', (event) => {
    if (event.key === 'siteLanguage' || event.key === 'sosLang') {
      applyStaticTranslations(getSiteLanguage());
    }
  });
}

export { applyStaticTranslations, t as siteT };
