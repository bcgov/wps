import { vi, describe, it, expect } from 'vitest'
import InfoAccordion from 'features/fba/components/infoPanel/InfoAccordion'
import { render } from '@testing-library/react'

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
})
