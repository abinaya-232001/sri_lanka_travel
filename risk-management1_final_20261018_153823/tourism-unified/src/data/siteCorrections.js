// Corrections identified against Sri Lanka Tourism reference material.
// Merge this into your site data (see wiring note below).
// Key = site_id, value = fields to override.

export const SITE_CORRECTIONS = {
  24: { category: "Nature", subcategory: "Viewpoint" },
  25: { district: "Kandy / Matale", category: "Nature", subcategory: "Mountain Range" },
  33: { category: "Landmark", subcategory: "Observation Tower" },
  37: { district: "Matale / Kandy", category: "Nature", subcategory: "Forest Reserve" },
  39: { category: "Nature", subcategory: "Marine National Park" },
  40: { district: "Batticaloa", category: "Beach", subcategory: "Tropical Beach" },
  42: { category: "Religious", subcategory: "Pilgrimage Island" },
  44: { district: "Ratnapura / Moneragala", category: "Nature", subcategory: "Reservoir" },
  45: { category: "Religious", subcategory: "Pilgrimage Centre" },
  50: { category: "Nature", subcategory: "Lake" },
  51: { category: "Heritage", subcategory: "Railway Landmark" },
  55: { category: "Nature", subcategory: "Mountain Viewpoint" },
  61: { category: "Religious", subcategory: "Buddha Statue" },
  66: { category: "Heritage", subcategory: "Lighthouse" },
  72: { category: "Leisure", subcategory: "Urban Waterfront" },
  73: { category: "Leisure", subcategory: "Urban Park" },
  77: { category: "Nature", subcategory: "Lagoon & Wetland" },
  78: { category: "Nature", subcategory: "Coastal Forest & Hill" },
  79: { category: "Nature", subcategory: "Wetland Sanctuary" },
  80: {
    district: "Polonnaruwa / Batticaloa / Ampara",
    category: "Wildlife",
    subcategory: "National Park",
  },
  16: { district: "Ratnapura / Moneragala" },
  49: { district: "Kalutara" },
};

export function applyCorrections(sites) {
  return sites.map((site) => {
    const fix = SITE_CORRECTIONS[site.site_id];
    return fix ? { ...site, ...fix } : site;
  });
}
