import AdvisoryReport from 'features/fba/components/infoPanel/AdvisoryReport'
import { render } from '@testing-library/react'
import { DateTime } from 'luxon'
import { FireCenter } from 'api/fbaAPI'

import { Provider } from 'react-redux'
import { createTestStore } from '@/test/testUtils'

const issueDate = DateTime.now()
const forDate = DateTime.now()

const mockFireCenter: FireCenter = {
  id: 1,
  name: 'Fire Center 1',
  stations: []
}

describe('AdvisoryReport', () => {
  const testStore = createTestStore()
  it('should render', () => {
    const { getByTestId } = render(
      <Provider store={testStore}>
        <AdvisoryReport issueDate={issueDate} forDate={forDate} selectedFireCenter={mockFireCenter} />
      </Provider>
    )
    const advisoryReport = getByTestId('advisory-report')
    expect(advisoryReport).toBeInTheDocument()
  })
  it('should render advisoryText as children', () => {
    const { getByTestId } = render(
      <Provider store={testStore}>
        <AdvisoryReport issueDate={issueDate} forDate={forDate} selectedFireCenter={mockFireCenter} />
      </Provider>
    )
    const advisoryText = getByTestId('advisory-text')
    expect(advisoryText).toBeInTheDocument()
  })
})
