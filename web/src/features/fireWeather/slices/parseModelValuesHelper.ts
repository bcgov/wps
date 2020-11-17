import { ModelRun, ModelValue } from 'api/modelAPI'
import { isNoonInPST } from 'utils/date'

export const parseModelValuesHelper = (
  model_runs: ModelRun[],
  separate_noon_values: boolean
): Record<string, ModelValue[]> => {
  const pastModelValues: ModelValue[] = []
  const modelValues: ModelValue[] = []
  const noonModelValues: ModelValue[] = []
  const allModelValues = model_runs.reduce(
    (values: ModelValue[], modelRun) => values.concat(modelRun.values),
    []
  )
  const currDate = new Date()
  allModelValues.forEach(v => {
    const isFutureModel = new Date(v.datetime) >= currDate
    if (isFutureModel) {
      modelValues.push(v)
    } else {
      pastModelValues.push(v)
    }
    if (separate_noon_values && isNoonInPST(v.datetime)) {
      noonModelValues.push(v)
    }
  })

  return {
    pastValues: pastModelValues,
    modelValues: modelValues,
    noonValues: noonModelValues,
    allValues: allModelValues
  }
}
