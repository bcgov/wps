import React from 'react'
import { cleanup, fireEvent } from '@testing-library/react'

import { renderWithRedux } from 'utils/testUtils'
import { PercentileCalculatorPageWithDisclaimer } from 'features/percentileCalculator/pages/PercentileCalculatorPageWithDisclaimer'

afterEach(cleanup)

it('renders Disclaimer modal', async () => {
  const { getByText, getByTestId, queryByTestId } = renderWithRedux(
    <PercentileCalculatorPageWithDisclaimer showDisclaimer />
  )

  // Make sure the page is not rendered
  expect(queryByTestId('percentile-calculator-page')).not.toBeInTheDocument()

  expect(getByText(/Disclaimer/i)).toBeInTheDocument()

  // Click the accept disclaimer button
  fireEvent.click(getByTestId('disclaimer-accept-button'))

  // The page should be rendered after accepting
  expect(getByTestId('percentile-calculator-page')).toBeInTheDocument()
})
