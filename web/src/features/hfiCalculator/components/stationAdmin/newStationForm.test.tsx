import { render } from '@testing-library/react'
import { FuelType } from 'api/hfiCalculatorAPI'
import {
  AdminStation,
  BasicWFWXStation
} from 'features/hfiCalculator/components/stationAdmin/AddStationModal'
import NewStationForm from 'features/hfiCalculator/components/stationAdmin/NewStationForm'
import React from 'react'

describe('NewStationForm', () => {
  const setNewStationMock = jest.fn()
  const setInvalidMock = jest.fn()

  beforeEach(() => {
    setNewStationMock.mockReset()
    setInvalidMock.mockReset()
  })

  const renderNewStationForm = (
    newStation: AdminStation,
    invalid: boolean,
    stationAddedError: string | null
  ) => {
    return render(
      <NewStationForm
        newStation={newStation}
        invalid={invalid}
        setNewStation={setNewStationMock}
        setInvalid={setInvalidMock}
        stationAddedError={stationAddedError}
      />
    )
  }
  describe('valid states', () => {
    it('should not render error message when new station has not been edited', () => {
      const { queryByText } = renderNewStationForm({ dirty: false }, false, null)

      const errorMessage = queryByText('Please complete empty fields to continue')
      expect(errorMessage).not.toBeInTheDocument()
    })
    it('should not render error outline for planning area dropdown when it exists', () => {
      const planningArea = { id: 1, name: 'test' }
      const { getByTestId } = renderNewStationForm(
        { dirty: true, planningArea },
        false,
        null
      )

      const planningAreaSelect = getByTestId('select-planning-area')
      expect(planningAreaSelect.getElementsByClassName('Mui-error').length).toBe(0)
    })
    it('should not render error outline for station dropdown when it exists', () => {
      const station: BasicWFWXStation = {
        code: 1,
        name: 'test'
      }

      const { getByTestId } = renderNewStationForm({ dirty: true, station }, false, null)

      const planningAreaSelect = getByTestId('select-station')
      expect(planningAreaSelect.getElementsByClassName('Mui-error').length).toBe(0)
    })
    it('should not render error outline for fuel type dropdown when it exists', () => {
      const fuelType: FuelType = {
        id: 1,
        abbrev: 'c1',
        description: 'c1',
        fuel_type_code: 'c1',
        percentage_conifer: 0,
        percentage_dead_fir: 0
      }

      const { getByTestId } = renderNewStationForm({ dirty: true, fuelType }, false, null)

      const planningAreaSelect = getByTestId('select-fuel-type')
      expect(planningAreaSelect.getElementsByClassName('Mui-error').length).toBe(0)
    })
    it('should not render error outline for planning area dropdown when missing but unedited', () => {
      const { getByTestId } = renderNewStationForm({ dirty: false }, false, null)

      const planningAreaSelect = getByTestId('select-planning-area')
      expect(planningAreaSelect.getElementsByClassName('Mui-error').length).toBe(0)
    })
    it('should not render error outline for station dropdown when missing but unedited', () => {
      const { getByTestId } = renderNewStationForm({ dirty: false }, false, null)

      const stationSelect = getByTestId('select-station')
      expect(stationSelect.getElementsByClassName('Mui-error').length).toBe(0)
    })
    it('should not render error outline for fuel type dropdown when missing but unedited', () => {
      const { getByTestId } = renderNewStationForm({ dirty: false }, false, null)

      const fuelTypeSelect = getByTestId('select-fuel-type')
      expect(fuelTypeSelect.getElementsByClassName('Mui-error').length).toBe(0)
    })
  })
  describe('invalid states', () => {
    it('should render error message when new station is edited with empty fields', () => {
      const { queryByText } = renderNewStationForm({ dirty: true }, true, null)

      const errorMessage = queryByText('Please complete empty fields to continue')
      expect(errorMessage).toBeInTheDocument()
    })
    it('should render error message when new station already exists', () => {
      const alreadyExistsMessage = 'Station already exists'
      const { queryByText } = renderNewStationForm(
        { dirty: true },
        true,
        alreadyExistsMessage
      )

      const errorMessage = queryByText(alreadyExistsMessage)
      expect(errorMessage).toBeInTheDocument()
    })
    describe('dropdown error outlines', () => {
      const renderIncompleteForm = () => renderNewStationForm({ dirty: true }, true, null)
      it('should render error outline for planning area dropdown when missing and station is edited', () => {
        const { getByTestId } = renderIncompleteForm()

        const planningAreaSelect = getByTestId('select-planning-area')
        expect(
          planningAreaSelect.getElementsByClassName('Mui-error').length
        ).toBeGreaterThanOrEqual(1)
      })
      it('should render error outline for station dropdown when missing and station is edited', () => {
        const { getByTestId } = renderIncompleteForm()

        const planningAreaSelect = getByTestId('select-station')
        expect(
          planningAreaSelect.getElementsByClassName('Mui-error').length
        ).toBeGreaterThanOrEqual(1)
      })
      it('should render error outline for fuel type dropdown when missing and station is edited', () => {
        const { getByTestId } = renderIncompleteForm()

        const planningAreaSelect = getByTestId('select-fuel-type')
        expect(
          planningAreaSelect.getElementsByClassName('Mui-error').length
        ).toBeGreaterThanOrEqual(1)
      })
    })
  })
})
