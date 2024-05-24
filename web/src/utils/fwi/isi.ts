/**
 * Computes the Initial Spread Index From the FWI System. Equations are from
 * Van Wagner (1985) as listed below, except for the modification for fbp
 * takene from FCFDG (1992).
 *
 * Equations and FORTRAN program for the Canadian Forest Fire
 * Weather Index System. 1985. Van Wagner, C.E.; Pickett, T.L.
 * Canadian Forestry Service, Petawawa National Forestry
 * Institute, Chalk River, Ontario. Forestry Technical Report 33.
 * 18 p.
 *
 * Forestry Canada  Fire Danger Group (FCFDG) (1992). Development and
 * Structure of the Canadian Forest Fire Behavior Prediction System."
 * Technical ReportST-X-3, Forestry Canada, Ottawa, Ontario.
 *
 * @param {number} ffmc - Fine Fuel Moisture Code
 * @param {number} ws - Wind Speed (km/h)
 * @param {boolean} [fbpMod=false] - use fbp modification at the extreme end
 * @returns {number} Intial Spread Index
 */
export function isi(ffmc: number, ws: number, fbpMod: boolean = false) {
  // FIX: works for now
  const exp = Math.exp;
  // Eq. 10 - Moisture content
  const fm = (147.27723 * (101 - ffmc)) / (59.5 + ffmc);
  // Eq. 24 - Wind Effect
  // the ifelse, also takes care of the ISI modification for the fbp functions
  // This modification is Equation 53a in FCFDG (1992)
  const fW =
    ws >= 40 && fbpMod
      ? 12 * (1 - exp(-0.0818 * (ws - 28)))
      : exp(0.05039 * ws);
  //Eq. 25 - Fine Fuel Moisture
  const fF = 91.9 * exp(-0.1386 * fm) * (1 + (fm ** 5.31) / 49300000);
  //Eq. 26 - Spread Index Equation
  const isi1 = 0.208 * fW * fF;
  return isi1;
}

export default isi;
