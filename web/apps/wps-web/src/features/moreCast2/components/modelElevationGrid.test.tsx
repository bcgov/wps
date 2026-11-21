import type { DataGridProProps } from '@mui/x-data-grid-pro'
import { configureStore } from '@reduxjs/toolkit'
import { act, render, screen, waitFor, within } from '@testing-library/react'
import { userEvent } from '@testing-library/user-event'
import { WeatherDeterminate, type WeatherIndeterminate } from '@wps/api/moreCast2API'
import rootReducer, { type RootState } from 'app/rootReducer'
import { useMemo } from 'react'
import { Provider, useSelector } from 'react-redux'
import { vi } from 'vitest'
import { MorecastDraftForecast } from '../forecastDraft'
import * as modelElevation from '../modelElevation'
import { getWeatherIndeterminatesSuccess, selectAllMoreCast2Rows } from '../slices/dataSlice'
import { selectedStationsChanged, selectSelectedStations } from '../slices/selectedStationsSlice'
import { DataGridColumns } from './DataGridColumns'
import TabbedDataGrid from './TabbedDataGrid'

vi.mock('@mui/x-data-grid-pro', async importOriginal => {
  const actual = await importOriginal<typeof import('@mui/x-data-grid-pro')>()
  return {
    ...actual,
    DataGridPro: (props: DataGridProProps) => <actual.DataGridPro {...props} disableVirtualization />
  }
})

const prediction: WeatherIndeterminate = {
  id: '1',
  station_code: 1,
  station_name: 'Alpha station',
  determinate: WeatherDeterminate.HRDPS,
  utc_timestamp: '2030-07-04T20:00:00Z',
  prediction_run_timestamp: '2030-07-04T00:00:00Z',
  model_elevation: 850.4,
  latitude: 50,
  longitude: -120,
  temperature: 20,
  relative_humidity: 40,
  precipitation: 0,
  wind_speed: 10,
  wind_direction: 180,
  grass_curing: null,
  fine_fuel_moisture_code: null,
  duff_moisture_code: null,
  drought_code: null,
  initial_spread_index: null,
  build_up_index: null,
  fire_weather_index: null,
  danger_rating: null
}

const stations = [
  { id: '1', station_code: 1, display_label: 'Alpha station', elevation: 900 },
  { id: '2', station_code: 2, display_label: 'Beta station', elevation: 1200 }
].map(station => ({
  ...station,
  station_status: 'ACTIVE',
  fire_centre: { id: '1', display_label: 'Centre' },
  fire_zone: { id: '1', display_label: 'Zone', fire_centre: '1' }
}))

const predictions = [
  prediction,
  { ...prediction, id: '2', station_code: 2, station_name: 'Beta station', model_elevation: 1000 }
]

const TestGrid = () => {
  const rows = useSelector(selectAllMoreCast2Rows)
  const predictions = useSelector((state: RootState) => state.weatherIndeterminates.predictions)
  const selected = useSelector(selectSelectedStations)
  const elevations = useMemo(
    () =>
      modelElevation.getModelElevationData(
        rows.filter(row => selected.some(station => station.station_code === row.stationCode)),
        predictions,
        selected
      ),
    [rows, predictions, selected]
  )
  return (
    <TabbedDataGrid
      fromTo={{}}
      setFromTo={vi.fn()}
      fetchWeatherIndeterminates={vi.fn()}
      modelElevationData={elevations}
      onCompareElevations={vi.fn()}
    />
  )
}

const renderGrid = () => {
  const initial = rootReducer(undefined, { type: 'test' })
  const store = configureStore({
    reducer: rootReducer,
    preloadedState: {
      ...initial,
      selectedStations: { selectedStations: stations },
      weatherIndeterminates: {
        ...initial.weatherIndeterminates,
        predictions,
        forecasts: predictions.map(row => ({
          ...row,
          determinate: WeatherDeterminate.FORECAST,
          prediction_run_timestamp: null,
          model_elevation: null,
          temperature: null,
          relative_humidity: null,
          precipitation: null,
          wind_speed: null,
          wind_direction: null
        }))
      }
    }
  })
  const result = render(
    <Provider store={store}>
      <TestGrid />
    </Provider>
  )
  return { store, ...result }
}

const stationHeader = (stationName: string): HTMLElement =>
  screen.getByRole('button', { name: `Station metadata for ${stationName}` }).closest<HTMLElement>('[role="row"]')!

const weatherRow = (stationCode: number): HTMLElement | undefined => {
  const header = stationHeader(stationCode === 1 ? 'Alpha station' : 'Beta station')
  const next = header.nextElementSibling as HTMLElement | null
  return next?.dataset.id && !next.dataset.id.startsWith('model-elevation-') ? next : undefined
}

const weatherCell = (stationCode: number, field = 'tempHRDPS'): HTMLElement =>
  weatherRow(stationCode)!.querySelector<HTMLElement>(`[data-field="${field}"]`)!

