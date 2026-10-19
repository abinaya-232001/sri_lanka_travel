import siteDetails from "../data/site_details.json";

const bySiteName = {};
siteDetails.forEach((s) => {
  bySiteName[s.site_name] = s;
});

export function getSiteInsights(siteName) {
  const s = bySiteName[siteName];
  if (!s) {
    if (import.meta.env.DEV) {
      console.warn("getSiteInsights: no match for site_name \"" + siteName + "\" in site_details.json");
    }
    return null;
  }
  const highlights = [s.description];
  if (s.specialties && s.specialties.length > 0) {
    highlights.push("Known for: " + s.specialties.slice(0, 3).join(", ") + ".");
  }
  return {
    highlights: highlights,
    context: s.culture || null,
    food: s.nearby_stay_eat || null,
    activities: s.activities && s.activities.length > 0 ? s.activities : null,
    recommendedDuration: s.recommended_duration || null,
    dressCode: (s.visitor_information && s.visitor_information.dress_code) || null,
    safety: s.safety && s.safety.length > 0 ? s.safety : null,
  };
}