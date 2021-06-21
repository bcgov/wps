import React from 'react'

import { ObservedValue } from 'api/observationAPI'
import SortableTableByDatetime, {
  Column
} from 'features/fireWeather/components/tables/SortableTableByDatetime'
import { FFMC_VALUES_DECIMAL, ISI_VALUES_DECIMAL } from 'utils/constants'
import {
  formatWindDirection,
  formatWindSpeed,
  formatTemperature,
  formatRelativeHumidity,
  formatPrecipitation
} from 'utils/format'
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
    format: formatTemperature,
    maxWidth: 70
  },
  {
    id: 'relative_humidity',
    label: 'RH (%)',
    align: 'right',
    format: formatRelativeHumidity,
    maxWidth: 70
  },
  {
    id: 'dewpoint',
    label: 'Dew Point (°C)',
    align: 'right',
    maxWidth: 70,
    format: formatTemperature
  },
  {
    id: 'wind_direction',
    label: 'Wind Dir (°)',
    align: 'right',
    format: formatWindDirection,
    maxWidth: 70
  },
  {
    id: 'wind_speed',
    label: 'Wind Spd (km/h)',
    align: 'right',
    maxWidth: 70,
    format: formatWindSpeed
  },
  {
    id: 'precipitation',
    label: 'Precip (mm)',
    align: 'right',
    maxWidth: 70,
    format: formatPrecipitation
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
