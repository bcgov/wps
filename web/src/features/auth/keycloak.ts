import { KC_AUTH_URL, KC_REALM, KC_CLIENT } from 'utils/env'
import { KeycloakInitOptions } from 'types/keycloak'

export const kcInitOption: KeycloakInitOptions = {
  onLoad: 'login-required',
  checkLoginIframe: false,
  enableLogging: process.env.NODE_ENV !== 'production'
}

let isLoaded = false

const getInstance = (): Keycloak.KeycloakInstance => {
  return window.Keycloak({
    url: KC_AUTH_URL,
    realm: KC_REALM,
    clientId: KC_CLIENT
  })
}

const resolveInstance = () => {
  // NOTE: The documentation for Keycloak now states that: "A good practice is to include the "
  // JavaScript adapter in your application using a package manager like NPM or Yarn."
  // So this complicated approach is no longer needed! (Documentation used to recomend loading
  // from the server, but this is no longer the case.)
  return new Promise<Keycloak.KeycloakInstance | null>(resolve => {
    if (isLoaded) {
      // If keycloak is loaded, we can resolve right away.
      resolve(getInstance())
    } else {
      // If keycloak is not loaded, then we have to wait for it to load.
      const script = document.createElement('script')
      script.src = KC_AUTH_URL + '/js/keycloak.js'
      script.type = 'text/javascript'
      script.onload = function () {
        isLoaded = true
        resolve(getInstance())
      }
      document.head.appendChild(script)
    }
  })
}

export default resolveInstance
