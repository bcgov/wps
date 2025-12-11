import { RunType } from '@/api/fbaAPI'
import { createLayerMock } from '@/test/testUtils'
import { createHillshadeVectorTileLayer, createVectorTileLayer, getStyleJson } from '@/utils/vectorLayerUtils'
import { render } from '@testing-library/react'
import store from 'app/store'
import FBAMap from 'features/fba/components/map/FBAMap'
import { DateTime } from 'luxon'
import { Provider } from 'react-redux'
import { Mock } from 'vitest'

vi.mock('@/utils/vectorLayerUtils', async () => {
  return {
    getStyleJson: vi.fn(),
    createVectorTileLayer: vi.fn(),
    createHillshadeVectorTileLayer: vi.fn()
  }
})

describe('FBAMap', () => {
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
  it('should render height with height and width properties set', () => {
    ;(getStyleJson as Mock).mockResolvedValue({})
    ;(createVectorTileLayer as Mock).mockResolvedValue(createLayerMock('basemap'))
    ;(createHillshadeVectorTileLayer as Mock).mockResolvedValue(createLayerMock('hillshade'))

    const { getByTestId } = render(
      <Provider store={store}>
        <FBAMap
          forDate={DateTime.fromISO('2016-05-25')}
          selectedFireCenter={undefined}
          selectedFireShape={undefined}
          runType={RunType.FORECAST}
          setSelectedFireShape={function (): void {
            throw new Error('Function not implemented.')
          }}
          zoomSource={'fireCenter'}
          setZoomSource={function (): void {
            throw new Error('Function not implemented.')
          }}
        />
      </Provider>
    )

    const fireTable = getByTestId('fba-map')
    expect(fireTable).toBeVisible()
  })
})
