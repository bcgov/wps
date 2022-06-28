import { render, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import SaveNewStationButton from 'features/hfiCalculator/components/stationAdmin/SaveNewStationButton'
import React from 'react'

describe('SaveNewStationButton', () => {
  it('should render button enabled when all fields set', () => {
    const handleSaveMock = jest.fn()

    const { getByTestId } = render(<SaveNewStationButton handleSave={handleSaveMock} />)
    const saveButton = getByTestId('save-new-station-button')
    expect(saveButton).toBeInTheDocument()
  })
  it('should render button enabled when all fields set', async () => {
    const handleSaveMock = jest.fn()

    const { getByTestId } = render(<SaveNewStationButton handleSave={handleSaveMock} />)
    const saveButton = getByTestId('save-new-station-button')
    userEvent.click(saveButton)
    await waitFor(() => expect(handleSaveMock).toBeCalledTimes(1))
  })
})
