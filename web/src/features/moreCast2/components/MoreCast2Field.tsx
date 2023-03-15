import { GridColDef, GridValueFormatterParams } from '@mui/x-data-grid'
import { DateTime } from 'luxon'
import { GridNumberRenderer } from 'features/moreCast2/components/DataGridNumberRenderer'

export type Morecast2Field = 'stationName' | 'forDate' | 'temp' | 'rh' | 'windDirection' | 'windSpeed' | 'precip'

export interface ForecastField {
  field: Morecast2Field
  headerName: string
  type: 'number' | 'string'
  precision: 0 | 1
  generateColDef: () => GridColDef
}

export class StationForecastField implements ForecastField {
  private static instance: StationForecastField

  readonly field = 'stationName'
  readonly headerName = 'Station'
  readonly type = 'string'
  readonly precision = 0
  private constructor() {
    /* no op */
  }
  public generateColDef = () => {
    return { field: this.field, flex: 1, headerName: this.headerName, maxWidth: 200 }
  }

  public static getInstance(): StationForecastField {
    if (!StationForecastField.instance) {
      StationForecastField.instance = new StationForecastField()
    }

    return StationForecastField.instance
  }
}

export class DateForecastField implements ForecastField {
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
      maxWidth: 250,
      sortable: false,
      valueFormatter: (params: GridValueFormatterParams<DateTime>) => {
        return params.value.toLocaleString(DateTime.DATE_MED)
      }
    }
  }
  public static getInstance(): DateForecastField {
    if (!DateForecastField.instance) {
      DateForecastField.instance = new DateForecastField()
    }

    return DateForecastField.instance
  }
}

export class TempForecastField extends GridNumberRenderer implements ForecastField {
  private static instance: TempForecastField

  readonly field = 'temp'
  readonly headerName = 'Temp'
  readonly type = 'number'
  readonly precision = 1
  private constructor() {
    super()
  }
  public generateColDef = () => {
    return this.generateColDefWith(this.field, this.headerName, this.precision)
  }

  public static getInstance(): TempForecastField {
    if (!TempForecastField.instance) {
      TempForecastField.instance = new TempForecastField()
    }

    return TempForecastField.instance
  }
}

export class RHForecastField extends GridNumberRenderer implements ForecastField {
  private static instance: RHForecastField

  readonly field = 'rh'
  readonly headerName = 'RH'
  readonly type = 'number'
  readonly precision = 0
  private constructor() {
    super()
  }
  public generateColDef = () => {
    return this.generateColDefWith(this.field, this.headerName, this.precision)
  }

  public static getInstance(): RHForecastField {
    if (!RHForecastField.instance) {
      RHForecastField.instance = new RHForecastField()
    }

    return RHForecastField.instance
  }
}

export class WindDirForecastField extends GridNumberRenderer implements ForecastField {
  private static instance: WindDirForecastField

  readonly field = 'windDirection'
  readonly headerName = 'Wind Dir'
  readonly type = 'number'
  readonly precision = 0
  private constructor() {
    super()
  }
  public generateColDef = () => {
    return this.generateColDefWith(this.field, this.headerName, this.precision)
  }

  public static getInstance(): WindDirForecastField {
    if (!WindDirForecastField.instance) {
      WindDirForecastField.instance = new WindDirForecastField()
    }

    return WindDirForecastField.instance
  }
}

export class WindSpeedForecastField extends GridNumberRenderer implements ForecastField {
  private static instance: WindSpeedForecastField

  readonly field = 'windSpeed'
  readonly headerName = 'Wind Speed'
  readonly type = 'number'
  readonly precision = 1
  private constructor() {
    super()
  }
  public generateColDef = () => {
    return this.generateColDefWith(this.field, this.headerName, this.precision)
  }
  public static getInstance(): WindSpeedForecastField {
    if (!WindSpeedForecastField.instance) {
      WindSpeedForecastField.instance = new WindSpeedForecastField()
    }

    return WindSpeedForecastField.instance
  }
}

export class PrecipForecastField extends GridNumberRenderer implements ForecastField {
  private static instance: PrecipForecastField

  readonly field = 'precip'
  readonly headerName = 'Precip'
  readonly type = 'number'
  readonly precision = 1
  private constructor() {
    super()
  }
  public generateColDef = () => {
    return this.generateColDefWith(this.field, this.headerName, this.precision)
  }

  public static getInstance(): PrecipForecastField {
    if (!PrecipForecastField.instance) {
      PrecipForecastField.instance = new PrecipForecastField()
    }

    return PrecipForecastField.instance
  }
}

export const MORECAST2_FIELDS: ForecastField[] = [
  StationForecastField.getInstance(),
  DateForecastField.getInstance(),
  TempForecastField.getInstance(),
  RHForecastField.getInstance(),
  WindDirForecastField.getInstance(),
  WindSpeedForecastField.getInstance(),
  PrecipForecastField.getInstance()
]
