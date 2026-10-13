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

  it('does not auto-hide a persistent notification', () => {
    vi.useFakeTimers()
    const onClose = vi.fn()
    render(<NotificationSnackbar autoHideDuration={null} open={true} onClose={onClose} message="Still here" />)

    act(() => vi.runAllTimers())
    expect(onClose).not.toHaveBeenCalled()
  })

  it('renders edge-to-edge without overflowing narrow screens', () => {
    render(<NotificationSnackbar open={true} onClose={vi.fn()} message="Something went wrong" />)

    const alert = screen.getByRole('alert')

    expect(alert.parentElement).toHaveStyle({
      position: 'absolute',
      top: '0px',
      left: '0px',
      right: '0px'
    })
    expect(alert).toHaveStyle({
      width: '100%',
      boxSizing: 'border-box',
      borderRadius: 0
    })
  })
})
