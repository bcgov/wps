import { render } from '@testing-library/react'
import store from 'app/store'
import SaveForecastButton from 'features/moreCast2/components/SaveForecastButton'
import { vi, describe, it, expect } from 'vitest'
import { Provider } from 'react-redux'

describe('SaveForecastButton', () => {
  it('should render the button as enabled', () => {
    const { getByTestId } = render(
      <Provider store={store}>
        <SaveForecastButton enabled={true} label="test" onClick={() => undefined} />
      </Provider>
    )

    const manageStationsButton = getByTestId('submit-forecast-button')
    expect(manageStationsButton).toBeInTheDocument()
    expect(manageStationsButton).toBeEnabled()
  })
  it('should render the button as disabled', () => {
    const { getByTestId } = render(
      <Provider store={store}>
        <SaveForecastButton enabled={false} label="test" onClick={() => undefined} />
      </Provider>
    )

    const manageStationsButton = getByTestId('submit-forecast-button')
    expect(manageStationsButton).toBeInTheDocument()
    expect(manageStationsButton).toBeDisabled()
  })
})
