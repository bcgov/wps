import { render } from '@testing-library/react'
import FBATable from 'features/fbaCalculator/components/FBATable'
import React from 'react'

describe('FBAProgressRow', () => {
  it('should render height with height and width properties set', () => {
    const maxWidth = 1000
    const maxHeight = 1000
    const minHeight = 500

    const { getByTestId } = render(
      <FBATable
        testId={'test-table'}
        maxWidth={maxWidth}
        maxHeight={maxHeight}
        minHeight={minHeight}
      />
    )
    expect(getByTestId('test-table')).toHaveStyle({
      maxWidth: maxWidth,
      maxHeight: maxHeight,
      minHeight: minHeight
    })
  })
})
