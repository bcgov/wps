import { render } from '@testing-library/react'
import { FuelType } from 'api/hfiCalculatorAPI'
import { BasicPlanningArea, BasicWFWXStation } from 'features/hfiCalculator/components/stationAdmin/AddStationModal'
import SaveNewStationButton from 'features/hfiCalculator/components/stationAdmin/SaveNewStationButton'
import React from 'react'

describe('SaveNewStationButton', () => {
  const planningArea: BasicPlanningArea = { id: 1, name: 'test' }
  const station: BasicWFWXStation = {
    code: 1,
    name: 'test'
  }
  const fuelType: FuelType = {
    id: 1,
    abbrev: 'c1',
    description: 'c1',
    fuel_type_code: 'c1',
    percentage_conifer: 0,
    percentage_dead_fir: 0
  }

  it('should render button enabled when all fields set', () => {
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
      <SaveNewStationButton newStation={{ dirty: true }} invalidNewStation={true} handleSave={handleSaveMock} />
    )

    const saveButton = getByTestId('save-new-station-button')
    expect(saveButton).toBeInTheDocument()
    expect(saveButton).toHaveAttribute('disabled')
  })
  it('should render button disabled when missing fields and unedited', () => {
    const handleSaveMock = jest.fn()

    const { getByTestId } = render(
      <SaveNewStationButton newStation={{ dirty: false }} invalidNewStation={false} handleSave={handleSaveMock} />
    )

    const saveButton = getByTestId('save-new-station-button')
    expect(saveButton).toBeInTheDocument()
    expect(saveButton).toHaveAttribute('disabled')
  })
})
