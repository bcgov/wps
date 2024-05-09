import React from 'react'
import { render } from '@testing-library/react'
import FireCentreInfo from 'features/fba/components/infoPanel/FireCentreInfo'
import { FireShapeAreaDetail } from 'api/fbaAPI'

describe('FireCentreInfo', () => {
  it('should render', () => {
    const { getByTestId } = render(
      <FireCentreInfo advisoryThreshold={20} fireCentreName="foo" fireZoneUnitInfos={[]} />
    )
    const fireCentreInfo = getByTestId('fire-centre-info')
    expect(fireCentreInfo).toBeInTheDocument()
  })
  it('should render the fire centre name', () => {
    const { getByTestId } = render(
      <FireCentreInfo advisoryThreshold={20} fireCentreName="foo" fireZoneUnitInfos={[]} />
    )
    const fireCentreInfo = getByTestId('fire-centre-info')
    expect(fireCentreInfo).toBeInTheDocument()
    expect(fireCentreInfo).toHaveTextContent('foo')
  })
  it('should render fireZoneUnit children', () => {
    const fireShapeAreaDetails: FireShapeAreaDetail[] = [
      {
        fire_shape_id: 1,
        fire_shape_name: 'foo',
        fire_centre_name: 'fizz',
        combustible_area: 2,
        threshold: 1,
        elevated_hfi_area: 100,
        elevated_hfi_percentage: 0
      }
    ]
    const { getByTestId } = render(
      <FireCentreInfo advisoryThreshold={20} fireCentreName="foo" fireZoneUnitInfos={fireShapeAreaDetails} />
    )
    const fireZoneUnitInfo = getByTestId('fire-zone-unit-info')
    expect(fireZoneUnitInfo).toBeInTheDocument()
  })
})
