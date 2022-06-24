import { KC_AUTH_URL, KC_REALM, KC_CLIENT } from 'utils/env'
import { KeycloakInitOptions } from 'types/keycloak'

export const kcInitOption: KeycloakInitOptions = {
  onLoad: 'login-required',
  checkLoginIframe: false,
  enableLogging: process.env.NODE_ENV !== 'production'
}

const getInstance = () => {
  return window.Keycloak({
    url: KC_AUTH_URL,
    realm: KC_REALM,
    clientId: KC_CLIENT
  })
}

export default getInstance