const toggleStation = async (stationName: string) => {
  const header = stationHeader(stationName)
  const toggle = within(header).getByRole('button', { name: /hide children|see children/ })
  await userEvent.click(toggle)
}

describe('station sections', () => {
  beforeEach(() => localStorage.clear())
  afterEach(() => {
    localStorage.clear()
    vi.restoreAllMocks()
  })

  it('labels the terrain action and model elevations with tooltips, including unavailable elevations', async () => {
    renderGrid()
    const terrain = await screen.findByRole('button', { name: 'Compare model elevations for Alpha station' })
    await userEvent.hover(terrain)
    expect(await screen.findByRole('tooltip')).toHaveTextContent('Forecast by elevation')
    await userEvent.unhover(terrain)
    await waitFor(() => expect(screen.queryByRole('tooltip')).not.toBeInTheDocument())
    const header = stationHeader('Alpha station')
    for (const model of ['HRDPS', 'ECMWF']) {
      const elevation = header.querySelector<HTMLElement>(`[data-field="temp${model}"] span`)!
      await userEvent.hover(elevation)
      expect(await screen.findByRole('tooltip')).toHaveTextContent(`${model} Elevation`)
      await userEvent.unhover(elevation)
      await waitFor(() => expect(screen.queryByRole('tooltip')).not.toBeInTheDocument())
    }
  })

  it('starts expanded with one header per station and centred model values', async () => {
    const { container } = renderGrid()
    await screen.findByRole('button', { name: 'Station metadata for Alpha station' })
    const row = stationHeader('Alpha station')
    expect(container.querySelector('.MuiDataGrid-pinnedRows--top')).toBeNull()
    expect(container.querySelectorAll('.modelElevationRow')).toHaveLength(2)
    expect(screen.getAllByText('Alpha station')).toHaveLength(1)
    expect(row).toHaveAttribute('aria-expanded', 'true')
    expect(stationHeader('Beta station')).toHaveAttribute('aria-expanded', 'true')
    expect(row).toHaveTextContent('Elevation: 900 m')
    expect(row.querySelector('[data-field="forDate"]')).toHaveTextContent(/^$/)
    expect(within(row).getByText('850 m')).toHaveStyle({ textAlign: 'center', justifyContent: 'center' })
    expect(row.querySelector('[data-field="tempECMWF"]')?.firstElementChild).toHaveStyle({
      textAlign: 'center',
      justifyContent: 'center'
    })
    expect(row.querySelector('[data-field="tempECMWF"]')).toHaveTextContent('N/A')
    expect(row.querySelector('[data-field="tempHRDPS_BIAS"]')).toHaveTextContent(/^$/)
    expect(row.querySelector('[data-field="tempForecast"]')).toHaveTextContent(/^$/)
    expect(within(weatherCell(1)).getByRole('textbox')).toHaveValue('20')
    expect(within(weatherCell(2)).getByRole('textbox')).toHaveValue('20')
  })

  it('collapses stations independently by mouse and keyboard while keeping their metadata visible', async () => {
    renderGrid()
    await screen.findByRole('button', { name: 'Station metadata for Alpha station' })
    const metadata = vi.spyOn(modelElevation, 'getModelElevationData')
    const columns = vi.spyOn(DataGridColumns, 'getTabColumns')
    await toggleStation('Alpha station')
    expect(stationHeader('Alpha station')).toHaveAttribute('aria-expanded', 'false')
    expect(weatherRow(1)).toBeUndefined()
    expect(within(weatherCell(2)).getByRole('textbox')).toHaveValue('20')
    expect(stationHeader('Alpha station')).toHaveTextContent('850 m')
    await userEvent.click(stationHeader('Beta station').querySelector('[role="gridcell"]')!)
    await userEvent.keyboard('{Enter}')
    expect(stationHeader('Beta station')).toHaveAttribute('aria-expanded', 'false')
    expect(weatherRow(2)).toBeUndefined()
    await userEvent.keyboard(' ')
    expect(stationHeader('Beta station')).toHaveAttribute('aria-expanded', 'true')
    expect(within(weatherCell(2)).getByRole('textbox')).toHaveValue('20')
    await toggleStation('Alpha station')
    expect(within(weatherCell(1)).getByRole('textbox')).toHaveValue('20')
    expect(metadata).not.toHaveBeenCalled()
    expect(columns).not.toHaveBeenCalled()
  })

  it('keeps station headers read only', async () => {
    const { store } = renderGrid()
    const before = store.getState().weatherIndeterminates
    await screen.findByRole('button', { name: 'Station metadata for Alpha station' })
    const row = stationHeader('Alpha station')
    await userEvent.dblClick(within(row).getByText('850 m'))
    await userEvent.keyboard('{Enter}42{Enter}')
    expect(within(row).getByText('850 m')).toBeInTheDocument()
    expect(within(row).queryByRole('textbox')).not.toBeInTheDocument()
    expect(row).not.toHaveClass('Mui-selected')
    expect(store.getState().weatherIndeterminates).toBe(before)
  })

  it('keeps edits and drafts when a station collapses, and still copies model weather values', async () => {
    renderGrid()
    await screen.findByRole('button', { name: 'Station metadata for Alpha station' })
    const metadata = vi.spyOn(modelElevation, 'getModelElevationData')
    const forecastCell = weatherCell(1, 'tempForecast')
    await userEvent.dblClick(forecastCell)
    const input = within(forecastCell).getByRole('spinbutton')
    await userEvent.clear(input)
    await userEvent.type(input, '25{Enter}')
    await waitFor(() => expect(within(weatherCell(1, 'tempForecast')).getByRole('textbox')).toHaveValue('25'))
    const draft = new MorecastDraftForecast(localStorage)
    const savedDraft = draft.getStoredDraftForecasts()
    expect(savedDraft?.rows.find(row => row.stationCode === 1)?.tempForecast?.value).toBe(25)
    await toggleStation('Alpha station')
    await toggleStation('Alpha station')
    expect(within(weatherCell(1, 'tempForecast')).getByRole('textbox')).toHaveValue('25')
    expect(draft.getStoredDraftForecasts()).toEqual(savedDraft)
    await userEvent.dblClick(weatherCell(2))
    await waitFor(() => expect(within(weatherCell(2, 'tempForecast')).getByRole('textbox')).toHaveValue('20'))
    expect(metadata).not.toHaveBeenCalled()
  })

  it('applies a model column to collapsed stations as well as expanded stations', async () => {
    renderGrid()
    await screen.findByRole('button', { name: 'Station metadata for Alpha station' })
    await toggleStation('Beta station')
    await userEvent.click(screen.getByTestId('tempForecast-column-header'))
    await userEvent.click(screen.getByTestId('apply-model-to-column-button'))
    await userEvent.keyboard('{Escape}')
    await toggleStation('Beta station')
    expect(within(weatherCell(1, 'tempForecast')).getByRole('textbox')).toHaveValue('20')
    expect(within(weatherCell(2, 'tempForecast')).getByRole('textbox')).toHaveValue('20')
    expect(new MorecastDraftForecast(localStorage).getStoredDraftForecasts()?.rows.map(row => row.stationCode)).toEqual(
      [1, 2]
    )
  })

  it('keeps expansion when switching parameters and returning from Forecast Summary', async () => {
    renderGrid()
    await screen.findByRole('button', { name: 'Station metadata for Alpha station' })
    await toggleStation('Beta station')
    await userEvent.click(screen.getByTestId('rh-tab-button-unselected'))
    expect(stationHeader('Beta station')).toHaveAttribute('aria-expanded', 'false')
    await userEvent.click(screen.getByTestId('summary-tab-button-unselected'))
    expect(document.querySelector('.modelElevationRow')).toBeNull()
    await userEvent.click(screen.getByTestId('temp-tab-button-unselected'))
    await screen.findByRole('button', { name: 'Station metadata for Alpha station' })
    expect(stationHeader('Beta station')).toHaveAttribute('aria-expanded', 'false')
    expect(stationHeader('Alpha station')).toHaveAttribute('aria-expanded', 'true')
  })

  it('starts newly selected stations expanded and removes headers for empty data', async () => {
    const { store } = renderGrid()
    await screen.findByRole('button', { name: 'Station metadata for Alpha station' })
    await toggleStation('Beta station')
    act(() => {
      store.dispatch(selectedStationsChanged([stations[0]]))
    })
    await waitFor(() => expect(screen.queryByText('Beta station')).not.toBeInTheDocument())
    act(() => {
      store.dispatch(selectedStationsChanged(stations))
    })
    await waitFor(() => expect(stationHeader('Beta station')).toHaveAttribute('aria-expanded', 'true'))
    act(() => {
      store.dispatch(selectedStationsChanged([]))
    })
    await waitFor(() => expect(document.querySelector('.modelElevationRow')).toBeNull())
  })

  it('refreshes elevations without expanding collapsed stations or changing the header run', async () => {
    const { store } = renderGrid()
    await screen.findByRole('button', { name: 'Station metadata for Alpha station' })
    await toggleStation('Beta station')
    act(() => {
      store.dispatch(
        getWeatherIndeterminatesSuccess({
          actuals: [],
          forecasts: [],
          grassCuring: [],
          predictions: predictions.map(row => ({
            ...row,
            utc_timestamp: '2030-07-05T20:00:00Z',
            prediction_run_timestamp: '2030-07-05T00:00:00Z',
            model_elevation: 1120
          }))
        })
      )
    })
    await waitFor(() => expect(stationHeader('Beta station')).toHaveTextContent('1,120 m'))
    expect(stationHeader('Beta station')).toHaveAttribute('aria-expanded', 'false')
    expect(stationHeader('Alpha station')).toHaveTextContent('1,120 m')
  })
})
