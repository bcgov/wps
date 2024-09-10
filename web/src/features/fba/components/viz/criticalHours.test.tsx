import React from 'react'
import { render } from '@testing-library/react'
import CriticalHours from '@/features/fba/components/viz/CriticalHours'

describe('CriticalHours', () => {
  it('should render hours in 24 hour format', () => {
    const { getByTestId } = render(
        <CriticalHours start={8.0} end={11.0} />
    )

    const element = getByTestId('critical-hours')
    expect(element).toBeInTheDocument()
    expect(element).toHaveTextContent("8:00 - 11:00")
  })
})
