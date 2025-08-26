import { useTheme } from "@mui/material/styles";
import Typography from "@mui/material/Typography";
import { Box, Grid2 as Grid } from "@mui/material";
import { FireZoneTPIStats } from "@/api/fbaAPI";
import Mountain from "@/images/mountain.png";
import ElevationLabel from "@/components/profile/ElevationLabel";
import ElevationFlag from "@/components/profile/ElevationFlag";

enum ElevationOption {
  BOTTOM = "Valley Bottom",
  MID = "Mid Slope",
  UPPER = "Upper Slope",
}

interface ElevationStatusProps {
  tpiStats: Required<FireZoneTPIStats>;
}

const ElevationStatus = ({ tpiStats }: ElevationStatusProps) => {
  const theme = useTheme();
  const mid_percent =
    tpiStats.mid_slope_tpi === 0
      ? 0
      : Math.round((tpiStats.mid_slope_hfi / tpiStats.mid_slope_tpi) * 100);
  const upper_percent =
    tpiStats.upper_slope_tpi === 0
      ? 0
      : Math.round((tpiStats.upper_slope_hfi / tpiStats.upper_slope_tpi) * 100);
  const bottom_percent =
    tpiStats.valley_bottom_tpi === 0
      ? 0
      : Math.round(
          (tpiStats.valley_bottom_hfi / tpiStats.valley_bottom_tpi) * 100
        );
  return (
    <Grid container size={12} data-testid="elevation-status">
      <Grid container sx={{ height: theme.spacing(6) }} size={12}>
        <Grid
          sx={{
            paddingLeft: theme.spacing(0.5),
            paddingRight: theme.spacing(0.5),
          }}
          size={6}
        >
          <Typography
            sx={{
              color: "#003366",
              fontWeight: "bold",
              textAlign: "left",
            }}
          >
            Topographic Position:
          </Typography>
        </Grid>
        <Grid sx={{ display: "flex", justifyContent: "flex-end" }} size={6}>
          <Typography
            sx={{
              color: "#003366",
              fontWeight: "bold",
              textAlign: "right",
            }}
          >
            Portion under advisory:
          </Typography>
        </Grid>
      </Grid>
      <Grid size={12}>
        <Box
          sx={{
            background: `url(${Mountain})`,
            backgroundRepeat: "round",
            display: "flex",
            width: "100%",
          }}
          data-testid="tpi-mountain"
        >
          <Grid
            sx={{
              paddingLeft: theme.spacing(0.5),
              paddingRight: theme.spacing(0.5),
            }}
            container
            size={12}
          >
            <Grid container sx={{ height: theme.spacing(8) }} size={12}>
              <ElevationLabel label={ElevationOption.UPPER} />
              <ElevationFlag percent={upper_percent} testId="upper-slope" />
            </Grid>
            <Grid container sx={{ height: theme.spacing(8) }} size={12}>
              <ElevationLabel label={ElevationOption.MID} />
              <ElevationFlag percent={mid_percent} testId="mid-slope" />
            </Grid>
            <Grid container sx={{ height: theme.spacing(8) }} size={12}>
              <ElevationLabel label={ElevationOption.BOTTOM} />
              <ElevationFlag percent={bottom_percent} testId="valley-bottom" />
            </Grid>
          </Grid>
        </Box>
      </Grid>
    </Grid>
  );
};

export default ElevationStatus;
