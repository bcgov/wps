import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import FireZoneUnitTabs from './FireZoneUnitTabs'
import { FireCenter, FireCentreHFIStats, FireCentreTPIResponse, FireShape, FireShapeStatusDetail } from 'api/fbaAPI'
import { vi } from 'vitest'
import { ADVISORY_ORANGE_FILL, ADVISORY_RED_FILL } from '@/features/fba/components/map/featureStylers'
import { combineReducers } from '@reduxjs/toolkit'
import fireCentreTPIStatsSlice, { initialState as tpiInitialState } from '@/features/fba/slices/fireCentreTPIStatsSlice'
import fireCentreHFIFuelStatsSlice, {
  initialState as hfiInitialState
} from '@/features/fba/slices/fireCentreHFIFuelStatsSlice'
import { Provider } from 'react-redux'
import { AdvisoryStatus } from '@/utils/constants'
import { createTestStore } from '@/test/testUtils'

const getAdvisoryDetails = (
  fireZoneName: string,
  fireShapeId: number,
  advisoryStatus: AdvisoryStatus
): FireShapeStatusDetail[] => {
  return [
    {
      fire_shape_id: fireShapeId,
      fire_shape_name: fireZoneName,
      fire_centre_name: fireCentre1,
      status: advisoryStatus
    }
  ]
}

const fireZoneUnitReducer = combineReducers({
  fireCentreHFIFuelStats: fireCentreHFIFuelStatsSlice,
  fireCentreTPIStats: fireCentreTPIStatsSlice
})

const fireCentre1 = 'Centre 1'
const zoneA = 'A Zone'
const zoneB = 'B Zone'

const mockSelectedFireZoneUnitA: FireShape = {
  fire_shape_id: 1,
  mof_fire_centre_name: fireCentre1,
  mof_fire_zone_name: zoneA
}

const mockSelectedFireCenter: FireCenter = {
  id: 1,
  name: fireCentre1,
  stations: []
}

const mockFireCentreTPIStats: FireCentreTPIResponse = {
  fire_centre_name: 'test_name',
  firezone_tpi_stats: [
    {
      fire_zone_id: 1,
      valley_bottom_hfi: 10,
      valley_bottom_tpi: 11,
      mid_slope_hfi: 90,
      mid_slope_tpi: 91,
      upper_slope_hfi: 10,
      upper_slope_tpi: 11
    }
  ]
}

const mockFireCentreHFIFuelStats: FireCentreHFIStats = {
  'Centre 1': {
    1: {
      min_wind_stats: [
        {
          threshold: { id: 1, name: 'threshold', description: 'description' },
          min_wind_speed: 1
        }
      ],
      fuel_area_stats: [
        {
          fuel_type: { fuel_type_id: 1, fuel_type_code: 'C', description: 'fuel type' },
          area: 10,
          threshold: { id: 1, name: 'threshold', description: 'description' },
          critical_hours: { start_time: 8, end_time: 11 },
          fuel_area: 20
        }
      ]
    },
    2: {
      min_wind_stats: [
        {
          threshold: { id: 1, name: 'threshold', description: 'description' },
          min_wind_speed: 1
        }
      ],
      fuel_area_stats: [
        {
          fuel_type: { fuel_type_id: 1, fuel_type_code: 'C', description: 'fuel type' },
          area: 10,
          threshold: { id: 1, name: 'threshold', description: 'description' },
          critical_hours: { start_time: 8, end_time: 11 },
          fuel_area: 20
        }
      ]
    }
  }
}

const mockSortedFireZoneUnits: FireShapeStatusDetail[] = [
  {
    fire_shape_id: 1,
    fire_shape_name: zoneA,
    fire_centre_name: fireCentre1,
    status: AdvisoryStatus.ADVISORY
  },
  {
    fire_shape_id: 2,
    fire_shape_name: zoneB,
    fire_centre_name: fireCentre1,
    status: AdvisoryStatus.WARNING
  }
]

vi.mock('features/fba/hooks/useFireCentreDetails', () => ({
  useFireCentreDetails: () => mockSortedFireZoneUnits
}))

const setSelectedFireShapeMock = vi.fn()
const setZoomSourceMock = vi.fn()

const renderComponent = (testStore: any) =>
  render(
    <Provider store={testStore}>
      <FireZoneUnitTabs
        selectedFireZoneUnit={undefined}
        setZoomSource={setZoomSourceMock}
        selectedFireCenter={mockSelectedFireCenter}
        setSelectedFireShape={setSelectedFireShapeMock}
      />
    </Provider>
  )

describe('FireZoneUnitTabs', () => {
  const testStore = createTestStore(
    {
      fireCentreHFIFuelStats: { ...hfiInitialState, fireCentreHFIFuelStats: mockFireCentreHFIFuelStats },
      fireCentreTPIStats: { ...tpiInitialState, fireCentreTPIStats: mockFireCentreTPIStats }
    },
    fireZoneUnitReducer
  )
  it('should render', () => {
    const { getByTestId } = renderComponent(testStore)

    const summaryTabs = getByTestId('firezone-summary-tabs')
    expect(summaryTabs).toBeInTheDocument()
    expect(getByTestId('fire-zone-title-tabs')).toBeInTheDocument()
  })

  it('should render tabs for each zone in a centre', () => {
    const { getByTestId } = renderComponent(testStore)

    const tab1 = getByTestId('zone-1-tab')
    expect(tab1).toBeInTheDocument()
    const tab2 = getByTestId('zone-2-tab')
    expect(tab2).toBeInTheDocument()
    const tabs = screen.getAllByRole('tab')
    expect(tabs.length).toBe(2)
  })

  it('should select the first zone tab of a fire centre alphabetically if no zone is selected, but not zoom to it', () => {
    renderComponent(testStore)

    expect(setSelectedFireShapeMock).toHaveBeenCalledWith(mockSelectedFireZoneUnitA)
    expect(setZoomSourceMock).not.toHaveBeenCalled()
  })

  it('should switch to a different tab when clicked and set the map zoom source', () => {
    renderComponent(testStore)

    const tab2 = screen.getByTestId('zone-2-tab')
    fireEvent.click(tab2)

    expect(setSelectedFireShapeMock).toHaveBeenCalledWith({
      fire_shape_id: 2,
      mof_fire_centre_name: fireCentre1,
      mof_fire_zone_name: zoneB
    })
    expect(setZoomSourceMock).toHaveBeenCalledWith('fireShape')
  })

  it('should render empty if there is no selected Fire Centre', () => {
    const { getByTestId, queryByTestId } = render(
      <Provider store={testStore}>
        <FireZoneUnitTabs
          selectedFireZoneUnit={undefined}
          setZoomSource={setZoomSourceMock}
          selectedFireCenter={undefined}
          setSelectedFireShape={setSelectedFireShapeMock}
        />
      </Provider>
    )

    const emptyTabs = getByTestId('fire-zone-unit-tabs-empty')
    expect(emptyTabs).toBeInTheDocument()
    expect(queryByTestId('fire-zone-title-tabs')).not.toBeInTheDocument()
  })

  it('should render tabs with the correct advisory colour', () => {
    const { getByTestId } = renderComponent(testStore)

    const tab1 = getByTestId('zone-1-tab')
    expect(tab1).toHaveStyle(`backgroundColor: ${ADVISORY_ORANGE_FILL}`)
    const tab2 = getByTestId('zone-2-tab')
    expect(tab2).toHaveStyle(`backgroundColor: ${ADVISORY_RED_FILL}`)
  })
})
