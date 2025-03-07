import PSUMap from '@/features/sfmsInsights/components/map/SFMSMap'
import { render } from '@testing-library/react'

describe('PSUMap', () => {
  it('should render the map', () => {
    class ResizeObserver {
      observe() {
        // mock no-op
      }
      unobserve() {
        // mock no-op
      }
      disconnect() {
        // mock no-op
      }
    }
    window.ResizeObserver = ResizeObserver
    const { getByTestId } = render(<PSUMap />)
    const map = getByTestId('psu-map')
    expect(map).toBeVisible()
  })
})
