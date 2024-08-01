"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.isi = void 0;
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
function isi(ffmc, ws, fbpMod) {
    if (fbpMod === void 0) { fbpMod = false; }
    // FIX: works for now
    var exp = Math.exp;
    // used in conversion between FFMC and moisture content
    var FFMC_COEFFICIENT = 250.0 * 59.5 / 101.0;
    // Eq. 10 - Moisture content
    var fm = (FFMC_COEFFICIENT * (101 - ffmc)) / (59.5 + ffmc);
    // Eq. 24 - Wind Effect
    // the ifelse, also takes care of the ISI modification for the fbp functions
    // This modification is Equation 53a in FCFDG (1992)
    var fW = ws >= 40 && fbpMod
        ? 12 * (1 - exp(-0.0818 * (ws - 28)))
        : exp(0.05039 * ws);
    //Eq. 25 - Fine Fuel Moisture
    var fF = 91.9 * exp(-0.1386 * fm) * (1 + (Math.pow(fm, 5.31)) / 49300000);
    //Eq. 26 - Spread Index Equation
    var isi1 = 0.208 * fW * fF;
    return isi1;
}
exports.isi = isi;
exports.default = isi;
