import { act, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import LoadingOverlay from './LoadingOverlay'

describe('LoadingOverlay', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('does not show for loads shorter than the delay', () => {
    const { rerender } = render(<LoadingOverlay loading />)

    act(() => vi.advanceTimersByTime(199))
    rerender(<LoadingOverlay loading={false} />)
    act(() => vi.runAllTimers())

    expect(screen.queryByTestId('loading-overlay')).not.toBeInTheDocument()
  })

  it('shows after the delay and remains visible for the minimum duration', () => {
    const { rerender } = render(<LoadingOverlay loading />)

    act(() => vi.advanceTimersByTime(200))

    expect(screen.getByRole('status')).toHaveTextContent('Data Updating')
    expect(screen.getByRole('progressbar', { name: 'Data Updating' })).toBeInTheDocument()

    rerender(<LoadingOverlay loading={false} />)
    act(() => vi.advanceTimersByTime(399))
    expect(screen.getByTestId('loading-overlay')).toBeInTheDocument()

    act(() => vi.advanceTimersByTime(1))
    expect(screen.queryByTestId('loading-overlay')).not.toBeInTheDocument()
  })

  it('cancels a pending dismissal when loading restarts', () => {
    const { rerender } = render(<LoadingOverlay loading />)
    act(() => vi.advanceTimersByTime(200))

    rerender(<LoadingOverlay loading={false} />)
    act(() => vi.advanceTimersByTime(200))
    rerender(<LoadingOverlay loading />)
    act(() => vi.advanceTimersByTime(400))

    expect(screen.getByTestId('loading-overlay')).toBeInTheDocument()
  })
})
