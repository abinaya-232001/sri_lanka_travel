import { SITE_LANGUAGE_CODES } from './languages.js'
import { EXTRA_KEYS } from './extraKeys.js'
import { ITINERARY_PAGE_KEYS } from './itineraryPageKeys.js'
import siLocale from './locales/si.json'
import taLocale from './locales/ta.json'
import ruLocale from './locales/ru.json'
import deLocale from './locales/de.json'
import zhLocale from './locales/zh.json'
import jaLocale from './locales/ja.json'
import esLocale from './locales/es.json'
import frLocale from './locales/fr.json'
import koLocale from './locales/ko.json'

/** English base — all UI keys for tourist apps. */
export const EN = {
  language: 'Language',
  logIn: 'Log in',
  logOut: 'Log out',
  planTrip: 'Plan a trip',
  openMenu: 'Open menu',
  hoursLabel: '09:00 AM — 05:00 PM',
  tab_home: 'Home',
  tab_itinerary: 'Itinerary',
  tab_wellness: 'Wellness',
  tab_livedata: 'Live Data',
  tab_sos: 'SOS',
  footer_tagline:
    'Beach-to-highlands travel for Sri Lanka — itineraries, wellness matching, live safety data, and one-tap SOS.',
  footer_explore: 'Explore',
  footer_contact: 'Contact',
  footer_hours: 'Hours',
  footer_copyright: 'All rights reserved.',
  footer_tagline2: 'Sri Lanka tourism · wellness · safety',
  nav_home: 'Home',
  nav_trips: 'Trips',
  nav_sos: 'SOS',
  nav_messages: 'Messages',
  nav_profile: 'Profile',
  sos_title: 'ARE YOU IN DANGER?',
  sos_hold: 'Hold 2s — SOS GET HELP',
  sos_sent: 'HELP REQUEST SENT',
  location_sharing: 'Your location is being shared with authorized responders',
  safety_status: 'Safety status',
  ready: 'Ready',
  active_case: 'Active case',
  loading: 'Loading…',
  checkingLogin: 'Checking login…',
  openingLogin: 'Opening Tour Ceylon login…',
  visitor: 'Visitor',
  noActiveEmergency: 'No active emergency',
  latestUpdates: 'Latest response updates',
  safetyCard: 'Safety card',
  safeJourney: 'Safe Journey',
  nearbyHelp: 'Nearby help',
  emergencyInstructionsLink: 'Police dashboard',
  immigrationDashboardLogin: 'Immigration dashboard login',
  emergencyInstructions: 'Emergency instructions',
  readTipsSosNearby: 'Read tips — SOS one tap away',
  policeCommandCenter: 'Police command center',
  policeCommandDesc:
    'Officers at the nearest police station receive your SOS with profile and Safe Journey route. Open the police dashboard to monitor and respond.',
  openPoliceDashboard: 'Open police dashboard',
  openImmigrationDashboard: 'Open immigration dashboard',
  needHelpNow: 'Need help now?',
  openSos: 'Open SOS',
  sendingSos: 'Sending SOS…',
  sendingSosDesc: 'Alerting nearest police with your profile, GPS, and route.',
  policeResponse: 'Police response',
  stationChat: 'Station chat',
  nearbyServices: 'Nearby services',
  localHelpDirections: 'LOCAL HELP, CLEAR DIRECTIONS',
  nearbyServicesDesc:
    'Sorted by distance from your current GPS. Message nearby police with voice or text — your language is translated for officers.',
  findingServices: 'Finding nearby services...',
  noServicesFound: 'No services found for this location.',
  safeJourneyTitle: 'Safe Journey',
  voluntaryMonitoring: 'VOLUNTARY LOCATION MONITORING',
  waitingGps: 'Waiting for GPS… allow location access to see the map.',
  currentLocationRequired: 'Current location required.',
  recordedRoute: 'Recorded route',
  digitalSafetyCard: 'Digital safety card',
  updatingServer: 'Updating from server…',
  embassyMatch: 'Your embassy match',
  signInForCard: 'Sign in to show your profile on the safety card.',
  addFamilyContact: 'Add family WhatsApp contact',
  safetyTips: 'Safety tips',
  touristPolice: 'Tourist Police',
  seeDirectory: 'see directory',
  tripsCheckin: 'Trips & check-in',
  tripsDesc: 'Voluntary check-in at destinations helps responders locate you.',
  recentCheckins: 'Recent check-ins',
  messagesTitle: 'Messages',
  noActiveConversation: 'No active conversation. Use SOS to contact police.',
  sosRecords: 'SOS records',
  sosRecordsDesc: 'Current open cases and your past history',
  current: 'Current',
  otherActive: 'Other active',
  noOpenSos: 'No open SOS right now.',
  noClosedIncidents: 'No closed incidents yet.',
  history: 'History',
  yourProfile: 'Your profile',
  loadingProfile: 'Loading profile…',
  saveProfile: 'Save profile',
  profileSaved: 'Profile saved.',
  generateCompletedProfile: 'Generate completed profile',
  generatingProfile: 'Generating card…',
  profileCompleted: 'Your visitor profile is complete.',
  profileLocked: 'Completed',
  profileLockedHint: 'This visitor pass is locked and can no longer be edited.',
  profileEditHint: 'Tap Edit to update your visitor pass.',
  editProfile: 'Edit',
  cancelEdit: 'Cancel',
  saveChanges: 'Save changes',
  visitorPass: 'Visitor pass',
  tripDates: 'Trip dates',
  completeProfileMissing: 'Fill name, phone, nationality, passport, and emergency contact first.',
  fullName: 'Full name',
  phone: 'Phone',
  nationality: 'Nationality',
  passportNic: 'Passport / NIC',
  tripStart: 'Trip start',
  tripEnd: 'Trip end',
  hotelName: 'Hotel name',
  hotelContact: 'Hotel contact',
  travelVisa: 'Travel & visa',
  dateOfBirth: 'Date of birth',
  gender: 'Gender',
  visaType: 'Visa type',
  visaExpiry: 'Visa expiry',
  travelPurpose: 'Travel purpose',
  preferredLanguage: 'Preferred language',
  optionalMedical: 'Optional emergency medical',
  medicalInfo: 'Medical info',
  allergies: 'Allergies',
  bloodGroup: 'Blood group',
  specialRequirements: 'Special requirements',
  consent: 'Consent',
  emergencyContact: 'Emergency contact',
  emergencyName: 'Name',
  emergencyPhone: 'Phone',
  emergencyEmail: 'Email',
  emergencyRelationship: 'Relationship',
  newPassword: 'New password (optional)',
  updatePhoto: 'Update photo',
  updateDocument: 'Update document photo',
  workflowSosSent: 'SOS sent',
  workflowAcknowledged: 'Acknowledged',
  workflowDispatched: 'Dispatched',
  workflowEscalated: 'Escalated',
  workflowResolved: 'Resolved',
  nearestPoliceStation: 'Nearest police station',
  policeContactTitle: 'Contact nearby police',
  policeContactDesc:
    'Speak or type in your language. Speech is converted to text, detected, translated, and sent to this station\'s dashboard.',
  supportedLanguagesNote:
    'Supported languages: English, Sinhala, Tamil, Russian, German, Chinese, Japanese, Spanish, French, Korean.',
  sendMessage: 'Send message',
  recordVoice: 'Record voice',
  stopRecording: 'Stop recording',
  step_attractions: 'Attractions',
  step_budget: 'Budget',
  step_stay: 'Stay',
  step_itinerary: 'Itinerary',
  step_discover: 'Discover',
  step_export: 'Export',
  step_attractions_full: 'Attractions Selection',
  step_budget_full: 'Budget Allocation',
  step_stay_full: 'Accommodation Selection',
  step_itinerary_full: 'Itinerary Summary',
  step_discover_full: 'Recommendations Discovery',
  step_export_full: 'Export Summary',
  profile: 'Profile',
  tripHistory: 'Trip History',
  planning: 'Planning',
  closeMenu: 'Close menu',
  tripSteps: 'Trip steps',
  tripProgress: 'Trip progress',
  searchAttractions: 'Search attractions…',
  touristSos: 'Tourist SOS',
  ...EXTRA_KEYS,
  ...ITINERARY_PAGE_KEYS,
}

function bundle(overrides) {
  return { ...EN, ...overrides }
}

const SI = bundle(siLocale)
const TA = bundle(taLocale)
const RU = bundle(ruLocale)
const DE = bundle(deLocale)
const ZH = bundle(zhLocale)
const JA = bundle(jaLocale)
const ES = bundle(esLocale)
const FR = bundle(frLocale)
const KO = bundle(koLocale)

export const messages = {
  en: EN,
  si: SI,
  ta: TA,
  ru: RU,
  de: DE,
  zh: ZH,
  ja: JA,
  es: ES,
  fr: FR,
  ko: KO,
}

/** Legacy key aliases used by older tourist components. */
export const KEY_ALIASES = {
  nav_home: 'nav_home',
  nav_trips: 'nav_trips',
  nav_sos: 'nav_sos',
  nav_messages: 'nav_messages',
  nav_profile: 'nav_profile',
}

export function isSupportedLanguage(code) {
  return SITE_LANGUAGE_CODES.includes(code)
}

export function translate(key, language = 'en') {
  const lang = isSupportedLanguage(language) ? language : 'en'
  return messages[lang]?.[key] || messages.en[key] || key
}
