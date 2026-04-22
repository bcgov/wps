// react-testing-library renders your components to document.body,
// this adds jest-dom's custom assertions

import '@testing-library/jest-dom'
import { cleanup } from '@testing-library/react'
import { afterEach, vi } from 'vitest'

let uuidCounter = 0

const randomUUID = () => {
  uuidCounter += 1
  return `00000000-0000-4000-8000-${uuidCounter.toString().padStart(12, '0')}`
}

afterEach(() => {
  cleanup()
})

Object.defineProperty(globalThis, 'crypto', {
  value: {
    randomUUID
  }
})

vi.mock('@mui/x-license', () => ({
  LicenseInfo: {
    setLicenseKey: vi.fn()
  },
  useLicenseVerifier: () => 'Valid',
  Watermark: () => null
}))
