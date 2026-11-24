import { Box, Typography } from '@mui/material'
import type { ClimatologyVariable } from '@wps/api/climatologyAPI'
import { type ClimatologyRow, formatDay, formatValue } from '@/features/climatology/climatologyRows'
import type { ComparedYear } from '@/features/climatology/comparedYears'

interface ReadoutItem {
  label: string
  value: string
  // The colour of the line the value is from, for a compared year.
  colour?: string
}

/** The values of a day, in the order they are read: the year, the years compared, then the history. */
export const readoutItems = (
  row: ClimatologyRow,
  variable: ClimatologyVariable,
  year: number,
  comparedYears: ComparedYear[]
): ReadoutItem[] => {
  const format = (value: number) => formatValue(value, variable)
  const combined = row.stationCount > 1
  const items: (ReadoutItem | null)[] = [
    row.value === null
      ? null
      : {
          label: `${year}`,
          value:
            combined && row.valueStationCount !== null
              ? `${format(row.value)} (${row.valueStationCount} stations)`
              : format(row.value)
        },
    ...comparedYears.map(({ year: comparedYear, colour }) =>
      row.compared[comparedYear] === undefined
        ? null
        : { label: `${comparedYear}`, value: format(row.compared[comparedYear]), colour }
    ),
    { label: 'Median', value: format(row.median) },
    { label: 'Middle half', value: `${format(row.p25)} to ${format(row.p75)}` },
    { label: '90th percentile', value: format(row.p90) },
    { label: 'Lowest to highest', value: `${format(row.minimum)} to ${format(row.maximum)}` },
    combined
      ? { label: 'Drawn from', value: `${row.count} values at ${row.stationCount} stations` }
      : { label: 'Years of record', value: `${row.count}` }
  ]
  return items.filter((item): item is ReadoutItem => item !== null)
}

export interface ClimatologyReadoutProps {
  // The day pointed at, or null with none.
  row: ClimatologyRow | null
  variable: ClimatologyVariable
  year: number
  comparedYears: ComparedYear[]
}

/**
 * The values of the day pointed at on the chart, in one line above it. A tooltip beside the
 * pointer would cover the lines being read.
 */
const ClimatologyReadout = ({ row, variable, year, comparedYears }: ClimatologyReadoutProps) => (
  <Box
    data-testid="climatology-readout"
    aria-live="polite"
    sx={{
      display: 'flex',
      flexWrap: 'wrap',
      alignItems: 'baseline',
      columnGap: 2,
      rowGap: 0.25,
      // Room for a wrapped line, so the chart below does not jump as the pointer moves.
      minHeight: '2.6em',
      paddingX: 1
    }}
  >
    {row === null ? (
      <Typography variant="body2" color="text.secondary">
        Point at a day on the chart, or focus it and use the arrow keys, to see its values.
      </Typography>
    ) : (
      <>
        <Typography variant="body2" component="span" sx={{ fontWeight: 600 }}>
          {formatDay(row.time)}
        </Typography>
        {readoutItems(row, variable, year, comparedYears).map(item => (
          <Typography key={item.label} variant="body2" component="span">
            {item.colour && (
              <Box
                component="span"
                aria-hidden
                sx={{
                  display: 'inline-block',
                  width: 10,
                  height: 10,
                  marginRight: 0.5,
                  borderRadius: '50%',
                  backgroundColor: item.colour
                }}
              />
            )}
            <Box component="span" sx={{ color: 'text.secondary' }}>
              {item.label}
            </Box>{' '}
            <Box component="span" sx={{ fontWeight: 500 }}>
              {item.value}
            </Box>
          </Typography>
        ))}
      </>
    )}
  </Box>
)

export default ClimatologyReadout
