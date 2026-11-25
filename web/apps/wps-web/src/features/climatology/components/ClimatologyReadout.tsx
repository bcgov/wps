import { Box, ButtonBase, Typography } from '@mui/material'
import type { ClimatologyVariable } from '@wps/api/climatologyAPI'
import { type ClimatologyRow, formatDay, formatRange, formatValue } from '@/features/climatology/climatologyRows'
import type { ComparedYear } from '@/features/climatology/comparedYears'
import { BAND_COLOURS, MEDIAN_COLOUR, YEAR_COLOUR } from '@/features/climatology/components/climatologyColours'

const NO_VALUE = '–'

export interface ReadoutItem {
  label: string
  value: string
  colour: string
  // A band is keyed with a filled box and a line with a stroke, as each is drawn.
  kind: 'band' | 'line'
  // The compared year the line is of, which can be highlighted.
  comparedYear?: number
}

/** The values of a day in each year: the selected one, then those it is compared with. */
export const yearItems = (
  row: ClimatologyRow,
  variable: ClimatologyVariable,
  year: number,
  comparedYears: ComparedYear[]
): ReadoutItem[] => {
  const format = (value: number | null | undefined) => (value == null ? NO_VALUE : formatValue(value, variable))
  return [
    { label: `${year}`, value: format(row.value), colour: YEAR_COLOUR, kind: 'line' },
    ...comparedYears.map(
      (compared): ReadoutItem => ({
        label: `${compared.year}`,
        value: format(row.compared[compared.year]),
        colour: compared.colour,
        kind: 'line',
        comparedYear: compared.year
      })
    )
  ]
}

/** The values a day has had over its history, from the top of the chart to the bottom. */
export const historyItems = (row: ClimatologyRow, variable: ClimatologyVariable): ReadoutItem[] => {
  const range = (low: number, high: number) => formatRange(low, high, variable)
  return [
    { label: 'Highest 10%', value: range(row.p90, row.maximum), colour: BAND_COLOURS.highest, kind: 'band' },
    { label: '75th to 90th', value: range(row.p75, row.p90), colour: BAND_COLOURS.high, kind: 'band' },
    { label: 'Middle half', value: range(row.p25, row.p75), colour: BAND_COLOURS.middle, kind: 'band' },
    { label: 'Median', value: formatValue(row.median, variable), colour: MEDIAN_COLOUR, kind: 'line' },
    { label: 'Lowest 25%', value: range(row.minimum, row.p25), colour: BAND_COLOURS.lowest, kind: 'band' }
  ]
}

/** What the values are drawn from: a count of years, or of stations when several are combined. */
export const readoutNotes = (row: ClimatologyRow, year: number): string[] => {
  if (row.stationCount <= 1) {
    return [`${row.count} years of record`]
  }
  const notes = [`History from ${row.count} values at ${row.stationCount} stations`]
  return row.valueStationCount === null ? notes : [`${year} is the mean of ${row.valueStationCount} stations`, ...notes]
}

const Key = ({ item, thickness }: { item: ReadoutItem; thickness: number }) => (
  <Box
    component="span"
    aria-hidden
    sx={{
      flexShrink: 0,
      ...(item.kind === 'band'
        ? {
            width: 14,
            height: 14,
            marginX: '3px',
            backgroundColor: item.colour,
            // The lightest bands are close to the page's white.
            border: '1px solid',
            borderColor: 'divider'
          }
        : { width: 20, borderTop: `${thickness}px solid ${item.colour}` })
    }}
  />
)

const nameSx = { display: 'flex', alignItems: 'center', gap: 1, width: '100%', justifyContent: 'flex-start' }

interface RowsProps {
  items: ReadoutItem[]
  // The label of the item to set in bold, or null with none.
  strong: string | null
  highlightedYear: number | null
  onHighlight: (year: number | null) => void
}

const Rows = ({ items, strong, highlightedYear, onHighlight }: RowsProps) => (
  <Box component="tbody" sx={{ '& + tbody::before': { content: '""', display: 'block', height: 8 } }}>
    {items.map(item => {
      const highlighted = item.comparedYear !== undefined && item.comparedYear === highlightedYear
      const weight = highlighted || item.label === strong ? 600 : 400
      const name = (
        <>
          <Key item={item} thickness={highlighted || item.label === strong ? 3 : 2} />
          <Typography variant="body2" component="span" sx={{ fontWeight: weight, whiteSpace: 'nowrap' }}>
            {item.label}
          </Typography>
        </>
      )
      return (
        <tr key={item.label}>
          <Box component="th" scope="row" sx={{ padding: 0, textAlign: 'left', fontWeight: 400 }}>
            {item.comparedYear === undefined ? (
              <Box sx={nameSx}>{name}</Box>
            ) : (
              <ButtonBase
                aria-pressed={highlighted}
                onClick={() => onHighlight(highlighted ? null : (item.comparedYear ?? null))}
                sx={{ ...nameSx, borderRadius: 1, '&:hover, &:focus-visible': { bgcolor: 'action.hover' } }}
              >
                {name}
              </ButtonBase>
            )}
          </Box>
          <Box component="td" sx={{ padding: '3px 0 3px 8px', textAlign: 'right', whiteSpace: 'nowrap' }}>
            <Typography
              variant="body2"
              component="span"
              sx={{ fontWeight: weight === 600 ? 600 : 500, fontVariantNumeric: 'tabular-nums' }}
            >
              {item.value}
            </Typography>
          </Box>
        </tr>
      )
    })}
  </Box>
)

export interface ClimatologyReadoutProps {
  // The day to show the values of.
  row: ClimatologyRow
  variable: ClimatologyVariable
  year: number
  comparedYears: ComparedYear[]
  // The compared year that stands out on the chart, or null with none.
  highlightedYear: number | null
  onHighlight: (year: number | null) => void
}

/**
 * What each line and band on the chart is, and its value on a day. It is beside the chart, as a
 * tooltip beside the pointer would cover the lines being read. Choosing a compared year makes its
 * line stand out.
 */
const ClimatologyReadout = ({
  row,
  variable,
  year,
  comparedYears,
  highlightedYear,
  onHighlight
}: ClimatologyReadoutProps) => (
  <Box data-testid="climatology-readout" sx={{ flex: '0 1 250px', paddingTop: 1 }}>
    <Box component="table" aria-live="polite" sx={{ width: '100%', borderCollapse: 'collapse' }}>
      <Typography
        variant="subtitle2"
        component="caption"
        sx={{ textAlign: 'left', captionSide: 'top', paddingBottom: 0.5 }}
      >
        {formatDay(row.time)}
      </Typography>
      <Rows
        items={yearItems(row, variable, year, comparedYears)}
        strong={`${year}`}
        highlightedYear={highlightedYear}
        onHighlight={onHighlight}
      />
      <Rows
        items={historyItems(row, variable)}
        strong={null}
        highlightedYear={highlightedYear}
        onHighlight={onHighlight}
      />
    </Box>
    {readoutNotes(row, year).map(note => (
      <Typography key={note} variant="caption" color="text.secondary" sx={{ display: 'block', marginTop: 0.5 }}>
        {note}
      </Typography>
    ))}
  </Box>
)

export default ClimatologyReadout
