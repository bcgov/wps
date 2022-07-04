// use TypeScript's interface declaration merging
interface Window {
  env: {
    REACT_APP_SM_LOGOUT_URL: string
    REACT_APP_KEYCLOAK_AUTH_URL: string
    REACT_APP_KEYCLOAK_REALM: string
    REACT_APP_KEYCLOAK_CLIENT: string
    API_BASE_URL: string | undefined
  }
  Cypress: {} | undefined
}
