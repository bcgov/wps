import { render, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import store from 'app/store'
import ResetForecastButton from 'features/moreCast2/components/ResetForecastButton'
import React from 'react'
import { Provider } from 'react-redux'

describe('SaveForecastButton', () => {
  it('should render the button as enabled', () => {
    const { getByTestId } = render(
      <Provider store={store}>
        <ResetForecastButton enabled={true} label="test" onClick={() => undefined} />
      </Provider>
    )

    const resetForecastButton = getByTestId('reset-forecast-button')
    expect(resetForecastButton).toBeInTheDocument()
    expect(resetForecastButton).toBeEnabled()
  })
  it('should render the button as disabled', () => {
    const { getByTestId } = render(
      <Provider store={store}>
        <ResetForecastButton enabled={false} label="test" onClick={() => undefined} />
      </Provider>
    )

    const manageStationsButton = getByTestId('reset-forecast-button')
    expect(manageStationsButton).toBeInTheDocument()
    expect(manageStationsButton).toBeDisabled()
  })
  it('should call the reset click handler when clicked', async () => {
    const handleResetClickMock = jest.fn()
    const { getByTestId } = render(
      <Provider store={store}>
        <ResetForecastButton enabled={true} label="test" onClick={handleResetClickMock} />
      </Provider>
    )
    const resetForecastButton = getByTestId('reset-forecast-button')
    userEvent.click(resetForecastButton)
    await waitFor(() => expect(handleResetClickMock).toHaveBeenCalledTimes(1))
  })
})
