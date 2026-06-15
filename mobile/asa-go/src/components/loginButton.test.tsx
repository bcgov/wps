import { createTheme, ThemeProvider } from '@mui/material/styles'
import { fireEvent, render, screen } from '@testing-library/react'
import { useDispatch } from 'react-redux'
import { beforeEach, describe, expect, it, type Mock, vi } from 'vitest'
import LoginButton from '@/components/LoginButton'
import { authenticate } from '@/slices/authenticationSlice'

vi.mock('react-redux', async () => {
  const actual = await vi.importActual('react-redux')
  return {
    ...actual,
    useDispatch: vi.fn()
  }
})

vi.mock('@/slices/authenticationSlice', () => ({
  authenticate: vi.fn(() => ({ type: 'AUTHENTICATE' }))
}))

describe('LoginButton', () => {
  const mockDispatch = vi.fn()
  const theme = createTheme()

  beforeEach(() => {
    ;(useDispatch as unknown as Mock).mockReturnValue(mockDispatch)
    mockDispatch.mockClear()
  })

  const renderComponent = () =>
    render(
      <ThemeProvider theme={theme}>
        <LoginButton />
      </ThemeProvider>
    )

  it('renders the IDIR label', () => {
    renderComponent()

    expect(screen.getByRole('button', { name: /idir/i })).toBeInTheDocument()
  })

  it('dispatches authenticate on click', () => {
    renderComponent()

    fireEvent.click(screen.getByRole('button', { name: /idir/i }))

    expect(mockDispatch).toHaveBeenCalledWith(authenticate())
  })
})
