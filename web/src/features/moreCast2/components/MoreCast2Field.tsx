import { GridColDef, GridValueFormatterParams } from '@mui/x-data-grid'
import { DateTime } from 'luxon'
import { GridNumberRenderer } from 'features/moreCast2/components/DataGridNumberRenderer'
import { WeatherDeterminate, WeatherDeterminateType } from 'api/moreCast2API'

export interface Morecast2Field {
  field: string
  headerName: string
  type: 'number' | 'string'
  precision: 0 | 1
  generateColDef: () => GridColDef
  generateColDefs: () => GridColDef[]
}

export interface ForecastField {
  generateForecastColDef: () => GridColDef
}

const DEFAULT_COLUMN_WIDTH = 80

const COLUMN_HEADERS: WeatherDeterminateType[] = [
  WeatherDeterminate.ACTUAL,
  WeatherDeterminate.HRDPS,
  WeatherDeterminate.GDPS,
  WeatherDeterminate.GFS,
  WeatherDeterminate.RDPS
]

export class StationForecastField implements Morecast2Field {
  private static instance: StationForecastField

  readonly field = 'stationName'
  readonly headerName = 'Station'
  readonly type = 'string'
  readonly precision = 0
  private constructor() {
    /* no op */
  }
  public generateColDef = () => {
    return { field: this.field, flex: 1, headerName: this.headerName, maxWidth: 200, width: 200 }
  }

  public generateColDefs = () => {
    return [this.generateColDef()]
  }

  public static getInstance(): StationForecastField {
    if (!StationForecastField.instance) {
      StationForecastField.instance = new StationForecastField()
    }

    return StationForecastField.instance
  }
}

export class DateForecastField implements Morecast2Field {
  private static instance: DateForecastField

  readonly field = 'forDate'
  readonly headerName = 'Date'
  readonly type = 'string'
  readonly precision = 0
  private constructor() {
    /* no op */
  }

  public generateColDef = () => {
    return {
      field: this.field,
      disableColumnMenu: true,
      disableReorder: true,
      flex: 1,
      headerName: this.headerName,
      maxWidth: 150,
      width: 150,
      sortable: false,
      valueFormatter: (params: GridValueFormatterParams<DateTime>) => {
        return params.value.toLocaleString(DateTime.DATE_MED)
      }
    }
  }

  public generateColDefs = () => {
    return [this.generateColDef()]
  }

  public static getInstance(): DateForecastField {
    if (!DateForecastField.instance) {
      DateForecastField.instance = new DateForecastField()
    }

    return DateForecastField.instance
  }
}

export class TempForecastField extends GridNumberRenderer implements Morecast2Field, ForecastField {
  private static instance: TempForecastField

  readonly field = 'temp'
  readonly headerName = 'Temp'
  readonly type = 'number'
  readonly precision = 1
  private constructor() {
    super()
  }
  public generateForecastColDef = () => {
    return this.generateForecastColDefWith(
      `${this.field}${WeatherDeterminate.FORECAST}`,
      this.headerName,
      this.precision,
      DEFAULT_COLUMN_WIDTH
    )
  }
  public generateColDef = () => {
    return this.generateColDefWith(this.field, this.headerName, this.precision, DEFAULT_COLUMN_WIDTH)
  }

  public generateColDefs = () => {
    const gridColDefs: GridColDef[] = []
    // Forecast columns have unique requirement (eg. column header menu, editable, etc.)
    const forecastColDef = this.generateForecastColDef()
    gridColDefs.push(forecastColDef)

    // Actual and model prediction columns only show data, so require a simple column definition
    for (const determinate of COLUMN_HEADERS) {
      const fieldName = `${this.field}${determinate}`
      const gridColDef = this.generateColDefWith(fieldName, determinate, this.precision, DEFAULT_COLUMN_WIDTH)
      gridColDefs.push(gridColDef)
    }
    return gridColDefs
  }

  public static getInstance(): TempForecastField {
    if (!TempForecastField.instance) {
      TempForecastField.instance = new TempForecastField()
    }

    return TempForecastField.instance
  }
}

export class RHForecastField extends GridNumberRenderer implements Morecast2Field, ForecastField {
  private static instance: RHForecastField

  readonly field = 'rh'
  readonly headerName = 'RH'
  readonly type = 'number'
  readonly precision = 0
  private constructor() {
    super()
  }

  public generateForecastColDef = () => {
    return this.generateForecastColDefWith(
      `${this.field}${WeatherDeterminate.FORECAST}`,
      this.headerName,
      this.precision,
      DEFAULT_COLUMN_WIDTH
    )
  }

  public generateColDef = () => {
    return this.generateColDefWith(this.field, this.headerName, this.precision, DEFAULT_COLUMN_WIDTH)
  }

  public generateColDefs = () => {
    const gridColDefs: GridColDef[] = []
    // Forecast columns have unique requirement (eg. column header menu, editable, etc.)
    const forecastColDef = this.generateForecastColDef()
    gridColDefs.push(forecastColDef)

    // Actual and model prediction columns only show data, so require a simple column definition
    for (const determinate of COLUMN_HEADERS) {
      const fieldName = `${this.field}${determinate}`
      const gridColDef = this.generateColDefWith(fieldName, determinate, this.precision, DEFAULT_COLUMN_WIDTH)
      gridColDefs.push(gridColDef)
    }
    return gridColDefs
  }

  public static getInstance(): RHForecastField {
    if (!RHForecastField.instance) {
      RHForecastField.instance = new RHForecastField()
    }

    return RHForecastField.instance
  }
}

