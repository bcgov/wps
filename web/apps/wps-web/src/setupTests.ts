// react-testing-library renders your components to document.body,
// this adds jest-dom's custom assertions

import '@testing-library/jest-dom'
import { cleanup } from '@testing-library/react'
import { afterEach, vi } from 'vitest'

afterEach(() => {
  cleanup()
})

vi.mock('@mui/x-license', () => ({
  LicenseInfo: {
    setLicenseKey: vi.fn()
  },
  useLicenseVerifier: () => 'Valid',
  Watermark: () => null
}))
