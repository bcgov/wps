import { render } from '@testing-library/react'
import store from 'app/store'
import FBAMap from 'features/fba/components/FBAMap'
import { DateTime } from 'luxon'
import React from 'react'
import { Provider } from 'react-redux'

describe('FBAMap', () => {
  it('should render height with height and width properties set', () => {
    const { getByTestId } = render(
      <Provider store={store}>
        <FBAMap
          date={DateTime.fromISO('2016-05-25')}
          selectedFireCenter={undefined}
          className={''}
          showRawHFI={false}
        />
      </Provider>
    )

    const fireTable = getByTestId('fba-map')
    expect(fireTable).toBeVisible()
  })
})
