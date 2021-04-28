// Custom React Hook for the temp & rh graph toggle state
import { useState } from 'react'

export interface ToggleValues {
  showObservations: boolean
  showGdps: boolean
  showForecasts: boolean
  showBiasAdjGdps: boolean
  showHrdps: boolean
  showRdps: boolean
}

export type SetToggleValues = (
  key: keyof ToggleValues,
  value: ValueOf<ToggleValues>
) => void

export const useGraphToggles = (
  initialValues: ToggleValues
): [ToggleValues, SetToggleValues] => {
  const [values, setValues] = useState(initialValues)

  return [
    values,
    (key, value) => {
      setValues(prevValues => ({
        ...prevValues,
        [key]: value
      }))
    }
  ]
}
