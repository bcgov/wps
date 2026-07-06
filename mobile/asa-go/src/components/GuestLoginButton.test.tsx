import { createTheme, ThemeProvider } from '@mui/material/styles'
import { fireEvent, render, screen } from '@testing-library/react'
import { useDispatch } from 'react-redux'
import { beforeEach, describe, expect, it, type Mock, vi } from 'vitest'
import PublicLoginButton from '@/components/GuestLoginButton'
import { continueAsGuestSession } from '@/slices/authenticationSlice'

vi.mock('react-redux', async () => {
  const actual = await vi.importActual('react-redux')
  return {
    ...actual,
    useDispatch: vi.fn()
  }
})

vi.mock('@/slices/authenticationSlice', () => ({
  continueAsGuestSession: vi.fn(() => ({ type: 'CONTINUE_AS_GUEST_SESSION' }))
}))

describe('PublicLoginButton', () => {
  const mockDispatch = vi.fn()
  const theme = createTheme()

  beforeEach(() => {
    ;(useDispatch as unknown as Mock).mockReturnValue(mockDispatch)
    mockDispatch.mockClear()
  })

  const renderComponent = () =>
    render(
      <ThemeProvider theme={theme}>
        <PublicLoginButton />
      </ThemeProvider>
    )

  it('renders the continue as guest button', () => {
    renderComponent()

    expect(screen.getByRole('button', { name: /log in as guest/i })).toBeInTheDocument()
  })

  it('dispatches continueAsGuestSession on click', () => {
    renderComponent()

    fireEvent.click(screen.getByRole('button', { name: /log in as guest/i }))

    expect(mockDispatch).toHaveBeenCalledWith(continueAsGuestSession())
  })
})
