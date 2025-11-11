// DYNAMIC BACKEND URL CONFIGURATION
// Uses environment variable if set, otherwise detects automatically

const getBackendURL = () => {
  // Priority 1: Check environment variable
  const envURL = process.env.REACT_APP_BACKEND_URL;
  if (envURL && envURL.trim() !== '') {
    return envURL.trim();
  }
  
  // Priority 2: Detect from current page
  const protocol = window.location.protocol; // 'http:' or 'https:'
  const host = window.location.hostname;     // 'suporte.help' or '151.243.218.223'
  
  return `${protocol}//${host}`;
};

export const BASE_URL = getBackendURL();
export const API_BASE_URL = `${BASE_URL}/api`;

console.log('🔧 API CONFIG:', {
  ENV_VAR: process.env.REACT_APP_BACKEND_URL || '(not set)',
  DETECTED_PROTOCOL: window.location.protocol,
  DETECTED_HOST: window.location.hostname,
  FINAL_BASE_URL: BASE_URL,
  FINAL_API_URL: API_BASE_URL
});
