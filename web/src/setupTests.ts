// react-testing-library renders your components to document.body,
// this adds jest-dom's custom assertions

import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach, vi } from 'vitest'
import crypto from 'crypto'

afterEach(() => {
  cleanup()
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
