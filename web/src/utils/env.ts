let ENV = {
  API_BASE_URL: import.meta.env.VITE_API_BASE_URL as string,
  HIDE_DISCLAIMER: import.meta.env.VITE_HIDE_DISCLAIMER,
  KC_AUTH_URL: import.meta.env.VITE_KEYCLOAK_AUTH_URL as string,
  KC_REALM: import.meta.env.VITE_KEYCLOAK_REALM as string,
  KC_CLIENT: import.meta.env.VITE_KEYCLOAK_CLIENT as string
}

// If the app is built using 'npm run build'
if (import.meta.env.NODE_ENV === 'production') {
  // window.env is set in index.html, populated by env variables.
  ENV = {
    // TODO: Figure out why axios goes to http on gets!
    API_BASE_URL: `${window.location.protocol}//${window.location.host}/api`,
    HIDE_DISCLAIMER: undefined,
    KC_AUTH_URL: window.env.VITE_KEYCLOAK_AUTH_URL,
    KC_REALM: window.env.VITE_KEYCLOAK_REALM,
    KC_CLIENT: window.env.VITE_KEYCLOAK_CLIENT
  }
}

export const { API_BASE_URL, HIDE_DISCLAIMER, KC_AUTH_URL, KC_REALM, KC_CLIENT } = ENV
