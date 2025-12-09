import React from 'react'
import { render } from '@testing-library/react'
import CriticalHours from '@/features/fba/components/viz/CriticalHours'

describe('CriticalHours', () => {
  it('should not render hours in 24 hour format', () => {
    const { getByTestId } = render(<CriticalHours start={8} end={11} />)

    const element = getByTestId('critical-hours')
    expect(element).toBeInTheDocument()
    expect(element).toHaveTextContent('8 - 11')
  })

  it('should render no critical hours', () => {
    const { getByTestId } = render(
        <CriticalHours start={undefined} end={undefined} />
    )

    const element = getByTestId('critical-hours')
    expect(element).toBeInTheDocument()
    expect(element).toHaveTextContent("-")
  })
})
