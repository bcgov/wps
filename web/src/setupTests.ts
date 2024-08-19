// react-testing-library renders your components to document.body,
// this adds jest-dom's custom assertions
import '@testing-library/jest-dom'
import crypto from 'crypto'
import { vi } from 'vitest'

Object.defineProperty(global, 'crypto', {
  value: {
    randomUUID: () => crypto.randomUUID()
  }
})

vi.mock('@mui/x-license-pro', () => ({
  ...jest.requireActual('@mui/x-license-pro'),
  useLicenseVerifier: () => 'Valid',
  Watermark: () => null
}))
