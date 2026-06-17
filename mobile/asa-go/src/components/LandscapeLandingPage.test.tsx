import { ThemeProvider } from '@mui/material/styles'
import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import LandscapeLandingPage from '@/components/LandscapeLandingPage'
import { useIsXSSmallScreen } from '@/hooks/useIsXSScreen'
import { theme } from '@/theme'

vi.mock('@/hooks/useIsXSScreen', () => ({ useIsXSSmallScreen: vi.fn() }))
vi.mock('@/components/LoginActions', () => ({
  default: ({ direction }: { direction?: string }) => (
    <div data-testid="login-actions" data-direction={direction ?? 'column'} />
  )
}))
vi.mock('@/assets/asa-go-transparent.png', () => ({
  default: 'mocked-image.png'
}))

const renderComponent = () =>
  render(
    <ThemeProvider theme={theme}>
      <LandscapeLandingPage />
    </ThemeProvider>
  )

describe('LandscapeLandingPage', () => {
  beforeEach(() => {
    vi.mocked(useIsXSSmallScreen).mockReturnValue(false)
  })

  describe('static content', () => {
    it('renders the ASA Go title', () => {
      renderComponent()

      expect(screen.getByRole('heading', { level: 3, name: 'ASA Go' })).toBeInTheDocument()
    })

    it('renders the app description', () => {
      renderComponent()

      expect(screen.getByTestId('app-description-p1')).toBeInTheDocument()
      expect(screen.getByTestId('app-description-p2')).toBeInTheDocument()
    })

    it('renders the icon', () => {
      renderComponent()

      expect(screen.getByRole('img')).toHaveAttribute('src', 'mocked-image.png')
    })

    it('renders LoginActions with row direction', () => {
      renderComponent()

      expect(screen.getByTestId('login-actions')).toHaveAttribute('data-direction', 'row')
    })
  })
})
