import { createTheme, ThemeProvider } from '@mui/material/styles'
import { render, screen } from '@testing-library/react'
import { Provider } from 'react-redux'
import { describe, expect, it } from 'vitest'
import GuestDisclaimerBanner from '@/components/GuestDisclaimerBanner'
import { type AuthSessionMode, initialState as authInitialState } from '@/slices/authenticationSlice'
import { createTestStore } from '@/testUtils'

const theme = createTheme()

const renderWithSessionMode = (sessionMode: AuthSessionMode) =>
  render(
    <Provider store={createTestStore({ authentication: { ...authInitialState, sessionMode } })}>
      <ThemeProvider theme={theme}>
        <GuestDisclaimerBanner />
      </ThemeProvider>
    </Provider>
  )

describe('GuestDisclaimerBanner', () => {
  it('renders the disclaimer when in guest mode', () => {
    renderWithSessionMode('guest')

    expect(screen.getByTestId('guest-disclaimer-banner')).toBeInTheDocument()
    expect(screen.getByText(/These are not public safety warnings/)).toBeInTheDocument()
  })

  it('does not render when authenticated', () => {
    renderWithSessionMode('authenticated')

    expect(screen.queryByTestId('guest-disclaimer-banner')).not.toBeInTheDocument()
  })

  it('does not render on the login screen', () => {
    renderWithSessionMode('login')

    expect(screen.queryByTestId('guest-disclaimer-banner')).not.toBeInTheDocument()
  })
})
