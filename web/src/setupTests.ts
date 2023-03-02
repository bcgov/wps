// react-testing-library renders your components to document.body,
// this adds jest-dom's custom assertions
import '@testing-library/jest-dom'
import crypto from 'crypto'

Object.defineProperty(global, 'crypto', {
  value: {
    randomUUID: () => crypto.randomUUID()
  }
})
