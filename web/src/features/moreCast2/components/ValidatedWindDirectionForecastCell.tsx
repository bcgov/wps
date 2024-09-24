import { Grid } from '@mui/material'
import { GridRenderCellParams } from '@mui/x-data-grid-pro'
import ValidatedCell from '@/features/moreCast2/components/ValidatedCell'

interface ForecastCellProps {
  disabled: boolean
  label: string
  value: Pick<GridRenderCellParams, 'formattedValue'>
  validator?: (value: string) => string
}

const ValidatedWindDirectionForecastCell = ({ disabled, label, value, validator }: ForecastCellProps) => {
  const error = validator ? validator(value as string) : ''

  return (
    <Grid container sx={{ justifyContent: 'center', alignItems: 'center' }}>
      <Grid item xs={8}>
        <ValidatedCell disabled={disabled} label={label} value={value} error={error !== ''} invalid={error} />
      </Grid>
    </Grid>
  )
}

export default ValidatedWindDirectionForecastCell
