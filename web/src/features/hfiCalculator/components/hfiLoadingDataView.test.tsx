import { render } from '@testing-library/react'
import { FireCentre } from 'api/hfiCalcAPI'
import HFILoadingDataView from 'features/hfiCalculator/components/HFILoadingDataView'
import {
  HFIResultResponse,
  PrepDateRange
} from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import React from 'react'

describe('HFILoadingDataView', () => {
  const child = (
    <div>
      <p>child-text</p>
    </div>
  )
  const errorNotification = <React.Fragment></React.Fragment>
  const selectedFireCentre: FireCentre = {
    id: 1,
    name: 'test',
    planning_areas: []
  }
  const dateRange: PrepDateRange = {
    start_date: '',
    end_date: ''
  }
  const result: HFIResultResponse = {
    date_range: dateRange,
    selected_fire_center_id: 1,
    planning_area_station_info: {},
    planning_area_hfi_results: [],
    fire_start_ranges: []
  }
  it('should render spinner when fire centres loading', () => {
    const { getByTestId, queryByText } = render(
      <HFILoadingDataView
        loading={false}
        stationDataLoading={false}
        fireCentresLoading={true}
        fireCentresError={null}
        hfiError={null}
        errorNotification={errorNotification}
        selectedFireCentre={selectedFireCentre}
        dateRange={dateRange}
        result={result}
      >
        {child}
      </HFILoadingDataView>
    )
    const loadingContainer = getByTestId('loading-container')
    const renderedChild = queryByText('child-text')
    expect(loadingContainer).toBeDefined()
    expect(renderedChild).not.toBeInTheDocument()
  })
  it('should render spinner when stations data is loading', () => {
    const { getByTestId, queryByText } = render(
      <HFILoadingDataView
        loading={false}
        stationDataLoading={true}
        fireCentresLoading={false}
        fireCentresError={null}
        hfiError={null}
        errorNotification={errorNotification}
        selectedFireCentre={selectedFireCentre}
        dateRange={dateRange}
        result={result}
      >
        {child}
      </HFILoadingDataView>
    )
    const loadingContainer = getByTestId('loading-container')
    const renderedChild = queryByText('child-text')
    expect(loadingContainer).toBeDefined()
    expect(renderedChild).not.toBeInTheDocument()
  })
  it('should render spinner when hfi result data is loading', () => {
    const { getByTestId, queryByText } = render(
      <HFILoadingDataView
        loading={true}
        stationDataLoading={false}
        fireCentresLoading={false}
        fireCentresError={null}
        hfiError={null}
        errorNotification={errorNotification}
        selectedFireCentre={selectedFireCentre}
        dateRange={dateRange}
        result={result}
      >
        {child}
      </HFILoadingDataView>
    )
    const loadingContainer = getByTestId('loading-container')
    const renderedChild = queryByText('child-text')
    expect(loadingContainer).toBeDefined()
    expect(renderedChild).not.toBeInTheDocument()
  })
  it('should render empty table row when no fire centre is selected', () => {
    const { getByTestId, queryByText } = render(
      <HFILoadingDataView
        loading={false}
        stationDataLoading={false}
        fireCentresLoading={false}
        fireCentresError={null}
        hfiError={null}
        errorNotification={errorNotification}
        selectedFireCentre={undefined}
        dateRange={dateRange}
        result={result}
      >
        {child}
      </HFILoadingDataView>
    )
    const emptyRow = getByTestId('hfi-empty-fire-centre')
    const renderedChild = queryByText('child-text')
    expect(emptyRow).toBeDefined()
    expect(renderedChild).not.toBeInTheDocument()
  })
  it('should render error notification when there is a fire centres error', () => {
    const { queryByText } = render(
      <HFILoadingDataView
        loading={false}
        stationDataLoading={false}
        fireCentresLoading={false}
        fireCentresError={null}
        hfiError={null}
        errorNotification={errorNotification}
        selectedFireCentre={selectedFireCentre}
        dateRange={dateRange}
        result={result}
      >
        {child}
      </HFILoadingDataView>
    )

    const renderedChild = queryByText('child-text')
    expect(renderedChild).toBeDefined()
  })
  it('should render children when not loading, no errors and fire centre is selected', () => {
    const { queryByText } = render(
      <HFILoadingDataView
        loading={false}
        stationDataLoading={false}
        fireCentresLoading={false}
        fireCentresError={null}
        hfiError={null}
        errorNotification={errorNotification}
        selectedFireCentre={selectedFireCentre}
        dateRange={dateRange}
        result={result}
      >
        {child}
      </HFILoadingDataView>
    )

    const renderedChild = queryByText('child-text')
    expect(renderedChild).toBeDefined()
  })
})
