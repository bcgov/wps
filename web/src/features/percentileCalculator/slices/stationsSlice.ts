import {
  getStationsStart,
  getStationsSuccess,
  getStationsFailed
} from 'features/stations/slices/stationsSlice'

import { StationSource, getStations } from 'api/stationAPI'
import { AppThunk } from 'app/store'
import { logError } from 'utils/error'

export const fetchWxStations = (): AppThunk => async dispatch => {
  try {
    dispatch(getStationsStart())
    const stations = await getStations(StationSource.local_storage)
    dispatch(getStationsSuccess(stations))
  } catch (err) {
    dispatch(getStationsFailed(err.toString()))
    logError(err)
  }
}
