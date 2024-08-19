import { render } from '@testing-library/react'
import DateRangePickerWrapper from 'components/dateRangePicker/DateRangePickerWrapper'
import { DateRange } from 'components/dateRangePicker/types'
import { vi, describe, it, expect } from 'vitest'

const setup = (open: boolean, toggleMock: () => void, initialDateRange: DateRange, onChangeMock: () => void) => {
  const { getByTestId, getByRole } = render(
    <DateRangePickerWrapper
      open={open}
      toggle={toggleMock}
      initialDateRange={initialDateRange}
      onChange={onChangeMock}
    />
  )
  return { getByTestId, getByRole }
}
describe('DateRangePickerWrapper', () => {
  const startDate = new Date('2021/2/21')
  const endDate = new Date('2021/2/25')
  const toggleMock = vi.fn((): void => {
    /** no op */
  })
  const onChangeMock = vi.fn((): void => {
    /** no op */
  })

  beforeEach(() => {
    // Reset all mocks
    toggleMock.mockReset()
    onChangeMock.mockReset()
  })

  it('should render the date picker wrapper and children', () => {
    const dateRange = { startDate, endDate }
    const { getByTestId } = setup(true, toggleMock, dateRange, onChangeMock)
    const datePickerWrapper = getByTestId('date-range-picker-menu')

    expect(datePickerWrapper).toBeDefined()
    expect(toggleMock).toHaveBeenCalledTimes(0)
    expect(onChangeMock).toHaveBeenCalledTimes(0)
  })
})
