/**
 * Description: Fine Fuel Moisture Code Calculation. All code
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
 *
 * @param {number} ffmc_yda - The Fine Fuel Moisture Code from previous iteration
 * @param {number} temp - Temperature (centigrade)
 * @param {number} rh - Relative Humidity (%)
 * @param {number} prec - Precipitation (mm)
 * @param {number} ws - Wind speed (km/h)
 * @returns {number} A single ffmc value
 */
export declare function ffmc(ffmc_yda: number, temp: number, rh: number, ws: number, prec: number): number;
export default ffmc;
