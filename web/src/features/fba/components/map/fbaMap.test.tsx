import { RunType } from '@/api/fbaAPI'
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
          selectedFireCenter={undefined}
          selectedFireShape={undefined}
          fireZoneStatuses={[]}
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
