// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom/extend-expect'

// adding polyfill for js-dom createRange function
// https://github.com/popperjs/popper-core/issues/478#issuecomment-344745255
/* eslint-disable */
if (window.document) {
  window.document.createRange = () => ({
    setStart: () => {},
    setEnd: () => {},
    // @ts-ignore
    commonAncestorContainer: {
      nodeName: 'BODY',
      ownerDocument: document
    }
  })
}

// mock Keycloak function to always be authenticated
window.Keycloak = () => ({
  init: () =>
    // @ts-ignore
    new Promise((resolve, reject) => {
      resolve(true)
    })
})

window.env = {
  REACT_APP_FIDER_LINK: 'https://psufiderdev.pathfinder.gov.bc.ca/',
  REACT_APP_KEYCLOAK_AUTH_URL: 'https://sso-dev.pathfinder.gov.bc.ca/auth',
  REACT_APP_KEYCLOAK_REALM: 'keycloak_realm',
  REACT_APP_KEYCLOAK_CLIENT: 'keycloak_client'
}
