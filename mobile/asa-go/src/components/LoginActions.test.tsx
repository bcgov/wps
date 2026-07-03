import { ThemeProvider } from '@mui/material/styles'
import { render, screen } from '@testing-library/react'
import { Provider } from 'react-redux'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import LoginActions from '@/components/LoginActions'
import * as selectors from '@/store'
import { createTestStore } from '@/testUtils'
import { theme } from '@/theme'

vi.mock('@/components/LoginButton', () => ({
  default: () => <button type="button">IDIR</button>
}))

const mockStore = createTestStore()

const renderComponent = (direction?: 'row' | 'column') =>
  render(
    <Provider store={mockStore}>
      <ThemeProvider theme={theme}>
        <LoginActions direction={direction} />
      </ThemeProvider>
    </Provider>
  )

const mockAuthState = (authenticating: boolean, error: string | null = null) =>
  vi.spyOn(selectors, 'selectAuthentication').mockReturnValue({
    authenticating,
    error,
    idToken: undefined,
    idir: undefined,
    token: undefined,
    email: undefined,
    sessionMode: 'login'
  })

describe('LoginActions', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  describe('authentication state', () => {
    it('renders login button when not authenticating', () => {
      mockAuthState(false)
      renderComponent()

      expect(screen.getByRole('button', { name: /idir/i })).toBeInTheDocument()
    })

    it('renders a spinner when authenticating', () => {
      mockAuthState(true)
      renderComponent()

      expect(screen.getByRole('progressbar')).toBeInTheDocument()
    })

    it('hides login button when authenticating', () => {
      mockAuthState(true)
      renderComponent()

      expect(screen.queryByRole('button', { name: /idir/i })).not.toBeInTheDocument()
    })
  })

  describe('error state', () => {
    it('renders an error message when login fails', () => {
      mockAuthState(false, 'Invalid credentials')
      renderComponent()

      expect(screen.getByText('Unable to login, please try again.')).toBeInTheDocument()
    })

    it('does not render an error message when there is no error', () => {
      mockAuthState(false, null)
      renderComponent()

      expect(screen.queryByText('Unable to login, please try again.')).not.toBeInTheDocument()
    })
  })

  describe('direction prop', () => {
    it('renders button with column direction by default', () => {
      mockAuthState(false)
      renderComponent()

      expect(screen.getByRole('button', { name: /idir/i })).toBeInTheDocument()
    })

    it('renders button with row direction', () => {
      mockAuthState(false)
      renderComponent('row')

      expect(screen.getByRole('button', { name: /idir/i })).toBeInTheDocument()
    })
  })
})
