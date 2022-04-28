import { render } from '@testing-library/react'
import NewStationForm from 'features/hfiCalculator/components/stationAdmin/NewStationForm'
import React from 'react'

describe('NewStationForm', () => {
  describe('valid states', () => {
    it('should not render error message when new station has not been edited', () => {
      const { queryByText } = render(
        <NewStationForm newStation={{ dirty: false }} invalid={false} />
      )

      const errorMessage = queryByText('Please complete empty fields to continue')
      expect(errorMessage).not.toBeInTheDocument()
    })

    it('should render error message when new station is edited with empty fields', () => {
      const { queryByText } = render(
        <NewStationForm newStation={{ dirty: true }} invalid={true} />
      )

      const errorMessage = queryByText('Please complete empty fields to continue')
      expect(errorMessage).toBeInTheDocument()
    })
    it('should not render error outline for planning area dropdown when it exists', () => {
      const planningArea = { id: 1, name: 'test' }

      const { getByTestId } = render(
        <NewStationForm newStation={{ planningArea, dirty: true }} invalid={false} />
      )

      const planningAreaSelect = getByTestId('select-planning-area')
      expect(planningAreaSelect.getElementsByClassName('Mui-error').length).toBe(0)
    })
    it('should not render error outline for station dropdown when it exists', () => {
      const station = { code: 1, name: 'test' }

      const { getByTestId } = render(
        <NewStationForm newStation={{ station, dirty: true }} invalid={false} />
      )

      const planningAreaSelect = getByTestId('select-station')
      expect(planningAreaSelect.getElementsByClassName('Mui-error').length).toBe(0)
    })
    it('should not render error outline for fuel type dropdown when it exists', () => {
      const fuelType = { id: 1, name: 'test' }

      const { getByTestId } = render(
        <NewStationForm newStation={{ fuelType, dirty: true }} invalid={false} />
      )

      const planningAreaSelect = getByTestId('select-fuel-type')
      expect(planningAreaSelect.getElementsByClassName('Mui-error').length).toBe(0)
    })
    it('should not render error outline for planning area dropdown when missing but unedited', () => {
      const { getByTestId } = render(
        <NewStationForm newStation={{ dirty: false }} invalid={false} />
      )

      const planningAreaSelect = getByTestId('select-planning-area')
      expect(planningAreaSelect.getElementsByClassName('Mui-error').length).toBe(0)
    })
    it('should not render error outline for station dropdown when missing but unedited', () => {
      const { getByTestId } = render(
        <NewStationForm newStation={{ dirty: false }} invalid={false} />
      )

      const planningAreaSelect = getByTestId('select-station')
      expect(planningAreaSelect.getElementsByClassName('Mui-error').length).toBe(0)
    })
    it('should not render error outline for fuel type dropdown when missing but unedited', () => {
      const { getByTestId } = render(
        <NewStationForm newStation={{ dirty: false }} invalid={false} />
      )

      const planningAreaSelect = getByTestId('select-fuel-type')
      expect(planningAreaSelect.getElementsByClassName('Mui-error').length).toBe(0)
    })
  })
  describe('invalid states', () => {
    it('should render error message when new station is edited with empty fields', () => {
      const { queryByText } = render(
        <NewStationForm newStation={{ dirty: true }} invalid={true} />
      )

      const errorMessage = queryByText('Please complete empty fields to continue')
      expect(errorMessage).toBeInTheDocument()
    })
    it('should render error outline for planning area dropdown when missing and station is edited', () => {
      const { getByTestId } = render(
        <NewStationForm newStation={{ dirty: true }} invalid={true} />
      )

      const planningAreaSelect = getByTestId('select-planning-area')
      expect(
        planningAreaSelect.getElementsByClassName('Mui-error').length
      ).toBeGreaterThanOrEqual(1)
    })
    it('should render error outline for station dropdown when missing and station is edited', () => {
      const { getByTestId } = render(
        <NewStationForm newStation={{ dirty: true }} invalid={true} />
      )

      const planningAreaSelect = getByTestId('select-station')
      expect(
        planningAreaSelect.getElementsByClassName('Mui-error').length
      ).toBeGreaterThanOrEqual(1)
    })
    it('should render error outline for fuel type dropdown when missing and station is edited', () => {
      const { getByTestId } = render(
        <NewStationForm newStation={{ dirty: true }} invalid={true} />
      )

      const planningAreaSelect = getByTestId('select-fuel-type')
      expect(
        planningAreaSelect.getElementsByClassName('Mui-error').length
      ).toBeGreaterThanOrEqual(1)
    })
  })
})
