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
export declare function isi(ffmc: number, ws: number, fbpMod?: boolean): number;
export default isi;
