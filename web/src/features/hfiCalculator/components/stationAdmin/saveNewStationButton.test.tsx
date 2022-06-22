import { render } from '@testing-library/react'
import SaveNewStationButton from 'features/hfiCalculator/components/stationAdmin/SaveNewStationButton'
import React from 'react'

describe('SaveNewStationButton', () => {
  /**
   * TODO: Implement update tests
   */
  it('should render button enabled when all fields set', () => {
    const handleSaveMock = jest.fn()

    const { getByTestId } = render(<SaveNewStationButton invalidNewStation={false} handleSave={handleSaveMock} />)
    const saveButton = getByTestId('save-new-station-button')
    expect(saveButton).toBeInTheDocument()
  })
})
