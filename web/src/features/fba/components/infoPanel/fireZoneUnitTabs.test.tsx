import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import FireZoneUnitTabs from './FireZoneUnitTabs'
import { FireCenter, FireCentreHfiFuelsData, FireShape, FireShapeAreaDetail, FireZoneTPIStats } from 'api/fbaAPI'
import { vi } from 'vitest'
import { ADVISORY_ORANGE_FILL, ADVISORY_RED_FILL } from '@/features/fba/components/map/featureStylers'

const getAdvisoryDetails = (
  fireZoneName: string,
  fireShapeId: number,
  advisoryPercent: number,
  warningPercent: number
): FireShapeAreaDetail[] => {
  return [
    {
      fire_shape_id: fireShapeId,
      threshold: 1,
      combustible_area: 1,
      elevated_hfi_area: 2,
      elevated_hfi_percentage: advisoryPercent,
      fire_shape_name: fireZoneName,
      fire_centre_name: fireCentre1
    },
    {
      fire_shape_id: fireShapeId,
      threshold: 2,
      combustible_area: 1,
      elevated_hfi_area: 2,
      elevated_hfi_percentage: warningPercent,
      fire_shape_name: fireZoneName,
      fire_centre_name: fireCentre1
    }
  ]
}

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

const mockFireCentreTPIStats: Record<string, FireZoneTPIStats[]> = {
  [fireCentre1]: [{ fire_zone_id: 1, valley_bottom: 10, mid_slope: 90, upper_slope: 10 }]
}

const mockFireCentreHfiFuelTypes: FireCentreHfiFuelsData = {
  [fireCentre1]: {
    '1': [
      {
        fuel_type: { fuel_type_id: 1, fuel_type_code: 'C', description: 'fuel type' },
        area: 10,
        threshold: { id: 1, name: 'threshold', description: 'description' },
        critical_hours: { start_time: 9, end_time: 11}
      }
    ]
  }
}

const mockSortedGroupedFireZoneUnits = [
  {
    fire_shape_id: 1,
    fire_shape_name: zoneA,
    fire_centre_name: fireCentre1,
    fireShapeDetails: getAdvisoryDetails(zoneA, 1, 30, 10)
  },
  {
    fire_shape_id: 2,
    fire_shape_name: zoneB,
    fire_centre_name: fireCentre1,
    fireShapeDetails: getAdvisoryDetails(zoneB, 2, 30, 30)
  }
]

vi.mock('features/fba/hooks/useFireCentreDetails', () => ({
  useFireCentreDetails: () => mockSortedGroupedFireZoneUnits
}))

const setSelectedFireShapeMock = vi.fn()
const setZoomSourceMock = vi.fn()

const renderComponent = () =>
  render(
    <FireZoneUnitTabs
      selectedFireZoneUnit={undefined}
      setZoomSource={setZoomSourceMock}
      fireCentreTPIStats={mockFireCentreTPIStats}
      fireCentreHfiFuelTypes={mockFireCentreHfiFuelTypes}
      selectedFireCenter={mockSelectedFireCenter}
      advisoryThreshold={20}
      setSelectedFireShape={setSelectedFireShapeMock}
    />
  )

describe('FireZoneUnitTabs', () => {
  it('should render', () => {
    const { getByTestId } = renderComponent()

    const summaryTabs = getByTestId('firezone-summary-tabs')
    expect(summaryTabs).toBeInTheDocument()
  })

  it('should render tabs for each zone in a centre', () => {
    const { getByTestId } = renderComponent()

    const tab1 = getByTestId('zone-1-tab')
    expect(tab1).toBeInTheDocument()
    const tab2 = getByTestId('zone-2-tab')
    expect(tab2).toBeInTheDocument()
    const tabs = screen.getAllByRole('tab')
    expect(tabs.length).toBe(2)
  })

  it('should select the first zone tab of a fire centre alphabetically if no zone is selected, but not zoom to it', () => {
    renderComponent()

    expect(setSelectedFireShapeMock).toHaveBeenCalledWith(mockSelectedFireZoneUnitA)
    expect(setZoomSourceMock).not.toHaveBeenCalled()
  })

  it('should switch to a different tab when clicked and set the map zoom source', () => {
    renderComponent()

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
    const { getByTestId } = render(
      <FireZoneUnitTabs
        selectedFireZoneUnit={undefined}
        setZoomSource={setZoomSourceMock}
        fireCentreTPIStats={{}}
        fireCentreHfiFuelTypes={{}}
        selectedFireCenter={undefined}
        advisoryThreshold={20}
        setSelectedFireShape={setSelectedFireShapeMock}
      />
    )

    const emptyTabs = getByTestId('fire-zone-unit-tabs-empty')
    expect(emptyTabs).toBeInTheDocument()
  })

  it('should render tabs with the correct advisory colour', () => {
    const { getByTestId } = renderComponent()

    const tab1 = getByTestId('zone-1-tab')
    expect(tab1).toHaveStyle(`backgroundColor: ${ADVISORY_ORANGE_FILL}`)
    const tab2 = getByTestId('zone-2-tab')
    expect(tab2).toHaveStyle(`backgroundColor: ${ADVISORY_RED_FILL}`)
  })
})
