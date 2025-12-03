import { render } from '@testing-library/react'
import FireZoneUnitInfo from 'features/fba/components/infoPanel/FireZoneUnitInfo'
import { ADVISORY_ORANGE_FILL, ADVISORY_RED_FILL } from 'features/fba/components/map/featureStylers'
import { TRANSPARENT_COLOUR } from 'app/theme'
import { FireShapeStatusDetail } from 'api/fbaAPI'
import { AdvisoryStatus } from '@/utils/constants'

const fireShapeAreaDetailA: FireShapeStatusDetail = {
  fire_shape_id: 1,
  fire_shape_name: 'foo',
  fire_centre_name: 'fizz',
  status: null
}
const fireShapeAreaDetailB: FireShapeStatusDetail = {
  fire_shape_id: 2,
  fire_shape_name: 'foo',
  fire_centre_name: 'fizz',
  status: null
}

describe('FireZoneUnitInfo', () => {
  beforeEach(() => {
    fireShapeAreaDetailA.status = null
    fireShapeAreaDetailB.status = null
  })
  it('should render', () => {
    const { getByTestId } = render(
      <FireZoneUnitInfo fireZoneUnitName="foo" fireZoneUnitDetails={fireShapeAreaDetailA} />
    )
    const fireZoneUnitInfo = getByTestId('fire-zone-unit-info')
    expect(fireZoneUnitInfo).toBeInTheDocument()
  })
  it('should render the fire zone unit name', () => {
    const { getByTestId } = render(
      <FireZoneUnitInfo fireZoneUnitName="foo" fireZoneUnitDetails={fireShapeAreaDetailA} />
    )
    const fireZoneUnitInfo = getByTestId('fire-zone-unit-info')
    expect(fireZoneUnitInfo).toHaveTextContent('foo')
  })
  it('should render a LIGHT_GREY swatch when fireZoneUnitDetails have no advisory status', () => {
    const { getByTestId } = render(
      <FireZoneUnitInfo fireZoneUnitName="foo" fireZoneUnitDetails={fireShapeAreaDetailA} />
    )
    const fireZoneUnitInfoSwatch = getByTestId('fire-zone-unit-info-swatch')
    expect(fireZoneUnitInfoSwatch).toBeInTheDocument()
    expect(fireZoneUnitInfoSwatch).toHaveStyle(`background-color: ${TRANSPARENT_COLOUR}`)
  })
  it('should render an ADVISORY_ORANGE_FILL swatch when fireZoneUnitDetails contain an advisory status', () => {
    fireShapeAreaDetailA.status = AdvisoryStatus.ADVISORY
    const { getByTestId } = render(
      <FireZoneUnitInfo fireZoneUnitName="foo" fireZoneUnitDetails={fireShapeAreaDetailA} />
    )
    const fireZoneUnitInfoSwatch = getByTestId('fire-zone-unit-info-swatch')
    expect(fireZoneUnitInfoSwatch).toBeInTheDocument()
    expect(fireZoneUnitInfoSwatch).toHaveStyle(`background-color: ${ADVISORY_ORANGE_FILL}`)
  })
  it('should render an ADVISORY_RED_FILL swatch when fireZoneUnitDetails contain a warning status', () => {
    fireShapeAreaDetailA.status = AdvisoryStatus.WARNING
    const { getByTestId } = render(
      <FireZoneUnitInfo fireZoneUnitName="foo" fireZoneUnitDetails={fireShapeAreaDetailA} />
    )
    const fireZoneUnitInfoSwatch = getByTestId('fire-zone-unit-info-swatch')
    expect(fireZoneUnitInfoSwatch).toBeInTheDocument()
    expect(fireZoneUnitInfoSwatch).toHaveStyle(`background-color: ${ADVISORY_RED_FILL}`)
  })
})
