import React from 'react'
import { Button, TextField } from '@mui/material'
import {
  GridColDef,
  GridColumnHeaderParams,
  GridRenderCellParams,
  GridValueFormatterParams,
  GridValueGetterParams,
  GridValueSetterParams
} from '@mui/x-data-grid'
import { DateTime } from 'luxon'
import { ModelChoice } from 'api/moreCast2API'

const NOT_AVAILABLE = 'N/A'

export type Morecast2Field = 'stationName' | 'forDate' | 'temp' | 'rh' | 'windDirection' | 'windSpeed' | 'precip'

export interface ForecastField {
  field: Morecast2Field
  headerName: string
  type: 'number' | 'string'
  precision: 0 | 1
  generateColDef: () => GridColDef
}

class StationForecastField implements ForecastField {
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

class DateForecastField implements ForecastField {
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

class GridNumberRenderer {
  protected renderHeaderWith = (params: GridColumnHeaderParams) => {
    return <Button>{params.colDef.headerName}</Button>
  }
  protected renderCellWith = (params: GridRenderCellParams, field: string) => (
    <TextField size="small" label={params.row[field].choice} value={params.formattedValue}></TextField>
  )

  predictionItemValueSetter = (params: GridValueSetterParams, field: string, precision: number) => {
    const oldValue = params.row[field].value
    const newValue = Number(params.value)

    if (isNaN(oldValue) && isNaN(newValue)) {
      return { ...params.row }
    }
    // Check if the user has edited the value. If so, update the value and choice to reflect the Manual edit.
    if (newValue.toFixed(precision) !== params.row[field].value.toFixed(precision)) {
      params.row[field].choice = ModelChoice.MANUAL
      params.row[field].value = newValue
    }

    return { ...params.row }
  }

  predictionItemValueFormatter = (params: GridValueFormatterParams, precision: number) => {
    const value = Number.parseFloat(params?.value)

    return isNaN(value) ? NOT_AVAILABLE : value.toFixed(precision)
  }

  predictionItemValueGetter = (params: GridValueGetterParams, precision: number) => {
    const value = params?.value?.value
    if (isNaN(value)) {
      return 'NaN'
    }
    return value.toFixed(precision)
  }

  public generateColDefWith = (field: string, headerName: string, precision: number) => {
    return {
      field: field,
      disableColumnMenu: true,
      disableReorder: true,
      editable: true,
      headerName: headerName,
      sortable: false,
      type: 'number',
      width: 120,
      renderHeader: (params: GridColumnHeaderParams) => {
        return this.renderHeaderWith(params)
      },
      renderCell: (params: GridRenderCellParams) => {
        return this.renderCellWith(params, field)
      },
      valueFormatter: (params: GridValueFormatterParams) => {
        return this.valueFormatterWith(params, precision)
      },
      valueGetter: (params: GridValueGetterParams) => this.valueGetterWith(params, precision),
      valueSetter: (params: GridValueSetterParams) => this.valueSetterWith(params, field, precision)
    }
  }

  protected valueFormatterWith = (params: GridValueFormatterParams, precision: number) =>
    this.predictionItemValueFormatter(params, precision)
  protected valueGetterWith = (params: GridValueGetterParams, precision: number) =>
    this.predictionItemValueGetter(params, precision)
  protected valueSetterWith = (params: GridValueSetterParams, field: string, precision: number) =>
    this.predictionItemValueSetter(params, field, precision)
}

class TempForecastField extends GridNumberRenderer implements ForecastField {
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

class RHForecastField extends GridNumberRenderer implements ForecastField {
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

class WindDirForecastField extends GridNumberRenderer implements ForecastField {
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

class WindSpeedForecastField extends GridNumberRenderer implements ForecastField {
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

class PrecipForecastField extends GridNumberRenderer implements ForecastField {
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

export const MORECAST2_GRID_COLUMNS: ForecastField[] = [
  StationForecastField.getInstance(),
  DateForecastField.getInstance(),
  TempForecastField.getInstance(),
  RHForecastField.getInstance(),
  WindDirForecastField.getInstance(),
  WindSpeedForecastField.getInstance(),
  PrecipForecastField.getInstance()
]
