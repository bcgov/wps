import Grid from "@mui/material/Grid2";
import { Box, IconButton } from "@mui/material";
import LocationOnIcon from "@mui/icons-material/LocationOn";
import AccountCircleIcon from "@mui/icons-material/AccountCircle";
import ArticleIcon from "@mui/icons-material/Article";
import ThunderstormIcon from "@mui/icons-material/Thunderstorm";
import { theme } from "@/theme";

export const ASATabs = () => {
  return (
    <Box
      sx={{
        height: 100,
        background: theme.palette.primary.main,
      }}
    >
      <Grid
        container
        spacing={5}
        sx={{
          flexGrow: 1,
          width: "fit-content",
          marginTop: 2,
        }}
      >
        <Grid>
          <IconButton sx={{ paddingLeft: 7, color: "white" }} size="large">
            <LocationOnIcon />
          </IconButton>
        </Grid>
        <Grid>
          <IconButton sx={{ color: "white" }}>
            <AccountCircleIcon />
          </IconButton>
        </Grid>
        <Grid>
          <IconButton sx={{ color: "white" }}>
            <ArticleIcon />
          </IconButton>
        </Grid>
        <Grid>
          <IconButton sx={{ color: "white" }}>
            <ThunderstormIcon />
          </IconButton>
        </Grid>
      </Grid>
    </Box>
  );
};
