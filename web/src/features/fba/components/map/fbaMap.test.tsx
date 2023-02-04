import { render } from '@testing-library/react'
import store from 'app/store'
import FBAMap from 'features/fba/components/map/FBAMap'
import { RunType } from 'features/fba/pages/FireBehaviourAdvisoryPage'
import { DateTime } from 'luxon'
import React from 'react'
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
          runDate={DateTime.fromISO('2016-05-25')}
          advisoryThreshold={0}
          selectedFireCenter={undefined}
          selectedFireZoneID={null}
          className={''}
          fireZoneAreas={[]}
          runType={RunType.FORECAST}
          setIssueDate={function (): void {
            throw new Error('Function not implemented.')
          }}
          setSelectedFireZoneID={function (): void {
            throw new Error('Function not implemented.')
          }}
        />
      </Provider>
    )

    const fireTable = getByTestId('fba-map')
    expect(fireTable).toBeVisible()
  })
})