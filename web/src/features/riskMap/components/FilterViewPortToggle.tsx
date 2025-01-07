import { theme } from '@/app/theme'
import { FormControl, FormLabel, RadioGroup, FormControlLabel, Radio } from '@mui/material'
import { isNull } from 'lodash'

interface FilterViewportToggleProps {
  withinViewport: boolean
  setWithinViewPort: React.Dispatch<React.SetStateAction<boolean>>
}

export const FilterViewportToggle = ({ withinViewport, setWithinViewPort }: FilterViewportToggleProps) => {
  const changeHandler = (_: React.ChangeEvent<{}>, value: string) => {
    if (!isNull(value)) {
      const toggle = value.toLocaleLowerCase() === 'true'
      setWithinViewPort(toggle)
    }
  }

  return (
    <FormControl
      variant="outlined"
      sx={{
        border: '1px solid rgba(0, 0, 0, 0.23)',
        borderRadius: '4px',
        padding: '8px 12px 4px',
        position: 'relative',
        margin: theme.spacing(1)
      }}
    >
      <FormLabel
        sx={{
          fontSize: '0.75rem',
          color: 'rgba(0, 0, 0, 0.6)',
          position: 'absolute',
          top: '-10px',
          left: '12px',
          backgroundColor: 'white',
          padding: '0 4px'
        }}
      >
        Time Frame
      </FormLabel>
      <RadioGroup row value={withinViewport} onChange={changeHandler}>
        <FormControlLabel
          value={true}
          control={
            <Radio inputProps={{ 'data-testid': 'actual-radio' } as React.InputHTMLAttributes<HTMLInputElement>} />
          }
          label="Filter Values to Viewport"
        />
        <FormControlLabel
          value={false}
          control={
            <Radio inputProps={{ 'data-testid': 'forecast-radio' } as React.InputHTMLAttributes<HTMLInputElement>} />
          }
          label="No Filter"
        />
      </RadioGroup>
    </FormControl>
  )
}
