import type { DataGridProProps } from '@mui/x-data-grid-pro'
import { configureStore } from '@reduxjs/toolkit'
import { act, render, screen, waitFor, within } from '@testing-library/react'
import { userEvent } from '@testing-library/user-event'
import { ModelChoice } from '@wps/api/moreCast2API'
import rootReducer from 'app/rootReducer'
import { DateTime } from 'luxon'
import { Provider } from 'react-redux'
import { vi } from 'vitest'
import type { ModelElevationData } from '../modelElevation'
import { createEmptyMoreCast2Row } from '../slices/dataSlice'
import { DataGridColumns } from './DataGridColumns'
import ForecastDataGrid, { type ForecastDataGridProps } from './ForecastDataGrid'

vi.mock('@mui/x-data-grid-pro', async importOriginal => {
  const actual = await importOriginal<typeof import('@mui/x-data-grid-pro')>()
  return {
    ...actual,
    DataGridPro: (props: DataGridProProps) => <actual.DataGridPro {...props} disableVirtualization />
  }
})

const renderGrid = () => {
  const store = configureStore({ reducer: rootReducer })
  const columnClickHandlerProps = {
    colDef: null,
    contextMenu: null,
    updateColumnWithModel: vi.fn(),
    handleClose: vi.fn()
  }
  const data: ModelElevationData = {
    latestRuns: { HRDPS: DateTime.utc(2030, 7, 4) },
    stationElevations: new Map([
      [1, { stationElevation: 900, modelElevations: { HRDPS: 850.4, ECMWF: 1100 } }],
      [2, { stationElevation: 1200, modelElevations: { HRDPS: 1000 } }]
    ])
  }
  const props: ForecastDataGridProps = {
    loading: false,
    columnClickHandlerProps,
    columnVisibilityModel: DataGridColumns.initGridColumnVisibilityModel(columnClickHandlerProps),
    setColumnVisibilityModel: vi.fn(),
    onCellDoubleClickHandler: vi.fn(),
    handleColumnHeaderClick: vi.fn(),
    columnGroupingModel: [],
    allMoreCast2Rows: ['Alpha station', 'Beta station'].map((name, index) => ({
      ...createEmptyMoreCast2Row(`station-${index + 1}`, index + 1, name, DateTime.utc(2030, 7, 4, 20), 50, -120),
      tempHRDPS: 20,
      tempForecast: { choice: ModelChoice.MANUAL, value: 22 }
    })),
    collapsedStationCodes: new Set(),
    onStationExpansionChange: vi.fn(),
    modelElevationData: data,
    processRowUpdate: vi.fn(row => row)
  }
  return {
    props,
    ...render(<ForecastDataGrid {...props} />, {
      wrapper: ({ children }) => <Provider store={store}>{children}</Provider>
    })
  }
}

describe('station elevation comparison', () => {
  afterEach(() => vi.restoreAllMocks())

  it('opens the selected station without changing forecasts, expansion, or columns', async () => {
    const { props } = renderGrid()
    const columns = vi.spyOn(DataGridColumns, 'getTabColumns')
    const button = screen.getByRole('button', { name: 'Compare model elevations for Beta station' })
    const header = button.closest<HTMLElement>('[role="row"]')!
    const draft = localStorage.getItem('morecastForecastDraft')
    expect(header).toHaveAttribute('aria-expanded', 'true')
    await userEvent.click(button)
    const dialog = screen.getByRole('dialog', { name: 'Model elevations for Beta station' })
    expect(within(dialog).getByText('Station elevation: 1,200 m')).toBeInTheDocument()
    expect(within(dialog).getByText('-200 m')).toBeInTheDocument()
    await userEvent.click(within(dialog).getByRole('button', { name: 'Close' }))
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
    expect(header).toHaveAttribute('aria-expanded', 'true')
    expect(header).not.toHaveClass('Mui-selected')
    expect(props.processRowUpdate).not.toHaveBeenCalled()
    expect(props.onCellDoubleClickHandler).not.toHaveBeenCalled()
    expect(props.onStationExpansionChange).not.toHaveBeenCalled()
    expect(localStorage.getItem('morecastForecastDraft')).toBe(draft)
    expect(columns).not.toHaveBeenCalled()
  })

  it('supports keyboard activation, the tooltip, and Escape without collapsing the station', async () => {
    renderGrid()
    const button = screen.getByRole('button', { name: 'Compare model elevations for Alpha station' })
    await userEvent.hover(button)
    expect(await screen.findByRole('tooltip')).toHaveTextContent('Compare model elevations')
    act(() => button.focus())
    await userEvent.keyboard(' ')
    expect(screen.getByRole('dialog', { name: 'Model elevations for Alpha station' })).toBeInTheDocument()
    await userEvent.keyboard('{Escape}')
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
    expect(button.closest('[role="row"]')).toHaveAttribute('aria-expanded', 'true')
  })

  it('refreshes the open chart from current grid elevations', async () => {
    const { props, rerender } = renderGrid()
    await userEvent.click(screen.getByRole('button', { name: 'Compare model elevations for Alpha station' }))
    rerender(
      <ForecastDataGrid
        {...props}
        modelElevationData={{
          ...props.modelElevationData,
          stationElevations: new Map([[1, { stationElevation: 900, modelElevations: { HRDPS: 1120 } }]])
        }}
      />
    )
    const dialog = screen.getByRole('dialog')
    expect(within(dialog).getByText('1,120 m')).toBeInTheDocument()
    expect(within(dialog).getByText('+220 m')).toBeInTheDocument()
  })

  it('closes when the station is removed and stays closed if it is added again', async () => {
    const { props, rerender } = renderGrid()
    await userEvent.click(screen.getByRole('button', { name: 'Compare model elevations for Alpha station' }))
    rerender(<ForecastDataGrid {...props} allMoreCast2Rows={props.allMoreCast2Rows.slice(1)} />)
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
    rerender(<ForecastDataGrid {...props} />)
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })
})
