import { HFITableCSVFormatter } from 'features/hfiCalculator/HFITableCSVFormatter'
import { DateTime } from 'luxon'
import { FireCentre } from 'api/hfiCalcAPI'
import { StationDaily } from 'api/hfiCalculatorAPI'
import { NUM_WEEK_DAYS } from 'features/hfiCalculator/constants'
import { HFIResult } from 'features/hfiCalculator/slices/hfiCalculatorSlice'
describe('RowManager', () => {
  const fireCentres: Record<string, FireCentre> = {
    0: {
      id: 12,
      name: 'Kamloops Fire Centre',
      planning_areas: {
        1: {
          name: 'Kamloops (K2)',
          id: 1,
          stations: [
            {
              code: 322,
              station_props: {
                name: 'AFTON',
                elevation: 780,
                fuel_type: {
                  abbrev: 'O1B',
                  description: 'Standing grass'
                },
                uuid: 'bfe0a6e2-e3d0-0210-e053-259e228e58c7'
              }
            },
            {
              code: 1108,
              station_props: {
                name: 'BLUE RIVER 2',
                elevation: 695,
                fuel_type: {
                  abbrev: 'C5',
                  description: 'Red and white pine'
                },
                uuid: 'bfe0a6e2-e16f-0210-e053-259e228e58c7'
              }
            },
            {
              code: 239,
              station_props: {
                name: 'CLEARWATER HUB',
                elevation: 453,
                fuel_type: {
                  abbrev: 'C7',
                  description: 'Ponderosa pine/Douglas fir'
                },
                uuid: 'bfe0a6e2-e286-0210-e053-259e228e58c7'
              }
            },
            {
              code: 1082,
              station_props: {
                name: 'MAYSON',
                elevation: 1315,
                fuel_type: {
                  abbrev: 'C3',
                  description: 'Mature jack or lodgepole pine'
                },
                uuid: 'bfe0a6e2-e15b-0210-e053-259e228e58c7'
              }
            },
            {
              code: 305,
              station_props: {
                name: 'SPARKS LAKE',
                elevation: 972,
                fuel_type: {
                  abbrev: 'C7',
                  description: 'Ponderosa pine/Douglas fir'
                },
                uuid: 'bfe0a6e2-e3bf-0210-e053-259e228e58c7'
              }
            },
            {
              code: 266,
              station_props: {
                name: 'WELLS GRAY',
                elevation: 959,
                fuel_type: {
                  abbrev: 'C5',
                  description: 'Red and white pine'
                },
                uuid: 'bfe0a6e2-e2a0-0210-e053-259e228e58c7'
              }
            }
          ]
        },
        2: {
          name: 'Vernon (K4)',
          id: 2,
          stations: [
            {
              code: 298,
              station_props: {
                name: 'FINTRY',
                elevation: 670,
                fuel_type: {
                  abbrev: 'C7',
                  description: 'Ponderosa pine/Douglas fir'
                },
                uuid: 'bfe0a6e2-e3b8-0210-e053-259e228e58c7'
              }
            },
            {
              code: 388,
              station_props: {
                name: 'KETTLE 2',
                elevation: 1389,
                fuel_type: {
                  abbrev: 'C5',
                  description: 'Red and white pine'
                },
                uuid: 'bfe0a6e2-e412-0210-e053-259e228e58c7'
              }
            },
            {
              code: 346,
              station_props: {
                name: 'SALMON ARM',
                elevation: 527,
                fuel_type: {
                  abbrev: 'C7',
                  description: 'Ponderosa pine/Douglas fir'
                },
                uuid: 'bfe0a6e2-e3e8-0210-e053-259e228e58c7'
              }
            },
            {
              code: 344,
              station_props: {
                name: 'SEYMOUR ARM',
                elevation: 511,
                fuel_type: {
                  abbrev: 'C5',
                  description: 'Red and white pine'
                },
                uuid: 'bfe0a6e2-e3e6-0210-e053-259e228e58c7'
              }
            },
            {
              code: 286,
              station_props: {
                name: 'TURTLE',
                elevation: 640,
                fuel_type: {
                  abbrev: 'C7',
                  description: 'Ponderosa pine/Douglas fir'
                },
                uuid: 'bfe0a6e2-e3ac-0210-e053-259e228e58c7'
              }
            }
          ]
        },
        3: {
          name: 'Penticton (K5)',
          id: 3,
          stations: [
            {
              code: 334,
              station_props: {
                name: 'MCCUDDY',
                elevation: 1067,
                fuel_type: {
                  abbrev: 'C7',
                  description: 'Ponderosa pine/Douglas fir'
                },
                uuid: 'bfe0a6e2-e3dc-0210-e053-259e228e58c7'
              }
            },
            {
              code: 328,
              station_props: {
                name: 'PENTICTON RS',
                elevation: 427,
                fuel_type: {
                  abbrev: 'C7',
                  description: 'Ponderosa pine/Douglas fir'
                },
                uuid: 'bfe0a6e2-e3d6-0210-e053-259e228e58c7'
              }
            }
          ]
        },
        4: {
          name: 'Lillooet (K7)',
          id: 4,
          stations: [
            {
              code: 1029,
              station_props: {
                name: 'FIVE MILE',
                elevation: 865,
                fuel_type: {
                  abbrev: 'C7',
                  description: 'Ponderosa pine/Douglas fir'
                },
                uuid: 'bfe0a6e2-e137-0210-e053-259e228e58c7'
              }
            },
            {
              code: 306,
              station_props: {
                name: 'FRENCH BAR',
                elevation: 1320,
                fuel_type: {
                  abbrev: 'C7',
                  description: 'Ponderosa pine/Douglas fir'
                },
                uuid: 'bfe0a6e2-e3c0-0210-e053-259e228e58c7'
              }
            },
            {
              code: 309,
              station_props: {
                name: 'GWYNETH LAKE',
                elevation: 1205,
                fuel_type: {
                  abbrev: 'C7',
                  description: 'Ponderosa pine/Douglas fir'
                },
                uuid: 'bfe0a6e2-e3c3-0210-e053-259e228e58c7'
              }
            },
            {
              code: 280,
              station_props: {
                name: 'LILLOOET',
                elevation: 408,
                fuel_type: {
                  abbrev: 'C7',
                  description: 'Ponderosa pine/Douglas fir'
                },
                uuid: 'bfe0a6e2-e2ae-0210-e053-259e228e58c7'
              }
            },
            {
              code: 1055,
              station_props: {
                name: 'SPLINTLUM',
                elevation: 424,
                fuel_type: {
                  abbrev: 'C7',
                  description: 'Ponderosa pine/Douglas fir'
                },
                uuid: 'bfe0a6e2-e14c-0210-e053-259e228e58c7'
              }
            }
          ]
        },
        5: {
          name: 'Merritt (K6)',
          id: 5,
          stations: [
            {
              code: 836,
              station_props: {
                name: 'AUGUST LAKE',
                elevation: 855,
                fuel_type: {
                  abbrev: 'C7',
                  description: 'Ponderosa pine/Douglas fir'
                },
                uuid: 'bfe0a6e2-e2df-0210-e053-259e228e58c7'
              }
            },
            {
              code: 1399,
              station_props: {
                name: 'MERRITT 2 HUB',
                elevation: 640,
                fuel_type: {
                  abbrev: 'C7',
                  description: 'Ponderosa pine/Douglas fir'
                },
                uuid: 'bfe0a6e2-e2df-0210-e053-259e228e58c7'
              }
            }
          ]
        }
      }
    }
  }

  const dailies: StationDaily[] = [
    {
      code: 1029,
      status: 'ACTUAL',
      temperature: 1.4,
      relative_humidity: 57,
      wind_speed: 7,
      wind_direction: 205,
      grass_cure_percentage: NaN,
      precipitation: 0,
      ffmc: 69.486,
      dmc: 0.735,
      dc: 252.982,
      isi: 0.876,
      bui: 1.459,
      fwi: 0.25,
      danger_class: NaN,
      observation_valid: true,
      observation_valid_comment: '',
      rate_of_spread: 0.00012874160446133809,
      hfi: 0.001674288538958154,
      intensity_group: 1,
      sixty_minute_fire_size: 4.292671622254363e-9,
      fire_type: 'SUR',
      date: DateTime.fromISO('2021-10-31T13:00:00.000-07:00')
    },
    {
      code: 1055,
      status: 'ACTUAL',
      temperature: 4.8,
      relative_humidity: 57,
      wind_speed: 4.8,
      wind_direction: 223,
      grass_cure_percentage: NaN,
      precipitation: 0,
      ffmc: 47.664,
      dmc: 5.62,
      dc: 460.989,
      isi: 0.154,
      bui: 10.908,
      fwi: 0.098,
      danger_class: NaN,
      observation_valid: true,
      observation_valid_comment: '',
      rate_of_spread: 0.0005064989712502368,
      hfi: 0.04487372124219935,
      intensity_group: 1,
      sixty_minute_fire_size: 9.103019828315551e-8,
      fire_type: 'SUR',
      date: DateTime.fromISO('2021-10-31T13:00:00.000-07:00')
    },
    {
      code: 1082,
      status: 'ACTUAL',
      temperature: 3,
      relative_humidity: 37,
      wind_speed: 7.4,
      wind_direction: 101,
      grass_cure_percentage: NaN,
      precipitation: 2.2,
      ffmc: 54.328,
      dmc: 0.391,
      dc: 376.251,
      isi: 0.381,
      bui: 0.781,
      fwi: 0.096,
      danger_class: NaN,
      observation_valid: true,
      observation_valid_comment: '',
      rate_of_spread: 6.567957698791182e-12,
      hfi: 5.598693076585927e-13,
      intensity_group: 1,
      sixty_minute_fire_size: 8.627591343329349e-24,
      fire_type: 'SUR',
      date: DateTime.fromISO('2021-10-31T13:00:00.000-07:00')
    }
  ]

  it('should export Daily Table to a CSV string correctly', () => {
    const planningAreaHFIResults: {
      [key: string]: HFIResult
    } = {
      "Kamloops (K2)": {}
    }
    const dailyTableCSVString = HFITableCSVFormatter.exportDailyRowsAsStrings(
      NUM_WEEK_DAYS,
      fireCentres,
      dailies
    )
    const expectedDailyString = `"Location,Elev. (m),FBP Fuel Type,Status,Temp (°C),RH (%),Wind Dir (°),Wind Speed (km/h),Precip (mm),Grass Cure (%),FFMC,DMC,DC,ISI,BUI,FWI,DGR CL,ROS (m/min),HFI,60 min fire size (ha),Fire Type,M/FIG,Fire Starts,Prep Level"
    Kamloops Fire Centre
    "Kamloops (K2), ,,,,,,,,,,,,,,,,,,,, 1, 0-1, 1"
    AFTON (322),780,O1B,ND,ND,ND,ND,ND,ND,ERROR,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND
    BLUE RIVER 2 (1108),695,C5,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND
    CLEARWATER HUB (239),453,C7,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND
    MAYSON (1082),1315,C3,ACTUAL,3.0,37.0,101,7.4,2.2,NaN,54.328,0.391,376.251,0.381,0.781,0.096,NaN,0.0,0.0,0.0,SUR,1
    SPARKS LAKE (305),972,C7,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND
    WELLS GRAY (266),959,C5,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND
    "Vernon (K4), ,,,,,,,,,,,,,,,,,,,, undefined, 0-1, undefined"
    FINTRY (298),670,C7,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND
    KETTLE 2 (388),1389,C5,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND
    SALMON ARM (346),527,C7,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND
    SEYMOUR ARM (344),511,C5,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND
    TURTLE (286),640,C7,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND
    "Penticton (K5), ,,,,,,,,,,,,,,,,,,,, undefined, 0-1, undefined"
    MCCUDDY (334),1067,C7,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND
    PENTICTON RS (328),427,C7,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND
    "Merritt (K6), ,,,,,,,,,,,,,,,,,,,, undefined, 0-1, undefined"
    AUGUST LAKE (836),855,C7,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND
    MERRITT 2 HUB (1399),640,C7,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND
    "Lillooet (K7), ,,,,,,,,,,,,,,,,,,,, 1, 0-1, 1"
    FIVE MILE (1029),865,C7,ACTUAL,1.4,57.0,205,7.0,0.0,NaN,69.486,0.735,252.982,0.876,1.459,0.25,NaN,0.0,0.0,0.0,SUR,1
    FRENCH BAR (306),1320,C7,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND
    GWYNETH LAKE (309),1205,C7,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND
    LILLOOET (280),408,C7,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND
    SPLINTLUM (1055),424,C7,ACTUAL,4.8,57.0,223,4.8,0.0,NaN,47.664,5.62,460.989,0.154,10.908,0.098,NaN,0.0,0.0,0.0,SUR,1`

    expect(dailyTableCSVString.replace(/\s+/g, '')).toEqual(
      expectedDailyString.replace(/\s+/g, '')
    )
  })

  it('should export Weekly Table to a CSV string correctly', () => {
    const startDate = DateTime.fromISO('2021-08-02T13:00:00.000-07:00')
    const stationDailiesForWeek: StationDaily[] = [
      {
        code: 1029,
        status: 'ACTUAL',
        temperature: 28.5,
        relative_humidity: 39,
        wind_speed: 7.1,
        wind_direction: 210,
        grass_cure_percentage: NaN,
        precipitation: 0,
        ffmc: 90.081,
        dmc: 228.649,
        dc: 879.147,
        isi: 6.203,
        bui: 277.116,
        fwi: 28.983,
        danger_class: NaN,
        observation_valid: true,
        observation_valid_comment: '',
        rate_of_spread: 1.4018578498133272,
        hfi: 1365.3478720077194,
        intensity_group: 3,
        sixty_minute_fire_size: 0.5190222203123409,
        fire_type: 'SUR',
        date: startDate
      },
      {
        code: 1029,
        status: 'ACTUAL',
        temperature: 30.1,
        relative_humidity: 19,
        wind_speed: 9.7,
        wind_direction: 237,
        grass_cure_percentage: NaN,
        precipitation: 0,
        ffmc: 94.802,
        dmc: 233.866,
        dc: 887.569,
        isi: 13.735,
        bui: 281.983,
        fwi: 48.729,
        danger_class: NaN,
        observation_valid: true,
        observation_valid_comment: 'null',
        rate_of_spread: 5.52911714908419,
        hfi: 5545.449104111655,
        intensity_group: 5,
        sixty_minute_fire_size: 6.09065638734279,
        fire_type: 'SUR',
        date: startDate.plus({days:})
      },
      {
        code: 1029,
        status: 'ACTUAL',
        temperature: 30.1,
        relative_humidity: 15,
        wind_speed: 8.1,
        wind_direction: 211,
        grass_cure_percentage: NaN,
        precipitation: 0,
        ffmc: 96.074,
        dmc: 239.341,
        dc: 895.991,
        isi: 15.07,
        bui: 287.012,
        fwi: 51.664,
        danger_class: NaN,
        observation_valid: true,
        observation_valid_comment: '',
        rate_of_spread: 6.41285421966408,
        hfi: 6468.903773298901,
        intensity_group: 5,
        sixty_minute_fire_size: 10.051119945012843,
        fire_type: 'SUR',
        date: startDate.plus({ days: 2 })
      },
      {
        code: 1029,
        status: 'ACTUAL',
        temperature: 27.6,
        relative_humidity: 27,
        wind_speed: 7.1,
        wind_direction: 250,
        grass_cure_percentage: NaN,
        precipitation: 0,
        ffmc: 94.941,
        dmc: 243.666,
        dc: 903.963,
        isi: 12.282,
        bui: 291.139,
        fwi: 45.441,
        danger_class: NaN,
        observation_valid: true,
        observation_valid_comment: '',
        rate_of_spread: 4.612191031826653,
        hfi: 4630.031283212997,
        intensity_group: 5,
        sixty_minute_fire_size: 5.8353996010594384,
        fire_type: 'SUR',
        date: startDate.plus({ days: 3 })
      },
      {
        code: 1029,
        status: 'ACTUAL',
        temperature: 20,
        relative_humidity: 39,
        wind_speed: 18.4,
        wind_direction: 268,
        grass_cure_percentage: NaN,
        precipitation: 0.2,
        ffmc: 91.788,
        dmc: 246.323,
        dc: 910.567,
        isi: 13.982,
        bui: 293.891,
        fwi: 49.325,
        danger_class: NaN,
        observation_valid: true,
        observation_valid_comment: '',
        rate_of_spread: 5.6964225750060855,
        hfi: 5619.733709460678,
        intensity_group: 5,
        sixty_minute_fire_size: 3.025776248052835,
        fire_type: 'SUR',
        date: startDate.plus({ days: 4 })
      },
      {
        code: 1055,
        status: 'ACTUAL',
        temperature: 27.3,
        relative_humidity: 54,
        wind_speed: 8,
        wind_direction: 143,
        grass_cure_percentage: NaN,
        precipitation: 0.4,
        ffmc: 69.682,
        dmc: 78.334,
        dc: 834.602,
        isi: 0.927,
        bui: 126.893,
        fwi: 5.393,
        danger_class: NaN,
        observation_valid: true,
        observation_valid_comment: '',
        rate_of_spread: 0.03541630670421867,
        hfi: 14.693607481768483,
        intensity_group: 1,
        sixty_minute_fire_size: 0.0002857324028999626,
        fire_type: 'SUR',
        date: startDate
      },
      {
        code: 1055,
        status: 'ACTUAL',
        temperature: 32.5,
        relative_humidity: 25,
        wind_speed: 12.5,
        wind_direction: 159,
        grass_cure_percentage: NaN,
        precipitation: 0,
        ffmc: 92.477,
        dmc: 83.536,
        dc: 843.456,
        isi: 11.446,
        bui: 133.915,
        fwi: 38.769,
        danger_class: NaN,
        observation_valid: true,
        observation_valid_comment: '',
        rate_of_spread: 3.970566253068135,
        hfi: 3817.978206084299,
        intensity_group: 4,
        sixty_minute_fire_size: 2.3142452776597726,
        fire_type: 'SUR',
        date: startDate.plus({ days: 1 })
      },
      {
        code: 1055,
        status: 'ACTUAL',
        temperature: 32.5,
        relative_humidity: 23,
        wind_speed: 13.4,
        wind_direction: 154,
        grass_cure_percentage: NaN,
        precipitation: 0,
        ffmc: 94.613,
        dmc: 88.877,
        dc: 852.31,
        isi: 16.126,
        bui: 140.997,
        fwi: 49.047,
        danger_class: NaN,
        observation_valid: true,
        observation_valid_comment: '',
        rate_of_spread: 6.922482970502497,
        hfi: 6770.372391737391,
        intensity_group: 5,
        sixty_minute_fire_size: 6.580497981162746,
        fire_type: 'SUR',
        date: startDate.plus({ days: 2 })
      },
      {
        code: 1055,
        status: 'ACTUAL',
        temperature: 33.2,
        relative_humidity: 21,
        wind_speed: 13.8,
        wind_direction: 173,
        grass_cure_percentage: NaN,
        precipitation: 0,
        ffmc: 95.271,
        dmc: 94.471,
        dc: 861.29,
        isi: 18.008,
        bui: 148.281,
        fwi: 53.295,
        danger_class: NaN,
        observation_valid: true,
        observation_valid_comment: '',
        rate_of_spread: 8.214727396150723,
        hfi: 8413.742269643013,
        intensity_group: 5,
        sixty_minute_fire_size: 4.179466308544374,
        fire_type: 'IC',
        date: startDate.plus({ days: 3 })
      },
      {
        code: 1055,
        status: 'ACTUAL',
        temperature: 27.2,
        relative_humidity: 29,
        wind_speed: 22.3,
        wind_direction: 147,
        grass_cure_percentage: NaN,
        precipitation: 0,
        ffmc: 94.231,
        dmc: 98.619,
        dc: 869.19,
        isi: 23.959,
        bui: 153.654,
        fwi: 64.066,
        danger_class: NaN,
        observation_valid: true,
        observation_valid_comment: '',
        rate_of_spread: 12.38668677449597,
        hfi: 13489.807298046951,
        intensity_group: 5,
        sixty_minute_fire_size: 10.488183633122842,
        fire_type: 'IC',
        date: startDate.plus({ days: 4 })
      }
    ]
    const weeklyTableString = HFITableCSVFormatter.exportWeeklyRowsAsStrings(
      NUM_WEEK_DAYS,
      fireCentres,
      stationDailiesForWeek
    )
    const expectedWeeklyString = ` , , , ,Mon Aug 2, , , , ,Tue Aug 3, , , , ,Wed Aug 4, , , , ,Thu Aug 5, , , , ,Fri Aug 6, , , , 
    Location,Elev. (m),FBP Fuel Type,Grass Cure (%),ROS (m/min),HFI,M / FIG,Fire Starts,Prep Level,ROS (m/min),HFI,M / FIG,Fire Starts,Prep Level,ROS (m/min),HFI,M / FIG,Fire Starts,Prep Level,ROS (m/min),HFI,M / FIG,Fire Starts,Prep Level,ROS (m/min),HFI,M / FIG,Fire Starts,Prep Level,Highest Daily FIG,Calc. Prep
    Kamloops Fire Centre
    Kamloops (K2), , , ,,,ND,0-1,ND,,,ND,0-1,ND,,,ND,0-1,ND,,,ND,0-1,ND,,,ND,0-1,ND,-Infinity,ND
    AFTON (322),780,O1B,ERROR,,
    BLUE RIVER 2 (1108),695,C5,ND,,
    CLEARWATER HUB (239),453,C7,ND,,
    MAYSON (1082),1315,C3,ND,,
    SPARKS LAKE (305),972,C7,ND,,
    WELLS GRAY (266),959,C5,ND,,
    Vernon (K4), , , ,,,ND,0-1,ND,,,ND,0-1,ND,,,ND,0-1,ND,,,ND,0-1,ND,,,ND,0-1,ND,-Infinity,ND
    FINTRY (298),670,C7,ND,,
    KETTLE 2 (388),1389,C5,ND,,
    SALMON ARM (346),527,C7,ND,,
    SEYMOUR ARM (344),511,C5,ND,,
    TURTLE (286),640,C7,ND,,
    Penticton (K5), , , ,,,ND,0-1,ND,,,ND,0-1,ND,,,ND,0-1,ND,,,ND,0-1,ND,,,ND,0-1,ND,-Infinity,ND
    MCCUDDY (334),1067,C7,ND,,
    PENTICTON RS (328),427,C7,ND,,
    Merritt (K6), , , ,,,ND,0-1,ND,,,ND,0-1,ND,,,ND,0-1,ND,,,ND,0-1,ND,,,ND,0-1,ND,-Infinity,ND
    AUGUST LAKE (836),855,C7,ND,,
    MERRITT 2 HUB (1399),640,C7,ND,,
    Lillooet (K7), , , ,,,2,0-1,1,,,4.5,0-1,4,,,5,0-1,4,,,5,0-1,4,,,5,0-1,4,5,3
    FIVE MILE (1029),865,C7,NaN,1.4,1365.3,3,,,5.5,5545.4,5,,,6.4,6468.9,5,,,4.6,4630.0,5,,,5.7,5619.7,5,,,,
    FRENCH BAR (306),1320,C7,ND,,
    GWYNETH LAKE (309),1205,C7,ND,,
    LILLOOET (280),408,C7,ND,,
    SPLINTLUM (1055),424,C7,NaN,0.0,14.7,1,,,4.0,3818.0,4,,,6.9,6770.4,5,,,8.2,8413.7,5,,,12.4,13489.8,5,,,,`

    expect(weeklyTableString.replace(/\s+/g, '')).toEqual(
      expectedWeeklyString.replace(/\s+/g, '')
    )
  })

  it("should not break CSV export when there's a escape character in the station name", () => {
    const escapeCharFireCentres = JSON.parse(JSON.stringify(fireCentres)) // hack to deep copy
    escapeCharFireCentres[0].planning_areas[1].stations[0].station_props.name = 'AF`TON'
    escapeCharFireCentres[0].planning_areas[1].stations[2].station_props.name =
      '`CLEARWATER HUB'
    escapeCharFireCentres[0].planning_areas[1].stations[4].station_props.name =
      'SPARKS LAKE`'
    escapeCharFireCentres[0].planning_areas[1].stations[5].station_props.name =
      'WELLS" GRAY'
    escapeCharFireCentres[0].planning_areas[2].stations[0].station_props.name = 'FINTRY,'
    const dailyTableCSVString = HFITableCSVFormatter.exportDailyRowsAsStrings(
      NUM_WEEK_DAYS,
      escapeCharFireCentres,
      dailies
    )

    const expectedDailyEscapeString = `"Location,Elev. (m),FBP Fuel Type,Status,Temp (°C),RH (%),Wind Dir (°),Wind Speed (km/h),Precip (mm),Grass Cure (%),FFMC,DMC,DC,ISI,BUI,FWI,DGR CL,ROS (m/min),HFI,60 min fire size (ha),Fire Type,M/FIG,Fire Starts,Prep Level"
    Kamloops Fire Centre
    "Kamloops (K2), ,,,,,,,,,,,,,,,,,,,, 1, 0-1, 1"
    AF\`TON (322),780,O1B,ND,ND,ND,ND,ND,ND,ERROR,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND
    BLUE RIVER 2 (1108),695,C5,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND
    \`CLEARWATER HUB (239),453,C7,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND
    MAYSON (1082),1315,C3,ACTUAL,3.0,37.0,101,7.4,2.2,NaN,54.328,0.391,376.251,0.381,0.781,0.096,NaN,0.0,0.0,0.0,SUR,1
    SPARKS LAKE\` (305),972,C7,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND
    "WELLS"" GRAY (266)",959,C5,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND
    "Vernon (K4), ,,,,,,,,,,,,,,,,,,,, undefined, 0-1, undefined"
    "FINTRY, (298)",670,C7,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND
    KETTLE 2 (388),1389,C5,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND
    SALMON ARM (346),527,C7,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND
    SEYMOUR ARM (344),511,C5,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND
    TURTLE (286),640,C7,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND
    "Penticton (K5), ,,,,,,,,,,,,,,,,,,,, undefined, 0-1, undefined"
    MCCUDDY (334),1067,C7,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND
    PENTICTON RS (328),427,C7,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND
    "Merritt (K6), ,,,,,,,,,,,,,,,,,,,, undefined, 0-1, undefined"
    AUGUST LAKE (836),855,C7,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND
    MERRITT 2 HUB (1399),640,C7,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND
    "Lillooet (K7), ,,,,,,,,,,,,,,,,,,,, 1, 0-1, 1"
    FIVE MILE (1029),865,C7,ACTUAL,1.4,57.0,205,7.0,0.0,NaN,69.486,0.735,252.982,0.876,1.459,0.25,NaN,0.0,0.0,0.0,SUR,1
    FRENCH BAR (306),1320,C7,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND
    GWYNETH LAKE (309),1205,C7,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND
    LILLOOET (280),408,C7,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND
    SPLINTLUM (1055),424,C7,ACTUAL,4.8,57.0,223,4.8,0.0,NaN,47.664,5.62,460.989,0.154,10.908,0.098,NaN,0.0,0.0,0.0,SUR,1`

    expect(dailyTableCSVString.replace(/\s+/g, '')).toEqual(
      expectedDailyEscapeString.replace(/\s+/g, '')
    )
  })

  it('should insert ND for station that has no elevation data available', () => {
    const missingElevationFireCentres = JSON.parse(JSON.stringify(fireCentres)) // a hack to deep copy
    missingElevationFireCentres[0].planning_areas[1].stations[0].station_props.elevation =
      undefined
    missingElevationFireCentres[0].planning_areas[1].stations[2].station_props.elevation =
      undefined

    const dailyTableCSVString = HFITableCSVFormatter.exportDailyRowsAsStrings(
      NUM_WEEK_DAYS,
      missingElevationFireCentres,
      dailies
    )
    const expectedDailyNDString = `"Location,Elev. (m),FBP Fuel Type,Status,Temp (°C),RH (%),Wind Dir (°),Wind Speed (km/h),Precip (mm),Grass Cure (%),FFMC,DMC,DC,ISI,BUI,FWI,DGR CL,ROS (m/min),HFI,60 min fire size (ha),Fire Type,M/FIG,Fire Starts,Prep Level"
    Kamloops Fire Centre
    "Kamloops (K2), ,,,,,,,,,,,,,,,,,,,, 1, 0-1, 1"
    AFTON (322),ND,O1B,ND,ND,ND,ND,ND,ND,ERROR,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND
    BLUE RIVER 2 (1108),695,C5,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND
    CLEARWATER HUB (239),ND,C7,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND
    MAYSON (1082),1315,C3,ACTUAL,3.0,37.0,101,7.4,2.2,NaN,54.328,0.391,376.251,0.381,0.781,0.096,NaN,0.0,0.0,0.0,SUR,1
    SPARKS LAKE (305),972,C7,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND
    WELLS GRAY (266),959,C5,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND
    "Vernon (K4), ,,,,,,,,,,,,,,,,,,,, undefined, 0-1, undefined"
    FINTRY (298),670,C7,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND
    KETTLE 2 (388),1389,C5,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND
    SALMON ARM (346),527,C7,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND
    SEYMOUR ARM (344),511,C5,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND
    TURTLE (286),640,C7,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND
    "Penticton (K5), ,,,,,,,,,,,,,,,,,,,, undefined, 0-1, undefined"
    MCCUDDY (334),1067,C7,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND
    PENTICTON RS (328),427,C7,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND
    "Merritt (K6), ,,,,,,,,,,,,,,,,,,,, undefined, 0-1, undefined"
    AUGUST LAKE (836),855,C7,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND
    MERRITT 2 HUB (1399),640,C7,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND
    "Lillooet (K7), ,,,,,,,,,,,,,,,,,,,, 1, 0-1, 1"
    FIVE MILE (1029),865,C7,ACTUAL,1.4,57.0,205,7.0,0.0,NaN,69.486,0.735,252.982,0.876,1.459,0.25,NaN,0.0,0.0,0.0,SUR,1
    FRENCH BAR (306),1320,C7,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND
    GWYNETH LAKE (309),1205,C7,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND
    LILLOOET (280),408,C7,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND,ND
    SPLINTLUM (1055),424,C7,ACTUAL,4.8,57.0,223,4.8,0.0,NaN,47.664,5.62,460.989,0.154,10.908,0.098,NaN,0.0,0.0,0.0,SUR,1`

    expect(dailyTableCSVString.replace(/\s+/g, '')).toEqual(
      expectedDailyNDString.replace(/\s+/g, '')
    )
  })
})
