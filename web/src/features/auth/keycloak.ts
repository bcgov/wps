import { KC_AUTH_URL, KC_REALM, KC_CLIENT } from 'utils/env'
import { KeycloakInitOptions } from 'types/keycloak'

export const kcInitOption: KeycloakInitOptions = {
  onLoad: 'login-required',
  checkLoginIframe: false,
  enableLogging: process.env.NODE_ENV !== 'production'
}

// Let Typescript know we are using the 'native' promise type
const instance = window.Keycloak
  ? window.Keycloak({
      url: KC_AUTH_URL,
      realm: KC_REALM,
      clientId: KC_CLIENT
    })
  : null

export default instance
