// use TypeScript's interface declaration merging
interface Window {
  env: {
    VITE_KEYCLOAK_AUTH_URL: string
    VITE_KEYCLOAK_REALM: string
    VITE_KEYCLOAK_CLIENT: string
    VITE_KEYCLOAK_CLIENT: string
    VITE_SM_LOGOUT_URL: string
    API_BASE_URL: string | undefined
    RASTER_SERVER_BASE_URL: string | undefined
  }
  Cypress: {} | undefined
}
