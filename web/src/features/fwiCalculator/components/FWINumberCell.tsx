import { OutlinedTextFieldProps, TableCell, TextField } from '@mui/material'
import { FWIInputParameters } from 'features/fwiCalculator/components/BasicFWIGrid'
import { isEqual, isNull, isUndefined } from 'lodash'
import React, { ChangeEvent, useState } from 'react'

export interface FWIStationCellProps {
  isLoading: boolean
  inputField: keyof FWIInputParameters
  input: FWIInputParameters
  setInput: React.Dispatch<React.SetStateAction<FWIInputParameters>>
  inputProps?: OutlinedTextFieldProps['InputProps']
}
const FWINumberCell = ({ isLoading, inputField, input, inputProps, setInput }: FWIStationCellProps) => {
  const [previousValue, setPreviousValue] = useState(input[inputField])
  const [value, setValue] = useState(input[inputField])

  // eslint-disable-next-line

  const changeHandler = (
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    event: ChangeEvent<HTMLTextAreaElement | HTMLInputElement>
  ) => {
    const stringInput = String(event.target.value)
    const numberInput = Number(stringInput)
    if (isUndefined(stringInput) || isNull(stringInput) || isNaN(numberInput) || stringInput.length <= 3) {
      setValue(Number(numberInput))
    }
  }

  const enterHandler = (event: React.KeyboardEvent<HTMLDivElement>) => {
    if (event.key === 'Enter') {
      setInput(prevState => ({
        ...prevState,
        [inputField]: value
      }))
    }
  }

  const blurHandler = () => {
    if (!isEqual(previousValue, value)) {
      setPreviousValue(value)
      setInput(prevState => ({
        ...prevState,
        [inputField]: value
      }))
    }
  }

  return (
    <React.Fragment>
      <TableCell>
        <TextField
          type="number"
          inputMode="numeric"
          size="small"
          variant="outlined"
          disabled={isLoading}
          InputProps={inputProps}
          inputProps={{ min: 0, max: 100 }}
          fullWidth
          defaultValue={input[inputField]}
          onChange={changeHandler}
          onKeyDown={enterHandler}
          onBlur={blurHandler}
        />
      </TableCell>
    </React.Fragment>
  )
}
export default React.memo(FWINumberCell)
