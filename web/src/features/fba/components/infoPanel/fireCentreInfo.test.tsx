import { vi, describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import FireCentreInfo from 'features/fba/components/infoPanel/FireCentreInfo'
import { FireShapeAreaDetail } from 'api/fbaAPI'
import { vi } from 'vitest'
describe('FireCentreInfo', () => {
  it('should render', () => {
    const { getByTestId } = render(
      <FireCentreInfo
        advisoryThreshold={20}
        expanded={false}
        fireCentreName="foo"
        fireZoneUnitInfos={[]}
        onChangeExpanded={vi.fn()}
      />
    )
    const fireCentreInfo = getByTestId('fire-centre-info')
    expect(fireCentreInfo).toBeInTheDocument()
  })
  it('should render the fire centre name', () => {
    const { getByTestId } = render(
      <FireCentreInfo
        advisoryThreshold={20}
        expanded={false}
        fireCentreName="foo"
        fireZoneUnitInfos={[]}
        onChangeExpanded={vi.fn()}
      />
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
      <FireCentreInfo
        advisoryThreshold={20}
        expanded={true}
        fireCentreName="foo"
        fireZoneUnitInfos={fireShapeAreaDetails}
        onChangeExpanded={vi.fn()}
      />
    )
    const fireZoneUnitInfo = getByTestId('fire-zone-unit-info')
    expect(fireZoneUnitInfo).toBeInTheDocument()
  })
})
