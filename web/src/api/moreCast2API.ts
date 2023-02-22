import axios from 'api/axios'
import { BiasAdjModelResponse, ModelsForStation } from 'api/modelAPI'
import { Station } from 'api/stationAPI'

export enum ModelChoice {
  GDPS = 'GDPS',
  GFS = 'GFS',
  HRDPS = 'HRDPS',
  NAMM = 'NAMM',
  RDPS = 'RDPS',
  MANUAL = 'MANUAL'
}

interface PredictionValues {
  precip: number
  rh: number
  temp: number
  wind_direction: number
  wind_speed: number
}

export interface StationPrediction {
  date: number
  model: ModelChoice
  station: Station
  values: PredictionValues
}

export interface ModelPredictionResponse {
  predictions: StationPrediction[]
}

export type ModelType = 'HRDPS' | 'GDPS' | 'GFS' | 'MANUAL' | 'NAMM' | 'RDPS'

export const ModelChoices: ModelType[] = [
  ModelChoice.GDPS,
  ModelChoice.GFS,
  ModelChoice.HRDPS,
  ModelChoice.MANUAL,
  ModelChoice.NAMM,
  ModelChoice.RDPS
]

/**
 * Get noon model predictions for the specified date range
 * @param stationCodes A list of station codes of interest
 * @param model The weather model abbreviation
 * @param from_date The first date (epoch time) for which predictions will be returned
 * @param to_date The last date (epoch time) for which predictions will be returned
 */
// TODO - Uncomment once we're wired up to the API
// export async function getModelPredictionsWIP(
//   stationCodes: number[],
//   model: ModelType,
//   startDate: number,
//   endDate: number
// ): Promise<ModelsForStation[]> {
//   const url = `/weather_models/${model}/predictions/most_recent/${startDate}/${endDate}`
//   const { data } = await axios.post<BiasAdjModelResponse>(url, {
//     stations: stationCodes
//   })

//   return data.stations
// }

// TODO - To be removed once we're wired up to the API
export async function getModelPredictions(
  stationCodes: number[],
  model: ModelType,
  startDate: number,
  endDate: number
): Promise<ModelsForStation[]> {
  try {
    const url = `/weather_models/${model}/predictions/most_recent/${startDate}/${endDate}`
    await axios.post<BiasAdjModelResponse>(url, {
      stations: stationCodes
    })
  } catch {
    console.log('Not expecting the API to work yet.')
  }

  if (model === ModelChoice.HRDPS) {
    return completeSampleData.stations
  }

  return []
}

