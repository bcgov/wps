import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ChartPanel from './ChartPanel'

const defaultProps = {
  imageSrc: null,
  chartKey: 'test-key',
  isFailed: false,
  isExpanded: false,
  onToggleExpand: vi.fn()
}

describe('ChartPanel', () => {
  it('renders the container box', () => {
    const { container } = render(<ChartPanel {...defaultProps} />)
    expect(container.firstChild).toBeInTheDocument()
  })

  it('renders the image when imageSrc is provided', () => {
    render(<ChartPanel {...defaultProps} imageSrc="https://example.com/chart.png" />)
    const img = screen.getByRole('img', { name: '4-panel chart' })
    expect(img).toBeInTheDocument()
    expect(img).toHaveAttribute('src', 'https://example.com/chart.png')
  })

  it('does not render an image when imageSrc is null', () => {
    render(<ChartPanel {...defaultProps} />)
    expect(screen.queryByRole('img')).not.toBeInTheDocument()
  })

  it('renders a loading spinner when imageSrc is null and not failed', () => {
    render(<ChartPanel {...defaultProps} />)
    expect(screen.getByRole('progressbar')).toBeInTheDocument()
  })

  it('does not render a loading spinner when imageSrc is provided', () => {
    render(<ChartPanel {...defaultProps} imageSrc="https://example.com/chart.png" />)
    expect(screen.queryByRole('progressbar')).not.toBeInTheDocument()
  })

  it('does not render a loading spinner when isFailed is true', () => {
    render(<ChartPanel {...defaultProps} isFailed={true} />)
    expect(screen.queryByRole('progressbar')).not.toBeInTheDocument()
  })

  it('renders the error state when isFailed is true', () => {
    render(<ChartPanel {...defaultProps} chartKey="some/chart/key" isFailed={true} />)
    expect(screen.getByText('Image not available')).toBeInTheDocument()
    expect(screen.getByText('some/chart/key')).toBeInTheDocument()
  })

  it('does not render the error state when isFailed is false', () => {
    render(<ChartPanel {...defaultProps} chartKey="some/chart/key" />)
    expect(screen.queryByText('Image not available')).not.toBeInTheDocument()
    expect(screen.queryByText('some/chart/key')).not.toBeInTheDocument()
  })

  it('shows the error state and not the image when isFailed is true even if imageSrc is provided', () => {
    render(
      <ChartPanel
        {...defaultProps}
        imageSrc="https://example.com/chart.png"
        chartKey="some/chart/key"
        isFailed={true}
      />
    )
    expect(screen.queryByRole('img')).not.toBeInTheDocument()
    expect(screen.getByText('Image not available')).toBeInTheDocument()
    expect(screen.getByText('some/chart/key')).toBeInTheDocument()
  })

  describe('zoom controls', () => {
    it('zooms in and out and restores the full chart', async () => {
      const user = userEvent.setup()
      render(<ChartPanel {...defaultProps} imageSrc="chart.png" />)
      expect(screen.getByRole('button', { name: 'Zoom out' })).toBeDisabled()
      await user.click(screen.getByRole('button', { name: 'Zoom in' }))
      expect(screen.getByText('150%')).toBeInTheDocument()
      expect(screen.getByRole('region', { name: 'Chart viewport' }).firstChild).toHaveStyle({
        width: '150%',
        height: '150%'
      })
      await user.click(screen.getByRole('button', { name: 'Zoom in' }))
      await user.click(screen.getByRole('button', { name: 'Zoom out' }))
      expect(screen.getByText('150%')).toBeInTheDocument()
      await user.click(screen.getByRole('button', { name: 'Fit chart to view' }))
      expect(screen.getByText('100%')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Fit chart to view' })).toBeDisabled()
    })

    it('limits magnification and keeps it when changing timesteps', async () => {
      const user = userEvent.setup()
      const { rerender } = render(<ChartPanel {...defaultProps} imageSrc="chart.png" />)
      for (let i = 0; i < 4; i++) await user.click(screen.getByRole('button', { name: 'Zoom in' }))
      expect(screen.getByText('300%')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Zoom in' })).toBeDisabled()
      rerender(<ChartPanel {...defaultProps} imageSrc="next-chart.png" chartKey="next" />)
      expect(screen.getByText('300%')).toBeInTheDocument()
    })

    it.each([false, true])('disables zoom when no chart can be shown (failed: %s)', isFailed => {
      render(<ChartPanel {...defaultProps} isFailed={isFailed} />)
      expect(screen.getByRole('button', { name: 'Zoom in' })).toBeDisabled()
      expect(screen.getByRole('button', { name: 'Zoom out' })).toBeDisabled()
    })

    it('allows keyboard scrolling without changing the forecast timestep', async () => {
      const onKeyDown = vi.fn()
      window.addEventListener('keydown', onKeyDown)
      try {
        render(<ChartPanel {...defaultProps} imageSrc="chart.png" />)
        screen.getByRole('region', { name: 'Chart viewport' }).focus()
        await userEvent.keyboard('{ArrowRight}')
        expect(onKeyDown).not.toHaveBeenCalled()
      } finally {
        window.removeEventListener('keydown', onKeyDown)
      }
    })
  })

  describe('expand/collapse button', () => {
    it('renders the expand button when not expanded', () => {
      render(<ChartPanel {...defaultProps} isExpanded={false} />)
      expect(screen.getByRole('button', { name: 'Expand chart' })).toBeInTheDocument()
    })

    it('renders the collapse button when expanded', () => {
      render(<ChartPanel {...defaultProps} isExpanded={true} />)
      expect(screen.getByRole('button', { name: 'Restore header and footer' })).toBeInTheDocument()
    })

    it('calls onToggleExpand when the button is clicked', async () => {
      const onToggleExpand = vi.fn()
      render(<ChartPanel {...defaultProps} onToggleExpand={onToggleExpand} />)
      await userEvent.click(screen.getByRole('button', { name: 'Expand chart' }))
      expect(onToggleExpand).toHaveBeenCalledTimes(1)
    })
  })
})
