import { act, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import NotificationSnackbar from './NotificationSnackbar'

describe('NotificationSnackbar', () => {
  afterEach(() => vi.useRealTimers())

  it('renders the message when open', () => {
    render(<NotificationSnackbar open={true} onClose={vi.fn()} message="Something went wrong" />)
    expect(screen.getByText('Something went wrong')).toBeInTheDocument()
  })

  it('does not render when closed', () => {
    render(<NotificationSnackbar open={false} onClose={vi.fn()} message="Something went wrong" />)
    expect(screen.queryByText('Something went wrong')).not.toBeInTheDocument()
  })

  it('renders with error severity', () => {
    render(<NotificationSnackbar open={true} onClose={vi.fn()} message="Something went wrong" />)
    expect(screen.getByRole('alert')).toHaveClass('MuiAlert-colorError')
  })

  it('calls onClose when the close button is clicked', () => {
    const onClose = vi.fn()
    render(<NotificationSnackbar open={true} onClose={onClose} message="Something went wrong" />)
    fireEvent.click(screen.getByRole('button', { name: /close/i }))
    expect(onClose).toHaveBeenCalled()
  })

  it('calls onClose after the auto-hide duration', () => {
    vi.useFakeTimers()
    const onClose = vi.fn()
    render(
      <NotificationSnackbar autoHideDuration={1000} open={true} onClose={onClose} message="Something went wrong" />
    )

    act(() => vi.advanceTimersByTime(1000))
    expect(onClose).toHaveBeenCalled()
  })

  it('renders edge-to-edge by default', () => {
    render(<NotificationSnackbar open={true} onClose={vi.fn()} message="Something went wrong" />)

    expect(screen.getByRole('alert').parentElement).toHaveStyle({
      left: '0px',
      right: '0px',
      transform: 'none',
      width: '100%'
    })
  })
})
