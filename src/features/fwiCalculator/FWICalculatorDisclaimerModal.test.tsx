import React from 'react'
import { cleanup, fireEvent } from '@testing-library/react'

import { renderWithRedux } from 'utils/testUtils'
import { FWICalculatorDisclaimerModal } from 'features/fwiCalculator/FWICalculatorDisclaimerModal'

afterEach(cleanup)

it('renders Disclaimer modal', async () => {
  const { getByText, getByTestId, queryByTestId } = renderWithRedux(
    <FWICalculatorDisclaimerModal />
  )

  // Make sure the page is not rendered
  expect(queryByTestId('fwi-calculator-page')).not.toBeInTheDocument()

  expect(getByText(/Disclaimer/i)).toBeInTheDocument()

  // Click the accept disclaimer button
  fireEvent.click(getByTestId('disclaimer-accept-button'))

  // The page should be rendered after accepting
  expect(getByTestId('fwi-calculator-page')).toBeInTheDocument()
})
