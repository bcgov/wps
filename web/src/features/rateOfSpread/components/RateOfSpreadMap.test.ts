import {
  ROScalc,
  ISIcalc,
  Slopecalc,
  BEcalc
} from 'features/rateOfSpread/components/RateOfSpreadMap'

describe('something', () => {
  it('ISIcalc', () => {
    // in python: cffrds._ISIcalc(50, 0)
    expect(ISIcalc(50, 0)).toEqual(0.16407612040504677)
  })
  it('BEcalc', () => {
    // in python: cffrds._BEcalc('C3', 35)
    expect(BEcalc('C3', 35)).toEqual(0.8361287104457107)
  })
  it('ROScalc C3', () => {
    // in python: cffrds._ROScalc('C3', 0.16407612040504677, -1, 97)
    expect(ROScalc('C3', 0.16407612040504677, -1, 97, 0, 0, 0, 0, 0)).toEqual(
      0.00004206635402158481
    )
  })
  it('Slopecalc C3', () => {
    //   #   FUELTYPE: The Fire Behaviour Prediction FuelType
    //   #       FFMC: Fine Fuel Moisture Code
    //   #        BUI: The Buildup Index value
    //   #         WS: Windspeed (km/h)
    //   #        WAZ: Wind Azimuth
    //   #         GS: Ground Slope (%)
    //   #        SAZ: Slope Azimuth
    //   #        FMC: Foliar Moisture Content
    //   #        SFC: Surface Fuel Consumption (kg/m^2)
    //   #         PC: Percent Conifer (%)
    //   #        PDF: Percent Dead Balsam Fir (%)
    //   #         CC: Constant
    //   #        CBH: Crown Base Height (m)
    //   #        ISI: Initial Spread Index
    //   #     output: Type of variable to output (RAZ/WSV, default=RAZ)
    /*
    in python: cffrds._Slopecalc(
    FUELTYPE='C3', 
    FFMC=50, 
    BUI=35, 
    WS=15, 
    WAZ=0, 
    GS=0, 
    SAZ=0, 
    FMC=FMC,
    PC=3,
    ISI=0,
    output='WSV')
    */
    const wsv = Slopecalc(
      'C3', // FUELTYPE
      50, //FFMC
      35, // BUI
      15, //WS
      0, // WAZ
      0, // GS
      0, // SAZ
      97, // FMC
      undefined, // SFC
      3, // PC
      0, // PDF
      0, // CC
      0, // CBH
      0, // ISI
      'WSV' //output
    )
    expect(wsv).toEqual(15.000000000000071)
  })
})
// const noonDate = '2020-12-09T20:00:00+00:00'
// const precip = calculateAccumulatedPrecip(noonDate, [
//   {
//     datetime: '2020-12-08T20:00:00+00:00',
//     delta_precipitation: 1.1
//   },
//   { datetime: '2020-12-08T19:00:00+00:00', delta_precipitation: 1.1 },
//   {
//     datetime: '2020-12-09T19:00:00+00:00',
//     delta_precipitation: 1.1
//   },
//   {
//     datetime: '2020-12-09T18:00:00+00:00',
//     delta_precipitation: 1.1
//   }
// ] as ModelValue[])
// // we expect that only two of the records to summed up.
// expect(precip?.precipitation).toEqual(2.2)
// expect(precip?.values.length).toEqual(2)
