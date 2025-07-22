import { FireZoneTPIStats } from "@/api/fbaAPI";
import { isNil } from "lodash";

export const hasRequiredFields = (
  stats: FireZoneTPIStats
): stats is Required<FireZoneTPIStats> => {
  return (
    !isNil(stats.mid_slope_hfi) &&
    !isNil(stats.mid_slope_tpi) &&
    !isNil(stats.upper_slope_hfi) &&
    !isNil(stats.upper_slope_tpi) &&
    !isNil(stats.valley_bottom_hfi) &&
    !isNil(stats.valley_bottom_tpi)
  );
};
