import { render } from '@testing-library/react'
import HFIErrorAlert from 'features/hfiCalculator/components/HFIErrorAlert'
import { vi, describe, it, expect } from 'vitest'

describe('HFIErrorAlert', () => {
  it('should render an alert', () => {
    const { getByRole } = render(<HFIErrorAlert errors={['500 - no dailies', '500 - no fire centres']} />)
    const alertLink = getByRole('link')
    expect(alertLink).toBeDefined()
    expect(alertLink).toHaveAttribute(
      'href',
      'mailto:bcws.predictiveservices@gov.bc.ca?subject=Predictive Services Unit - HFI Error'
    )
  })
})
