import { Box } from '@mui/material'
import type { GridRenderCellParams } from '@mui/x-data-grid-pro'
import { configureStore } from '@reduxjs/toolkit'
import { act, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type { StationGroupMember } from '@wps/api/stationAPI'
import { DataGridColumns } from 'features/moreCast2/components/DataGridColumns'
import StationNameCell from 'features/moreCast2/components/StationNameCell'
import type { ColumnClickHandlerProps } from 'features/moreCast2/components/TabbedDataGrid'
import type { MoreCast2Row } from 'features/moreCast2/interfaces'
import { createEmptyMoreCast2Row } from 'features/moreCast2/slices/dataSlice'
import selectedStationsReducer, { selectedStationsChanged } from 'features/moreCast2/slices/selectedStationsSlice'
import { DateTime } from 'luxon'
import { Provider } from 'react-redux'
import { vi } from 'vitest'

const station = (elevation?: number | null): StationGroupMember => ({
  id: 'station-1',
  station_code: 123,
  display_label: 'Current station label',
  station_status: 'ACTIVE',
  fire_centre: { id: 'centre', display_label: 'Centre' },
  fire_zone: { id: 'zone', display_label: 'Zone', fire_centre: 'centre' },
  elevation
})

const makeStore = (stations: StationGroupMember[]) =>
  configureStore({
    reducer: { selectedStations: selectedStationsReducer },
    preloadedState: { selectedStations: { selectedStations: stations } }
  })

describe('StationNameCell', () => {
  it.each([
    [625, '625 m'],
    [1250, '1,250 m'],
    [0, '0 m'],
    [-5, '-5 m'],
    [null, 'Unknown'],
    [undefined, 'Unknown'],
    [NaN, 'Unknown']
  ])('shows station elevation %s as %s in the tooltip only', async (elevation, expected) => {
    const user = userEvent.setup()
    render(
      <Provider store={makeStore([station(elevation)])}>
        <StationNameCell stationCode={123} stationName="Station name" />
      </Provider>
    )
    expect(screen.getByText('Station name')).toBeVisible()
    expect(screen.queryByText(expected)).not.toBeInTheDocument()
    expect(screen.queryByText(/^Station elevation:/)).not.toBeInTheDocument()
    await user.hover(screen.getByRole('button', { name: 'Station metadata for Station name' }))
    const tooltip = await screen.findByRole('tooltip')
    expect(within(tooltip).getByText(`Station elevation: ${expected}`)).toBeVisible()
  })

  it('only opens station metadata when hovering over the info icon', async () => {
    const user = userEvent.setup()
    render(
      <Provider store={makeStore([station(1250)])}>
        <StationNameCell stationCode={123} stationName="Station name" />
      </Provider>
    )
    const trigger = screen.getByRole('button', { name: 'Station metadata for Station name' })
    const stationName = screen.getByText('Station name')
    await user.hover(stationName)
    expect(screen.queryByRole('tooltip')).not.toBeInTheDocument()
    expect(stationName).not.toHaveAttribute('title')
    await user.hover(trigger)
    const tooltip = await screen.findByRole('tooltip')
    expect(trigger).toHaveAttribute('aria-describedby', tooltip.id)
    expect(within(tooltip).getByText('Station name')).toBeVisible()
    expect(within(tooltip).getByText('Station code: 123')).toBeVisible()
    expect(within(tooltip).getByText('Station elevation: 1,250 m')).toBeVisible()
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    await user.unhover(trigger)
    await waitFor(() => expect(screen.queryByRole('tooltip')).not.toBeInTheDocument())
    await user.hover(stationName)
    expect(screen.queryByRole('tooltip')).not.toBeInTheDocument()
  })

  it('shows unknown for a station without metadata rather than borrowing another station elevation', async () => {
    const user = userEvent.setup()
    render(
      <Provider store={makeStore([station(625)])}>
        <StationNameCell stationCode={456} stationName="Other station" />
      </Provider>
    )
    await user.hover(screen.getByRole('button', { name: 'Station metadata for Other station' }))
    const tooltip = await screen.findByRole('tooltip')
    expect(within(tooltip).getByText('Station code: 456')).toBeVisible()
    expect(within(tooltip).getByText('Station elevation: Unknown')).toBeVisible()
  })

  it('updates the open tooltip when metadata arrives and shows the full name for truncated cells', async () => {
    const user = userEvent.setup()
    const store = makeStore([])
    const name = 'A station name that is longer than the pinned column'
    render(
      <Provider store={store}>
        <StationNameCell stationCode={123} stationName={name} />
      </Provider>
    )
    const stationName = screen.getByText(name)
    expect(stationName).not.toHaveAttribute('title')
    expect(screen.queryByText('Unknown')).not.toBeInTheDocument()
    await user.hover(screen.getByRole('button', { name: `Station metadata for ${name}` }))
    const tooltip = await screen.findByRole('tooltip')
    expect(within(tooltip).getByText(name)).toBeVisible()
    expect(within(tooltip).getByText('Station elevation: Unknown')).toBeVisible()
    act(() => {
      store.dispatch(selectedStationsChanged([station(625)]))
    })
    expect(screen.queryByText('625 m')).not.toBeInTheDocument()
    expect(within(tooltip).getByText('Station elevation: 625 m')).toBeVisible()
  })

  it('opens with keyboard focus and closes with Escape while keeping focus on the icon', async () => {
    const user = userEvent.setup()
    render(
      <Provider store={makeStore([station(625)])}>
        <StationNameCell stationCode={123} stationName="Station name" hasFocus />
      </Provider>
    )
    const trigger = screen.getByRole('button', { name: 'Station metadata for Station name' })
    const matches = trigger.matches.bind(trigger)
    // jsdom does not track keyboard focus visibility
    const focusVisible = vi
      .spyOn(trigger, 'matches')
      .mockImplementation(selector =>
        selector === ':focus-visible' ? document.activeElement === trigger : matches(selector)
      )
    await user.tab()
    expect(trigger).toHaveFocus()
    const tooltip = await screen.findByRole('tooltip')
    expect(trigger).toHaveAttribute('aria-describedby', tooltip.id)
    expect(within(tooltip).getByText('Station code: 123')).toBeVisible()
    expect(within(tooltip).getByText('Station elevation: 625 m')).toBeVisible()
    await user.keyboard('{Escape}')
    await waitFor(() => expect(screen.queryByRole('tooltip')).not.toBeInTheDocument())
    expect(trigger).toHaveFocus()
    focusVisible.mockRestore()
  })

  it.each(['click', '{Enter}', ' '])('keeps %s activation from reaching grid handlers', async activation => {
    const user = userEvent.setup()
    const gridClick = vi.fn()
    const gridKeyDown = vi.fn()
    const gridDoubleClick = vi.fn()
    render(
      <Provider store={makeStore([station(625)])}>
        <Box role="gridcell" tabIndex={-1} onClick={gridClick} onKeyDown={gridKeyDown} onDoubleClick={gridDoubleClick}>
          <StationNameCell stationCode={123} stationName="Station name" hasFocus />
        </Box>
      </Provider>
    )
    const trigger = screen.getByRole('button', { name: 'Station metadata for Station name' })
    await user.hover(trigger)
    const tooltip = await screen.findByRole('tooltip')
    if (activation === 'click') {
      await user.click(trigger)
    } else {
      await user.tab()
      gridKeyDown.mockClear()
      await user.keyboard(activation)
    }
    await user.dblClick(within(tooltip).getByText('Station code: 123'))
    expect(gridClick).not.toHaveBeenCalled()
    expect(gridKeyDown).not.toHaveBeenCalled()
    expect(gridDoubleClick).not.toHaveBeenCalled()
  })

  it('keeps inactive station cells out of the tab order', () => {
    const { rerender } = render(
      <Provider store={makeStore([station(625)])}>
        <StationNameCell stationCode={123} stationName="Station name" />
      </Provider>
    )
    const trigger = screen.getByRole('button', { name: 'Station metadata for Station name' })
    expect(trigger).toHaveAttribute('tabindex', '-1')
    rerender(
      <Provider store={makeStore([station(625)])}>
        <StationNameCell stationCode={123} stationName="Station name" hasFocus />
      </Provider>
    )
    expect(trigger).toHaveAttribute('tabindex', '0')
  })

  it.each([
    ['forecast grid', DataGridColumns.getTabColumns],
    ['forecast summary', DataGridColumns.getSummaryColumns]
  ])('uses current station metadata for a restored row in the %s', async (_, columnsForGrid) => {
    const user = userEvent.setup()
    const store = makeStore([station(1250)])
    const restoredRow = {
      ...createEmptyMoreCast2Row('draft', 123, 'Saved station name', DateTime.utc(2026, 11, 11), 49, -123),
      stationElevation: 100
    }
    const before = JSON.stringify(restoredRow)
    const props: ColumnClickHandlerProps = {
      colDef: null,
      contextMenu: null,
      updateColumnWithModel: vi.fn(),
      handleClose: vi.fn()
    }
    const column = columnsForGrid(props).find(column => column.field === 'stationName')
    expect(column?.width).toBe(200)
    render(
      <Provider store={store}>
        {column?.renderCell?.({
          row: restoredRow,
          value: restoredRow.stationName,
          hasFocus: true
        } as unknown as GridRenderCellParams<MoreCast2Row, string>)}
      </Provider>
    )
    expect(screen.getByText('Saved station name')).toBeVisible()
    expect(screen.queryByText('1,250 m')).not.toBeInTheDocument()
    const trigger = screen.getByRole('button', { name: 'Station metadata for Saved station name' })
    expect(trigger).toHaveAttribute('tabindex', '0')
    await user.hover(trigger)
    const tooltip = await screen.findByRole('tooltip')
    expect(within(tooltip).getByText('Station code: 123')).toBeVisible()
    expect(within(tooltip).getByText('Station elevation: 1,250 m')).toBeVisible()
    act(() => {
      store.dispatch(selectedStationsChanged([station(900)]))
    })
    expect(screen.queryByText('900 m')).not.toBeInTheDocument()
    expect(within(tooltip).getByText('Station elevation: 900 m')).toBeVisible()
    expect(JSON.stringify(restoredRow)).toBe(before)
  })
})
