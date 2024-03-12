import { render } from '@testing-library/react'
import store from 'app/store'
import ResetForecastButton from 'features/moreCast2/components/ResetForecastButton'
import React from 'react'
import { Provider } from 'react-redux'

describe('SaveForecastButton', () => {
  it('should render the button as enabled', () => {
    const { getByTestId } = render(
      <Provider store={store}>
        <ResetForecastButton enabled={true} label="test" allRows={[]} setAllRows={jest.fn()} />
      </Provider>
    )

    const manageStationsButton = getByTestId('reset-forecast-button')
    expect(manageStationsButton).toBeInTheDocument()
    expect(manageStationsButton).toBeEnabled()
  })
  it('should render the button as disabled', () => {
    const { getByTestId } = render(
      <Provider store={store}>
        <ResetForecastButton enabled={false} label="test" allRows={[]} setAllRows={jest.fn()} />
      </Provider>
    )

    const manageStationsButton = getByTestId('reset-forecast-button')
    expect(manageStationsButton).toBeInTheDocument()
    expect(manageStationsButton).toBeDisabled()
  })
})
