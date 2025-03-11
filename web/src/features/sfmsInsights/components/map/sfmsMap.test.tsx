import SFMSMap from '@/features/sfmsInsights/components/map/SFMSMap'
import { render } from '@testing-library/react'

describe('SFMSMap', () => {
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
    const { getByTestId } = render(<SFMSMap snowDate={null} />)
    const map = getByTestId('sfms-map')
    expect(map).toBeVisible()
  })
})
