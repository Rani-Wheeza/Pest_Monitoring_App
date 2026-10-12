// Local development. `ng serve` proxies /api to Django on port 8000 (proxy.conf.json).
export const environment = {
  production: false,
  apiUrl: '/api',
  // Leave empty to use the coordinate fields instead of the map. Never commit a real key.
  azureMapsKey: '',
};
