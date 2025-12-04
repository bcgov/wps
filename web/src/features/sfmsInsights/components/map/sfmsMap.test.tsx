vi.mock('@/utils/vectorLayerUtils', async () => {
  return {
    getStyleJson: vi.fn(),
    createVectorTileLayer: vi.fn()
  }
})

import SFMSMap from '@/features/sfmsInsights/components/map/SFMSMap'
import { createLayerMock } from '@/test/testUtils'
import { createVectorTileLayer, getStyleJson } from '@/utils/vectorLayerUtils'
import { render } from '@testing-library/react'
import { Mock } from 'vitest'

describe('SFMSMap', () => {
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
  it('should render the map', () => {
    ;(getStyleJson as Mock).mockResolvedValue({})
    ;(createVectorTileLayer as Mock).mockResolvedValue(createLayerMock('base'))
    const { getByTestId } = render(<SFMSMap snowDate={null} />)
    const map = getByTestId('sfms-map')
    expect(map).toBeVisible()
  })
})
