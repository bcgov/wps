import { ModelRun, ModelValue } from 'api/modelAPI'
import { isNoonInPST } from 'utils/date'

export const parseModelValuesHelper = (
  model_runs: ModelRun[],
  separate_noon_values: boolean
): Record<string, ModelValue[]> => {
  const pastModelValues: ModelValue[] = []
  const modelValues: ModelValue[] = []
  const noonModelValues: ModelValue[] = []
  const reducer = (values: ModelValue[], modelRun: ModelRun) => {
    // TODO: add in the model run time
    modelRun.values.forEach((value: ModelValue) => {
      value.model_run_datetime = modelRun.model_run.datetime
      values.push(value)
    })
    return values
    // return values.concat(modelRun.values)
  }
  const allModelValues = model_runs.reduce(reducer, [])
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
