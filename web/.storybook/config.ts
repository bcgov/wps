import { configure, addDecorator } from '@storybook/react'
import { ThemeDecorator } from './decorators/ThemeDecorator'

// @ts-ignore
window.env = {
  REACT_APP_FIDER_LINK: 'https://some-gov.gov.bc.ca/',
  REACT_APP_KEYCLOAK_AUTH_URL: 'https://some-auth-link/auth',
  REACT_APP_KEYCLOAK_REALM: 'some_realm',
  REACT_APP_KEYCLOAK_CLIENT: 'some_client'
}

const req = require.context('../src', true, /\.stories\.tsx$/)

function loadStories() {
  req.keys().forEach(req)
}

addDecorator(ThemeDecorator)

configure(loadStories, module)
