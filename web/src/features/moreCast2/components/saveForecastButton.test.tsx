import rootReducer from '@/app/rootReducer'
import { configureStore } from '@reduxjs/toolkit'
import { render } from '@testing-library/react'
import store from 'app/store'
import SaveForecastButton from 'features/moreCast2/components/SaveForecastButton'

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
  it('should render the button as disabled when input is invalid', () => {
    const testStore = configureStore({
      reducer: rootReducer,
      preloadedState: {
        morecastInputValid: {
          isValid: false,
          isRequiredEmpty: {
            empty: false
          }
        }
      }
    })
    const { getByTestId } = render(
      <Provider store={testStore}>
        <SaveForecastButton enabled={true} label="test" onClick={() => undefined} />
      </Provider>
    )

    const manageStationsButton = getByTestId('submit-forecast-button')
    expect(manageStationsButton).toBeInTheDocument()
    expect(manageStationsButton).toBeDisabled()
  })
})
