import { SITES } from './config';
import { clearTravelSessionCookie, hydrateTravelSessionFromCookie } from './travelSession.js';

const TRAVEL_LOGIN = `${SITES.home.replace(/\/$/, '')}/login`;

export function getLoginUrl(app) {
  if (app === 'police') return `${SITES.police.replace(/\/$/, '')}/login`;
  if (app === 'immigration') return `${SITES.immigration.replace(/\/$/, '')}/login`;
  return TRAVEL_LOGIN;
}

export function isLoggedIn(app) {
  hydrateTravelSessionFromCookie();
  if (app === 'police') return !!localStorage.getItem('policeToken');
  if (app === 'immigration') return !!localStorage.getItem('immigrationToken');
  if (app === 'tourist') {
    return !!localStorage.getItem('touristToken') || !!localStorage.getItem('access_token');
  }
  return !!localStorage.getItem('access_token');
}

function travelUserLabel() {
  try {
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    return user.name || user.email || null;
  } catch {
    return null;
  }
}

export function getUserLabel(app) {
  if (app === 'police') {
    try {
      const officer = JSON.parse(localStorage.getItem('policeOfficer') || '{}');
      return officer.name || officer.username || null;
    } catch {
      return null;
    }
  }
  if (app === 'immigration') {
    try {
      const officer = JSON.parse(localStorage.getItem('immigrationOfficer') || '{}');
      return officer.name || officer.username || null;
    } catch {
      return null;
    }
  }
  if (app === 'tourist') return localStorage.getItem('touristName') || travelUserLabel();
  return travelUserLabel();
}

export function clearAuthForApp(app) {
  if (app === 'police') {
    localStorage.removeItem('policeToken');
    localStorage.removeItem('policeOfficer');
    return;
  }
  if (app === 'immigration') {
    localStorage.removeItem('immigrationToken');
    localStorage.removeItem('immigrationOfficer');
    return;
  }
  if (app === 'tourist') {
    localStorage.removeItem('touristToken');
    localStorage.removeItem('touristId');
    localStorage.removeItem('touristName');
    localStorage.removeItem('activeIncidentId');
    localStorage.removeItem('activeStationName');
    return;
  }
  localStorage.removeItem('access_token');
  localStorage.removeItem('user');
  localStorage.removeItem('touristToken');
  localStorage.removeItem('touristId');
  localStorage.removeItem('touristName');
  localStorage.removeItem('activeIncidentId');
  localStorage.removeItem('activeStationName');
  clearTravelSessionCookie();
}

export function logout(app) {
  if (app === 'police') {
    clearAuthForApp('police');
    window.location.assign(getLoginUrl('police'));
    return;
  }
  if (app === 'immigration') {
    clearAuthForApp('immigration');
    window.location.assign(getLoginUrl('immigration'));
    return;
  }
  clearAuthForApp('travel');
  window.location.assign(getLoginUrl('travel'));
}
