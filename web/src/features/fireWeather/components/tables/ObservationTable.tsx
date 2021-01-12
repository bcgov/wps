import React from 'react'

import { ObservedValue } from 'api/observationAPI'
import SortableTableByDatetime, {
  Column
} from 'features/fireWeather/components/tables/SortableTableByDatetime'
import { HOURLY_VALUES_DECIMAL } from 'utils/constants'
import { formatDateInPDT } from 'utils/date'

export const columns: Column[] = [
  {
    id: 'datetime',
    label: 'Date (PDT)',
    minWidth: 120,
    align: 'left',
    formatDt: (value: string): string => formatDateInPDT(value)
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
    id: 'wind_direction',
    label: 'Wind Dir',
    align: 'right',
    format: (value: number): number => Math.round(value)
  },
  {
    id: 'wind_speed',
    label: 'Wind Spd (km/h)',
    minWidth: 70,
    maxWidth: 100,
    align: 'right',
    format: (value: number): string => value.toFixed(HOURLY_VALUES_DECIMAL)
  },
  {
    id: 'precipitation',
    label: 'Precip (mm/cm)',
    minWidth: 70,
    maxWidth: 100,
    align: 'right',
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
