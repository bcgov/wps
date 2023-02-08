import { render, within, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import FireStartsDropdown from 'features/hfiCalculator/components/FireStartsDropdown'
import { vi } from 'vitest'
import React from 'react'
describe('FireStartsDropdown', () => {
  const testAreaId = 1
  const dayOffset = 0
  const lowestFireStarts = { id: 1, label: '1' }
  const highestFireStarts = { id: 2, label: '2' }
  const fireStartRanges = [lowestFireStarts, highestFireStarts]

  it('should render with the default value', async () => {
    const setFireStartsMock = vi.fn()
    const { getByTestId } = render(
      <FireStartsDropdown
        fireStarts={lowestFireStarts}
        areaId={testAreaId}
        dayOffset={dayOffset}
        setFireStarts={setFireStartsMock}
        fireStartsEnabled={true}
        fireStartRanges={fireStartRanges}
      />
    )
    const autocomplete = getByTestId('fire-starts-dropdown')
    const input = within(autocomplete).getByRole('combobox') as HTMLInputElement

    await waitFor(() => expect(input.value).toBe(lowestFireStarts.label))
    await waitFor(() => expect(setFireStartsMock).toBeCalledTimes(0))
  })
  it('should change value on change and call parent callback', async () => {
    const setFireStartsMock = vi.fn()
    const { getByTestId } = render(
      <FireStartsDropdown
        fireStarts={lowestFireStarts}
        areaId={testAreaId}
        dayOffset={dayOffset}
        setFireStarts={setFireStartsMock}
        fireStartsEnabled={true}
        fireStartRanges={fireStartRanges}
      />
    )
    const autocomplete = getByTestId('fire-starts-dropdown')
    const input = within(autocomplete).getByRole('combobox') as HTMLInputElement

    autocomplete.focus()
    await userEvent.type(autocomplete, '2')

    await waitFor(() => expect(input.value).toBe('2'))

    await userEvent.type(autocomplete, '{enter}')
    await waitFor(() => expect(setFireStartsMock).toBeCalledTimes(1))
    await waitFor(() => expect(setFireStartsMock).toBeCalledWith(testAreaId, dayOffset, highestFireStarts))
  })
  it('should be disabled when fire starts are not enabled', async () => {
    const setFireStartsMock = vi.fn()
    const { getByTestId } = render(
      <FireStartsDropdown
        fireStarts={lowestFireStarts}
        areaId={testAreaId}
        dayOffset={dayOffset}
        setFireStarts={setFireStartsMock}
        fireStartsEnabled={false}
        fireStartRanges={fireStartRanges}
      />
    )
    const autocomplete = getByTestId('fire-starts-dropdown')
    const input = within(autocomplete).getByRole('combobox') as HTMLInputElement
    expect(input).toHaveAttribute('disabled')
  })
})
