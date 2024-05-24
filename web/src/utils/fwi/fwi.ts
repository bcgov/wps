/**
 * Fire Weather Index Calculation. All code
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
 * @param {number} isi - Initial Spread Index
 * @param {number} bui - Buildup Index
 * @returns {number} A single fwi value
 */
export function fwi(isi: number, bui: number) {
  // FIX: works for now
  const exp = Math.exp;
  const log = Math.log;
  //Eqs. 28b, 28a, 29
  const bb =
    bui > 80
      ? 0.1 * isi * (1000 / (25 + 108.64 / exp(0.023 * bui)))
      : 0.1 * isi * (0.626 * (bui ** 0.809) + 2);
  //Eqs. 30b, 30a
  const fwi1 = bb <= 1 ? bb : exp(2.72 * ((0.434 * log(bb)) ** 0.647));
  return fwi1;
}

export default fwi;
