import type { DataGridProProps } from '@mui/x-data-grid-pro'
import { configureStore } from '@reduxjs/toolkit'
import { render, screen, waitFor, within } from '@testing-library/react'
import { userEvent } from '@testing-library/user-event'
import { ModelChoice } from '@wps/api/moreCast2API'
import rootReducer from 'app/rootReducer'
import { DateTime } from 'luxon'
import { Provider } from 'react-redux'
import { vi } from 'vitest'
import { createEmptyMoreCast2Row } from '../slices/dataSlice'
import { DataGridColumns } from './DataGridColumns'
import ForecastSummaryDataGrid from './ForecastSummaryDataGrid'

vi.mock('@mui/x-data-grid-pro', async importOriginal => {
  const actual = await importOriginal<typeof import('@mui/x-data-grid-pro')>()
  return {
    ...actual,
    DataGridPro: (props: DataGridProProps) => <actual.DataGridPro {...props} disableVirtualization />
  }
})

const forecastRow = () => ({
  ...createEmptyMoreCast2Row('station-1', 1, 'Test station', DateTime.utc(2030, 7, 4, 20), 50, -120),
  tempForecast: { choice: ModelChoice.MANUAL, value: 22 },
  rhForecast: { choice: ModelChoice.MANUAL, value: 40 },
  ffmcCalcForecast: { choice: ModelChoice.MANUAL, value: 85 }
})

const renderSummary = (row = forecastRow()) => {
  const store = configureStore({ reducer: rootReducer })
  const props = {
    loading: false,
    rows: [row],
    columnClickHandlerProps: {
      colDef: { field: 'tempForecast' },
      contextMenu: null,
      updateColumnWithModel: vi.fn(),
      handleClose: vi.fn()
    },
    handleColumnHeaderClick: vi.fn(),
    processRowUpdate: vi.fn(updated => updated)
  }
  const result = render(<ForecastSummaryDataGrid {...props} />, {
    wrapper: ({ children }) => <Provider store={store}>{children}</Provider>
  })
  return { ...result, props }
}

const cell = (field: string): HTMLElement =>
  screen.getByRole('row', { name: /Test station/ }).querySelector<HTMLElement>(`[data-field="${field}"]`)!

describe('Forecast Summary grid', () => {
  afterEach(() => vi.restoreAllMocks())

  it('reuses columns when rows change and uses new column actions when supplied', async () => {
    const columns = vi.spyOn(DataGridColumns, 'getSummaryColumns')
    const { rerender, props } = renderSummary()
    expect(within(cell('tempForecast')).getByRole('textbox')).toHaveValue('22')
    rerender(
      <ForecastSummaryDataGrid
        {...props}
        rows={[{ ...props.rows[0], tempForecast: { choice: ModelChoice.MANUAL, value: 25 } }]}
      />
    )
    expect(within(cell('tempForecast')).getByRole('textbox')).toHaveValue('25')
    expect(columns).toHaveBeenCalledTimes(1)

    const updateColumnWithModel = vi.fn()
    rerender(
      <ForecastSummaryDataGrid
        {...props}
        columnClickHandlerProps={{ ...props.columnClickHandlerProps, updateColumnWithModel }}
      />
    )
    await userEvent.click(screen.getByTestId('tempForecast-column-header'))
    await userEvent.click(screen.getByTestId('apply-model-to-column-button'))
    expect(updateColumnWithModel).toHaveBeenCalledWith(ModelChoice.HRDPS, props.columnClickHandlerProps.colDef)
    expect(props.columnClickHandlerProps.updateColumnWithModel).not.toHaveBeenCalled()
    expect(columns).toHaveBeenCalledTimes(2)
  })

  it('validates forecast edits and keeps calculated indices read only', async () => {
    const { props } = renderSummary()
    await userEvent.dblClick(cell('ffmcCalcForecast'))
    expect(screen.queryByRole('spinbutton')).not.toBeInTheDocument()
    expect(props.processRowUpdate).not.toHaveBeenCalled()

    await userEvent.dblClick(cell('rhForecast'))
    const input = screen.getByRole('spinbutton')
    await userEvent.clear(input)
    await userEvent.type(input, '101{Enter}')
    expect(await screen.findByRole('tooltip')).toHaveTextContent('RH must be between 1 and 100')
    expect(props.processRowUpdate).not.toHaveBeenCalled()

    await userEvent.clear(input)
    await userEvent.type(input, '55{Enter}')
    await waitFor(() => expect(props.processRowUpdate).toHaveBeenCalled())
    expect(props.processRowUpdate.mock.calls.at(-1)?.[0].rhForecast.value).toBe(55)
    expect(within(cell('rhForecast')).getByRole('textbox')).toHaveValue('55')
  })

  it.each(['actual', 'past'])('disables forecast inputs for %s data', kind => {
    const row = forecastRow()
    if (kind === 'actual') row.tempActual = 18
    else row.forDate = DateTime.utc(2000, 1, 1, 20)
    renderSummary(row)
    expect(within(cell('tempForecast')).getByRole('textbox')).toBeDisabled()
  })
})
