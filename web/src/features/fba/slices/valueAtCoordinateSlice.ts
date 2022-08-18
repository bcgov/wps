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

const lookup = new Map([
  [1, 'C-1, Spruce-Lichen Woodland'],
  [2, 'C-2, Boreal Spruce'],
  [3, 'C-3, Mature Jack or Lodgepole Pine'],
  [4, 'C-4, Immature Jack or Lodgepole Pine or densely stocked Ponderosa Pine or Douglas Fir'],
  [5, 'C-5, Red and White Pine'],
  [6, 'C-6, Conifer Plantation'],
  [7, 'C-7, Ponderosa Pine or Douglas Fir'],
  [8, 'D-1/D-2, Leafless or Green Aspen or Deciduous shrub'],
  [9, 'S-1, Jack or Lodgepole Pine slash'],
  [10, 'S-2, White Spruce or Balsam slash'],
  [11, 'S-3, Coastal Cedar or Hemlock or Douglas Fir slash'],
  [12, 'O-1a, Matted Grass'],
  [14, 'M-1/M-2, M-1/M-2'],
  [32, 'O-1b, Standing Grass'],
  [40, 'M-1, Boreal Mixedwood - Leafless'],
  [50, 'M-2, Boreal Mixed wood - Green'],
  [81, 'D-1, Leafless Aspen'],
  [82, 'D-2, Green Aspen (with BUI Thresholding)'],
  [90, 'M-3/M-4, Dead Balsam Fir Mixedwood'],
  [99, 'Non-fuel, Non-fuel'],
  [100, 'Non-fuel, Interface'],
  [102, 'Non-fuel, Water'],
  [103, 'Non-fuel, Unknown'],
  [505, 'M-1/M-2 (05 PC), M-2 0-5% Conifer'],
  [510, 'M-1/M-2 (10 PC), M-2 5-10% Conifer'],
  [515, 'M-1/M-2 (15 PC), M-2 10-15% Conifer'],
  [520, 'M-1/M-2 (20 PC), M-2 15-20% Conifer'],
  [525, 'M-1/M-2 (25 PC), M-2 20-25% Conifer'],
  [530, 'M-1/M-2 (30 PC), M-2 25-30% Conifer'],
  [535, 'M-1/M-2 (35 PC), M-2 30-35% Conifer'],
  [540, 'M-1/M-2 (40 PC), M-2 35-40% Conifer'],
  [545, 'M-1/M-2 (45 PC), M-2 40-45% Conifer'],
  [550, 'M-1/M-2 (50 PC), M-2 45-50% Conifer'],
  [555, 'M-1/M-2 (55 PC), M-2 50-55% Conifer'],
  [560, 'M-1/M-2 (60 PC), M-2 55-60% Conifer'],
  [565, 'M-1/M-2 (65 PC), M-2 60-65% Conifer'],
  [570, 'M-1/M-2 (70 PC), M-2 65-70% Conifer'],
  [575, 'M-1/M-2 (75 PC), M-2 70-75% Conifer'],
  [580, 'M-1/M-2 (80 PC), M-2 75-80% Conifer'],
  [585, 'M-1/M-2 (85 PC), M-2 80-85% Conifer'],
  [590, 'M-1/M-2 (90 PC), M-2 85-90% Conifer'],
  [595, 'M-1/M-2 (95 PC), M-2 90-95% Conifer'],
  [765, 'M-3 (65 PDF), Dead Balsam Fir Mixedwood - Leafless (65% dead fir)'],
  [865, 'M-4 (65 PDF), Dead Balsam Fir Mixedwood - Green (65% dead fir)'],
  [965, 'M-3/M-4 (65 PDF), Dead Balsam Fir Mixedwood (65% Dead Fir)'],
  [-10000, 'Undefined'],
  [65535, 'Undefined']
])

const fbpValueEncoder = (value: number): string => {
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
          fbpValueEncoder
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
          `gpdqha/dem/cog/cog_BC_Area_CDEM.tif`,
          latitude,
          longitude,
          '12 arc second elevation',
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
