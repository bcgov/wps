import { render, within, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { StationGroup } from 'api/stationAPI'
import StationGroupDropdown from 'features/moreCast2/components/StationGroupDropdown'
import React from 'react'
describe('StationGroupsDropdown', () => {
  const idir = 'testIdir'
  const stationGroups: StationGroup[] = [
    { id: '1', display_label: 'g1', group_description: '', group_owner_user_guid: '1', group_owner_user_id: idir },
    {
      id: '2',
      display_label: 'g2',
      group_description: '',
      group_owner_user_guid: '2',
      group_owner_user_id: 'anotherTestIdir'
    }
  ]

  it('should render with the default value', async () => {
    const setSelectedStationGroup = jest.fn()
    const { getByTestId } = render(
      <StationGroupDropdown
        idir={idir}
        stationGroupOptions={stationGroups}
        selectedStationGroup={undefined}
        setSelectedStationGroup={setSelectedStationGroup}
      />
    )
    const autocomplete = getByTestId('station-group-dropdown')
    const input = within(autocomplete).getByRole('combobox') as HTMLInputElement

    await waitFor(() => expect(input.value).toBe(''))
    await waitFor(() => expect(setSelectedStationGroup).toBeCalledTimes(0))
  })
  it('should change value on change and call parent callback', async () => {
    const setSelectedStationGroup = jest.fn()
    const { getByTestId } = render(
      <StationGroupDropdown
        idir={idir}
        stationGroupOptions={stationGroups}
        selectedStationGroup={undefined}
        setSelectedStationGroup={setSelectedStationGroup}
      />
    )
    const autocomplete = getByTestId('station-group-dropdown')
    const input = within(autocomplete).getByRole('combobox') as HTMLInputElement

    autocomplete.focus()
    await userEvent.type(autocomplete, '1')

    await waitFor(() => expect(input.value).toBe('1'))

    await userEvent.type(autocomplete, '{arrowdown}')
    await userEvent.type(autocomplete, '{enter}')
    await waitFor(() => expect(setSelectedStationGroup).toBeCalledTimes(1))
    await waitFor(() => expect(setSelectedStationGroup).toBeCalledWith(stationGroups[0]))
  })
  it('should show all groups', async () => {
    const setSelectedStationGroup = jest.fn()
    const { getByTestId, findAllByRole } = render(
      <StationGroupDropdown
        idir={idir}
        stationGroupOptions={stationGroups}
        selectedStationGroup={undefined}
        setSelectedStationGroup={setSelectedStationGroup}
      />
    )
    const autocomplete = getByTestId('station-group-dropdown')
    const open = within(autocomplete).getByLabelText('Open')

    autocomplete.focus()
    await userEvent.click(open)

    const options = await findAllByRole('option')
    await waitFor(() => expect(options).toHaveLength(2))

    const onlyMyGroupsCheckbox = getByTestId('only-my-groups')
    await userEvent.click(onlyMyGroupsCheckbox)

    autocomplete.focus()
    await userEvent.click(open)
    const myOptions = await findAllByRole('option')
    await waitFor(() => expect(myOptions).toHaveLength(2))
  })
})
