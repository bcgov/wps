import React from 'react'
import { render } from '@testing-library/react'
import ElevationStatus from 'features/fba/components/viz/ElevationStatus'

describe('ElevationStatus', () => {
  it('should render all classifications and svg', () => {
    const { getByTestId } = render(
        <ElevationStatus bottom={0} mid={1} upper={2} />
    )

    const tpiMountain = getByTestId('tpi-mountain')
    expect(tpiMountain).toBeInTheDocument()

    const valleyBottom = getByTestId('valley-bottom')
    expect(valleyBottom).toBeInTheDocument()
    expect(valleyBottom).toHaveTextContent("0%")

    const midSlope = getByTestId('mid-slope')
    expect(midSlope).toBeInTheDocument()
    expect(midSlope).toHaveTextContent("33%")

    const upperSlope = getByTestId('upper-slope')
    expect(upperSlope).toBeInTheDocument()
    expect(upperSlope).toHaveTextContent("67%")
  })

  it('should render all zero classifications', () => {
    const { getByTestId } = render(
        <ElevationStatus bottom={0} mid={0} upper={0} />
    )

    const valleyBottom = getByTestId('valley-bottom')
    expect(valleyBottom).toBeInTheDocument()
    expect(valleyBottom).toHaveTextContent("0%")

    const midSlope = getByTestId('mid-slope')
    expect(midSlope).toBeInTheDocument()
    expect(midSlope).toHaveTextContent("0%")

    const upperSlope = getByTestId('upper-slope')
    expect(upperSlope).toBeInTheDocument()
    expect(upperSlope).toHaveTextContent("0%")
  })
})
