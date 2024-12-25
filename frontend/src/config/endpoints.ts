export const API_ENDPOINTS = {
  base: 'http://localhost:8000',
  cryptocurrencies: '/api/cryptocurrencies',
  marketData: '/api/market-data',
  analysis: '/api/analysis'
} as const;

export const getEndpoint = (path: keyof typeof API_ENDPOINTS) => API_ENDPOINTS[path];
export const buildUrl = (path: keyof typeof API_ENDPOINTS, ...segments: string[]) => {
  const base = API_ENDPOINTS.base;
  const endpoint = API_ENDPOINTS[path];
  return `${base}${endpoint}${segments.length ? '/' + segments.join('/') : ''}`;
}; 