import React from 'react'
import FireZoneUnitSummary from 'features/fba/components/infoPanel/FireZoneUnitSummary'
import { FireShape } from 'api/fbaAPI'
import { render } from '@testing-library/react'

describe('FireZoneUnitSummary', () => {
  class ResizeObserver {
    observe() {
      // mock no-op
    }
    unobserve() {
      // mock no-op
    }
    disconnect() {
      // mock no-op
    }
  }
  window.ResizeObserver = ResizeObserver
  it('should not render empty div if selectedFireZoneUnit is undefined', () => {
    const { getByTestId } = render(
      <FireZoneUnitSummary
        fireShapeAreas={[]}
        fuelTypeInfo={[]}
        hfiElevationInfo={[]}
        selectedFireZoneUnit={undefined}
      />
    )
    const fireZoneUnitInfo = getByTestId('fire-zone-unit-summary-empty')
    expect(fireZoneUnitInfo).toBeInTheDocument()
  })
  it('should render if selectedFireZoneUnit is not undefined', () => {
    const fireShape: FireShape = {
      fire_shape_id: 1,
      mof_fire_zone_name: 'foo',
      mof_fire_centre_name: 'fizz',
      area_sqm: 10
    }
    const { getByTestId } = render(
      <FireZoneUnitSummary
        fireShapeAreas={[]}
        fuelTypeInfo={[]}
        hfiElevationInfo={[]}
        selectedFireZoneUnit={fireShape}
      />
    )
    const fireZoneUnitInfo = getByTestId('fire-zone-unit-summary')
    expect(fireZoneUnitInfo).toBeInTheDocument()
  })
})
