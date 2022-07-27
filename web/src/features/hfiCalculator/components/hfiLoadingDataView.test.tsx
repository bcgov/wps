import { render } from '@testing-library/react'
import { FireCentre } from 'api/hfiCalculatorAPI'
import HFILoadingDataContainer from 'features/hfiCalculator/components/HFILoadingDataContainer'
import { PrepDateRange } from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import React from 'react'

describe('HFILoadingDataView', () => {
  const child = (
    <div>
      <p>child-text</p>
    </div>
  )
  const selectedFireCentre: FireCentre = {
    id: 1,
    name: 'test',
    planning_areas: []
  }
  const dateRange: PrepDateRange = {
    start_date: '',
    end_date: ''
  }
  it('should render spinner when fire centres loading', () => {
    const { getByTestId } = render(
      <HFILoadingDataContainer
        pdfLoading={false}
        fuelTypesLoading={false}
        stationDataLoading={false}
        fireCentresLoading={true}
        stationsUpdateLoading={false}
        fireCentresError={null}
        hfiError={null}
        selectedFireCentre={selectedFireCentre}
        dateRange={dateRange}
      >
        {child}
      </HFILoadingDataContainer>
    )
    const loadingBackdrop = getByTestId('loading-backdrop')
    expect(loadingBackdrop).toBeDefined()
  })
  it('should render spinner when stations data is loading', () => {
    const { getByTestId } = render(
      <HFILoadingDataContainer
        pdfLoading={false}
        fuelTypesLoading={false}
        stationDataLoading={true}
        fireCentresLoading={false}
        stationsUpdateLoading={false}
        fireCentresError={null}
        hfiError={null}
        selectedFireCentre={selectedFireCentre}
        dateRange={dateRange}
      >
        {child}
      </HFILoadingDataContainer>
    )
    const loadingBackdrop = getByTestId('loading-backdrop')
    expect(loadingBackdrop).toBeDefined()
  })
  it('should render spinner when fuel types are loading', () => {
    const { getByTestId } = render(
      <HFILoadingDataContainer
        fuelTypesLoading={true}
        pdfLoading={false}
        stationDataLoading={false}
        fireCentresLoading={false}
        stationsUpdateLoading={false}
        fireCentresError={null}
        hfiError={null}
        selectedFireCentre={selectedFireCentre}
        dateRange={dateRange}
      >
        {child}
      </HFILoadingDataContainer>
    )
    const loadingBackdrop = getByTestId('loading-backdrop')
    expect(loadingBackdrop).toBeDefined()
  })
  it('should render spinner when PDF result is loading', () => {
    const { getByTestId } = render(
      <HFILoadingDataContainer
        pdfLoading={true}
        fuelTypesLoading={false}
        stationDataLoading={false}
        fireCentresLoading={false}
        stationsUpdateLoading={false}
        fireCentresError={null}
        hfiError={null}
        selectedFireCentre={selectedFireCentre}
        dateRange={dateRange}
      >
        {child}
      </HFILoadingDataContainer>
    )
    const loadingBackdrop = getByTestId('loading-backdrop')
    expect(loadingBackdrop).toBeDefined()
  })
  it('should render empty table row when no fire centre is selected', () => {
    const { getByTestId, queryByText } = render(
      <HFILoadingDataContainer
        pdfLoading={false}
        fuelTypesLoading={false}
        stationDataLoading={false}
        fireCentresLoading={false}
        stationsUpdateLoading={false}
        fireCentresError={null}
        hfiError={null}
        selectedFireCentre={undefined}
        dateRange={dateRange}
      >
        {child}
      </HFILoadingDataContainer>
    )
    const emptyRow = getByTestId('hfi-empty-fire-centre')
    const renderedChild = queryByText('child-text')
    expect(emptyRow).toBeDefined()
    expect(renderedChild).not.toBeInTheDocument()
  })
  it('should render children when not loading, no errors and fire centre is selected', () => {
    const { queryByText } = render(
      <HFILoadingDataContainer
        pdfLoading={false}
        fuelTypesLoading={false}
        stationDataLoading={false}
        fireCentresLoading={false}
        stationsUpdateLoading={false}
        fireCentresError={null}
        hfiError={null}
        selectedFireCentre={selectedFireCentre}
        dateRange={dateRange}
      >
        {child}
      </HFILoadingDataContainer>
    )

    const renderedChild = queryByText('child-text')
    expect(renderedChild).toBeDefined()
  })
  it('should render error alert when this is a fire centres error, and the child', () => {
    const { getByTestId, queryByText } = render(
      <HFILoadingDataContainer
        pdfLoading={false}
        fuelTypesLoading={false}
        stationDataLoading={false}
        fireCentresLoading={false}
        stationsUpdateLoading={false}
        fireCentresError={'fc-error'}
        hfiError={null}
        selectedFireCentre={selectedFireCentre}
        dateRange={dateRange}
      >
        {child}
      </HFILoadingDataContainer>
    )

    const renderedError = getByTestId('hfi-error-alert')
    expect(renderedError).toBeDefined()
    const renderedChild = queryByText('child-text')
    expect(renderedChild).toBeDefined()
  })
  it('should render error alert when there is an hfi error, and the child', () => {
    const { getByTestId, queryByText } = render(
      <HFILoadingDataContainer
        pdfLoading={false}
        fuelTypesLoading={false}
        stationDataLoading={false}
        fireCentresLoading={false}
        stationsUpdateLoading={false}
        fireCentresError={null}
        hfiError={'hfi-error'}
        selectedFireCentre={selectedFireCentre}
        dateRange={dateRange}
      >
        {child}
      </HFILoadingDataContainer>
    )

    const renderedError = getByTestId('hfi-error-alert')
    expect(renderedError).toBeDefined()
    const renderedChild = queryByText('child-text')
    expect(renderedChild).toBeDefined()
  })
})
