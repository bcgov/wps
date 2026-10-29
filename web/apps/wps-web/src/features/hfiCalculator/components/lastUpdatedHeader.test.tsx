import { render } from '@testing-library/react'
import LastUpdatedHeader from 'features/hfiCalculator/components/LastUpdatedHeader'
import { buildStationDaily } from 'features/hfiCalculator/components/testHelpers'
import { DateTime } from 'luxon'

describe('LastUpdatedHeader', () => {
  const buildDaily = (status: string, lastUpdated: string) => ({
    ...buildStationDaily(1),
    status,
    last_updated: DateTime.fromISO(lastUpdated, { zone: 'utc' })
  })

  it('should show the latest forecast update in BC Pacific time', () => {
    const dailies = [
      buildDaily('FORECAST', '2026-11-02T18:00:00Z'),
      buildDaily('FORECAST', '2026-11-02T20:30:00Z'),
      buildDaily('ACTUAL', '2026-11-02T22:00:00Z')
    ]
    const { getByText } = render(<LastUpdatedHeader dailies={dailies} />)
    expect(getByText('Forecast last updated November 2, 13:30 PCT')).toBeDefined()
  })

  it('should render nothing without any forecasts', () => {
    const { container } = render(<LastUpdatedHeader dailies={[buildDaily('ACTUAL', '2026-11-02T22:00:00Z')]} />)
    expect(container.textContent).toEqual('')
  })
})
