import React from 'react'
import { render } from '@testing-library/react'
import ElevationFlag from 'features/fba/components/viz/ElevationFlag'

describe('ElevationFlag', () => {
  it('should have width relative to parent', () => {
    const { getByTestId } = render(
        <ElevationFlag percent={50} testId='valley-bottom' />
    )

    const element = getByTestId('valley-bottom')
    expect(element).toBeInTheDocument()
    expect(element).toHaveTextContent("50%")
  })
})
