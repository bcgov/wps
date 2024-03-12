import { GridValueFormatterParams } from '@mui/x-data-grid'
import { DateTime } from 'luxon'
import {
  ColDefGenerator,
  ColumnDefBuilder,
  ForecastColDefGenerator,
  GC_HEADER,
  PRECIP_HEADER,
  RH_HEADER,
  TEMP_HEADER,
  WIND_DIR_HEADER,
  WIND_SPEED_HEADER
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

export class GrassCuringCWFISField implements ColDefGenerator {
  private static instance: GrassCuringCWFISField
  private colDefBuilder: ColumnDefBuilder

  readonly field = 'grassCuringCWFIS'
  readonly headerName = 'CWFIS'
  readonly type = 'number'
  readonly precision = 0
  private constructor() {
    this.colDefBuilder = new ColumnDefBuilder(
      this.field,
      this.headerName,
      this.type,
      this.precision,
      new GridComponentRenderer()
    )
  }

  public generateColDef = () => {
    return this.colDefBuilder.generateColDefWith(this.field, this.headerName, this.precision)
  }

  public generateColDefs = () => {
    return [this.generateColDef()]
  }

  public static getInstance(): GrassCuringCWFISField {
    if (!GrassCuringCWFISField.instance) {
      GrassCuringCWFISField.instance = new GrassCuringCWFISField()
    }

    return GrassCuringCWFISField.instance
  }
}

export class IndeterminateField implements ColDefGenerator, ForecastColDefGenerator {
  private colDefBuilder: ColumnDefBuilder

  public constructor(
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

  public getField = () => this.field

  public generateForecastColDef = (headerName?: string) => {
    return {
      ...this.colDefBuilder.generateForecastColDef(headerName ?? this.headerName)
    }
  }

  public generateColDef = () => {
    return this.colDefBuilder.generateColDefWith(this.field, this.headerName, this.precision)
  }

  public generateColDefs = (headerName?: string) => {
    return this.colDefBuilder.generateColDefs(headerName ?? this.headerName, this.includeBias)
  }
}

export const tempForecastField = new IndeterminateField('temp', TEMP_HEADER, 'number', 1, true)
export const rhForecastField = new IndeterminateField('rh', RH_HEADER, 'number', 0, true)
export const windDirForecastField = new IndeterminateField('windDirection', WIND_DIR_HEADER, 'number', 0, true)
export const windSpeedForecastField = new IndeterminateField('windSpeed', WIND_SPEED_HEADER, 'number', 1, true)
export const precipForecastField = new IndeterminateField('precip', PRECIP_HEADER, 'number', 1, true)
export const gcForecastField = new IndeterminateField('grassCuring', GC_HEADER, 'number', 0, false)

export const buiField = new IndeterminateField('buiCalc', 'BUI', 'number', 0, false)
export const isiField = new IndeterminateField('isiCalc', 'ISI', 'number', 1, false)
export const fwiField = new IndeterminateField('fwiCalc', 'FWI', 'number', 0, false)
export const ffmcField = new IndeterminateField('ffmcCalc', 'FFMC', 'number', 1, false)
export const dmcField = new IndeterminateField('dmcCalc', 'DMC', 'number', 0, false)
export const dcField = new IndeterminateField('dcCalc', 'DC', 'number', 0, false)
export const dgrField = new IndeterminateField('dgrCalc', 'DGR', 'number', 0, false)

export const MORECAST2_STATION_DATE_FIELDS: ColDefGenerator[] = [
  StationForecastField.getInstance(),
  DateForecastField.getInstance()
]

export const MORECAST2_FIELDS: ColDefGenerator[] = [
  StationForecastField.getInstance(),
  DateForecastField.getInstance(),
  tempForecastField,
  rhForecastField,
  windDirForecastField,
  windSpeedForecastField,
  precipForecastField
]

export const MORECAST2_FORECAST_FIELDS: ForecastColDefGenerator[] = [
  tempForecastField,
  rhForecastField,
  windDirForecastField,
  windSpeedForecastField,
  precipForecastField,
  gcForecastField
]

export const MORECAST2_INDEX_FIELDS: ForecastColDefGenerator[] = [
  ffmcField,
  dmcField,
  dcField,
  isiField,
  buiField,
  fwiField,
  dgrField
]

export const MORECAST2_GRASS_CURING_FORECAST_FIELD: ForecastColDefGenerator = gcForecastField

export const MORECAST2_GRASS_CURING_CWFIS_FIELD: ColDefGenerator = GrassCuringCWFISField.getInstance()
