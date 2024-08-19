import { vi, describe, it, expect } from 'vitest'
import InfoPanel from 'features/fba/components/infoPanel/InfoPanel'
import { render } from '@testing-library/react'

describe('InfoPanel', () => {
  it('should render', () => {
    const { getByTestId } = render(
      <InfoPanel>
        <div id="test-div">Test div</div>
      </InfoPanel>
    )
    const infoPanelComponent = getByTestId('info-panel')
    expect(infoPanelComponent).toBeInTheDocument()
  })
  it('should render its children', () => {
    const { getByText } = render(
      <InfoPanel>
        <div id="test-div">Test div</div>
      </InfoPanel>
    )

    const testDiv = getByText('Test div')
    expect(testDiv).toBeDefined
  })
})
