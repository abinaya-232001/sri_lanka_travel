const travel = (import.meta.env?.VITE_TRAVEL_APP_URL || 'http://localhost:5180').replace(/\/$/, '');
const wellness = (import.meta.env?.VITE_WELLNESS_APP_URL || 'http://localhost:5181').replace(/\/$/, '');
const sos = (import.meta.env?.VITE_SOS_APP_URL || 'http://localhost:5175').replace(/\/$/, '');
const police = (import.meta.env?.VITE_POLICE_APP_URL || 'http://localhost:5176').replace(/\/$/, '');
const livedata = (import.meta.env?.VITE_LIVEDATA_APP_URL || 'http://localhost:5182').replace(/\/$/, '');

export const SITES = {
  home: `${travel}/`,
  itinerary: `${travel}/attractions`,
  wellness: `${wellness}/`,
  livedata: `${livedata}/`,
  police: `${police}/`,
  sos: `${sos}/`,
};

export const CONTACT = {
  hours: '09:00 AM — 05:00 PM',
  phone: '+94 11 243 7059',
  phoneHref: 'tel:+94112437059',
  mobile: '+94 77 123 4567',
  mobileHref: 'tel:+94771234567',
  email: 'hello@tourceylon.lk',
  emailHref: 'mailto:hello@tourceylon.lk',
  address: 'Colombo, Sri Lanka',
};

export const TABS = [
  { id: 'home', label: 'Home', href: SITES.home, internal: { travel: '/' } },
  { id: 'itinerary', label: 'Itinerary', href: SITES.itinerary, internal: { travel: '/attractions' } },
  { id: 'wellness', label: 'Wellness', href: SITES.wellness, internal: { wellness: '/' } },
  { id: 'livedata', label: 'Live Data', href: SITES.livedata, internal: { livedata: '/' } },
  { id: 'sos', label: 'SOS', href: SITES.sos, internal: { tourist: '/' } },
];
