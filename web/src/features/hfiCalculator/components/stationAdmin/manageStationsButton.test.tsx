import { fireEvent, render, waitFor } from '@testing-library/react'
import store from 'app/store'
import ManageStationsButton from 'features/hfiCalculator/components/stationAdmin/ManageStationsButton'

import { Provider } from 'react-redux'

describe('ManageStationsButton', () => {
  it('should render the button without the modal showing', () => {
    const { getByTestId, queryByText } = render(
      <Provider store={store}>
        <ManageStationsButton planningAreaStationInfo={{}} />
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
        <ManageStationsButton planningAreaStationInfo={{}} />
      </Provider>
    )

    const manageStationsButton = getByTestId('manage-stations-button')
    await waitFor(() => {
      manageStationsButton.focus()
      fireEvent.click(manageStationsButton)
      expect(getByTestId('manage-stations-modal')).toBeInTheDocument()
    })
  })
})
