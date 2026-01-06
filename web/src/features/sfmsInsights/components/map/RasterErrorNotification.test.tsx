import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import RasterErrorNotification from './RasterErrorNotification'
import { RasterError } from './layerManager'

describe('RasterErrorNotification', () => {
  it('should not render when error is null', () => {
    const { container } = render(<RasterErrorNotification error={null} onClose={vi.fn()} />)
    expect(container.firstChild).toBeNull()
  })

  it('should render warning severity for not_found error', () => {
    const error: RasterError = {
      type: 'not_found',
      message: 'Test message'
    }
    render(<RasterErrorNotification error={error} onClose={vi.fn()} />)

    const alert = screen.getByRole('alert')
    expect(alert).toBeInTheDocument()
    expect(alert).toHaveClass('MuiAlert-filledWarning')
  })

  it('should render error severity for forbidden error', () => {
    const error: RasterError = {
      type: 'forbidden',
      message: 'Test message'
    }
    render(<RasterErrorNotification error={error} onClose={vi.fn()} />)

    const alert = screen.getByRole('alert')
    expect(alert).toBeInTheDocument()
    expect(alert).toHaveClass('MuiAlert-filledError')
  })

  it('should render warning severity for network error', () => {
    const error: RasterError = {
      type: 'network',
      message: 'Test message'
    }
    render(<RasterErrorNotification error={error} onClose={vi.fn()} />)

    const alert = screen.getByRole('alert')
    expect(alert).toBeInTheDocument()
    expect(alert).toHaveClass('MuiAlert-filledWarning')
  })

  it('should render warning severity for unknown error', () => {
    const error: RasterError = {
      type: 'unknown',
      message: 'Test message'
    }
    render(<RasterErrorNotification error={error} onClose={vi.fn()} />)

    const alert = screen.getByRole('alert')
    expect(alert).toBeInTheDocument()
    expect(alert).toHaveClass('MuiAlert-filledWarning')
  })

  it('should display correct message for not_found error', () => {
    const error: RasterError = {
      type: 'not_found',
      message: 'Test message'
    }
    render(<RasterErrorNotification error={error} onClose={vi.fn()} rasterLabel="FWI" />)

    expect(screen.getByText(/FWI data not available for this date/i)).toBeInTheDocument()
  })

  it('should display correct message for forbidden error', () => {
    const error: RasterError = {
      type: 'forbidden',
      message: 'Test message'
    }
    render(<RasterErrorNotification error={error} onClose={vi.fn()} rasterLabel="Temperature" />)

    expect(screen.getByText(/Access denied to Temperature data/i)).toBeInTheDocument()
  })

  it('should display correct message for network error', () => {
    const error: RasterError = {
      type: 'network',
      message: 'Test message'
    }
    render(<RasterErrorNotification error={error} onClose={vi.fn()} rasterLabel="Precipitation" />)

    expect(screen.getByText(/Precipitation data not available/i)).toBeInTheDocument()
  })

  it('should use custom error message for unknown error type', () => {
    const error: RasterError = {
      type: 'unknown',
      message: 'Custom error message'
    }
    render(<RasterErrorNotification error={error} onClose={vi.fn()} />)

    expect(screen.getByText('Custom error message')).toBeInTheDocument()
  })

  it('should use default raster label when not provided', () => {
    const error: RasterError = {
      type: 'not_found',
      message: 'Test message'
    }
    render(<RasterErrorNotification error={error} onClose={vi.fn()} />)

    expect(screen.getByText(/Raster data not available/i)).toBeInTheDocument()
  })

  it('should call onClose when close button is clicked', async () => {
    const onClose = vi.fn()
    const error: RasterError = {
      type: 'not_found',
      message: 'Test message'
    }
    render(<RasterErrorNotification error={error} onClose={onClose} />)

    const closeButton = screen.getByRole('button', { name: /close/i })
    await userEvent.click(closeButton)

    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('should call onClose after autoHideDuration', () => {
    vi.useFakeTimers()

    const onClose = vi.fn()
    const error: RasterError = {
      type: 'not_found',
      message: 'Test message'
    }
    render(<RasterErrorNotification error={error} onClose={onClose} />)

    // Fast-forward time by 6 seconds
    vi.advanceTimersByTime(6100)
    vi.runAllTimers()

    expect(onClose).toHaveBeenCalled()

    vi.useRealTimers()
  })

  it('should render snackbar at bottom center position', () => {
    const error: RasterError = {
      type: 'not_found',
      message: 'Test message'
    }
    const { container } = render(<RasterErrorNotification error={error} onClose={vi.fn()} />)

    const snackbar = container.querySelector('.MuiSnackbar-root')
    expect(snackbar).toHaveClass('MuiSnackbar-anchorOriginBottomCenter')
  })

  it('should include status code in error object if provided', () => {
    const error: RasterError = {
      type: 'not_found',
      message: 'Test message',
      statusCode: 404
    }
    render(<RasterErrorNotification error={error} onClose={vi.fn()} />)

    // Component should still render correctly even with statusCode
    expect(screen.getByRole('alert')).toBeInTheDocument()
  })
})
