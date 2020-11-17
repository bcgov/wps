import { configure, addDecorator } from '@storybook/react'
import { ThemeDecorator } from './decorators/ThemeDecorator'

// @ts-ignore
window.env = {
  REACT_APP_FIDER_LINK: 'https://psufiderdev.pathfinder.gov.bc.ca/',
  REACT_APP_KEYCLOAK_AUTH_URL: 'https://sso-dev.pathfinder.gov.bc.ca/auth',
  REACT_APP_KEYCLOAK_REALM: 'keycloak_realm',
  REACT_APP_KEYCLOAK_CLIENT: 'keycloak_client'
}

const req = require.context('../src', true, /\.stories\.tsx$/)

function loadStories() {
  req.keys().forEach(req)
}

addDecorator(ThemeDecorator)

configure(loadStories, module)
