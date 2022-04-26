import { fireEvent, render, waitFor } from '@testing-library/react'
import ManageStationsButton from 'features/hfiCalculator/components/stationAdmin/ManageStationsButton'
import React from 'react'

describe.only('ManageStationsButton', () => {
  it('should render the button without the modal showing', () => {
    const { getByTestId, queryByText } = render(<ManageStationsButton />)

    const manageStationsButton = getByTestId('manage-stations-button')
    const closedModal = queryByText('Manage Weather Stations')
    expect(manageStationsButton).toBeInTheDocument()
    expect(closedModal).not.toBeInTheDocument()
  })
  it('should render the modal when the button is clicked', async () => {
    const { getByTestId } = render(<ManageStationsButton />)

    const manageStationsButton = getByTestId('manage-stations-button')
    manageStationsButton.focus()
    fireEvent.click(manageStationsButton)

    await waitFor(() => expect(getByTestId('manage-stations-modal')).toBeInTheDocument())
  })
})
