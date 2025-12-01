vi.mock('@/features/sfmsInsights/components/map/layerDefinitions', async () => {
  const actual = await import('@/features/sfmsInsights/components/map/layerDefinitions')

  return {
    ...actual,
    createBasemapLayer: vi.fn().mockImplementation(() => Promise.resolve(baseLayerMock))
  }
})

import SFMSMap from '@/features/sfmsInsights/components/map/SFMSMap'
import { baseLayerMock } from '@/test/testUtils'
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
