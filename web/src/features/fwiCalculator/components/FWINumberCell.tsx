import { OutlinedTextFieldProps, TableCell, TextField } from '@material-ui/core'
import { FWIInputParameters } from 'features/fwiCalculator/components/BasicFWIGrid'
import React, { ChangeEvent } from 'react'

export interface FWIStationCellProps {
  inputField: keyof FWIInputParameters
  input: FWIInputParameters
  setInput: React.Dispatch<React.SetStateAction<FWIInputParameters>>
  inputProps?: OutlinedTextFieldProps['InputProps']
}
const FWINumberCell = ({
  inputField,
  input,
  inputProps,
  setInput
}: FWIStationCellProps) => {
  // eslint-disable-next-line

  const handleChange = (
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    event: ChangeEvent<HTMLTextAreaElement | HTMLInputElement>
  ) => {
    const value = Number(event.target.value)
    setInput(prevState => ({
      ...prevState,
      [inputField]: value
    }))
  }

  return (
    <React.Fragment>
      <TableCell>
        <TextField
          type="number"
          inputMode="numeric"
          size="small"
          variant="outlined"
          InputProps={inputProps}
          inputProps={{ min: 0, max: 100 }}
          fullWidth
          defaultValue={input[inputField]}
          onChange={handleChange}
        />
      </TableCell>
    </React.Fragment>
  )
}
export default React.memo(FWINumberCell)
