import { createTheme, ThemeProvider } from '@mui/material/styles'
import { render, screen } from '@testing-library/react'
import { Provider } from 'react-redux'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { useIsPortrait } from '@/hooks/useIsPortrait'
import { useIsTablet } from '@/hooks/useIsTablet'
import * as selectors from '@/store'
import { createTestStore } from '@/testUtils'
import AuthWrapper from './AuthWrapper'

vi.mock('@/hooks/useIsPortrait', () => ({ useIsPortrait: vi.fn() }))
vi.mock('@/hooks/useIsTablet', () => ({ useIsTablet: vi.fn() }))
vi.mock('@/components/PortraitLandingPage', () => ({
  default: () => <div data-testid="portrait-landing-page" />
}))
vi.mock('@/components/LandscapeLandingPage', () => ({
  default: () => <div data-testid="landscape-landing-page" />
}))

const mockStore = createTestStore()
const theme = createTheme()

const renderWithProviders = (children = <div>Protected</div>) =>
  render(
    <Provider store={mockStore}>
      <ThemeProvider theme={theme}>
        <AuthWrapper>{children}</AuthWrapper>
      </ThemeProvider>
    </Provider>
  )

describe('AuthWrapper', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    vi.mocked(useIsPortrait).mockReturnValue(true)
    vi.mocked(useIsTablet).mockReturnValue(false)
  })

  it('renders children when authenticated', () => {
    vi.spyOn(selectors, 'selectAuthentication').mockReturnValue({
      sessionMode: 'authenticated',
      authenticating: false,
      error: null,
      tokenRefreshed: false,
      idToken: undefined,
      idir: undefined,
      token: 'test-token',
      email: 'test@email.com'
    })

    renderWithProviders()

    expect(screen.getByText('Protected')).toBeInTheDocument()
  })

  it('renders children when unauthenticated and offline', () => {
    vi.spyOn(selectors, 'selectAuthentication').mockReturnValue({
      sessionMode: 'login',
      authenticating: false,
      error: null,
      tokenRefreshed: false,
      idToken: undefined,
      idir: undefined,
      token: 'test-token',
      email: 'test@email.com'
    })
    vi.spyOn(selectors, 'selectNetworkStatus').mockReturnValue({
      networkStatus: { connected: false, connectionType: 'wifi' }
    })

    renderWithProviders()

    expect(screen.getByText('Protected')).toBeInTheDocument()
  })

  describe('landing page routing when online and unauthenticated', () => {
    beforeEach(() => {
      vi.spyOn(selectors, 'selectAuthentication').mockReturnValue({
        sessionMode: 'login',
        authenticating: false,
        error: null,
        tokenRefreshed: false,
        idToken: undefined,
        idir: undefined,
        token: undefined,
        email: undefined
      })
      vi.spyOn(selectors, 'selectNetworkStatus').mockReturnValue({
        networkStatus: { connected: true, connectionType: 'wifi' }
      })
    })

    it('renders PortraitLandingPage in portrait orientation', () => {
      vi.mocked(useIsPortrait).mockReturnValue(true)
      vi.mocked(useIsTablet).mockReturnValue(false)

      renderWithProviders()

      expect(screen.getByTestId('portrait-landing-page')).toBeInTheDocument()
    })

    it('renders PortraitLandingPage on a tablet regardless of orientation', () => {
      vi.mocked(useIsPortrait).mockReturnValue(false)
      vi.mocked(useIsTablet).mockReturnValue(true)

      renderWithProviders()

      expect(screen.getByTestId('portrait-landing-page')).toBeInTheDocument()
    })

    it('renders LandscapeLandingPage on a phone in landscape orientation', () => {
      vi.mocked(useIsPortrait).mockReturnValue(false)
      vi.mocked(useIsTablet).mockReturnValue(false)

      renderWithProviders()

      expect(screen.getByTestId('landscape-landing-page')).toBeInTheDocument()
    })
  })
})
