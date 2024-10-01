import InfoAccordion from 'features/fba/components/infoPanel/InfoAccordion'
import { render } from '@testing-library/react'
import { AdvisoryStatus } from '@/utils/constants'
import { ADVISORY_ORANGE_FILL, ADVISORY_RED_LINE } from '@/features/fba/components/map/featureStylers'

describe('InfoAccordion', () => {
  it('should render', () => {
    const { getByTestId } = render(
      <InfoAccordion defaultExpanded={false} title="foo">
        <div>fizz</div>
      </InfoAccordion>
    )
    const infoAccordion = getByTestId('info-accordion')
    expect(infoAccordion).toBeInTheDocument()
  })
  it('should render the title', () => {
    const { getByTestId } = render(
      <InfoAccordion defaultExpanded={false} title="foo">
        <div>fizz</div>
      </InfoAccordion>
    )
    const infoAccordionTitle = getByTestId('info-accordion-title')
    expect(infoAccordionTitle).toBeInTheDocument()
    expect(infoAccordionTitle).toHaveTextContent('foo')
  })
  it('should be collapsed when defaultExpanded is false', () => {
    const { getByTestId } = render(
      <InfoAccordion defaultExpanded={false} title="foo">
        <div data-testid="fizz">fizz</div>
      </InfoAccordion>
    )
    const infoAccordionDetails = getByTestId('info-accordion-details')
    expect(infoAccordionDetails).not.toBeVisible()
  })
  it('should be expanded when defaultExpanded is true', () => {
    const { getByTestId } = render(
      <InfoAccordion defaultExpanded={true} title="foo">
        <div data-testid="fizz">fizz</div>
      </InfoAccordion>
    )
    const infoAccordionDetails = getByTestId('info-accordion-details')
    expect(infoAccordionDetails).toBeVisible()
  })
  it('should render its children when defaultExpanded is true', () => {
    const { getByTestId } = render(
      <InfoAccordion defaultExpanded={true} title="foo">
        <div data-testid="fizz">fizz</div>
      </InfoAccordion>
    )
    const fizzDiv = getByTestId('fizz')
    expect(fizzDiv).toBeVisible()
  })
  it('should not render its children when defaultExpanded is false', () => {
    const { getByTestId } = render(
      <InfoAccordion defaultExpanded={false} title="foo">
        <div data-testid="fizz">fizz</div>
      </InfoAccordion>
    )
    const fizzDiv = getByTestId('fizz')
    expect(fizzDiv).not.toBeVisible()
  })
  it('should render a red advisory status bar if provided a Warning status', () => {
    const { getByTestId } = render(
      <InfoAccordion defaultExpanded={true} title="foo" advisoryStatus={AdvisoryStatus.WARNING}>
        <div data-testid="fizz">fizz</div>
      </InfoAccordion>
    )
    const statusBar = getByTestId('advisory-status-bar')
    expect(statusBar).toBeVisible()
    expect(statusBar).toHaveStyle(`
      background: repeating-linear-gradient(135deg, ${ADVISORY_RED_LINE} , ${ADVISORY_RED_LINE} 40px, white 40px, white 70px)
    `)
  })
  it('should render an orange advisory status bar if provided an Advisory status', () => {
    const { getByTestId } = render(
      <InfoAccordion defaultExpanded={true} title="foo" advisoryStatus={AdvisoryStatus.ADVISORY}>
        <div data-testid="fizz">fizz</div>
      </InfoAccordion>
    )
    const statusBar = getByTestId('advisory-status-bar')
    expect(statusBar).toBeVisible()
    expect(statusBar).toHaveStyle(`
      background: repeating-linear-gradient(135deg, ${ADVISORY_ORANGE_FILL} , ${ADVISORY_ORANGE_FILL} 40px, white 40px, white 70px)
    `)
  })
  it('should not render an advisory status bar if no status is provided or the status is undefined', () => {
    const { queryByTestId } = render(
      <InfoAccordion defaultExpanded={true} title="foo" advisoryStatus={undefined}>
        <div data-testid="fizz">fizz</div>
      </InfoAccordion>
    )
    const statusBar = queryByTestId('advisory-status-bar')
    expect(statusBar).not.toBeInTheDocument()
  })
})
