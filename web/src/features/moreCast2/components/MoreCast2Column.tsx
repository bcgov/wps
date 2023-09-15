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
    return this.colDefBuilder.generateColDefs(headerName, true)
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
    return this.colDefBuilder.generateColDefs(headerName, true)
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
    return this.colDefBuilder.generateColDefs(headerName, false)
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
    return this.colDefBuilder.generateColDefs(headerName, true)
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
    return this.colDefBuilder.generateColDefs(headerName, false)
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

export class ffmcField implements ColDefGenerator, ForecastColDefGenerator {
  private static instance: ffmcField

  static readonly field = 'ffmc'
  static readonly headerName = 'FFMC'
  static readonly type = 'number'
  static readonly precision = 2
  private constructor(readonly colDefBuilder: ColumnDefBuilder) {}

  public generateForecastColDef = (headerName?: string) => {
    return this.colDefBuilder.generateForecastColDef(headerName)
  }
  public generateColDef = () => {
    return this.colDefBuilder.generateColDefWith(ffmcField.field, ffmcField.headerName, ffmcField.precision)
  }

  public generateColDefs = (headerName?: string) => {
    return this.colDefBuilder.generateColDefs(headerName, false)
  }

  public static getInstance(): ffmcField {
    if (!ffmcField.instance) {
      ffmcField.instance = new ffmcField(
        new ColumnDefBuilder(
          ffmcField.field,
          ffmcField.headerName,
          ffmcField.type,
          ffmcField.precision,
          new GridComponentRenderer()
        )
      )
    }

    return ffmcField.instance
  }
}

export class dmcField implements ColDefGenerator, ForecastColDefGenerator {
  private static instance: dmcField

  static readonly field = 'dmc'
  static readonly headerName = 'DMC'
  static readonly type = 'number'
  static readonly precision = 0
  private constructor(readonly colDefBuilder: ColumnDefBuilder) {}

  public generateForecastColDef = (headerName?: string) => {
    return this.colDefBuilder.generateForecastColDef(headerName)
  }
  public generateColDef = () => {
    return this.colDefBuilder.generateColDefWith(dmcField.field, dmcField.headerName, dmcField.precision)
  }

  public generateColDefs = (headerName?: string) => {
    return this.colDefBuilder.generateColDefs(headerName, false)
  }

  public static getInstance(): dmcField {
    if (!dmcField.instance) {
      dmcField.instance = new dmcField(
        new ColumnDefBuilder(
          dmcField.field,
          dmcField.headerName,
          dmcField.type,
          dmcField.precision,
          new GridComponentRenderer()
        )
      )
    }

    return dmcField.instance
  }
}

export class dcField implements ColDefGenerator, ForecastColDefGenerator {
  private static instance: dcField

  static readonly field = 'dc'
  static readonly headerName = 'DC'
  static readonly type = 'number'
  static readonly precision = 0
  private constructor(readonly colDefBuilder: ColumnDefBuilder) {}

  public generateForecastColDef = (headerName?: string) => {
    return this.colDefBuilder.generateForecastColDef(headerName)
  }
  public generateColDef = () => {
    return this.colDefBuilder.generateColDefWith(dcField.field, dcField.headerName, dcField.precision)
  }

  public generateColDefs = (headerName?: string) => {
    return this.colDefBuilder.generateColDefs(headerName, false)
  }

  public static getInstance(): dcField {
    if (!dcField.instance) {
      dcField.instance = new dcField(
        new ColumnDefBuilder(
          dcField.field,
          dcField.headerName,
          dcField.type,
          dcField.precision,
          new GridComponentRenderer()
        )
      )
    }

    return dcField.instance
  }
}

export class isiField implements ColDefGenerator, ForecastColDefGenerator {
  private static instance: isiField

  static readonly field = 'isi'
  static readonly headerName = 'ISI'
  static readonly type = 'number'
  static readonly precision = 1
  private constructor(readonly colDefBuilder: ColumnDefBuilder) {}

