// Local development. `ng serve` proxies /api to Django on port 8000 (proxy.conf.json).
export const environment = {
  production: false,
  apiUrl: '/api',
  // Free OpenStreetMap vector tiles, no key or account needed. Set to '' to hide the map.
  mapStyleUrl: 'https://tiles.openfreemap.org/styles/liberty',
};