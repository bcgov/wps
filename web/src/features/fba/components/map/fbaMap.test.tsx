vi.mock('@/features/sfmsInsights/components/map/layerDefinitions', async () => {
  const actual = await import('@/features/sfmsInsights/components/map/layerDefinitions')

  return {
    ...actual,
    createBasemapLayer: vi.fn().mockImplementation(() => Promise.resolve(baseLayerMock))
  }
})

import { RunType } from '@/api/fbaAPI'
import { baseLayerMock } from '@/test/testUtils'
import { render } from '@testing-library/react'
import store from 'app/store'
import FBAMap from 'features/fba/components/map/FBAMap'
import { DateTime } from 'luxon'

import { Provider } from 'react-redux'

describe('FBAMap', () => {
  it('should render height with height and width properties set', () => {
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
