import { GridValueFormatterParams } from '@mui/x-data-grid'
import { DateTime } from 'luxon'
import {
  ColDefGenerator,
  ColumnDefBuilder,
  ForecastColDefGenerator
} from 'features/moreCast2/components/ColumnDefBuilder'
import { GridComponentRenderer } from 'features/moreCast2/components/GridComponentRenderer'

export class StationForecastField implements ColDefGenerator {
  private static instance: StationForecastField

  readonly field = 'stationName'
  readonly headerName = 'Station'
  readonly type = 'string'
  readonly precision = 0
  private constructor() {
    /* no op */
  }
  public generateColDef = () => {
    return { field: this.field, flex: 1, headerName: this.headerName, maxWidth: 200, minWidth: 200, width: 200 }
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

export class DateForecastField implements ColDefGenerator {
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
      minWidth: 150,
      width: 150,
      sortable: false,
      valueFormatter: (params: GridValueFormatterParams<DateTime>) => {
        return params.value.toLocaleString(DateTime.DATE_MED_WITH_WEEKDAY)
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

export class IndeterminateField implements ColDefGenerator, ForecastColDefGenerator {
  private colDefBuilder: ColumnDefBuilder

  constructor(
    readonly field: string,
    readonly headerName: string,
    readonly type: 'string' | 'number',
    readonly precision: number,
    readonly includeBias: boolean
  ) {
    this.colDefBuilder = new ColumnDefBuilder(
      this.field,
      this.headerName,
      this.type,
      this.precision,
      new GridComponentRenderer()
    )
  }

  public generateForecastColDef = (headerName?: string) => {
    return this.colDefBuilder.generateForecastColDef(headerName ?? this.headerName)
  }

  public generateColDef = () => {
    return this.colDefBuilder.generateColDefWith(this.field, this.headerName, this.precision)
  }

  public generateColDefs = (headerName?: string) => {
    return this.colDefBuilder.generateColDefs(headerName ?? this.headerName, this.includeBias)
  }
}

export const TempForecastField = new IndeterminateField('temp', 'Temp', 'number', 1, true)
export const RHForecastField = new IndeterminateField('rh', 'RH', 'number', 0, true)
export const WindDirForecastField = new IndeterminateField('windDirection', 'Wind Dir', 'number', 0, false)
export const WindSpeedForecastField = new IndeterminateField('windSpeed', 'Wind Speed', 'number', 1, true)
export const PrecipForecastField = new IndeterminateField('precip', 'Precip', 'number', 1, false)
export const buiField = new IndeterminateField('bui', 'BUI', 'number', 0, false)
export const isiField = new IndeterminateField('isi', 'ISI', 'number', 1, false)
export const fwiField = new IndeterminateField('fwi', 'FWI', 'number', 0, false)
export const ffmcField = new IndeterminateField('ffmc', 'FFMC', 'number', 1, false)
export const dmcField = new IndeterminateField('dmc', 'DMC', 'number', 0, false)
export const dcField = new IndeterminateField('dc', 'DC', 'number', 0, false)
export const dgrField = new IndeterminateField('dgr', 'DGR', 'number', 0, false)

export const MORECAST2_STATION_DATE_FIELDS: ColDefGenerator[] = [
  StationForecastField.getInstance(),
  DateForecastField.getInstance()
]

export const MORECAST2_FIELDS: ColDefGenerator[] = [
  StationForecastField.getInstance(),
  DateForecastField.getInstance(),
  TempForecastField,
  RHForecastField,
  WindDirForecastField,
  WindSpeedForecastField,
  PrecipForecastField
]

export const MORECAST2_FORECAST_FIELDS: ForecastColDefGenerator[] = [
  TempForecastField,
  RHForecastField,
  WindDirForecastField,
  WindSpeedForecastField,
  PrecipForecastField
]

export const MORECAST2_INDICES_FIELDS: ColDefGenerator[] = [
  buiField,
  isiField,
  fwiField,
  ffmcField,
  dmcField,
  dcField,
  dgrField
]
