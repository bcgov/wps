import { fireEvent, render, waitFor, within } from '@testing-library/react'
import { MARKERS } from 'components/dateRangePicker/DateRangePicker'
import Month from 'components/dateRangePicker/Month'
import { DateRange, NavigationAction } from 'components/dateRangePicker/types'
import React from 'react'

const setup = (
  value: Date,
  setValueStub: (date: Date) => void,
  dateRange: DateRange,
  minDate: Date,
  maxDate: Date,
  inHoverRangeStub: (date: Date) => boolean,
  onDayClickStub: (date: Date) => void,
  onDayHoverStub: (date: Date) => void,
  onMonthNavigateStub: (marker: symbol, action: NavigationAction) => void
) => {
  const { getByTestId, getByRole } = render(
    <Month
      testId="testMonth"
      value={value}
      marker={MARKERS.FIRST_MONTH}
      dateRange={dateRange}
      minDate={minDate}
      maxDate={maxDate}
      navState={[true, true]}
      setValue={setValueStub}
      helpers={{
        inHoverRange: inHoverRangeStub
      }}
      handlers={{
        onDayClick: onDayClickStub,
        onDayHover: onDayHoverStub,
        onMonthNavigate: onMonthNavigateStub
      }}
    />
  )
  return { getByTestId, getByRole }
}
describe('Month', () => {
  const startDate = new Date('2021/2/21')
  const endDate = new Date('2021/2/25')
  const setValueStub = jest.fn((date: Date): void => {
    /** no op */
  })
  const inHoverRangeStub = jest.fn((date: Date): boolean => {
    return false
  })
  const onDayClickStub = jest.fn((date: Date): void => {
    /** no op */
  })
  const onDayHover = jest.fn((date: Date): void => {
    /** no op */
  })
  const onMonthNavigate = jest.fn((marker: symbol, action: NavigationAction): void => {
    /** no op */
  })

  it('should render the month', () => {
    const dateRange = { startDate, endDate }
    const { getByTestId } = setup(
      startDate,
      setValueStub,
      dateRange,
      startDate,
      endDate,
      inHoverRangeStub,
      onDayClickStub,
      onDayHover,
      onMonthNavigate
    )
    const month = getByTestId('testMonth')

    expect(month).toBeDefined()
    expect(setValueStub).toBeCalledTimes(0)
    expect(onDayClickStub).toBeCalledTimes(0)
    expect(onDayHover).toBeCalledTimes(0)
    expect(onMonthNavigate).toBeCalledTimes(0)
  })
  it('should render the month', () => {
    const dateRange = { startDate, endDate }
    const { getByTestId } = setup(
      startDate,
      setValueStub,
      dateRange,
      startDate,
      endDate,
      inHoverRangeStub,
      onDayClickStub,
      onDayHover,
      onMonthNavigate
    )
    const month = getByTestId('testMonth')

    expect(month).toBeDefined()
    expect(setValueStub).toBeCalledTimes(0)
    expect(onDayClickStub).toBeCalledTimes(0)
    expect(onDayHover).toBeCalledTimes(0)
    expect(onMonthNavigate).toBeCalledTimes(0)
  })
  it('should handle day clicks', async () => {
    const dateRange = { startDate, endDate }
    const { getByTestId } = setup(
      startDate,
      setValueStub,
      dateRange,
      startDate,
      endDate,
      inHoverRangeStub,
      onDayClickStub,
      onDayHover,
      onMonthNavigate
    )
    const startDay = getByTestId(`day-${startDate.toISOString()}`)

    expect(startDay.className).toMatch(/makeStyles-buttonContainer-/)
    const startDayButton = within(startDay).getByRole('button') as HTMLInputElement

    startDayButton.focus()
    fireEvent.click(startDayButton)
    await waitFor(() => expect(onDayClickStub).toBeCalledTimes(1))

    const endDay = getByTestId(`day-${endDate.toISOString()}`)

    const endDayButton = within(endDay).getByRole('button') as HTMLInputElement
    endDayButton.focus()

    fireEvent.click(endDayButton)
    await waitFor(() => expect(onDayClickStub).toBeCalledTimes(2))

    expect(onDayHover).toBeCalledTimes(0)
    expect(onMonthNavigate).toBeCalledTimes(0)
  })
  it('should disable day buttons outside of 7 day range', async () => {
    const dateRange = { startDate: new Date('2021/2/1'), endDate: new Date('2021/2/7') }
    const dateOutOfRange = new Date('2021/2/8')
    const { getByTestId } = setup(
      startDate,
      setValueStub,
      dateRange,
      dateRange.startDate,
      dateRange.endDate,
      inHoverRangeStub,
      onDayClickStub,
      onDayHover,
      onMonthNavigate
    )
    const dayOutOfRange = getByTestId(`day-${dateOutOfRange.toISOString()}`)
    const outOfRangeButton = within(dayOutOfRange).getByRole('button') as HTMLInputElement

    expect(outOfRangeButton).toBeDisabled()
    expect(outOfRangeButton.className).toMatch(/Mui-disabled/)
  })
})
