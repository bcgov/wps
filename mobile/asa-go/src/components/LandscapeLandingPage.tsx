import AsaIcon from "@/assets/asa-go-transparent.png";
import AppDescription from "@/components/AppDescription";
import LoginButton from "@/components/LoginButton";
import PublicLoginButton from "@/components/PublicLoginButton";
import { useIsXSSmallScreen } from "@/hooks/useIsXSScreen";
import { selectAuthentication } from "@/store";
import { Box, CircularProgress, Typography, useTheme } from "@mui/material";
import { isNull } from "lodash";
import { useSelector } from "react-redux";

// Landscape orientation landing page for phones only, not to be used with tablets.
const LandscapeLandingPage = () => {
  const theme = useTheme();
  const isXSSmallScreen = useIsXSSmallScreen();
  const { authenticating, error } = useSelector(selectAuthentication);

  return (
    <Box
      sx={{
        bgcolor: theme.palette.primary.dark,
        display: "flex",
        height: "100vh",
      }}
    >
      <Box
        sx={{
          alignItems: "center",
          display: "flex",
          flexDirection: "row",
          px: theme.spacing(2),
          width: "100%",
          paddingRight: "env(safe-area-inset-right)",
          paddingLeft: "env(safe-area-inset-left)",
        }}
      >
        <Box
          sx={{
            alignItems: "center",
            display: "flex",
            flex: "0 0 40%",
            flexDirection: "column",
            justifyContent: "center",
          }}
        >
          <Box
            component="img"
            sx={{
              height: isXSSmallScreen ? "200px" : "250px",
              width: isXSSmallScreen ? "200px" : "250px",
            }}
            src={AsaIcon}
          />
          <Typography sx={{ color: "white", fontWeight: "bold" }} variant="h3">
            ASA Go
          </Typography>
        </Box>
        <Box
          sx={{
            alignItems: "center",
            display: "flex",
            flex: 1,
            flexDirection: "column",
            pl: theme.spacing(2),
          }}
        >
          <Box sx={{ maxWidth: "80%" }}>
            <AppDescription />
          </Box>
          <Box
            sx={{
              alignItems: "center",
              display: "flex",
              flexDirection: "row",
              gap: theme.spacing(2),
              justifyContent: "center",
              pt: theme.spacing(8),
            }}
          >
            {!authenticating && (
              <>
                <Box sx={{ pr: theme.spacing(4) }}>
                  <LoginButton />
                </Box>
                <Box sx={{ pl: theme.spacing(4) }}>
                  <PublicLoginButton />
                </Box>
              </>
            )}
            {authenticating && <CircularProgress color="secondary" />}
            {!isNull(error) && (
              <Typography sx={{ color: "white" }} variant="body1">
                Unable to login, please try again.
              </Typography>
            )}
          </Box>
        </Box>
      </Box>
    </Box>
  );
};

export default LandscapeLandingPage;
