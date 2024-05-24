/**
 * Duff Moisture Code Calculation. All code
 * is based on a C code library that was written by Canadian
 * Forest Service Employees, which was originally based on
 * the Fortran code listed in the reference below. All equations
 * in this code refer to that document.
 *
 * Equations and FORTRAN program for the Canadian Forest Fire
 * Weather Index System. 1985. Van Wagner, C.E.; Pickett, T.L.
 * Canadian Forestry Service, Petawawa National Forestry
 * Institute, Chalk River, Ontario. Forestry Technical Report 33.
 * 18 p.
 *
 * Additional reference on FWI system
 *
 * Development and structure of the Canadian Forest Fire Weather
 * Index System. 1987. Van Wagner, C.E. Canadian Forestry Service,
 * Headquarters, Ottawa. Forestry Technical Report 35. 35 p.
 *
 * @param {number} dmc_yda - The Duff Moisture Code from previous iteration
 * @param {number} temp - Temperature (centigrade)
 * @param {number} rh - Relative Humidity (%)
 * @param {number} prec - Precipitation(mm)
 * @param {number} lat - Latitude (decimal degrees)
 * @param {number} mon - Month (1-12)
 * @param {boolean} [lat_adjust=true] - Latitude adjustment
 * @returns {number} A single dmc value
 */
export function dmc(
  dmc_yda: number,
  temp: number,
  rh: number,
  prec: number,
  lat: number,
  mon: number,
  lat_adjust: boolean = true
) {
  // FIX: works for now
  const exp = Math.exp;
  const log = Math.log;
  // Reference latitude for DMC day length adjustment
  // 46N: Canadian standard, latitude >= 30N   (Van Wagner 1987)
  const ell01 = [6.5, 7.5, 9, 12.8, 13.9, 13.9, 12.4, 10.9, 9.4, 8, 7, 6];
  // 20N: For 30 > latitude >= 10
  const ell02 = [7.9, 8.4, 8.9, 9.5, 9.9, 10.2, 10.1, 9.7, 9.1, 8.6, 8.1, 7.8];
  // 20S: For -10 > latitude >= -30
  const ell03 = [10.1, 9.6, 9.1, 8.5, 8.1, 7.8, 7.9, 8.3, 8.9, 9.4, 9.9, 10.2];
  // 40S: For -30 > latitude
  const ell04 = [11.5, 10.5, 9.2, 7.9, 6.8, 6.2, 6.5, 7.4, 8.7, 10, 11.2, 11.8];
  // For latitude near the equator, we simple use a factor of 9 for all months

  // constrain low end of temperature
  temp = temp < -1.1 ? -1.1 : temp;
  // Eq. 16 - The log drying rate
  let rk = 1.894 * (temp + 1.1) * (100 - rh) * ell01[mon - 1] * 1e-4;
  //Adjust the day length  and thus the drying r, based on latitude and month
  if (lat_adjust) {
    rk =
      lat <= 30 && lat > 10
        ? 1.894 * (temp + 1.1) * (100 - rh) * ell02[mon - 1] * 1e-4
        : rk;
    rk =
      lat <= -10 && lat > -30
        ? 1.894 * (temp + 1.1) * (100 - rh) * ell03[mon - 1] * 1e-4
        : rk;
    rk =
      lat <= -30 && lat >= -90
        ? 1.894 * (temp + 1.1) * (100 - rh) * ell04[mon - 1] * 1e-4
        : rk;
    rk =
      lat <= 10 && lat > -10
        ? 1.894 * (temp + 1.1) * (100 - rh) * 9 * 1e-4
        : rk;
  }

  // Constrain P
  let pr = dmc_yda;
  if (prec > 1.5) {
    const ra = prec;
    // Eq. 11 - Net rain amount
    const rw = 0.92 * ra - 1.27;
    //Alteration to Eq. 12 to calculate more accurately
    const wmi = 20 + 280 / exp(0.023 * dmc_yda);
    //Eqs. 13a, 13b, 13c
    const b =
      dmc_yda <= 33
        ? 100 / (0.5 + 0.3 * dmc_yda)
        : dmc_yda <= 65
        ? 14 - 1.3 * log(dmc_yda)
        : 6.2 * log(dmc_yda) - 17.2;
    // Eq. 14 - Moisture content after rain
    const wmr = wmi + (1000 * rw) / (48.77 + b * rw);

    // Alteration to Eq. 15 to calculate more accurately
    pr = 43.43 * (5.6348 - log(wmr - 20));
  }

  pr = pr < 0 ? 0 : pr;
  // Calculate final P (DMC)
  let dmc1 = pr + rk;
  dmc1 = dmc1 < 0 ? 0 : dmc1;
  return dmc1;
}

export default dmc;
