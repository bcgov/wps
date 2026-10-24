import { render, screen } from '@testing-library/react'
import { userEvent } from '@testing-library/user-event'
import { vi } from 'vitest'
import ForecastPublishResultDialog from './ForecastPublishResultDialog'

describe('ForecastPublishResultDialog', () => {
  test.each([0, 1])('shows counts and skipped station details with %i forecasts published', async publishedCount => {
    const onClose = vi.fn()
    render(
      <ForecastPublishResultDialog
        result={{
          savedCount: publishedCount + 1,
          publishedCount,
          skipped: [{ station_code: 123, station_name: 'Test station', for_date: 1720123200000 }]
        }}
        onClose={onClose}
      />
    )
    const savedMessage = publishedCount === 0 ? 'Saved 1 forecast in MoreCast.' : 'Saved 2 forecasts in MoreCast.'
    expect(screen.getByText(new RegExp(savedMessage))).toHaveTextContent(`Published ${publishedCount} to WF1.`)
    expect(screen.getByRole('table')).toHaveTextContent('Test station')
    expect(screen.getByRole('table')).toHaveTextContent('123')
    expect(screen.getByRole('table')).toHaveTextContent('2024-07-04')
    expect(
      screen.getByText('WF1 already has actuals for the rows below. These forecasts were saved only in MoreCast.')
    ).toBeVisible()
    await userEvent.click(screen.getByRole('button', { name: 'Close' }))
    expect(onClose).toHaveBeenCalledTimes(1)
  })
})
