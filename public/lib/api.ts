const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";
const DEFAULT_APP_BASE_URL = "http://localhost:3000";

export function getApiBaseUrl() {
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? DEFAULT_API_BASE_URL;
}

export function getAppBaseUrl() {
  if (typeof window !== "undefined") {
    return window.location.origin;
  }

  return process.env.NEXT_PUBLIC_APP_BASE_URL ?? DEFAULT_APP_BASE_URL;
}
