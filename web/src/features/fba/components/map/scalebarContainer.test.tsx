
import { render } from '@testing-library/react'
import ScalebarContainer from 'features/fba/components/map/ScaleBarContainer'
import React from 'react'

describe('ScalebarContainer', () => {
  it('should render', () => {
    const ref = React.createRef<HTMLElement | null>()
    const { getByTestId } = render(<ScalebarContainer ref={ref} />)
    const scalebarContainer = getByTestId('scalebar-container')
    expect(scalebarContainer).toBeVisible()
  })
})
