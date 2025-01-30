import React from 'react'
import { render } from '@testing-library/react'
import ElevationStatus from 'features/fba/components/viz/ElevationStatus'

describe('ElevationStatus', () => {
  it('should render all classifications and svg', () => {
    const { getByTestId } = render(
      <ElevationStatus
        tpiStats={{
          fire_zone_id: 1,
          valley_bottom_hfi: 0,
          valley_bottom_tpi: 10,
          mid_slope_hfi: 1,
          mid_slope_tpi: 3,
          upper_slope_hfi: 2,
          upper_slope_tpi: 3
        }}
      />
    )

    const tpiMountain = getByTestId('tpi-mountain')
    expect(tpiMountain).toBeInTheDocument()

    const valleyBottom = getByTestId('valley-bottom')
    expect(valleyBottom).toBeInTheDocument()
    expect(valleyBottom).toHaveTextContent('0%')

    const midSlope = getByTestId('mid-slope')
    expect(midSlope).toBeInTheDocument()
    expect(midSlope).toHaveTextContent('33%')

    const upperSlope = getByTestId('upper-slope')
    expect(upperSlope).toBeInTheDocument()
    expect(upperSlope).toHaveTextContent('67%')
  })

  it('should render all zero classifications', () => {
    const { getByTestId } = render(
      <ElevationStatus
        tpiStats={{
          fire_zone_id: 1,
          valley_bottom_hfi: 0,
          mid_slope_hfi: 0,
          upper_slope_hfi: 0,
          valley_bottom_tpi: 1,
          mid_slope_tpi: 1,
          upper_slope_tpi: 1
        }}
      />
    )

    const valleyBottom = getByTestId('valley-bottom')
    expect(valleyBottom).toBeInTheDocument()
    expect(valleyBottom).toHaveTextContent('0%')

    const midSlope = getByTestId('mid-slope')
    expect(midSlope).toBeInTheDocument()
    expect(midSlope).toHaveTextContent('0%')

    const upperSlope = getByTestId('upper-slope')
    expect(upperSlope).toBeInTheDocument()
    expect(upperSlope).toHaveTextContent('0%')
  })
})
