import React from 'react'
import { render } from '@testing-library/react'
import FireZoneUnitInfo from 'features/fba/components/infoPanel/FireZoneUnitInfo'
import { ADVISORY_ORANGE_FILL, ADVISORY_RED_FILL } from 'features/fba/components/map/featureStylers'
import { TRANSPARENT_COLOUR } from 'app/theme'
import { FireShapeAreaDetail } from 'api/fbaAPI'

const fireShapeAreaDetailA: FireShapeAreaDetail = {
  fire_shape_id: 1,
  fire_shape_name: 'foo',
  fire_centre_name: 'fizz',
  combustible_area: 100,
  threshold: 1,
  elevated_hfi_area: 0,
  elevated_hfi_percentage: 0
}
const fireShapeAreaDetailB: FireShapeAreaDetail = {
  fire_shape_id: 2,
  fire_shape_name: 'foo',
  fire_centre_name: 'fizz',
  combustible_area: 100,
  threshold: 2,
  elevated_hfi_area: 0,
  elevated_hfi_percentage: 0
}

describe('FireZoneUnitInfo', () => {
  beforeEach(() => {
    fireShapeAreaDetailA.threshold = 1
    fireShapeAreaDetailA.elevated_hfi_area = 0
    fireShapeAreaDetailA.elevated_hfi_percentage = 0
    fireShapeAreaDetailB.threshold = 2
    fireShapeAreaDetailB.elevated_hfi_area = 0
    fireShapeAreaDetailB.elevated_hfi_percentage = 0
  })
  it('should render', () => {
    const { getByTestId } = render(
      <FireZoneUnitInfo advisoryThreshold={20} fireZoneUnitName="foo" fireZoneUnitDetails={[]} />
    )
    const fireZoneUnitInfo = getByTestId('fire-zone-unit-info')
    expect(fireZoneUnitInfo).toBeInTheDocument()
  })
  it('should render the fire zone unit name', () => {
    const { getByTestId } = render(
      <FireZoneUnitInfo advisoryThreshold={20} fireZoneUnitName="foo" fireZoneUnitDetails={[]} />
    )
    const fireZoneUnitInfo = getByTestId('fire-zone-unit-info')
    expect(fireZoneUnitInfo).toHaveTextContent('foo')
  })
  it('should render a LIGHT_GREY swatch when fireZoneUnitDetails have no threshold specified', () => {
    fireShapeAreaDetailA.threshold = undefined
    const { getByTestId } = render(
      <FireZoneUnitInfo advisoryThreshold={20} fireZoneUnitName="foo" fireZoneUnitDetails={[fireShapeAreaDetailA]} />
    )
    const fireZoneUnitInfoSwatch = getByTestId('fire-zone-unit-info-swatch')
    expect(fireZoneUnitInfoSwatch).toBeInTheDocument()
    expect(fireZoneUnitInfoSwatch).toHaveStyle(`background-color: ${TRANSPARENT_COLOUR}`)
  })
  it('should render a LIGHT_GREY swatch when fireZoneUnitDetails values do not exceed advisoryThreshold', () => {
    fireShapeAreaDetailA.elevated_hfi_area = 2
    fireShapeAreaDetailA.elevated_hfi_percentage = 19
    const { getByTestId } = render(
      <FireZoneUnitInfo advisoryThreshold={20} fireZoneUnitName="foo" fireZoneUnitDetails={[fireShapeAreaDetailA]} />
    )
    const fireZoneUnitInfoSwatch = getByTestId('fire-zone-unit-info-swatch')
    expect(fireZoneUnitInfoSwatch).toBeInTheDocument()
    expect(fireZoneUnitInfoSwatch).toHaveStyle(`background-color: ${TRANSPARENT_COLOUR}`)
  })
  it('should render an ADVISORY_ORANGE_FILL swatch when fireZoneUnitDetails values do not exceed advisoryThreshold', () => {
    fireShapeAreaDetailA.elevated_hfi_area = 21
    fireShapeAreaDetailA.elevated_hfi_percentage = 21
    const { getByTestId } = render(
      <FireZoneUnitInfo advisoryThreshold={20} fireZoneUnitName="foo" fireZoneUnitDetails={[fireShapeAreaDetailA]} />
    )
    const fireZoneUnitInfoSwatch = getByTestId('fire-zone-unit-info-swatch')
    expect(fireZoneUnitInfoSwatch).toBeInTheDocument()
    expect(fireZoneUnitInfoSwatch).toHaveStyle(`background-color: ${ADVISORY_ORANGE_FILL}`)
  })
  it('should render an ADVISORY_ORANGE_FILL swatch when fireZoneUnitDetails values exceed advisoryThreshold with multiple details', () => {
    fireShapeAreaDetailA.elevated_hfi_area = 16
    fireShapeAreaDetailA.elevated_hfi_percentage = 16
    fireShapeAreaDetailB.elevated_hfi_area = 5
    fireShapeAreaDetailB.elevated_hfi_percentage = 5
    const { getByTestId } = render(
      <FireZoneUnitInfo
        advisoryThreshold={20}
        fireZoneUnitName="foo"
        fireZoneUnitDetails={[fireShapeAreaDetailA, fireShapeAreaDetailB]}
      />
    )
    const fireZoneUnitInfoSwatch = getByTestId('fire-zone-unit-info-swatch')
    expect(fireZoneUnitInfoSwatch).toBeInTheDocument()
    expect(fireZoneUnitInfoSwatch).toHaveStyle(`background-color: ${ADVISORY_ORANGE_FILL}`)
  })
  it('should render an ADVISORY_RED_FILL swatch when fireZoneUnitDetails threshold 2 value exceeds advisoryThreshold', () => {
    fireShapeAreaDetailA.elevated_hfi_area = 16
    fireShapeAreaDetailA.elevated_hfi_percentage = 16
    fireShapeAreaDetailB.elevated_hfi_area = 21
    fireShapeAreaDetailB.elevated_hfi_percentage = 21
    const { getByTestId } = render(
      <FireZoneUnitInfo
        advisoryThreshold={20}
        fireZoneUnitName="foo"
        fireZoneUnitDetails={[fireShapeAreaDetailA, fireShapeAreaDetailB]}
      />
    )
    const fireZoneUnitInfoSwatch = getByTestId('fire-zone-unit-info-swatch')
    expect(fireZoneUnitInfoSwatch).toBeInTheDocument()
    expect(fireZoneUnitInfoSwatch).toHaveStyle(`background-color: ${ADVISORY_RED_FILL}`)
  })
})
