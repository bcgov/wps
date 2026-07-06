import { renderHook, waitFor } from '@testing-library/react'
import * as smurfiApi from '@wps/api/SMURFIAPI'
import { type SpotForecastOutput, type SpotRequestOutput, SpotRequestStatus } from '@wps/api/SMURFIAPI'
import * as stationApi from '@wps/api/stationAPI'
import type { GeoJsonStation } from '@wps/types/stationTypes'
import type { ReactNode } from 'react'
import { Provider } from 'react-redux'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import useSpotForecastData from '@/features/smurfi/hooks/useSpotForecastData'
import { createTestStore } from '@/test/testUtils'

const buildSpotRequest = (id = 42): SpotRequestOutput =>
  ({
    id,
    request_reference: `WPS-${id}`,
    fire_number: ['V10001'],
    fire_centre: 1,
    status: SpotRequestStatus.STARTED,
    requestor_name: 'Owner',
    requestor_idir: 'owner_idir',
    requestor_email: 'owner@example.com',
    request_frequency: ['Monday'],
    request_type: 'Full',
    requested_at: '2026-05-20T18:30:00.000Z',
    start_at: '2026-05-21T00:00:00.000-07:00',
    end_at: '2026-05-23T23:59:00.000-07:00',
    subscribers: [],
    distribution_group_ids: [],
    request_instance: {
      id,
      geographic_description: 'Clearwater Valley',
      aspect: 'North',
      elevation: 1000,
      valley: null,
      latitude: 50.1234,
      longitude: -122.5678,
      created_at: '2026-05-20T18:30:00.000Z'
    }
  }) as SpotRequestOutput

const buildSpotForecast = (id = 99, representativeStationCodes = [101, 202]): SpotForecastOutput =>
  ({
    id,
    spot_request_base_id: 42,
    spot_request_instance_id: 12,
    spot_request_instance: {
      id: 12,
      geographic_description: 'Clearwater Valley',
      aspect: 'North',
      elevation: 1000,
      valley: null,
      latitude: 50.1234,
      longitude: -122.5678,
      created_at: '2026-05-20T18:30:00.000Z'
    },
    forecast_type: 'Full',
    issued_at: '2026-05-21T14:30:00.000-07:00',
    expires_at: '2026-05-22T14:30:00.000-07:00',
    created_at: '2026-05-21T14:30:00.000-07:00',
    forecaster_name: 'Forecaster',
    forecaster_email: 'forecaster@example.com',
    representative_station_codes: representativeStationCodes,
    descriptive_weather: [],
    tabular_weather: []
  }) as SpotForecastOutput

const buildStation = (code: number, name: string, elevation: number): GeoJsonStation => ({
  type: 'Feature',
  geometry: { type: 'Point', coordinates: [-122.5, 50.1] },
  properties: {
    code,
    name,
    elevation,
    ecodivision_name: null,
    core_season: { start_month: 4, start_day: 1, end_month: 10, end_day: 31 }
  }
})

const renderForecastDataHook = ({
  spotForecastsByRequestId = { 42: [buildSpotForecast()] },
  stationsByCode = {
    101: buildStation(101, 'Station 101', 900),
    202: buildStation(202, 'Station 202', 1200)
  },
  route = '/smurfi/42/forecasts/99'
}: {
  spotForecastsByRequestId?: Record<number, SpotForecastOutput[]>
  stationsByCode?: Record<number, GeoJsonStation | undefined>
  route?: string
} = {}) => {
  const store = createTestStore({
    smurfi: {
      loading: false,
      error: null,
      spotForecastSubmitting: false,
      spotForecastSubmitError: null,
      submittedSpotForecast: null,
      spotForecastsByRequestId,
      spotForecastsError: null,
      spotForecastsLoading: false,
      spotRequestSubmitting: false,
      spotRequestSubmitError: null,
      spotRequestStatusUpdateError: null,
      spotRequestStatusUpdatingById: {},
      spotRequestsError: null,
      spotRequestsLoading: false,
      spotRequests: [buildSpotRequest()],
      distributionGroups: [],
      distributionGroupsLoading: false,
      distributionGroupsError: null
    },
    fireWeatherStations: {
      loading: false,
      error: null,
      stations: Object.values(stationsByCode).filter((station): station is GeoJsonStation => Boolean(station)),
      stationsByCode,
      selectedStationsByCode: [],
      codesOfRetrievedStationData: []
    }
  })

  const wrapper = ({ children }: { children: ReactNode }) => (
    <Provider store={store}>
      <MemoryRouter initialEntries={[route]}>
        <Routes>
          <Route path="/smurfi/:id/forecasts/:forecastId" element={children} />
        </Routes>
      </MemoryRouter>
    </Provider>
  )

  return { store, ...renderHook(() => useSpotForecastData(), { wrapper }) }
}

describe('useSpotForecastData', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('returns cached request, forecast, and representative station details', () => {
    const fetchForecasts = vi.spyOn(smurfiApi, 'getSpotForecasts').mockResolvedValue({ spot_forecasts: [] })
    const fetchStations = vi.spyOn(stationApi, 'getStations').mockResolvedValue([])

    const { result } = renderForecastDataHook()

    expect(result.current.loading).toBe(false)
    expect(result.current.spotRequest?.id).toBe(42)
    expect(result.current.spotForecast?.id).toBe(99)
    expect(result.current.representativeStations).toEqual([
      { code: 101, name: 'Station 101', elevation: 900 },
      { code: 202, name: 'Station 202', elevation: 1200 }
    ])
    expect(fetchForecasts).not.toHaveBeenCalled()
    expect(fetchStations).not.toHaveBeenCalled()
  })

  it('fetches forecasts when the request forecast cache is missing', async () => {
    const forecast = buildSpotForecast(99, [101])
    const fetchForecasts = vi.spyOn(smurfiApi, 'getSpotForecasts').mockResolvedValue({ spot_forecasts: [forecast] })

    const { result } = renderForecastDataHook({ spotForecastsByRequestId: {} })

    await waitFor(() => expect(fetchForecasts).toHaveBeenCalledWith(42))
    await waitFor(() => expect(result.current.spotForecast?.id).toBe(99))
  })

  it('fetches stations when station cache is empty and ignores missing representative stations', async () => {
    const station = buildStation(101, 'Station 101', 900)
    const fetchStations = vi.spyOn(stationApi, 'getStations').mockResolvedValue([station])

    const { result } = renderForecastDataHook({ stationsByCode: {} })

    await waitFor(() => expect(fetchStations).toHaveBeenCalledWith(stationApi.StationSource.wildfire_one, undefined))
    await waitFor(() =>
      expect(result.current.representativeStations).toEqual([{ code: 101, name: 'Station 101', elevation: 900 }])
    )
  })
})
