import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import TimelineController from './TimelineController'

const defaultProps = {
  currentHour: 0,
  setCurrentHour: vi.fn(),
  start: 0,
  end: 48,
  step: 3
}

const renderController = (props: Partial<typeof defaultProps> = {}) =>
  render(<TimelineController {...defaultProps} {...props} />)

describe('TimelineController', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('rendering', () => {
    it('renders the Previous timestep button', () => {
      renderController()
      expect(screen.getByRole('button', { name: 'Previous timestep' })).toBeInTheDocument()
    })

    it('renders the Next timestep button', () => {
      renderController()
      expect(screen.getByRole('button', { name: 'Next timestep' })).toBeInTheDocument()
    })

    it('renders the slider', () => {
      renderController()
      expect(screen.getByRole('slider')).toBeInTheDocument()
    })

    it('renders the slider with the correct aria-label', () => {
      renderController({ end: 48 })
      expect(screen.getByRole('slider')).toHaveAttribute('aria-label', 'Timeline slider 0 to 48 hours')
    })

    it('sets the slider value to currentHour', () => {
      renderController({ currentHour: 12 })
      expect(screen.getByRole('slider')).toHaveAttribute('aria-valuenow', '12')
    })

    it('sets the slider max to end', () => {
      renderController({ end: 72 })
      expect(screen.getByRole('slider')).toHaveAttribute('aria-valuemax', '72')
    })

    it('sets the slider min to 0', () => {
      renderController()
      expect(screen.getByRole('slider')).toHaveAttribute('aria-valuemin', '0')
    })
  })

  describe('Previous button', () => {
    it('is disabled when currentHour is 0', () => {
      renderController({ currentHour: 0 })
      expect(screen.getByRole('button', { name: 'Previous timestep' })).toBeDisabled()
    })

    it('is enabled when currentHour is greater than 0', () => {
      renderController({ currentHour: 6 })
      expect(screen.getByRole('button', { name: 'Previous timestep' })).toBeEnabled()
    })

    it('calls setCurrentHour when clicked', async () => {
      const setCurrentHour = vi.fn()
      renderController({ currentHour: 6, setCurrentHour })
      await userEvent.click(screen.getByRole('button', { name: 'Previous timestep' }))
      expect(setCurrentHour).toHaveBeenCalledTimes(1)
    })

    it('decrements currentHour by step', async () => {
      const setCurrentHour = vi.fn()
      renderController({ currentHour: 6, setCurrentHour, step: 3 })
      await userEvent.click(screen.getByRole('button', { name: 'Previous timestep' }))
      const updater = setCurrentHour.mock.calls[0][0]
      expect(updater(6)).toBe(3)
    })

    it('clamps to 0 when decrement would go below 0', async () => {
      const setCurrentHour = vi.fn()
      renderController({ currentHour: 2, setCurrentHour, step: 3 })
      await userEvent.click(screen.getByRole('button', { name: 'Previous timestep' }))
      const updater = setCurrentHour.mock.calls[0][0]
      expect(updater(2)).toBe(0)
    })
  })

  describe('Next button', () => {
    it('is disabled when currentHour equals end', () => {
      renderController({ currentHour: 48, end: 48 })
      expect(screen.getByRole('button', { name: 'Next timestep' })).toBeDisabled()
    })

    it('is disabled when currentHour exceeds end', () => {
      renderController({ currentHour: 50, end: 48 })
      expect(screen.getByRole('button', { name: 'Next timestep' })).toBeDisabled()
    })

    it('is enabled when currentHour is less than end', () => {
      renderController({ currentHour: 6, end: 48 })
      expect(screen.getByRole('button', { name: 'Next timestep' })).toBeEnabled()
    })

    it('calls setCurrentHour when clicked', async () => {
      const setCurrentHour = vi.fn()
      renderController({ currentHour: 6, setCurrentHour })
      await userEvent.click(screen.getByRole('button', { name: 'Next timestep' }))
      expect(setCurrentHour).toHaveBeenCalledTimes(1)
    })

    it('increments currentHour by step', async () => {
      const setCurrentHour = vi.fn()
      renderController({ currentHour: 6, setCurrentHour, step: 3, end: 48 })
      await userEvent.click(screen.getByRole('button', { name: 'Next timestep' }))
      const updater = setCurrentHour.mock.calls[0][0]
      expect(updater(6)).toBe(9)
    })

    it('clamps to end when increment would exceed end', async () => {
      const setCurrentHour = vi.fn()
      renderController({ currentHour: 46, setCurrentHour, step: 3, end: 48 })
      await userEvent.click(screen.getByRole('button', { name: 'Next timestep' }))
      const updater = setCurrentHour.mock.calls[0][0]
      expect(updater(46)).toBe(48)
    })
  })

  describe('slider props', () => {
    it('passes step to the slider', () => {
      renderController({ step: 6 })
      // MUI Slider renders an underlying range input with the step attribute
      const input = document.querySelector('input[type="range"]') as HTMLInputElement
      expect(input).toHaveAttribute('step', '6')
    })

    it('passes end as max to the slider', () => {
      renderController({ end: 72 })
      const input = document.querySelector('input[type="range"]') as HTMLInputElement
      expect(input).toHaveAttribute('max', '72')
    })

    it('passes currentHour as value to the slider', () => {
      renderController({ currentHour: 12 })
      const input = document.querySelector('input[type="range"]') as HTMLInputElement
      expect(input).toHaveAttribute('aria-valuenow', '12')
    })
  })

  describe('marks', () => {
    it('shows "0h" label at hour 0', () => {
      renderController({ start: 0, end: 12, step: 3 })
      expect(screen.getByText('0h')).toBeInTheDocument()
    })

    it('shows labels every second step', () => {
      renderController({ start: 0, end: 12, step: 3 })
      expect(screen.getByText('+6h')).toBeInTheDocument()
      expect(screen.getByText('+12h')).toBeInTheDocument()
    })

    it('does not show labels for odd-numbered steps', () => {
      renderController({ start: 0, end: 12, step: 3 })
      expect(screen.queryByText('+3h')).not.toBeInTheDocument()
      expect(screen.queryByText('+9h')).not.toBeInTheDocument()
    })
  })
})
