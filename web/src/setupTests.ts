// react-testing-library renders your components to document.body,
// this adds jest-dom's custom assertions

import '@testing-library/jest-dom'
import { cleanup } from '@testing-library/react'
import { afterEach, vi } from 'vitest'
import crypto from 'crypto'
import { fetch } from 'whatwg-fetch'


afterEach(() => {
  cleanup()
})

beforeAll(() => {
  global.fetch = fetch
})

Object.defineProperty(global, 'crypto', {
  value: {
    randomUUID: () => crypto.randomUUID()
  }
})

vi.mock('@mui/x-license-pro', () => ({
  useLicenseVerifier: () => 'Valid',
  Watermark: () => null
}))
