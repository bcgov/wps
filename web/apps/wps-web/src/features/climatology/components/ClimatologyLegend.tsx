import { Box, ButtonBase, Typography } from '@mui/material'
import type { ComparedYear } from '@/features/climatology/comparedYears'
import { BAND_COLOURS, MEDIAN_COLOUR, YEAR_COLOUR } from '@/features/climatology/components/ClimatologyChart'

interface LegendItem {
  label: string
  colour: string
  // A band is keyed with a filled box and a line with a stroke, as each is drawn.
  kind: 'band' | 'line'
  thickness?: number
}

const Key = ({ item }: { item: LegendItem }) => (
  <Box
    aria-hidden
    sx={
      item.kind === 'band'
        ? {
            width: 14,
            height: 14,
            borderRadius: '2px',
            backgroundColor: item.colour,
            // The lightest bands are close to the page's white.
            border: '1px solid',
            borderColor: 'divider'
          }
        : { width: 22, height: 0, borderTop: `${item.thickness}px solid ${item.colour}` }
    }
  />
)

const HISTORY: LegendItem[] = [
  { label: 'Historical median', colour: MEDIAN_COLOUR, kind: 'line', thickness: 2 },
  { label: 'Highest 10%', colour: BAND_COLOURS.highest, kind: 'band' },
  { label: '75th to 90th percentile', colour: BAND_COLOURS.high, kind: 'band' },
  { label: 'Middle half (25th to 75th)', colour: BAND_COLOURS.middle, kind: 'band' },
  { label: 'Lowest 25%', colour: BAND_COLOURS.lowest, kind: 'band' }
]

const entrySx = { display: 'flex', alignItems: 'center', gap: 1 }

export interface ClimatologyLegendProps {
  // Names the line of the selected year, such as 2026, or 2026 (mean of stations).
  yearLabel: string
  comparedYears: ComparedYear[]
  // The compared year that stands out on the chart, or null with none.
  highlightedYear: number | null
  onHighlight: (year: number | null) => void
}

/** What each line and band is. Choosing a compared year makes its line stand out. */
const ClimatologyLegend = ({ yearLabel, comparedYears, highlightedYear, onHighlight }: ClimatologyLegendProps) => (
  <Box
    component="ul"
    data-testid="climatology-legend"
    sx={{ display: 'flex', flexWrap: 'wrap', columnGap: 3, rowGap: 1, listStyle: 'none', padding: 0, margin: 0 }}
  >
    <Box component="li" sx={entrySx}>
      <Key item={{ label: yearLabel, colour: YEAR_COLOUR, kind: 'line', thickness: 3 }} />
      <Typography variant="body2">{yearLabel}</Typography>
    </Box>
    {comparedYears.map(({ year, colour }) => {
      const highlighted = year === highlightedYear
      return (
        <Box component="li" key={year}>
          <ButtonBase
            aria-pressed={highlighted}
            onClick={() => onHighlight(highlighted ? null : year)}
            sx={{ ...entrySx, borderRadius: 1, paddingX: 0.5, '&:hover, &:focus-visible': { bgcolor: 'action.hover' } }}
          >
            <Key item={{ label: `${year}`, colour, kind: 'line', thickness: highlighted ? 3 : 2 }} />
            <Typography variant="body2" sx={{ fontWeight: highlighted ? 600 : 400 }}>
              {year}
            </Typography>
          </ButtonBase>
        </Box>
      )
    })}
    {HISTORY.map(item => (
      <Box component="li" key={item.label} sx={entrySx}>
        <Key item={item} />
        <Typography variant="body2">{item.label}</Typography>
      </Box>
    ))}
  </Box>
)

export default ClimatologyLegend
