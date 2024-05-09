import React from 'react'
import { render } from '@testing-library/react'
import FireZoneUnitInfo from 'features/fba/components/infoPanel/FireZoneUnitInfo'
import { ADVISORY_ORANGE_FILL, ADVISORY_RED_FILL } from 'features/fba/components/map/featureStylers'
import { LIGHT_GREY } from 'app/theme'
import { FireShapeAreaDetail } from 'api/fbaAPI'

describe('FireZoneUnitInfo', () => {
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
    const fireZoneUnitDetails: FireShapeAreaDetail[] = [
      {
        fire_shape_id: 1,
        fire_shape_name: 'foo',
        fire_centre_name: 'fizz',
        combustible_area: 2,
        threshold: undefined,
        elevated_hfi_area: 100
      }
    ]
    const { getByTestId } = render(
      <FireZoneUnitInfo advisoryThreshold={20} fireZoneUnitName="foo" fireZoneUnitDetails={fireZoneUnitDetails} />
    )
    const fireZoneUnitInfoSwatch = getByTestId('fire-zone-unit-info-swatch')
    expect(fireZoneUnitInfoSwatch).toBeInTheDocument()
    expect(fireZoneUnitInfoSwatch).toHaveStyle(`background-color: ${LIGHT_GREY}`)
  })
  it('should render a LIGHT_GREY swatch when fireZoneUnitDetails values do not exceed advisoryThreshold', () => {
    const fireZoneUnitDetails: FireShapeAreaDetail[] = [
      {
        fire_shape_id: 1,
        fire_shape_name: 'foo',
        fire_centre_name: 'fizz',
        combustible_area: 100,
        threshold: 1,
        elevated_hfi_area: 2
      }
    ]
    const { getByTestId } = render(
      <FireZoneUnitInfo advisoryThreshold={20} fireZoneUnitName="foo" fireZoneUnitDetails={fireZoneUnitDetails} />
    )
    const fireZoneUnitInfoSwatch = getByTestId('fire-zone-unit-info-swatch')
    expect(fireZoneUnitInfoSwatch).toBeInTheDocument()
    expect(fireZoneUnitInfoSwatch).toHaveStyle(`background-color: ${LIGHT_GREY}`)
  })
  it('should render an ADVISORY_ORANGE_FILL swatch when fireZoneUnitDetails values do not exceed advisoryThreshold', () => {
    const fireZoneUnitDetails: FireShapeAreaDetail[] = [
      {
        fire_shape_id: 1,
        fire_shape_name: 'foo',
        fire_centre_name: 'fizz',
        combustible_area: 100,
        threshold: 1,
        elevated_hfi_area: 21
      }
    ]
    const { getByTestId } = render(
      <FireZoneUnitInfo advisoryThreshold={20} fireZoneUnitName="foo" fireZoneUnitDetails={fireZoneUnitDetails} />
    )
    const fireZoneUnitInfoSwatch = getByTestId('fire-zone-unit-info-swatch')
    expect(fireZoneUnitInfoSwatch).toBeInTheDocument()
    expect(fireZoneUnitInfoSwatch).toHaveStyle(`background-color: ${ADVISORY_ORANGE_FILL}`)
  })
  it('should render an ADVISORY_ORANGE_FILL swatch when fireZoneUnitDetails values exceed advisoryThreshold with one set of details', () => {
    const fireZoneUnitDetails: FireShapeAreaDetail[] = [
      {
        fire_shape_id: 1,
        fire_shape_name: 'foo',
        fire_centre_name: 'fizz',
        combustible_area: 100,
        threshold: 1,
        elevated_hfi_area: 21
      }
    ]
    const { getByTestId } = render(
      <FireZoneUnitInfo advisoryThreshold={20} fireZoneUnitName="foo" fireZoneUnitDetails={fireZoneUnitDetails} />
    )
    const fireZoneUnitInfoSwatch = getByTestId('fire-zone-unit-info-swatch')
    expect(fireZoneUnitInfoSwatch).toBeInTheDocument()
    expect(fireZoneUnitInfoSwatch).toHaveStyle(`background-color: ${ADVISORY_ORANGE_FILL}`)
  })
  it('should render an ADVISORY_ORANGE_FILL swatch when fireZoneUnitDetails values exceed advisoryThreshold with multiple details', () => {
    const fireZoneUnitDetails: FireShapeAreaDetail[] = [
      {
        fire_shape_id: 1,
        fire_shape_name: 'foo',
        fire_centre_name: 'fizz',
        combustible_area: 100,
        threshold: 1,
        elevated_hfi_area: 16
      },
      {
        fire_shape_id: 2,
        fire_shape_name: 'foo',
        fire_centre_name: 'fizz',
        combustible_area: 100,
        threshold: 2,
        elevated_hfi_area: 5
      }
    ]
    const { getByTestId } = render(
      <FireZoneUnitInfo advisoryThreshold={20} fireZoneUnitName="foo" fireZoneUnitDetails={fireZoneUnitDetails} />
    )
    const fireZoneUnitInfoSwatch = getByTestId('fire-zone-unit-info-swatch')
    expect(fireZoneUnitInfoSwatch).toBeInTheDocument()
    expect(fireZoneUnitInfoSwatch).toHaveStyle(`background-color: ${ADVISORY_ORANGE_FILL}`)
  })
  it('should render an ADVISORY_RED_FILL swatch when fireZoneUnitDetails threshold 2 value exceeds advisoryThreshold', () => {
    const fireZoneUnitDetails: FireShapeAreaDetail[] = [
      {
        fire_shape_id: 1,
        fire_shape_name: 'foo',
        fire_centre_name: 'fizz',
        combustible_area: 100,
        threshold: 1,
        elevated_hfi_area: 16
      },
      {
        fire_shape_id: 2,
        fire_shape_name: 'foo',
        fire_centre_name: 'fizz',
        combustible_area: 100,
        threshold: 2,
        elevated_hfi_area: 21
      }
    ]
    const { getByTestId } = render(
      <FireZoneUnitInfo advisoryThreshold={20} fireZoneUnitName="foo" fireZoneUnitDetails={fireZoneUnitDetails} />
    )
    const fireZoneUnitInfoSwatch = getByTestId('fire-zone-unit-info-swatch')
    expect(fireZoneUnitInfoSwatch).toBeInTheDocument()
    expect(fireZoneUnitInfoSwatch).toHaveStyle(`background-color: ${ADVISORY_RED_FILL}`)
  })
})
