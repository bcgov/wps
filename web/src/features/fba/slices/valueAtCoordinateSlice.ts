import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { AppThunk } from 'app/store'
import { logError } from 'utils/error'
import { getValueAtCoordinate } from 'api/fbaAPI'
import { DateTime } from 'luxon'

export interface IValueAtCoordinate {
  value: string | undefined
  description: string
}
interface State {
  loading: boolean
  error: string | null
  values: IValueAtCoordinate[]
}

const initialState: State = {
  loading: false,
  error: null,
  values: []
}

const valueAtCoordinateSlice = createSlice({
  name: 'valueAtCoordinate',
  initialState,
  reducers: {
    getValueAtCoordinateStart(state: State) {
      state.error = null
      state.loading = true
      state.values = []
    },
    getValueAtCoordinateFailed(state: State, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getValueAtCoordinateSuccess(state: State, action: PayloadAction<IValueAtCoordinate[]>) {
      state.error = null
      state.values = action.payload
      state.loading = false
    }
  }
})

export const { getValueAtCoordinateStart, getValueAtCoordinateFailed, getValueAtCoordinateSuccess } =
  valueAtCoordinateSlice.actions

export default valueAtCoordinateSlice.reducer

const defaultValueEncoder = (value: number) => `${value}`

const fbpValueEncoder = (value: number): string => {
  const lookup = new Map()
  lookup.set(1, 'C-1, Spruce-Lichen Woodland')
  lookup.set(14, 'M-1/M-2')
  lookup.set(99, 'Non-fuel')

  return lookup.get(value) || 'Unknown'
}

export const fetchValuesAtCoordinate =
  (latitude: number, longitude: number, date: DateTime): AppThunk =>
  async dispatch => {
    const isoDate = date.toISODate().replaceAll('-', '')
    try {
      dispatch(getValueAtCoordinateStart())
      const actions = [
        getValueAtCoordinate(
          `gpdqha/sfms/cog/cog_hfi${isoDate}.tif`,
          latitude,
          longitude,
          `SFMS HFI ${date.toLocaleString()}`,
          defaultValueEncoder
        ),
        getValueAtCoordinate(
          `gpdqha/ftl/ftl_2018_cloudoptimized.tif`,
          latitude,
          longitude,
          '2018 FTL',
          fbpValueEncoder
        ),
        getValueAtCoordinate(
          `gpdqha/sfms/cog/static/cog_fbp2021.tif`,
          latitude,
          longitude,
          'SFMS 2021 FBP',
          defaultValueEncoder
        ),
        getValueAtCoordinate(
          `gpdqha/sfms/cog/static/cog_m12_2021.tif`,
          latitude,
          longitude,
          'SFMS 2021 M12',
          defaultValueEncoder
        ),
        getValueAtCoordinate(
          `gpdqha/sfms/cog/static/cog_bc_elevation.tif`,
          latitude,
          longitude,
          'SFMS elevation',
          defaultValueEncoder
        ),
        getValueAtCoordinate(
          `gpdqha/sfms/cog/static/cog_bc_aspect.tif`,
          latitude,
          longitude,
          'SFMS aspect',
          defaultValueEncoder
        ),
        getValueAtCoordinate(
          `gpdqha/sfms/cog/static/cog_bc_slope.tif`,
          latitude,
          longitude,
          'SFMS slope',
          defaultValueEncoder
        )
      ]
      const results = await Promise.all(
        actions.map(async promise => {
          const result = await promise
          return { value: result.value, description: result.description }
        })
      )
      // Only fetching the one right now...
      // const value = await getValueAtCoordinate(layer, latitude, longitude)
      dispatch(getValueAtCoordinateSuccess(results))
    } catch (err) {
      dispatch(getValueAtCoordinateFailed((err as Error).toString()))
      logError(err)
    }
  }
