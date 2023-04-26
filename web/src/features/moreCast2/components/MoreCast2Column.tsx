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

export class TempForecastField implements ColDefGenerator, ForecastColDefGenerator {
  private static instance: TempForecastField

  static readonly field = 'temp'
  static readonly headerName = 'Temp'
  static readonly type = 'number'
  static readonly precision = 1
  private constructor(readonly colDefBuilder: ColumnDefBuilder) {}
  public generateForecastColDef = (headerName?: string) => {
    return this.colDefBuilder.generateForecastColDef(headerName)
  }
  public generateColDef = () => {
    return this.colDefBuilder.generateColDefWith(
      TempForecastField.field,
      TempForecastField.headerName,
      TempForecastField.precision
    )
  }

  public generateColDefs = (headerName?: string) => {
    return this.colDefBuilder.generateColDefs(headerName)
  }

  public static getInstance(): TempForecastField {
    if (!TempForecastField.instance) {
      TempForecastField.instance = new TempForecastField(
        new ColumnDefBuilder(
          TempForecastField.field,
          TempForecastField.headerName,
          TempForecastField.type,
          TempForecastField.precision,
          new GridComponentRenderer()
        )
      )
    }

    return TempForecastField.instance
  }
}

export class RHForecastField implements ColDefGenerator, ForecastColDefGenerator {
  private static instance: RHForecastField

  static readonly field = 'rh'
  static readonly headerName = 'RH'
  static readonly type = 'number'
  static readonly precision = 0
  private constructor(readonly colDefBuilder: ColumnDefBuilder) {}

  public generateForecastColDef = (headerName?: string) => {
    return this.colDefBuilder.generateForecastColDef(headerName)
  }
  public generateColDef = () => {
    return this.colDefBuilder.generateColDefWith(
      RHForecastField.field,
      RHForecastField.headerName,
      RHForecastField.precision
    )
  }

  public generateColDefs = (headerName?: string) => {
    return this.colDefBuilder.generateColDefs(headerName)
  }

  public static getInstance(): RHForecastField {
    if (!RHForecastField.instance) {
      RHForecastField.instance = new RHForecastField(
        new ColumnDefBuilder(
          RHForecastField.field,
          RHForecastField.headerName,
          RHForecastField.type,
          RHForecastField.precision,
          new GridComponentRenderer()
        )
      )
    }

    return RHForecastField.instance
  }
}

export class WindDirForecastField implements ColDefGenerator, ForecastColDefGenerator {
  private static instance: WindDirForecastField

  static readonly field = 'windDirection'
  static readonly headerName = 'Wind Dir'
  static readonly type = 'number'
  static readonly precision = 0
  private constructor(readonly colDefBuilder: ColumnDefBuilder) {}

  public generateForecastColDef = (headerName?: string) => {
    return this.colDefBuilder.generateForecastColDef(headerName)
  }
  public generateColDef = () => {
    return this.colDefBuilder.generateColDefWith(
      WindDirForecastField.field,
      WindDirForecastField.headerName,
      WindDirForecastField.precision
    )
  }

  public generateColDefs = (headerName?: string) => {
    return this.colDefBuilder.generateColDefs(headerName)
  }

  public static getInstance(): WindDirForecastField {
    if (!WindDirForecastField.instance) {
      WindDirForecastField.instance = new WindDirForecastField(
        new ColumnDefBuilder(
          WindDirForecastField.field,
          WindDirForecastField.headerName,
          WindDirForecastField.type,
          WindDirForecastField.precision,
          new GridComponentRenderer()
        )
      )
    }

    return WindDirForecastField.instance
  }
}

export class WindSpeedForecastField implements ColDefGenerator, ForecastColDefGenerator {
  private static instance: WindSpeedForecastField

  static readonly field = 'windSpeed'
  static readonly headerName = 'Wind Speed'
  static readonly type = 'number'
  static readonly precision = 1
  private constructor(readonly colDefBuilder: ColumnDefBuilder) {}

  public generateForecastColDef = (headerName?: string) => {
    return this.colDefBuilder.generateForecastColDef(headerName)
  }
  public generateColDef = () => {
    return this.colDefBuilder.generateColDefWith(
      WindSpeedForecastField.field,
      WindSpeedForecastField.headerName,
      WindSpeedForecastField.precision
    )
  }

  public generateColDefs = (headerName?: string) => {
    return this.colDefBuilder.generateColDefs(headerName)
  }

  public static getInstance(): WindSpeedForecastField {
    if (!WindSpeedForecastField.instance) {
      WindSpeedForecastField.instance = new WindSpeedForecastField(
        new ColumnDefBuilder(
          WindSpeedForecastField.field,
          WindSpeedForecastField.headerName,
          WindSpeedForecastField.type,
          WindSpeedForecastField.precision,
          new GridComponentRenderer()
        )
      )
    }

    return WindSpeedForecastField.instance
  }
}

export class PrecipForecastField implements ColDefGenerator, ForecastColDefGenerator {
  private static instance: PrecipForecastField

  static readonly field = 'precip'
  static readonly headerName = 'Precip'
  static readonly type = 'number'
  static readonly precision = 1
  private constructor(readonly colDefBuilder: ColumnDefBuilder) {}

  public generateForecastColDef = (headerName?: string) => {
    return this.colDefBuilder.generateForecastColDef(headerName)
  }
  public generateColDef = () => {
    return this.colDefBuilder.generateColDefWith(
      PrecipForecastField.field,
      PrecipForecastField.headerName,
      PrecipForecastField.precision
    )
  }

  public generateColDefs = (headerName?: string) => {
    return this.colDefBuilder.generateColDefs(headerName)
  }

  public static getInstance(): PrecipForecastField {
    if (!PrecipForecastField.instance) {
      PrecipForecastField.instance = new PrecipForecastField(
        new ColumnDefBuilder(
          PrecipForecastField.field,
          PrecipForecastField.headerName,
          PrecipForecastField.type,
          PrecipForecastField.precision,
          new GridComponentRenderer()
        )
      )
    }

    return PrecipForecastField.instance
  }
}

export const MORECAST2_STATION_DATE_FIELDS: ColDefGenerator[] = [
  StationForecastField.getInstance(),
  DateForecastField.getInstance()
]

export const MORECAST2_FIELDS: ColDefGenerator[] = [
  StationForecastField.getInstance(),
  DateForecastField.getInstance(),
  TempForecastField.getInstance(),
  RHForecastField.getInstance(),
  WindDirForecastField.getInstance(),
  WindSpeedForecastField.getInstance(),
  PrecipForecastField.getInstance()
]

export const MORECAST2_FORECAST_FIELDS: ForecastColDefGenerator[] = [
  TempForecastField.getInstance(),
  RHForecastField.getInstance(),
  WindDirForecastField.getInstance(),
  WindSpeedForecastField.getInstance(),
  PrecipForecastField.getInstance()
]
