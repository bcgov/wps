import { render } from '@testing-library/react'
import SaveNewStationButton from 'features/hfiCalculator/components/stationAdmin/SaveNewStationButton'
import React from 'react'

describe('SaveNewStationButton', () => {
  const planningArea = { id: 1, name: 'test' }
  const station = { code: 1, name: 'test' }
  const fuelType = { id: 1, name: 'test' }

  it('should not render button enabled when all fields set and  ', () => {
    const handleSaveMock = jest.fn()

    const { getByTestId } = render(
      <SaveNewStationButton
        newStation={{ planningArea, station, fuelType, dirty: true }}
        invalidNewStation={false}
        handleSave={handleSaveMock}
      />
    )
    const saveButton = getByTestId('save-new-station-button')
    expect(saveButton).toBeInTheDocument()
    expect(saveButton).not.toHaveAttribute('disabled')
  })

  it('should render button disabled when missing fields and edited ', () => {
    const handleSaveMock = jest.fn()

    const { getByTestId } = render(
      <SaveNewStationButton
        newStation={{ dirty: true }}
        invalidNewStation={true}
        handleSave={handleSaveMock}
      />
    )

    const saveButton = getByTestId('save-new-station-button')
    expect(saveButton).toBeInTheDocument()
    expect(saveButton).toHaveAttribute('disabled')
  })
  it('should render button disabled when missing fields and unedited', () => {
    const handleSaveMock = jest.fn()

    const { getByTestId } = render(
      <SaveNewStationButton
        newStation={{ dirty: false }}
        invalidNewStation={false}
        handleSave={handleSaveMock}
      />
    )

    const saveButton = getByTestId('save-new-station-button')
    expect(saveButton).toBeInTheDocument()
    expect(saveButton).toHaveAttribute('disabled')
  })
})
