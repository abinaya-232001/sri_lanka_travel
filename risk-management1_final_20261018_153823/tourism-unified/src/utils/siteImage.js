export function siteImageSlug(siteName) {
  return String(siteName || "")
    .toLowerCase()
    .replace(/['\u2018\u2019]/g, "")
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");
}

export function siteImagePath(siteName) {
  return "/images/" + siteImageSlug(siteName) + ".jpg";
}