  public generateForecastColDef = (headerName?: string) => {
    return this.colDefBuilder.generateForecastColDef(headerName)
  }
  public generateColDef = () => {
    return this.colDefBuilder.generateColDefWith(isiField.field, isiField.headerName, isiField.precision)
  }

  public generateColDefs = (headerName?: string) => {
    return this.colDefBuilder.generateColDefs(headerName, false)
  }

  public static getInstance(): isiField {
    if (!isiField.instance) {
      isiField.instance = new isiField(
        new ColumnDefBuilder(
          isiField.field,
          isiField.headerName,
          isiField.type,
          isiField.precision,
          new GridComponentRenderer()
        )
      )
    }

    return isiField.instance
  }
}

export class buiField implements ColDefGenerator, ForecastColDefGenerator {
  private static instance: buiField

  static readonly field = 'bui'
  static readonly headerName = 'BUI'
  static readonly type = 'number'
  static readonly precision = 0
  private constructor(readonly colDefBuilder: ColumnDefBuilder) {}

  public generateForecastColDef = (headerName?: string) => {
    return this.colDefBuilder.generateForecastColDef(headerName)
  }
  public generateColDef = () => {
    return this.colDefBuilder.generateColDefWith(buiField.field, buiField.headerName, buiField.precision)
  }

  public generateColDefs = (headerName?: string) => {
    return this.colDefBuilder.generateColDefs(headerName, false)
  }

  public static getInstance(): buiField {
    if (!buiField.instance) {
      buiField.instance = new buiField(
        new ColumnDefBuilder(
          buiField.field,
          buiField.headerName,
          buiField.type,
          buiField.precision,
          new GridComponentRenderer()
        )
      )
    }

    return buiField.instance
  }
}

export class fwiField implements ColDefGenerator, ForecastColDefGenerator {
  private static instance: fwiField

  static readonly field = 'fwi'
  static readonly headerName = 'FWI'
  static readonly type = 'number'
  static readonly precision = 0
  private constructor(readonly colDefBuilder: ColumnDefBuilder) {}

  public generateForecastColDef = (headerName?: string) => {
    return this.colDefBuilder.generateForecastColDef(headerName)
  }
  public generateColDef = () => {
    return this.colDefBuilder.generateColDefWith(fwiField.field, fwiField.headerName, fwiField.precision)
  }

  public generateColDefs = (headerName?: string) => {
    return this.colDefBuilder.generateColDefs(headerName, false)
  }

  public static getInstance(): fwiField {
    if (!fwiField.instance) {
      fwiField.instance = new fwiField(
        new ColumnDefBuilder(
          fwiField.field,
          fwiField.headerName,
          fwiField.type,
          fwiField.precision,
          new GridComponentRenderer()
        )
      )
    }

    return fwiField.instance
  }
}

export class dgrField implements ColDefGenerator, ForecastColDefGenerator {
  private static instance: dgrField

  static readonly field = 'dgr'
  static readonly headerName = 'DGR'
  static readonly type = 'number'
  static readonly precision = 0
  private constructor(readonly colDefBuilder: ColumnDefBuilder) {}

  public generateForecastColDef = (headerName?: string) => {
    return this.colDefBuilder.generateForecastColDef(headerName)
  }
  public generateColDef = () => {
    return this.colDefBuilder.generateColDefWith(dgrField.field, dgrField.headerName, dgrField.precision)
  }

  public generateColDefs = (headerName?: string) => {
    return this.colDefBuilder.generateColDefs(headerName, false)
  }

  public static getInstance(): dgrField {
    if (!dgrField.instance) {
      dgrField.instance = new dgrField(
        new ColumnDefBuilder(
          dgrField.field,
          dgrField.headerName,
          dgrField.type,
          dgrField.precision,
          new GridComponentRenderer()
        )
      )
    }

    return dgrField.instance
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

export const MORECAST2_INDICES_FIELDS: ColDefGenerator[] = [
  buiField.getInstance(),
  isiField.getInstance(),
  fwiField.getInstance(),
  ffmcField.getInstance(),
  dmcField.getInstance(),
  dcField.getInstance(),
  dgrField.getInstance()
]
