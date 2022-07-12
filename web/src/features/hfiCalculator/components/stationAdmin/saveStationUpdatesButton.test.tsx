import { render, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import SaveStationUpdatesButton from 'features/hfiCalculator/components/stationAdmin/SaveStationUpdatesButton'
import React from 'react'
/**
 *   planningAreaId: number
  rowId: number
  station?: BasicWFWXStation
  fuelType?: Pick<FuelType, 'id' | 'abbrev'>
 */

describe('SaveStationUpdatesButton', () => {
  it('should render button enabled when there is a removed station', () => {
    const handleSaveMock = jest.fn()

    const { getByTestId } = render(
      <SaveStationUpdatesButton
        handleSave={handleSaveMock}
        addedStations={[]}
        removedStations={[{ planningAreaId: 1, rowId: 1 }]}
      />
    )
    const saveButton = getByTestId('save-new-station-button')
    expect(saveButton).toBeInTheDocument()
  })
  it('should render button enabled when there is an added station with all required fields', () => {
    const handleSaveMock = jest.fn()

    const { getByTestId } = render(
      <SaveStationUpdatesButton
        handleSave={handleSaveMock}
        addedStations={[
          { planningAreaId: 1, rowId: 1, fuelType: { id: 1, abbrev: 'c5' }, station: { code: 1, name: 'test' } }
        ]}
        removedStations={[]}
      />
    )
    const saveButton = getByTestId('save-new-station-button')
    expect(saveButton).toBeInTheDocument()
  })

  it('should not be enabled when there is no added or removed stations', () => {
    const handleSaveMock = jest.fn()

    const { getByTestId } = render(
      <SaveStationUpdatesButton handleSave={handleSaveMock} addedStations={[]} removedStations={[]} />
    )
    const saveButton = getByTestId('save-new-station-button')
    expect(saveButton).toBeDisabled()
  })
  it('should be enabled when an added station has all fields seleced', () => {
    const handleSaveMock = jest.fn()

    const { getByTestId } = render(
      <SaveStationUpdatesButton
        handleSave={handleSaveMock}
        addedStations={[
          { planningAreaId: 1, rowId: 1, fuelType: { id: 1, abbrev: 'c5' }, station: { code: 1, name: 'test' } }
        ]}
        removedStations={[]}
      />
    )
    const saveButton = getByTestId('save-new-station-button')
    expect(saveButton).toBeEnabled()
  })
  it('should not be enabled when an added station has nothing selected', () => {
    const handleSaveMock = jest.fn()

    const { getByTestId } = render(
      <SaveStationUpdatesButton
        handleSave={handleSaveMock}
        addedStations={[{ planningAreaId: 1, rowId: 1 }]}
        removedStations={[]}
      />
    )
    const saveButton = getByTestId('save-new-station-button')
    expect(saveButton).toBeDisabled()
  })
  it('should not be enabled when an added station name is not selected', () => {
    const handleSaveMock = jest.fn()

    const { getByTestId } = render(
      <SaveStationUpdatesButton
        handleSave={handleSaveMock}
        addedStations={[{ planningAreaId: 1, rowId: 1, fuelType: { id: 1, abbrev: 'c5' } }]}
        removedStations={[]}
      />
    )
    const saveButton = getByTestId('save-new-station-button')
    expect(saveButton).toBeDisabled()
  })
  it('should not be enabled when an added station fuel type is not selected', () => {
    const handleSaveMock = jest.fn()

    const { getByTestId } = render(
      <SaveStationUpdatesButton
        handleSave={handleSaveMock}
        addedStations={[{ planningAreaId: 1, rowId: 1, station: { code: 1, name: 'test' } }]}
        removedStations={[]}
      />
    )
    const saveButton = getByTestId('save-new-station-button')
    expect(saveButton).toBeDisabled()
  })
  it('should call save callback when clicked', async () => {
    const handleSaveMock = jest.fn()

    const { getByTestId } = render(
      <SaveStationUpdatesButton
        handleSave={handleSaveMock}
        addedStations={[]}
        removedStations={[{ planningAreaId: 1, rowId: 1 }]}
      />
    )
    const saveButton = getByTestId('save-new-station-button')
    userEvent.click(saveButton)
    await waitFor(() => expect(handleSaveMock).toBeCalledTimes(1))
  })
})
