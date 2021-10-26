import { render } from '@testing-library/react'
import store from 'app/store'
import FBAMap from 'features/fbaCalculator/components/map/FBAMap'
import React from 'react'
import { Provider } from 'react-redux'
import { CENTER_OF_BC } from 'utils/constants'

describe('FBAMap', () => {
  it('should render height with height and width properties set', () => {
    const { getByTestId } = render(
      <Provider store={store}>
        <FBAMap center={CENTER_OF_BC} />
      </Provider>
    )

    const fireTable = getByTestId('fba-map')
    expect(fireTable).toBeVisible()
  })
})
