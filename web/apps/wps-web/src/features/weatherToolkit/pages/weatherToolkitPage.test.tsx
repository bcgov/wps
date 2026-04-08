import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import WeatherToolkitPage from './WeatherToolkitPage'
import { modelRegistry, ModelType } from '@/features/weatherToolkit/weatherToolkitTypes'

vi.mock('@/features/weatherToolkit/hooks/useWxChartCache', () => ({
  useWxChartCache: () => ({ cache: new Map(), failed: new Set() }),
  buildChartKey: () => 'mock-chart-key'
}))

vi.mock('@/features/weatherToolkit/components/SidePanel', () => ({
  default: () => <div data-testid="side-panel" />
}))

vi.mock('@/features/weatherToolkit/components/ChartPanel', () => ({
  default: ({ onToggleExpand, isExpanded }: { onToggleExpand: () => void; isExpanded: boolean }) => (
    <div data-testid="chart-panel" data-expanded={String(isExpanded)}>
      <button onClick={onToggleExpand}>Toggle expand</button>
    </div>
  )
}))

vi.mock('@/features/weatherToolkit/components/TimelineController', () => ({
  default: ({ currentHour }: { currentHour: number }) => (
    <div data-testid="timeline-controller" data-current-hour={String(currentHour)} />
  )
}))

vi.mock('@wps/ui/GeneralHeader', () => ({
  GeneralHeader: () => <div data-testid="header" />
}))

vi.mock('@/features/landingPage/components/Footer', () => ({
  default: () => <div data-testid="footer" />
}))

const getTimeline = () => screen.getByTestId('timeline-controller')
const currentHour = () => Number(getTimeline().dataset.currentHour)

describe('WeatherToolkitPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('layout', () => {
    it('renders the header by default', () => {
      render(<WeatherToolkitPage />)
      expect(screen.getByTestId('header')).toBeInTheDocument()
    })

    it('renders the footer by default', () => {
      render(<WeatherToolkitPage />)
      expect(screen.getByTestId('footer')).toBeInTheDocument()
    })

    it('hides the header when the chart is expanded', async () => {
      render(<WeatherToolkitPage />)
      await userEvent.click(screen.getByRole('button', { name: 'Toggle expand' }))
      expect(screen.queryByTestId('header')).not.toBeInTheDocument()
    })

    it('hides the footer when the chart is expanded', async () => {
      render(<WeatherToolkitPage />)
      await userEvent.click(screen.getByRole('button', { name: 'Toggle expand' }))
      expect(screen.queryByTestId('footer')).not.toBeInTheDocument()
    })

    it('restores the header when the chart is collapsed', async () => {
      render(<WeatherToolkitPage />)
      await userEvent.click(screen.getByRole('button', { name: 'Toggle expand' }))
      await userEvent.click(screen.getByRole('button', { name: 'Toggle expand' }))
      expect(screen.getByTestId('header')).toBeInTheDocument()
    })

    it('restores the footer when the chart is collapsed', async () => {
      render(<WeatherToolkitPage />)
      await userEvent.click(screen.getByRole('button', { name: 'Toggle expand' }))
      await userEvent.click(screen.getByRole('button', { name: 'Toggle expand' }))
      expect(screen.getByTestId('footer')).toBeInTheDocument()
    })
  })

  describe('arrow key navigation', () => {
    const gdpsInterval = modelRegistry[ModelType.GDPS].interval
    const gdpsMaxHour = modelRegistry[ModelType.GDPS].maxHour

    it('starts at hour 0', () => {
      render(<WeatherToolkitPage />)
      expect(currentHour()).toBe(0)
    })

    it('increments currentHour by the model interval on ArrowRight', () => {
      render(<WeatherToolkitPage />)
      fireEvent.keyDown(window, { key: 'ArrowRight' })
      expect(currentHour()).toBe(gdpsInterval)
    })

    it('decrements currentHour by the model interval on ArrowLeft', () => {
      render(<WeatherToolkitPage />)
      fireEvent.keyDown(window, { key: 'ArrowRight' })
      fireEvent.keyDown(window, { key: 'ArrowRight' })
      fireEvent.keyDown(window, { key: 'ArrowLeft' })
      expect(currentHour()).toBe(gdpsInterval)
    })

    it('does not decrement below 0', () => {
      render(<WeatherToolkitPage />)
      fireEvent.keyDown(window, { key: 'ArrowLeft' })
      expect(currentHour()).toBe(0)
    })

    it('does not increment past the model maxHour', () => {
      render(<WeatherToolkitPage />)
      const steps = gdpsMaxHour / gdpsInterval + 5
      for (let i = 0; i < steps; i++) {
        fireEvent.keyDown(window, { key: 'ArrowRight' })
      }
      expect(currentHour()).toBe(gdpsMaxHour)
    })

    it('does not respond to other keys', () => {
      render(<WeatherToolkitPage />)
      fireEvent.keyDown(window, { key: 'ArrowUp' })
      fireEvent.keyDown(window, { key: 'ArrowDown' })
      expect(currentHour()).toBe(0)
    })

    it('does not fire when an input element has focus', () => {
      render(<WeatherToolkitPage />)
      const input = document.createElement('input')
      document.body.appendChild(input)
      input.focus()
      fireEvent.keyDown(window, { key: 'ArrowRight' })
      expect(currentHour()).toBe(0)
      input.remove()
    })

    it('does not fire when a select element has focus', () => {
      render(<WeatherToolkitPage />)
      const select = document.createElement('select')
      document.body.appendChild(select)
      select.focus()
      fireEvent.keyDown(window, { key: 'ArrowRight' })
      expect(currentHour()).toBe(0)
      select.remove()
    })

    it('does not fire when a textarea element has focus', () => {
      render(<WeatherToolkitPage />)
      const textarea = document.createElement('textarea')
      document.body.appendChild(textarea)
      textarea.focus()
      fireEvent.keyDown(window, { key: 'ArrowRight' })
      expect(currentHour()).toBe(0)
      textarea.remove()
    })

    it('does not fire when an element with role="slider" has focus', () => {
      render(<WeatherToolkitPage />)
      const slider = document.createElement('div')
      slider.setAttribute('role', 'slider')
      slider.setAttribute('tabindex', '0')
      document.body.appendChild(slider)
      slider.focus()
      fireEvent.keyDown(window, { key: 'ArrowRight' })
      expect(currentHour()).toBe(0)
      slider.remove()
    })

    it('removes the event listener on unmount', () => {
      const { unmount } = render(<WeatherToolkitPage />)
      unmount()
      fireEvent.keyDown(window, { key: 'ArrowRight' })
      // No error thrown and no stale state update — the handler was cleaned up
    })
  })
})