const completeSampleData = {
  stations: [
    {
      station: {
        zone_code: null,
        code: 209,
        name: 'ALEXIS CREEK',
        lat: 52.08377,
        long: -123.2732667,
        ecodivision_name: 'HUMID CONTINENTAL HIGHLANDS',
        core_season: {
          start_month: 5,
          start_day: 15,
          end_month: 8,
          end_day: 31
        },
        elevation: 791,
        wfwx_station_uuid: ''
      },
      model_runs: [
        {
          model_run: {
            datetime: '2023-02-16T06:00:00+00:00',
            name: 'High Resolution Deterministic Prediction System',
            abbreviation: 'HRDPS',
            projection: 'ps2.5km'
          },
          values: [
            {
              datetime: '2023-02-16T08:00:00+00:00',
              temperature: -5.702378226634263,
              bias_adjusted_temperature: null,
              relative_humidity: 76.1949614668931,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.8819849491119385,
              wind_direction: 146.09820556640625,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-16T09:00:00+00:00',
              temperature: -5.841687203310576,
              bias_adjusted_temperature: null,
              relative_humidity: 71.94332768379223,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.8301034569740295,
              wind_direction: 147.3894805908203,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-16T10:00:00+00:00',
              temperature: -5.744527044362089,
              bias_adjusted_temperature: null,
              relative_humidity: 68.25815609657433,
              bias_adjusted_relative_humidity: null,
              wind_speed: 1.1644506454467773,
              wind_direction: 138.16610717773438,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-16T11:00:00+00:00',
              temperature: -6.361876465578211,
              bias_adjusted_temperature: null,
              relative_humidity: 68.93013642120644,
              bias_adjusted_relative_humidity: null,
              wind_speed: 1.5852670669555664,
              wind_direction: 129.2194366455078,
              delta_precipitation: 0.0
            }
          ]
        },
        {
          model_run: {
            datetime: '2023-02-16T12:00:00+00:00',
            name: 'High Resolution Deterministic Prediction System',
            abbreviation: 'HRDPS',
            projection: 'ps2.5km'
          },
          values: [
            {
              datetime: '2023-02-16T12:00:00+00:00',
              temperature: -6.586932569088139,
              bias_adjusted_temperature: null,
              relative_humidity: 69.41504766971936,
              bias_adjusted_relative_humidity: null,
              wind_speed: 1.9599665403366089,
              wind_direction: 143.8845977783203,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-16T13:00:00+00:00',
              temperature: -5.960626678133433,
              bias_adjusted_temperature: null,
              relative_humidity: 70.5788049939381,
              bias_adjusted_relative_humidity: null,
              wind_speed: 1.4238580465316772,
              wind_direction: 137.1515350341797,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-16T14:00:00+00:00',
              temperature: -5.920976692341856,
              bias_adjusted_temperature: null,
              relative_humidity: 71.29874737038071,
              bias_adjusted_relative_humidity: null,
              wind_speed: 1.2912720441818237,
              wind_direction: 144.6224562,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-16T15:00:00+00:00',
              temperature: -6.62927908430583,
              bias_adjusted_temperature: null,
              relative_humidity: 75.15193844213965,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.7321051359176636,
              wind_direction: 168.87994384765625,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-16T16:00:00+00:00',
              temperature: -7.904622698104664,
              bias_adjusted_temperature: null,
              relative_humidity: 84.66110659853155,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.4208163321018219,
              wind_direction: 267.2933044433594,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-16T17:00:00+00:00',
              temperature: -6.707444912414455,
              bias_adjusted_temperature: null,
              relative_humidity: 84.97958741802142,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.7321051359176636,
              wind_direction: 302.8955383300781,
              delta_precipitation: 0.0
            }
          ]
        },
        {
          model_run: {
            datetime: '2023-02-16T18:00:00+00:00',
            name: 'High Resolution Deterministic Prediction System',
            abbreviation: 'HRDPS',
            projection: 'ps2.5km'
          },
          values: [
            {
              datetime: '2023-02-16T18:00:00+00:00',
              temperature: -4.0839437777007355,
              bias_adjusted_temperature: null,
              relative_humidity: 72.64979651884133,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.5361084938049316,
              wind_direction: 212.78318786621094,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-16T19:00:00+00:00',
              temperature: -2.560629784988855,
              bias_adjusted_temperature: null,
              relative_humidity: 68.59243160163741,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.126821368932724,
              wind_direction: 307.7839050292969,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-16T20:00:00+00:00',
              temperature: -1.9270361744477067,
              bias_adjusted_temperature: null,
              relative_humidity: 65.26191711425781,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.36893486976623535,
              wind_direction: 303.7256164550781,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-16T21:00:00+00:00',
              temperature: -1.442872080182978,
              bias_adjusted_temperature: null,
              relative_humidity: 64.40464673170058,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.5130500793457031,
              wind_direction: 339.78900146484375,
              delta_precipitation: 0.0013498094536718976
            },
            {
              datetime: '2023-02-16T22:00:00+00:00',
              temperature: -1.108188049022821,
              bias_adjusted_temperature: null,
              relative_humidity: 73.7832868527012,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.6341068148612976,
              wind_direction: 332.7792663574219,
              delta_precipitation: 0.010723874521914931
            },
            {
              datetime: '2023-02-16T23:00:00+00:00',
              temperature: -1.3298474444285917,
              bias_adjusted_temperature: null,
              relative_humidity: 88.0930739182281,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.7955158352851868,
              wind_direction: 300.40521240234375,
              delta_precipitation: 0.08729349903876296
            }
          ]
        },
        {
          model_run: {
            datetime: '2023-02-17T00:00:00+00:00',
            name: 'High Resolution Deterministic Prediction System',
            abbreviation: 'HRDPS',
            projection: 'ps2.5km'
          },
          values: [
            {
              datetime: '2023-02-17T00:00:00+00:00',
              temperature: -0.7607685671892186,
              bias_adjusted_temperature: -3.2,
              relative_humidity: 87.96679143650118,
              bias_adjusted_relative_humidity: 77.0,
              wind_speed: 0.8992787599563599,
              wind_direction: 256.7786560058594,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-17T01:00:00+00:00',
              temperature: -2.0870057681664216,
              bias_adjusted_temperature: null,
              relative_humidity: 93.22798231082848,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.6225776076316833,
              wind_direction: 214.6278533935547,
              delta_precipitation: 0.057065287508519164
            },
            {
              datetime: '2023-02-17T02:00:00+00:00',
              temperature: -2.4446149504694947,
              bias_adjusted_temperature: null,
              relative_humidity: 95.47093091138808,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.3574056625366211,
              wind_direction: 181.9771270751953,
              delta_precipitation: 0.020384173178141146
            },
            {
              datetime: '2023-02-17T03:00:00+00:00',
              temperature: -3.672639896009689,
              bias_adjusted_temperature: null,
              relative_humidity: 95.78578002145804,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.253642737865448,
              wind_direction: 146.83607482910156,
              delta_precipitation: 0.000825416602297957
            },
            {
              datetime: '2023-02-17T04:00:00+00:00',
              temperature: -5.014949197615715,
              bias_adjusted_temperature: null,
              relative_humidity: 95.04354784053871,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.17293822765350342,
              wind_direction: 327.890869140625,
              delta_precipitation: 0.00019623002948207513
            },
            {
              datetime: '2023-02-17T05:00:00+00:00',
              temperature: -5.836147295676589,
              bias_adjusted_temperature: null,
              relative_humidity: 91.98048940784659,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.8646910786628723,
              wind_direction: 294.96343994140625,
              delta_precipitation: 0.0
            }
          ]
        },
        {
          model_run: {
            datetime: '2023-02-17T06:00:00+00:00',
            name: 'High Resolution Deterministic Prediction System',
            abbreviation: 'HRDPS',
            projection: 'ps2.5km'
          },
          values: [
            {
              datetime: '2023-02-17T06:00:00+00:00',
              temperature: -7.118896026000062,
              bias_adjusted_temperature: -6.3,
              relative_humidity: 93.20975494384766,
              bias_adjusted_relative_humidity: 100.0,
              wind_speed: 1.1298630237579346,
              wind_direction: 299.11395263671875,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-17T07:00:00+00:00',
              temperature: -8.605783859064688,
              bias_adjusted_temperature: null,
              relative_humidity: 89.47702640617507,
              bias_adjusted_relative_humidity: null,
              wind_speed: 1.302801251411438,
              wind_direction: 266.7398986816406,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-17T08:00:00+00:00',
              temperature: -9.908731865032786,
              bias_adjusted_temperature: null,
              relative_humidity: 89.36484922748639,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.9569247961044312,
              wind_direction: 270.6137390136719,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-17T09:00:00+00:00',
              temperature: -10.773059476682764,
              bias_adjusted_temperature: null,
              relative_humidity: 88.72775119865554,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.3804640769958496,
              wind_direction: 281.12835693359375,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-17T10:00:00+00:00',
              temperature: -11.202626767080277,
              bias_adjusted_temperature: null,
              relative_humidity: 86.77078519853998,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.126821368932724,
              wind_direction: 344.21624755859375,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-17T11:00:00+00:00',
              temperature: -11.215874884102238,
              bias_adjusted_temperature: null,
              relative_humidity: 84.00637625675282,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.06917528808116913,
              wind_direction: 340.6191101074219,
              delta_precipitation: 0.0
            }
          ]
        },
        {
          model_run: {
            datetime: '2023-02-17T12:00:00+00:00',
            name: 'High Resolution Deterministic Prediction System',
            abbreviation: 'HRDPS',
            projection: 'ps2.5km'
          },
          values: [
            {
              datetime: '2023-02-17T12:00:00+00:00',
              temperature: -12.312169521388572,
              bias_adjusted_temperature: -12.5,
              relative_humidity: 86.77078519853998,
              bias_adjusted_relative_humidity: 87.0,
              wind_speed: 0.11529214680194855,
              wind_direction: 31.636165618896484,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-17T13:00:00+00:00',
              temperature: -11.849701676410728,
              bias_adjusted_temperature: null,
              relative_humidity: 83.0155489798751,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.29975956678390503,
              wind_direction: 315.53155517578125,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-17T14:00:00+00:00',
              temperature: -12.11997044944774,
              bias_adjusted_temperature: null,
              relative_humidity: 82.2117907791166,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.14987978339195251,
              wind_direction: 295.8857727050781,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-17T15:00:00+00:00',
              temperature: -12.584600576400867,
              bias_adjusted_temperature: null,
              relative_humidity: 83.0155489798751,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.08070450276136398,
              wind_direction: 306.4926452636719,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-17T16:00:00+00:00',
              temperature: -12.655759924702384,
              bias_adjusted_temperature: null,
              relative_humidity: 84.97619875377865,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.13835057616233826,
              wind_direction: 340.6191101074219,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-17T17:00:00+00:00',
              temperature: -11.299680060257,
              bias_adjusted_temperature: null,
              relative_humidity: 89.62353515625,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.06917528808116913,
              wind_direction: 60.4130859375,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-17T18:00:00+00:00',
              temperature: -8.25021584905584,
              bias_adjusted_temperature: null,
              relative_humidity: 86.82263551372455,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.20752586424350739,
              wind_direction: 21.58268928527832,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-17T19:00:00+00:00',
              temperature: -6.136180900433602,
              bias_adjusted_temperature: null,
              relative_humidity: 76.34392438062636,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.034587644040584564,
              wind_direction: 60.966487884521484,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-17T20:00:00+00:00',
              temperature: -4.52872583733904,
              bias_adjusted_temperature: -4.7,
              relative_humidity: 68.08540997632949,
              bias_adjusted_relative_humidity: 79.0,
              wind_speed: 0.10376293212175369,
              wind_direction: 91.86478424072266,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-17T21:00:00+00:00',
              temperature: -3.1589823689488323,
              bias_adjusted_temperature: -4.0,
              relative_humidity: 63.223337105006806,
              bias_adjusted_relative_humidity: 77.0,
              wind_speed: 0.253642737865448,
              wind_direction: 92.51042175292969,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-17T22:00:00+00:00',
              temperature: -1.6782782976959063,
              bias_adjusted_temperature: -3.3,
              relative_humidity: 56.71444837681535,
              bias_adjusted_relative_humidity: 77.0,
              wind_speed: 0.17293822765350342,
              wind_direction: 80.70450592041016,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-17T23:00:00+00:00',
              temperature: -1.2202677678843024,
              bias_adjusted_temperature: -2.7,
              relative_humidity: 54.17564084964684,
              bias_adjusted_relative_humidity: 75.0,
              wind_speed: 0.2305842936038971,
              wind_direction: 52.48098373413086,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-18T00:00:00+00:00',
              temperature: -1.4874670726124992,
              bias_adjusted_temperature: -3.2,
              relative_humidity: 57.0347751717169,
              bias_adjusted_relative_humidity: 77.0,
              wind_speed: 0.3804640769958496,
              wind_direction: 89.65117645263672,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-18T01:00:00+00:00',
              temperature: -2.2131295070937114,
              bias_adjusted_temperature: -3.2,
              relative_humidity: 62.21060145463842,
              bias_adjusted_relative_humidity: 81.0,
              wind_speed: 0.2767011523246765,
              wind_direction: 200.7928009033203,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-18T02:00:00+00:00',
              temperature: -3.1505710066128874,
              bias_adjusted_temperature: -4.0,
              relative_humidity: 68.44760206180504,
              bias_adjusted_relative_humidity: 84.0,
              wind_speed: 0.5879899263381958,
              wind_direction: 255.5796356201172,
              delta_precipitation: 0.005581922577392508
            },
            {
              datetime: '2023-02-18T03:00:00+00:00',
              temperature: -4.203843383380217,
              bias_adjusted_temperature: -2.4,
              relative_humidity: 95.70312,
              bias_adjusted_relative_humidity: 99.0,
              wind_speed: 0.7839865684509277,
              wind_direction: 117.41352081298828,
              delta_precipitation: 0.8663007895206221
            },
            {
              datetime: '2023-02-18T04:00:00+00:00',
              temperature: -4.2211164683126565,
              bias_adjusted_temperature: -3.3,
              relative_humidity: 95.80660063913382,
              bias_adjusted_relative_humidity: 97.0,
              wind_speed: 1.2797428369522095,
              wind_direction: 135.58355712890625,
              delta_precipitation: 1.20289979506932
            },
            {
              datetime: '2023-02-18T05:00:00+00:00',
              temperature: -4.035143944422762,
              bias_adjusted_temperature: -5.7,
              relative_humidity: 94.91081237792969,
              bias_adjusted_relative_humidity: 98.0,
              wind_speed: 1.152921438217163,
              wind_direction: 112.52513885498047,
              delta_precipitation: 0.38705701132000847
            },
            {
              datetime: '2023-02-18T06:00:00+00:00',
              temperature: -3.8749140499322094,
              bias_adjusted_temperature: -6.3,
              relative_humidity: 94.44732666015625,
              bias_adjusted_relative_humidity: 100.0,
              wind_speed: 0.8877495527267456,
              wind_direction: 134.84568786621094,
              delta_precipitation: 0.024093108847107025
            },
            {
              datetime: '2023-02-18T07:00:00+00:00',
              temperature: -4.231070602451891,
              bias_adjusted_temperature: -7.2,
              relative_humidity: 93.47750416313042,
              bias_adjusted_relative_humidity: 96.0,
              wind_speed: 0.47269779443740845,
              wind_direction: 181.79266357421875,
              delta_precipitation: 0.0
            }
          ]
        }
      ]
    },
    {
      station: {
        zone_code: null,
        code: 317,
        name: 'ALLISON PASS',
        lat: 49.0623139,
        long: -120.7674194,
        ecodivision_name: 'SEMI-ARID STEPPE HIGHLANDS',
        core_season: {
          start_month: 5,
          start_day: 1,
          end_month: 9,
          end_day: 15
        },
        elevation: null,
        wfwx_station_uuid: null
      },
      model_runs: [
        {
          model_run: {
            datetime: '2023-02-16T06:00:00+00:00',
            name: 'High Resolution Deterministic Prediction System',
            abbreviation: 'HRDPS',
            projection: 'ps2.5km'
          },
          values: [
            {
              datetime: '2023-02-16T08:00:00+00:00',
              temperature: -9.345457380120628,
              bias_adjusted_temperature: null,
              relative_humidity: 86.95683984697484,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.4842270016670227,
              wind_direction: 253.27378845214844,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-16T09:00:00+00:00',
              temperature: -9.233386399135789,
              bias_adjusted_temperature: null,
              relative_humidity: 87.06304656502581,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.36893486976623535,
              wind_direction: 245.24945068359375,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-16T10:00:00+00:00',
              temperature: -9.223343224137292,
              bias_adjusted_temperature: null,
              relative_humidity: 85.23625228355047,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.38622868061065674,
              wind_direction: 257.1476135253906,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-16T11:00:00+00:00',
              temperature: -9.200621971410754,
              bias_adjusted_temperature: null,
              relative_humidity: 82.7410157852157,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.39199328422546387,
              wind_direction: 262.9583435058594,
              delta_precipitation: 0.0
            }
          ]
        },
        {
          model_run: {
            datetime: '2023-02-16T12:00:00+00:00',
            name: 'High Resolution Deterministic Prediction System',
            abbreviation: 'HRDPS',
            projection: 'ps2.5km'
          },
          values: [
            {
              datetime: '2023-02-16T12:00:00+00:00',
              temperature: -9.061842774825063,
              bias_adjusted_temperature: null,
              relative_humidity: 81.90927028577076,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.6283422112464905,
              wind_direction: 281.7740173339844,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-16T13:00:00+00:00',
              temperature: -8.923337733392101,
              bias_adjusted_temperature: null,
              relative_humidity: 82.32942962646484,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.34587645530700684,
              wind_direction: 246.72518920898438,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-16T14:00:00+00:00',
              temperature: -8.983940729754723,
              bias_adjusted_temperature: null,
              relative_humidity: 76.94886408391022,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.4208163321018219,
              wind_direction: 242.85137939453125,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-16T15:00:00+00:00',
              temperature: -8.976189264910971,
              bias_adjusted_temperature: null,
              relative_humidity: 70.6666118737489,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.4842270016670227,
              wind_direction: 235.2882080078125,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-16T16:00:00+00:00',
              temperature: -8.897174121110481,
              bias_adjusted_temperature: null,
              relative_humidity: 64.77392139240602,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.553402304649353,
              wind_direction: 235.757812,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-16T17:00:00+00:00',
              temperature: -7.146839843828343,
              bias_adjusted_temperature: null,
              relative_humidity: 53.629718038820315,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.4208163321018219,
              wind_direction: 233.6280059814453,
              delta_precipitation: 0.0
            }
          ]
        },
        {
          model_run: {
            datetime: '2023-02-16T18:00:00+00:00',
            name: 'High Resolution Deterministic Prediction System',
            abbreviation: 'HRDPS',
            projection: 'ps2.5km'
          },
          values: [
            {
              datetime: '2023-02-16T18:00:00+00:00',
              temperature: -4.058373745678863,
              bias_adjusted_temperature: null,
              relative_humidity: 40.91148065343087,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.7321051359176636,
              wind_direction: 30.621593475341797,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-16T19:00:00+00:00',
              temperature: -1.192169972105052,
              bias_adjusted_temperature: null,
              relative_humidity: 47.593996422619185,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.26517194509506226,
              wind_direction: 265.725341796875,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-16T20:00:00+00:00',
              temperature: 0.7896501946558552,
              bias_adjusted_temperature: null,
              relative_humidity: 32.69604087755946,
              bias_adjusted_relative_humidity: null,
              wind_speed: 1.2220968008041382,
              wind_direction: 224.4968719482422,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-16T21:00:00+00:00',
              temperature: 0.9949306277594401,
              bias_adjusted_temperature: null,
              relative_humidity: 29.035872460326793,
              bias_adjusted_relative_humidity: null,
              wind_speed: 1.8619681596755981,
              wind_direction: 233.6280059814453,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-16T22:00:00+00:00',
              temperature: 0.6919919153774243,
              bias_adjusted_temperature: null,
              relative_humidity: 27.883196052945117,
              bias_adjusted_relative_humidity: null,
              wind_speed: 2.155963182449341,
              wind_direction: 232.1522674560547,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-16T23:00:00+00:00',
              temperature: 0.10218144879453694,
              bias_adjusted_temperature: null,
              relative_humidity: 33.75766414534112,
              bias_adjusted_relative_humidity: null,
              wind_speed: 2.305842876434326,
              wind_direction: 234.2736358642578,
              delta_precipitation: 0.0
            }
          ]
        },
        {
          model_run: {
            datetime: '2023-02-17T00:00:00+00:00',
            name: 'High Resolution Deterministic Prediction System',
            abbreviation: 'HRDPS',
            projection: 'ps2.5km'
          },
          values: [
            {
              datetime: '2023-02-17T00:00:00+00:00',
              temperature: -1.0867090167234643,
              bias_adjusted_temperature: 3.3,
              relative_humidity: 38.13848364188975,
              bias_adjusted_relative_humidity: 25.0,
              wind_speed: 1.6775007247924805,
              wind_direction: 221.7298583984375,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-17T01:00:00+00:00',
              temperature: -2.188894045133303,
              bias_adjusted_temperature: null,
              relative_humidity: 43.94838355754672,
              bias_adjusted_relative_humidity: null,
              wind_speed: 2.0060832500457764,
              wind_direction: 236.57948303222656,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-17T02:00:00+00:00',
              temperature: -3.800470381503866,
              bias_adjusted_temperature: null,
              relative_humidity: 52.000756279108536,
              bias_adjusted_relative_humidity: null,
              wind_speed: 1.7409113645553589,
              wind_direction: 236.39501953125,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-17T03:00:00+00:00',
              temperature: -5.072159967439158,
              bias_adjusted_temperature: null,
              relative_humidity: 60.09617470902474,
              bias_adjusted_relative_humidity: null,
              wind_speed: 1.4757394790649414,
              wind_direction: 230.215312,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-17T04:00:00+00:00',
              temperature: -5.840630099477972,
              bias_adjusted_temperature: null,
              relative_humidity: 65.56457090338343,
              bias_adjusted_relative_humidity: null,
              wind_speed: 1.256684422492981,
              wind_direction: 225.609062,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-17T05:00:00+00:00',
              temperature: -5.260844273203277,
              bias_adjusted_temperature: null,
              relative_humidity: 67.73248624762171,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.9684540033340454,
              wind_direction: 229.01632690429688,
              delta_precipitation: 0.0004547612592262816
            }
          ]
        },
        {
          model_run: {
            datetime: '2023-02-17T06:00:00+00:00',
            name: 'High Resolution Deterministic Prediction System',
            abbreviation: 'HRDPS',
            projection: 'ps2.5km'
          },
          values: [
            {
              datetime: '2023-02-17T06:00:00+00:00',
              temperature: -4.049249032984281,
              bias_adjusted_temperature: -2.9,
              relative_humidity: 72.2923696923013,
              bias_adjusted_relative_humidity: 78.0,
              wind_speed: 0.8762203454971313,
              wind_direction: 271.53607177734375,
              delta_precipitation: 0.012874479596937367
            },
            {
              datetime: '2023-02-17T07:00:00+00:00',
              temperature: -4.5224595704384205,
              bias_adjusted_temperature: null,
              relative_humidity: 81.06971023032781,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.5418730974197388,
              wind_direction: 261.4825744628906,
              delta_precipitation: 0.07509198929882813
            },
            {
              datetime: '2023-02-17T08:00:00+00:00',
              temperature: -4.33202930316489,
              bias_adjusted_temperature: null,
              relative_humidity: 89.07817519378823,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.4611685872077942,
              wind_direction: 250.10039062,
              delta_precipitation: 0.23898849797784652
            },
            {
              datetime: '2023-02-17T09:00:00+00:00',
              temperature: -4.107878820812868,
              bias_adjusted_temperature: null,
              relative_humidity: 90.90764296722571,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.4381101727485657,
              wind_direction: 256.963134765625,
              delta_precipitation: 0.33943173848142055
            },
            {
              datetime: '2023-02-17T10:00:00+00:00',
              temperature: -4.024875840069701,
              bias_adjusted_temperature: null,
              relative_humidity: 91.495849609375,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.507285475730896,
              wind_direction: 271.72052001953125,
              delta_precipitation: 0.5778158149592805
            },
            {
              datetime: '2023-02-17T11:00:00+00:00',
              temperature: -3.989108338204873,
              bias_adjusted_temperature: null,
              relative_humidity: 91.495849609375,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.5188146829605103,
              wind_direction: 275.1331787109375,
              delta_precipitation: 0.8321449084592434
            }
          ]
        },
        {
          model_run: {
            datetime: '2023-02-17T12:00:00+00:00',
            name: 'High Resolution Deterministic Prediction System',
            abbreviation: 'HRDPS',
            projection: 'ps2.5km'
          },
          values: [
            {
              datetime: '2023-02-17T12:00:00+00:00',
              temperature: -3.9992868006352342,
              bias_adjusted_temperature: -3.2,
              relative_humidity: 90.56449915235112,
              bias_adjusted_relative_humidity: 91.0,
              wind_speed: 0.5879899263381958,
              wind_direction: 246.90966796875,
              delta_precipitation: 0.7255292325304943
            },
            {
              datetime: '2023-02-17T13:00:00+00:00',
              temperature: -3.916338554251962,
              bias_adjusted_temperature: null,
              relative_humidity: 88.44476427164662,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.4842270016670227,
              wind_direction: 248.662109375,
              delta_precipitation: 0.2746364215971634
            },
            {
              datetime: '2023-02-17T14:00:00+00:00',
              temperature: -3.868740287183303,
              bias_adjusted_temperature: null,
              relative_humidity: 86.32503123470619,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.6802236437797546,
              wind_direction: 257.6087646484375,
              delta_precipitation: 0.11653296869670748
            },
            {
              datetime: '2023-02-17T15:00:00+00:00',
              temperature: -3.896817259007323,
              bias_adjusted_temperature: null,
              relative_humidity: 84.01754439544838,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.8762203454971313,
              wind_direction: 262.12823486328125,
              delta_precipitation: 0.047101853424464546
            },
            {
              datetime: '2023-02-17T16:00:00+00:00',
              temperature: -3.751636542761217,
              bias_adjusted_temperature: null,
              relative_humidity: 84.59225925760475,
              bias_adjusted_relative_humidity: null,
              wind_speed: 1.152921438217163,
              wind_direction: 262.77386474609375,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-17T17:00:00+00:00',
              temperature: -3.2097729197965106,
              bias_adjusted_temperature: null,
              relative_humidity: 78.08981335791384,
              bias_adjusted_relative_humidity: null,
              wind_speed: 1.4411518573760986,
              wind_direction: 256.87091064453125,
              delta_precipitation: -0.0002658089895887228
            },
            {
              datetime: '2023-02-17T18:00:00+00:00',
              temperature: -2.22948924728943,
              bias_adjusted_temperature: null,
              relative_humidity: 66.53710244908517,
              bias_adjusted_relative_humidity: null,
              wind_speed: 1.7063237428665161,
              wind_direction: 257.8854675292969,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-17T19:00:00+00:00',
              temperature: -1.7613050132867283,
              bias_adjusted_temperature: null,
              relative_humidity: 61.60086303066153,
              bias_adjusted_relative_humidity: null,
              wind_speed: 2.0060832500457764,
              wind_direction: 256.5942077636719,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-17T20:00:00+00:00',
              temperature: -1.466693594674076,
              bias_adjusted_temperature: 6.4,
              relative_humidity: 59.066992559887936,
              bias_adjusted_relative_humidity: 18.0,
              wind_speed: 2.121375560760498,
              wind_direction: 255.210693359375,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-17T21:00:00+00:00',
              temperature: -1.2356662158539167,
              bias_adjusted_temperature: 6.1,
              relative_humidity: 56.863795272926474,
              bias_adjusted_relative_humidity: 15.0,
              wind_speed: 2.2827844619750977,
              wind_direction: 252.62815856933594,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-17T22:00:00+00:00',
              temperature: -1.4297002289003333,
              bias_adjusted_temperature: 5.9,
              relative_humidity: 58.7934709103002,
              bias_adjusted_relative_humidity: 14.0,
              wind_speed: 2.2712552547454834,
              wind_direction: 249.0310312,
              delta_precipitation: 0.0013586939390146102
            },
            {
              datetime: '2023-02-17T23:00:00+00:00',
              temperature: -1.6020277581840363,
              bias_adjusted_temperature: 5.2,
              relative_humidity: 59.448597724620015,
              bias_adjusted_relative_humidity: 19.0,
              wind_speed: 2.3289012908935547,
              wind_direction: 246.07955932617188,
              delta_precipitation: 0.00031445622237225024
            },
            {
              datetime: '2023-02-18T00:00:00+00:00',
              temperature: -1.9754532086576093,
              bias_adjusted_temperature: 3.3,
              relative_humidity: 61.60392050220056,
              bias_adjusted_relative_humidity: 25.0,
              wind_speed: 2.351959705352783,
              wind_direction: 247.83200073242188,
              delta_precipitation: 0.0003482769481127912
            },
            {
              datetime: '2023-02-18T01:00:00+00:00',
              temperature: -2.7773705384548704,
              bias_adjusted_temperature: 0.7,
              relative_humidity: 67.03795264934358,
              bias_adjusted_relative_humidity: 35.0,
              wind_speed: 2.1905508041381836,
              wind_direction: 248.47763061523438,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-18T02:00:00+00:00',
              temperature: -3.6823078227098938,
              bias_adjusted_temperature: -0.8,
              relative_humidity: 73.21080780029297,
              bias_adjusted_relative_humidity: 48.0,
              wind_speed: 1.9138495922088623,
              wind_direction: 250.41453552246094,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-18T03:00:00+00:00',
              temperature: -4.209561168420498,
              bias_adjusted_temperature: -2.3,
              relative_humidity: 75.72681134973203,
              bias_adjusted_relative_humidity: 59.0,
              wind_speed: 1.7524406909942627,
              wind_direction: 255.85633850097656,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-18T04:00:00+00:00',
              temperature: -4.178811986663024,
              bias_adjusted_temperature: -3.1,
              relative_humidity: 75.69671214215663,
              bias_adjusted_relative_humidity: 66.0,
              wind_speed: 1.7178529500961304,
              wind_direction: 254.84176635742188,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-18T05:00:00+00:00',
              temperature: -4.297636259077176,
              bias_adjusted_temperature: -3.1,
              relative_humidity: 77.20194244384766,
              bias_adjusted_relative_humidity: 68.0,
              wind_speed: 1.8216159343719482,
              wind_direction: 254.4728240966797,
              delta_precipitation: 0.0038890832106396878
            },
            {
              datetime: '2023-02-18T06:00:00+00:00',
              temperature: -4.61932474118156,
              bias_adjusted_temperature: -2.9,
              relative_humidity: 79.04594075090978,
              bias_adjusted_relative_humidity: 78.0,
              wind_speed: 1.856203556060791,
              wind_direction: 253.458251953125,
              delta_precipitation: 0.01379381530246565
            },
            {
              datetime: '2023-02-18T07:00:00+00:00',
              temperature: -4.89160531843695,
              bias_adjusted_temperature: -3.0,
              relative_humidity: 79.04594075090978,
              bias_adjusted_relative_humidity: 85.0,
              wind_speed: 1.9138495922088623,
              wind_direction: 247.4630584716797,
              delta_precipitation: 0.0020700393492648628
            }
          ]
        }
      ]
    },
    {
      station: {
        zone_code: null,
        code: 838,
        name: 'AKOKLI CREEK',
        lat: 49.4358,
        long: -116.7464,
        ecodivision_name: 'HUMID CONTINENTAL HIGHLANDS',
        core_season: {
          start_month: 5,
          start_day: 15,
          end_month: 8,
          end_day: 31
        },
        elevation: 821,
        wfwx_station_uuid: ''
      },
      model_runs: [
        {
          model_run: {
            datetime: '2023-02-16T06:00:00+00:00',
            name: 'High Resolution Deterministic Prediction System',
            abbreviation: 'HRDPS',
            projection: 'ps2.5km'
          },
          values: [
            {
              datetime: '2023-02-16T08:00:00+00:00',
              temperature: -5.962998789274375,
              bias_adjusted_temperature: null,
              relative_humidity: 65.45828423679694,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.4438747763633728,
              wind_direction: 135.3990936279297,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-16T09:00:00+00:00',
              temperature: -6.097130320623354,
              bias_adjusted_temperature: null,
              relative_humidity: 65.48142757353017,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.44963937997817993,
              wind_direction: 138.53504943847656,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-16T10:00:00+00:00',
              temperature: -6.263019254835273,
              bias_adjusted_temperature: null,
              relative_humidity: 65.21814622971182,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.5130500793457031,
              wind_direction: 139.365562,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-16T11:00:00+00:00',
              temperature: -6.428006046691311,
              bias_adjusted_temperature: null,
              relative_humidity: 63.50330099774418,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.5245792865753174,
              wind_direction: 135.4913330078125,
              delta_precipitation: 0.0
            }
          ]
        },
        {
          model_run: {
            datetime: '2023-02-16T12:00:00+00:00',
            name: 'High Resolution Deterministic Prediction System',
            abbreviation: 'HRDPS',
            projection: 'ps2.5km'
          },
          values: [
            {
              datetime: '2023-02-16T12:00:00+00:00',
              temperature: -6.8268542815974325,
              bias_adjusted_temperature: null,
              relative_humidity: 70.64289325779427,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.4899916350841522,
              wind_direction: 357.8668212890625,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-16T13:00:00+00:00',
              temperature: -6.7484912964477655,
              bias_adjusted_temperature: null,
              relative_humidity: 68.24756108065844,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.5476377010345459,
              wind_direction: 135.1223907470703,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-16T14:00:00+00:00',
              temperature: -6.793122979434628,
              bias_adjusted_temperature: null,
              relative_humidity: 70.06735324990572,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.5879899263381958,
              wind_direction: 133.7388916015625,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-16T15:00:00+00:00',
              temperature: -6.893840923203946,
              bias_adjusted_temperature: null,
              relative_humidity: 74.940368986377,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.6456360220909119,
              wind_direction: 136.5059051513672,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-16T16:00:00+00:00',
              temperature: -6.392061303009676,
              bias_adjusted_temperature: null,
              relative_humidity: 77.76659021529869,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.6686944365501404,
              wind_direction: 137.52047729492188,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-16T17:00:00+00:00',
              temperature: -3.7782895035943493,
              bias_adjusted_temperature: null,
              relative_humidity: 70.67962796916802,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.5937545299530029,
              wind_direction: 151.72447204589844,
              delta_precipitation: 0.0
            }
          ]
        },
        {
          model_run: {
            datetime: '2023-02-16T18:00:00+00:00',
            name: 'High Resolution Deterministic Prediction System',
            abbreviation: 'HRDPS',
            projection: 'ps2.5km'
          },
          values: [
            {
              datetime: '2023-02-16T18:00:00+00:00',
              temperature: -2.5437994711083776,
              bias_adjusted_temperature: null,
              relative_humidity: 65.46317548753133,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.5879899263381958,
              wind_direction: 229.7541961669922,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-16T19:00:00+00:00',
              temperature: -0.7203167332820102,
              bias_adjusted_temperature: null,
              relative_humidity: 64.58772828457755,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.6975175142288208,
              wind_direction: 202.08407592773438,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-16T20:00:00+00:00',
              temperature: 0.2607399155343037,
              bias_adjusted_temperature: null,
              relative_humidity: 63.78617477416992,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.7609281539916992,
              wind_direction: 205.4044952392578,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-16T21:00:00+00:00',
              temperature: 0.9012085430866299,
              bias_adjusted_temperature: null,
              relative_humidity: 60.63288247444052,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.7609281539916992,
              wind_direction: 198.48695373535156,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-16T22:00:00+00:00',
              temperature: 1.1564119619807522,
              bias_adjusted_temperature: null,
              relative_humidity: 58.62138061057412,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.7148113250732422,
              wind_direction: 189.6325225830078,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-16T23:00:00+00:00',
              temperature: 1.2327678705373835,
              bias_adjusted_temperature: null,
              relative_humidity: 56.06494221443628,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.7321051359176636,
              wind_direction: 168.87994384765625,
              delta_precipitation: 0.0
            }
          ]
        },
        {
          model_run: {
            datetime: '2023-02-17T00:00:00+00:00',
            name: 'High Resolution Deterministic Prediction System',
            abbreviation: 'HRDPS',
            projection: 'ps2.5km'
          },
          values: [
            {
              datetime: '2023-02-17T00:00:00+00:00',
              temperature: 0.6783769975226465,
              bias_adjusted_temperature: 0.8,
              relative_humidity: 46.878147744057145,
              bias_adjusted_relative_humidity: 67.0,
              wind_speed: 0.8128096461296082,
              wind_direction: 301.8809509277344,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-17T01:00:00+00:00',
              temperature: -0.6844901347694756,
              bias_adjusted_temperature: null,
              relative_humidity: 58.699670316337894,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.6225776076316833,
              wind_direction: 131.3408203125,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-17T02:00:00+00:00',
              temperature: -1.4855321688493106,
              bias_adjusted_temperature: null,
              relative_humidity: 62.38987086250255,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.6341068148612976,
              wind_direction: 134.29229736328125,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-17T03:00:00+00:00',
              temperature: -1.7161624911509699,
              bias_adjusted_temperature: null,
              relative_humidity: 64.2679941960202,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.5188146829605103,
              wind_direction: 134.7534637451172,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-17T04:00:00+00:00',
              temperature: -1.7750412405763552,
              bias_adjusted_temperature: null,
              relative_humidity: 65.92045339029522,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.4611685872077942,
              wind_direction: 132.26315307617188,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-17T05:00:00+00:00',
              temperature: -1.7790834443858694,
              bias_adjusted_temperature: null,
              relative_humidity: 65.75520663970909,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.49575623869895935,
              wind_direction: 131.52528381347656,
              delta_precipitation: 0.0
            }
          ]
        },
        {
          model_run: {
            datetime: '2023-02-17T06:00:00+00:00',
            name: 'High Resolution Deterministic Prediction System',
            abbreviation: 'HRDPS',
            projection: 'ps2.5km'
          },
          values: [
            {
              datetime: '2023-02-17T06:00:00+00:00',
              temperature: -0.5874637251146917,
              bias_adjusted_temperature: -0.3,
              relative_humidity: 62.34931417086173,
              bias_adjusted_relative_humidity: 67.0,
              wind_speed: 1.1644506454467773,
              wind_direction: 258.16217041015625,
              delta_precipitation: 0.0007205759175121784
            },
            {
              datetime: '2023-02-17T07:00:00+00:00',
              temperature: -1.8418562322402834,
              bias_adjusted_temperature: null,
              relative_humidity: 66.53921085113487,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.4611685872077942,
              wind_direction: 134.10781562,
              delta_precipitation: 0.0006571409584364616
            },
            {
              datetime: '2023-02-17T08:00:00+00:00',
              temperature: -1.8284405653782203,
              bias_adjusted_temperature: null,
              relative_humidity: 66.41300974336886,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.4611685872077942,
              wind_direction: 131.8942108154297,
              delta_precipitation: 0.0003602879587560892
            },
            {
              datetime: '2023-02-17T09:00:00+00:00',
              temperature: -2.027996838225413,
              bias_adjusted_temperature: null,
              relative_humidity: 67.98264809234317,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.3574056625366211,
              wind_direction: 128.4815673828125,
              delta_precipitation: 0.0001167513970196331
            },
            {
              datetime: '2023-02-17T10:00:00+00:00',
              temperature: -2.2275654132426963,
              bias_adjusted_temperature: null,
              relative_humidity: 67.71248197823955,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.253642737865448,
              wind_direction: 121.10287475585938,
              delta_precipitation: 0.00018010160266073924
            },
            {
              datetime: '2023-02-17T11:00:00+00:00',
              temperature: -2.2260746958480553,
              bias_adjusted_temperature: null,
              relative_humidity: 68.60133711061701,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.253642737865448,
              wind_direction: 129.957820312,
              delta_precipitation: 0.0
            }
          ]
        },
        {
          model_run: {
            datetime: '2023-02-17T12:00:00+00:00',
            name: 'High Resolution Deterministic Prediction System',
            abbreviation: 'HRDPS',
            projection: 'ps2.5km'
          },
          values: [
            {
              datetime: '2023-02-17T12:00:00+00:00',
              temperature: -1.2703204323223796,
              bias_adjusted_temperature: -0.2,
              relative_humidity: 66.01870695027247,
              bias_adjusted_relative_humidity: 74.0,
              wind_speed: 1.614090085029602,
              wind_direction: 308.3373107910156,
              delta_precipitation: 0.001781117998082234
            },
            {
              datetime: '2023-02-17T13:00:00+00:00',
              temperature: -2.3350042896413123,
              bias_adjusted_temperature: null,
              relative_humidity: 71.31370840827122,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.14987978339195251,
              wind_direction: 147.6661834716797,
              delta_precipitation: 0.001309222656307023
            },
            {
              datetime: '2023-02-17T14:00:00+00:00',
              temperature: -2.4237188892506873,
              bias_adjusted_temperature: null,
              relative_humidity: 71.31370840827122,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.06917528808116913,
              wind_direction: 99.3357162475586,
              delta_precipitation: 0.0011924712592873896
            },
            {
              datetime: '2023-02-17T15:00:00+00:00',
              temperature: -2.5499439731570037,
              bias_adjusted_temperature: null,
              relative_humidity: 71.92166295873494,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.09223371744155884,
              wind_direction: 42.611976623535156,
              delta_precipitation: 0.0005937059993607447
            },
            {
              datetime: '2023-02-17T16:00:00+00:00',
              temperature: -2.4082986690135093,
              bias_adjusted_temperature: null,
              relative_humidity: 72.78944693366184,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.19599664211273193,
              wind_direction: 51.835350036621094,
              delta_precipitation: 0.000593706191197506
            },
            {
              datetime: '2023-02-17T17:00:00+00:00',
              temperature: -1.287573403209333,
              bias_adjusted_temperature: null,
              relative_humidity: 69.18156453068302,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.2305842936038971,
              wind_direction: 25.27203941345215,
              delta_precipitation: 0.0011874119987214894
            },
            {
              datetime: '2023-02-17T18:00:00+00:00',
              temperature: 0.4839150567417877,
              bias_adjusted_temperature: null,
              relative_humidity: 62.293685558180044,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.26517194509506226,
              wind_direction: 355.37652587890625,
              delta_precipitation: 0.0002968528078436117
            },
            {
              datetime: '2023-02-17T19:00:00+00:00',
              temperature: 1.2502212617482775,
              bias_adjusted_temperature: null,
              relative_humidity: 60.420817093501526,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.4611685872077942,
              wind_direction: 311.8421936035156,
              delta_precipitation: 0.0002968528078436117
            },
            {
              datetime: '2023-02-17T20:00:00+00:00',
              temperature: 1.33592342873342,
              bias_adjusted_temperature: 0.7,
              relative_humidity: 60.897190360824936,
              bias_adjusted_relative_humidity: 68.0,
              wind_speed: 0.4611685872077942,
              wind_direction: 248.47763061523438,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-17T21:00:00+00:00',
              temperature: 1.2533243114387682,
              bias_adjusted_temperature: 2.3,
              relative_humidity: 60.812347157067514,
              bias_adjusted_relative_humidity: 59.0,
              wind_speed: 0.7378697395324707,
              wind_direction: 196.08888244628906,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-17T22:00:00+00:00',
              temperature: 1.4960745287112789,
              bias_adjusted_temperature: 1.6,
              relative_humidity: 57.43936241013993,
              bias_adjusted_relative_humidity: 63.0,
              wind_speed: 0.9915124773979187,
              wind_direction: 183.6373291015625,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-17T23:00:00+00:00',
              temperature: 1.491539208427355,
              bias_adjusted_temperature: 2.0,
              relative_humidity: 55.75096457412904,
              bias_adjusted_relative_humidity: 61.0,
              wind_speed: 1.1875090599060059,
              wind_direction: 187.41891479492188,
              delta_precipitation: 0.0007205761093489384
            },
            {
              datetime: '2023-02-18T00:00:00+00:00',
              temperature: 1.0736929340052979,
              bias_adjusted_temperature: 0.8,
              relative_humidity: 55.813537003469996,
              bias_adjusted_relative_humidity: 67.0,
              wind_speed: 0.9569247961044312,
              wind_direction: 192.58399963378906,
              delta_precipitation: -0.0008474458356636117
            },
            {
              datetime: '2023-02-18T01:00:00+00:00',
              temperature: 0.2896222507433703,
              bias_adjusted_temperature: -0.3,
              relative_humidity: 59.50250945644533,
              bias_adjusted_relative_humidity: 70.0,
              wind_speed: 0.7609281539916992,
              wind_direction: 184.83636474609375,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-18T02:00:00+00:00',
              temperature: -0.38186905707445984,
              bias_adjusted_temperature: -0.7,
              relative_humidity: 62.62098002984679,
              bias_adjusted_relative_humidity: 71.0,
              wind_speed: 0.5764607191085815,
              wind_direction: 179.57904052734375,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-18T03:00:00+00:00',
              temperature: -0.7486534299838582,
              bias_adjusted_temperature: -0.1,
              relative_humidity: 64.3009031800602,
              bias_adjusted_relative_humidity: 65.0,
              wind_speed: 0.553402304649353,
              wind_direction: 180.77809143066406,
              delta_precipitation: 0.00048724263034213323
            },
            {
              datetime: '2023-02-18T04:00:00+00:00',
              temperature: -1.0739074534190811,
              bias_adjusted_temperature: -0.1,
              relative_humidity: 68.2821469852489,
              bias_adjusted_relative_humidity: 69.0,
              wind_speed: 0.749398946762085,
              wind_direction: 166.11293029785156,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-18T05:00:00+00:00',
              temperature: -1.4131158947399338,
              bias_adjusted_temperature: 0.0,
              relative_humidity: 71.77719726909814,
              bias_adjusted_relative_humidity: 68.0,
              wind_speed: 0.8646910786628723,
              wind_direction: 155.137851562,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-18T06:00:00+00:00',
              temperature: -1.6877098544356826,
              bias_adjusted_temperature: -0.3,
              relative_humidity: 75.13296943397938,
              bias_adjusted_relative_humidity: 67.0,
              wind_speed: 0.807045042514801,
              wind_direction: 150.986600312,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-18T07:00:00+00:00',
              temperature: -1.9007479347008753,
              bias_adjusted_temperature: -0.5,
              relative_humidity: 76.97755894631018,
              bias_adjusted_relative_humidity: 73.0,
              wind_speed: 0.8531618714332581,
              wind_direction: 147.20501708984375,
              delta_precipitation: 0.0
            }
          ]
        }
      ]
    }
  ]
}
