import { fireEvent, render, waitFor } from '@testing-library/react'
import store from 'app/store'
import AddStationButton from 'features/hfiCalculator/components/stationAdmin/AddStationButton'
import React from 'react'
import { Provider } from 'react-redux'

describe('ManageStationsButton', () => {
  it('should render the button without the modal showing', () => {
    const { getByTestId, queryByText } = render(
      <Provider store={store}>
        <AddStationButton planningAreaStationInfo={{}} />
      </Provider>
    )

    const manageStationsButton = getByTestId('manage-stations-button')
    const closedModal = queryByText('Manage Weather Stations')
    expect(manageStationsButton).toBeInTheDocument()
    expect(closedModal).not.toBeInTheDocument()
  })
  it('should render the modal when the button is clicked', async () => {
    const { getByTestId } = render(
      <Provider store={store}>
        <AddStationButton planningAreaStationInfo={{}} />
      </Provider>
    )

    const manageStationsButton = getByTestId('manage-stations-button')
    manageStationsButton.focus()
    fireEvent.click(manageStationsButton)

    await waitFor(() => expect(getByTestId('manage-stations-modal')).toBeInTheDocument())
  })
})
