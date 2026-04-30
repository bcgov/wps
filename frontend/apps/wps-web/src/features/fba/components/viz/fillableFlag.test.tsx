import React from 'react'
import { render } from '@testing-library/react'
import FillableFlag from '@/features/fba/components/viz/FillableFlag'

describe('FillableFlag', () => {
  it('should render', () => {
    const maskId = 'test'
    const { getByRole } = render(<FillableFlag maskId={maskId} percent={50} />)
    const element = getByRole('img')
    expect(element).toBeInTheDocument()
  })
  it("should use maskId in svg mask element's id", () => {
    const maskId = 'test'
    const result = render(<FillableFlag maskId={maskId} percent={50} />)
    const element = result.container.querySelector(`#mask-${maskId}`)
    expect(element).toBeInTheDocument()
  })
})
