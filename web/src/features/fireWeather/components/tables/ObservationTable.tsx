import React from 'react'

import { ObservedValue } from 'api/observationAPI'
import SortableTableByDatetime, {
  Column
} from 'features/fireWeather/components/tables/SortableTableByDatetime'
import {
  FFMC_VALUES_DECIMAL,
  ISI_VALUES_DECIMAL,
  PRECIP_VALUES_DECIMAL,
  TEMPERATURE_VALUES_DECIMAL,
  WIND_SPEED_VALUES_DECIMAL,
  WIND_DIRECTION_VALUES_DECIMAL
} from 'utils/constants'
import { formatDateInPST } from 'utils/date'

export const columns: Column[] = [
  {
    id: 'datetime',
    label: 'Date (PST)',
    minWidth: 135,
    align: 'left',
    formatDt: (value: string): string => formatDateInPST(value)
  },
  {
    id: 'temperature',
    label: 'Temp (°C)',
    align: 'right',
    format: (value: number): string => value.toFixed(TEMPERATURE_VALUES_DECIMAL)
  },
  {
    id: 'relative_humidity',
    label: 'RH (%)',
    align: 'right',
    format: (value: number): number => Math.round(value)
  },
  {
    id: 'dewpoint',
    label: 'Dew Point (°C)',
    align: 'right',
    maxWidth: 90,
    format: (value: number): string => value.toFixed(TEMPERATURE_VALUES_DECIMAL)
  },
  {
    id: 'wind_direction',
    label: 'Wind Dir °',
    align: 'right',
    format: (value: number): string =>
      value.toFixed(WIND_DIRECTION_VALUES_DECIMAL).padStart(3, '0')
  },
  {
    id: 'wind_speed',
    label: 'Wind Spd (km/h)',
    align: 'right',
    maxWidth: 80,
    format: (value: number): string => value.toFixed(WIND_SPEED_VALUES_DECIMAL)
  },
  {
    id: 'precipitation',
    label: 'Precip (mm)',
    align: 'right',
    maxWidth: 70,
    format: (value: number): string => value.toFixed(PRECIP_VALUES_DECIMAL)
  },
  {
    id: 'ffmc',
    label: 'FFMC',
    align: 'right',
    format: (value: number): string => value.toFixed(FFMC_VALUES_DECIMAL)
  },
  {
    id: 'isi',
    label: 'ISI',
    align: 'right',
    format: (value: number): string => value.toFixed(ISI_VALUES_DECIMAL)
  },
  {
    id: 'fwi',
    label: 'FWI',
    align: 'right',
    format: (value: number): string => value.toFixed(FFMC_VALUES_DECIMAL)
  }
]

interface Props {
  testId: string
  title: string
  rows: ObservedValue[] | undefined
}

const ObservationTable = (props: Props) => {
  return <SortableTableByDatetime {...props} columns={columns} />
}

export default React.memo(ObservationTable)
