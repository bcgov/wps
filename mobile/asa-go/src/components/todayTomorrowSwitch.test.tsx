import { act, fireEvent, render, screen } from '@testing-library/react'
import type { DateTime } from 'luxon'
import { Provider } from 'react-redux'
import { describe, expect, it } from 'vitest'
import { setDateOfInterest } from '@/slices/dateOfInterestSlice'
import { createTestStore } from '@/testUtils'
import { getToday } from '@/utils/dataSliceUtils'
import TodayTomorrowSwitch from './TodayTomorrowSwitch'

const renderSwitch = (date: DateTime) => {
  const dateKey = date.toISODate()!
  const store = createTestStore({ dateOfInterest: { dateKey } })
  render(
    <Provider store={store}>
      <TodayTomorrowSwitch />
    </Provider>
  )
  return store
}

describe('TodayTomorrowSwitch', () => {
  it('renders both buttons', () => {
    renderSwitch(getToday())

    expect(screen.getByText('NOW')).toBeInTheDocument()
    expect(screen.getByText('TMR')).toBeInTheDocument()
  })

  it('disables the NOW button when date is today', () => {
    renderSwitch(getToday())

    expect(screen.getByText('NOW').closest('button')).toBeDisabled()
    expect(screen.getByText('TMR').closest('button')).not.toBeDisabled()
  })

  it('disables the TMR button when date is tomorrow', () => {
    renderSwitch(getToday().plus({ days: 1 }))

    expect(screen.getByText('TMR').closest('button')).toBeDisabled()
    expect(screen.getByText('NOW').closest('button')).not.toBeDisabled()
  })

  it('clicking TMR updates the selected date to tomorrow', () => {
    const today = getToday()
    const store = renderSwitch(today)

    fireEvent.click(screen.getByText('TMR').closest('button')!)

    expect(store.getState().dateOfInterest.dateKey).toBe(today.plus({ days: 1 }).toISODate())
  })

  it('clicking NOW updates the selected date to today', () => {
    const today = getToday()
    const store = renderSwitch(today.plus({ days: 1 }))

    fireEvent.click(screen.getByText('NOW').closest('button')!)

    expect(store.getState().dateOfInterest.dateKey).toBe(today.toISODate())
  })

  it('clicking NOW from a stale date selects today instead of subtracting another day', () => {
    const today = getToday()
    const store = renderSwitch(today.minus({ days: 1 }))

    expect(screen.getByText('TMR').closest('button')).not.toBeDisabled()
    fireEvent.click(screen.getByText('NOW').closest('button')!)

    expect(store.getState().dateOfInterest.dateKey).toBe(today.toISODate())
  })

  it('updates when the selected date changes in the store', () => {
    const today = getToday()
    const store = renderSwitch(today)

    expect(screen.getByRole('button', { name: /NOW/i })).toBeDisabled()
    expect(screen.getByRole('button', { name: /TMR/i })).not.toBeDisabled()

    act(() => {
      store.dispatch(setDateOfInterest(today.plus({ days: 1 }).toISODate()!))
    })

    expect(screen.getByRole('button', { name: /NOW/i })).not.toBeDisabled()
    expect(screen.getByRole('button', { name: /TMR/i })).toBeDisabled()
  })
})
