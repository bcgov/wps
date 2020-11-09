import { KC_AUTH_URL, KC_REALM, KC_CLIENT } from 'utils/constants'
import { KeycloakInitOptions } from 'types/keycloak'

export const kcInitOption: KeycloakInitOptions = {
  onLoad: 'login-required',
  promiseType: 'native',
  checkLoginIframe: false
}

// Let Typescript know we are using the 'native' promise type
const instance = window.Keycloak
  ? window.Keycloak<'native'>({
      url: KC_AUTH_URL!,
      realm: KC_REALM!,
      clientId: KC_CLIENT!
    })
  : null

export default instance
