import React from 'react'

import { ObservedValue } from 'api/observationAPI'
import SortableTableByDatetime, {
  Column
} from 'features/fireWeather/components/tables/SortableTableByDatetime'
import { HOURLY_VALUES_DECIMAL } from 'utils/constants'
import { formatDateInPST } from 'utils/date'

export const columns: Column[] = [
  {
    id: 'datetime',
    label: 'Date (PST)',
    minWidth: 120,
    align: 'left',
    formatDt: (value: string): string => formatDateInPST(value)
  },
  {
    id: 'temperature',
    label: 'Temp (°C)',
    align: 'right',
    format: (value: number): string => value.toFixed(HOURLY_VALUES_DECIMAL)
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
    format: (value: number): string => value.toFixed(HOURLY_VALUES_DECIMAL)
  },
  {
    id: 'wind_direction',
    label: 'Wind Dir',
    align: 'right',
    format: (value: number): number => Math.round(value)
  },
  {
    id: 'wind_speed',
    label: 'Wind Spd (km/h)',
    align: 'right',
    maxWidth: 80,
    format: (value: number): string => value.toFixed(HOURLY_VALUES_DECIMAL)
  },
  {
    id: 'precipitation',
    label: 'Precip (mm)',
    align: 'right',
    maxWidth: 70,
    format: (value: number): string => value.toFixed(HOURLY_VALUES_DECIMAL)
  },
  {
    id: 'ffmc',
    label: 'FFMC',
    align: 'right',
    format: (value: number): string => value.toFixed(HOURLY_VALUES_DECIMAL)
  },
  {
    id: 'isi',
    label: 'ISI',
    align: 'right',
    format: (value: number): string => value.toFixed(HOURLY_VALUES_DECIMAL)
  },
  {
    id: 'fwi',
    label: 'FWI',
    align: 'right',
    format: (value: number): string => value.toFixed(HOURLY_VALUES_DECIMAL)
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
