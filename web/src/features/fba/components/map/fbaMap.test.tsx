vi.mock('@/features/fba/components/map/layerDefinitions', async () => {
  const actual = await import('@/features/fba/components/map/layerDefinitions')
  return {
    ...actual,
    createBasemapLayer: vi.fn(),
    createHillshadeLayer: vi.fn()
  }
})
import { createBasemapLayer, createHillshadeLayer } from '@/features/fba/components/map/layerDefinitions'
import { RunType } from '@/api/fbaAPI'
import { baseLayerMock, createLayerMock } from '@/test/testUtils'
import { render } from '@testing-library/react'
import store from 'app/store'
import FBAMap from 'features/fba/components/map/FBAMap'
import { DateTime } from 'luxon'
import { Provider } from 'react-redux'
import { Mock } from 'vitest'

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
    ;(createBasemapLayer as Mock).mockResolvedValue(createLayerMock('base'))
    ;(createHillshadeLayer as Mock).mockResolvedValue(createLayerMock('hillshade'))
    const { getByTestId } = render(
      <Provider store={store}>
        <FBAMap
          forDate={DateTime.fromISO('2016-05-25')}
          advisoryThreshold={0}
          selectedFireCenter={undefined}
          selectedFireShape={undefined}
          fireShapeAreas={[]}
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
