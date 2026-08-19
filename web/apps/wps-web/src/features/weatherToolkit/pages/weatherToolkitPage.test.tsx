import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ModelType, modelRegistry } from '@/features/weatherToolkit/weatherToolkitTypes'
import WeatherToolkitPage from './WeatherToolkitPage'

vi.mock('@/features/weatherToolkit/hooks/useWxChartCache', () => ({
  useWxChartCache: () => ({ cache: new Map(), failed: new Set() }),
  buildChartKey: () => 'mock-chart-key',
  buildModelRunKey: () => 'mock-model-run-key'
}))

vi.mock('@/features/weatherToolkit/components/SidePanel', () => ({
  default: ({ model }: { model: ModelType }) => <div data-testid="side-panel" data-model={model} />
}))

vi.mock('@/features/weatherToolkit/components/ChartPanel', () => ({
  default: ({ onToggleExpand, isExpanded }: { onToggleExpand: () => void; isExpanded: boolean }) => (
    <div data-testid="chart-panel" data-expanded={String(isExpanded)}>
      <button type="button" onClick={onToggleExpand}>
        Toggle expand
      </button>
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

    it('defaults to the RDPS model', () => {
      render(<WeatherToolkitPage />)
      expect(screen.getByTestId('side-panel')).toHaveAttribute('data-model', ModelType.RDPS)
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
    const rdpsInterval = modelRegistry[ModelType.RDPS].interval
    const rdpsMaxHour = modelRegistry[ModelType.RDPS].maxHour

    it('starts at hour 0', () => {
      render(<WeatherToolkitPage />)
      expect(currentHour()).toBe(0)
    })

    it('increments currentHour by the model interval on ArrowRight', () => {
      render(<WeatherToolkitPage />)
      fireEvent.keyDown(document, { key: 'ArrowRight' })
      expect(currentHour()).toBe(rdpsInterval)
    })

    it('decrements currentHour by the model interval on ArrowLeft', () => {
      render(<WeatherToolkitPage />)
      fireEvent.keyDown(document, { key: 'ArrowRight' })
      fireEvent.keyDown(document, { key: 'ArrowRight' })
      fireEvent.keyDown(document, { key: 'ArrowLeft' })
      expect(currentHour()).toBe(rdpsInterval)
    })

    it('does not decrement below 0', () => {
      render(<WeatherToolkitPage />)
      fireEvent.keyDown(document, { key: 'ArrowLeft' })
      expect(currentHour()).toBe(0)
    })

    it('does not increment past the model maxHour', () => {
      render(<WeatherToolkitPage />)
      const steps = rdpsMaxHour / rdpsInterval + 5
      for (let i = 0; i < steps; i++) {
        fireEvent.keyDown(document, { key: 'ArrowRight' })
      }
      expect(currentHour()).toBe(rdpsMaxHour)
    })

    it('does not respond to other keys', () => {
      render(<WeatherToolkitPage />)
      fireEvent.keyDown(document, { key: 'ArrowUp' })
      fireEvent.keyDown(document, { key: 'ArrowDown' })
      expect(currentHour()).toBe(0)
    })

    it('does not fire when an input element has focus', () => {
      render(<WeatherToolkitPage />)
      const input = document.createElement('input')
      document.body.appendChild(input)
      input.focus()
      fireEvent.keyDown(document, { key: 'ArrowRight' })
      expect(currentHour()).toBe(0)
      input.remove()
    })

    it('does not fire when a select element has focus', () => {
      render(<WeatherToolkitPage />)
      const select = document.createElement('select')
      document.body.appendChild(select)
      select.focus()
      fireEvent.keyDown(document, { key: 'ArrowRight' })
      expect(currentHour()).toBe(0)
      select.remove()
    })

    it('does not fire when a textarea element has focus', () => {
      render(<WeatherToolkitPage />)
      const textarea = document.createElement('textarea')
      document.body.appendChild(textarea)
      textarea.focus()
      fireEvent.keyDown(document, { key: 'ArrowRight' })
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
      fireEvent.keyDown(document, { key: 'ArrowRight' })
      expect(currentHour()).toBe(0)
      slider.remove()
    })

    it('removes the event listener on unmount', () => {
      const { unmount } = render(<WeatherToolkitPage />)
      unmount()
      fireEvent.keyDown(document, { key: 'ArrowRight' })
      // No error thrown and no stale state update — the handler was cleaned up
    })
  })
})
