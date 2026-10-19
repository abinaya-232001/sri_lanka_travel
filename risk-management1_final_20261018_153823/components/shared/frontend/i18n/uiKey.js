/** Build a stable i18n key suffix from a UI label (mood name, category, etc.). */
export function uiKey(prefix, value) {
  const slug = String(value)
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_|_$/g, '');
  return `${prefix}_${slug}`;
}
