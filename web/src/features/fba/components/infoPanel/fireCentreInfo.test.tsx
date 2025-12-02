import { vi } from 'vitest'
import { render } from '@testing-library/react'
import FireCentreInfo from 'features/fba/components/infoPanel/FireCentreInfo'
import { FireShapeAreaDetail } from 'api/fbaAPI'
import { AdvisoryStatus } from '@/utils/constants'

describe('FireCentreInfo', () => {
  it('should render', () => {
    const { getByTestId } = render(
      <FireCentreInfo expanded={false} fireCentreName="foo" fireZoneUnitInfos={[]} onChangeExpanded={vi.fn()} />
    )
    const fireCentreInfo = getByTestId('fire-centre-info')
    expect(fireCentreInfo).toBeInTheDocument()
  })
  it('should render the fire centre name', () => {
    const { getByTestId } = render(
      <FireCentreInfo expanded={false} fireCentreName="foo" fireZoneUnitInfos={[]} onChangeExpanded={vi.fn()} />
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
        status: AdvisoryStatus.ADVISORY
      }
    ]
    const { getByTestId } = render(
      <FireCentreInfo
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