export class WindDirForecastField extends GridNumberRenderer implements Morecast2Field, ForecastField {
  private static instance: WindDirForecastField

  readonly field = 'windDirection'
  readonly headerName = 'Wind Dir'
  readonly type = 'number'
  readonly precision = 0
  private constructor() {
    super()
  }

  public generateForecastColDef = () => {
    return this.generateForecastColDefWith(
      `${this.field}${WeatherDeterminate.FORECAST}`,
      this.headerName,
      this.precision,
      DEFAULT_COLUMN_WIDTH
    )
  }

  public generateColDef = () => {
    return this.generateColDefWith(this.field, this.headerName, this.precision, DEFAULT_COLUMN_WIDTH)
  }

  public generateColDefs = () => {
    const gridColDefs: GridColDef[] = []
    // Forecast columns have unique requirement (eg. column header menu, editable, etc.)
    const forecastColDef = this.generateForecastColDef()
    gridColDefs.push(forecastColDef)

    // Actual and model prediction columns only show data, so require a simple column definition
    for (const determinate of COLUMN_HEADERS) {
      const fieldName = `${this.field}${determinate}`
      const gridColDef = this.generateColDefWith(fieldName, determinate, this.precision, DEFAULT_COLUMN_WIDTH)
      gridColDefs.push(gridColDef)
    }
    return gridColDefs
  }

  public static getInstance(): WindDirForecastField {
    if (!WindDirForecastField.instance) {
      WindDirForecastField.instance = new WindDirForecastField()
    }

    return WindDirForecastField.instance
  }
}

export class WindSpeedForecastField extends GridNumberRenderer implements Morecast2Field, ForecastField {
  private static instance: WindSpeedForecastField

  readonly field = 'windSpeed'
  readonly headerName = 'Wind Speed'
  readonly type = 'number'
  readonly precision = 1
  private constructor() {
    super()
  }

  public generateForecastColDef = () => {
    return this.generateForecastColDefWith(
      `${this.field}${WeatherDeterminate.FORECAST}`,
      this.headerName,
      this.precision,
      DEFAULT_COLUMN_WIDTH
    )
  }

  public generateColDef = () => {
    return this.generateColDefWith(this.field, this.headerName, this.precision, DEFAULT_COLUMN_WIDTH)
  }

  public generateColDefs = () => {
    const gridColDefs: GridColDef[] = []
    // Forecast columns have a unique requirement (eg. column header menu, editable, etc.)
    const forecastColDef = this.generateForecastColDefWith(
      `${this.field}${WeatherDeterminate.FORECAST}`,
      WeatherDeterminate.FORECAST,
      this.precision,
      DEFAULT_COLUMN_WIDTH
    )
    gridColDefs.push(forecastColDef)

    // Actual and model prediction columns only show data, so require a simple column definition
    for (const determinate of COLUMN_HEADERS) {
      const fieldName = `${this.field}${determinate}`
      const gridColDef = this.generateColDefWith(fieldName, determinate, this.precision, DEFAULT_COLUMN_WIDTH)
      gridColDefs.push(gridColDef)
    }
    return gridColDefs
  }

  public static getInstance(): WindSpeedForecastField {
    if (!WindSpeedForecastField.instance) {
      WindSpeedForecastField.instance = new WindSpeedForecastField()
    }

    return WindSpeedForecastField.instance
  }
}

export class PrecipForecastField extends GridNumberRenderer implements Morecast2Field, ForecastField {
  private static instance: PrecipForecastField

  readonly field = 'precip'
  readonly headerName = 'Precip'
  readonly type = 'number'
  readonly precision = 1
  private constructor() {
    super()
  }

  public generateForecastColDef = () => {
    return this.generateForecastColDefWith(
      `${this.field}${WeatherDeterminate.FORECAST}`,
      this.headerName,
      this.precision,
      DEFAULT_COLUMN_WIDTH
    )
  }

  public generateColDef = () => {
    return this.generateColDefWith(this.field, this.headerName, this.precision, DEFAULT_COLUMN_WIDTH)
  }

  public generateColDefs = () => {
    const gridColDefs: GridColDef[] = []
    // Forecast columns have unique requirement (eg. column header menu, editable, etc.)
    const forecastColDef = this.generateForecastColDef()
    gridColDefs.push(forecastColDef)

    // Actual and model prediction columns only show data, so require a simple column definition
    for (const determinate of COLUMN_HEADERS) {
      const fieldName = `${this.field}${determinate}`
      const gridColDef = this.generateColDefWith(fieldName, determinate, this.precision, DEFAULT_COLUMN_WIDTH)
      gridColDefs.push(gridColDef)
    }
    return gridColDefs
  }

  public static getInstance(): PrecipForecastField {
    if (!PrecipForecastField.instance) {
      PrecipForecastField.instance = new PrecipForecastField()
    }

    return PrecipForecastField.instance
  }
}

export const MORECAST2_STATION_DATE_FIELDS: Morecast2Field[] = [
  StationForecastField.getInstance(),
  DateForecastField.getInstance()
]

export const MORECAST2_FIELDS: Morecast2Field[] = [
  StationForecastField.getInstance(),
  DateForecastField.getInstance(),
  TempForecastField.getInstance(),
  RHForecastField.getInstance(),
  WindDirForecastField.getInstance(),
  WindSpeedForecastField.getInstance(),
  PrecipForecastField.getInstance()
]

export const MORECAST2_FORECAST_FIELDS: ForecastField[] = [
  TempForecastField.getInstance(),
  RHForecastField.getInstance(),
  WindDirForecastField.getInstance(),
  WindSpeedForecastField.getInstance(),
  PrecipForecastField.getInstance()
]
