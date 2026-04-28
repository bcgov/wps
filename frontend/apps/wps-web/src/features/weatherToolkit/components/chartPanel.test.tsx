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
