import { FireCenter, FireShape } from "@/api/fbaAPI";
import FireCenterDropdown from "@/components/FireCenterDropdown";
import AdvisoryText from "@/components/report/AdvisoryText";
import FireZoneUnitTabs from "@/components/report/FireZoneUnitTabs";
import TodayTomorrowSwitch from "@/components/TodayTomorrowSwitch";
import { selectFireCenters } from "@/store";
import { HEADER_GREY, INFO_PANEL_CONTENT_BACKGROUND } from "@/theme";
import { TextSnippet } from "@mui/icons-material";
import { Box, FormControl, Typography, useTheme } from "@mui/material";
import { DateTime } from "luxon";
import { useSelector } from "react-redux";

interface AdvisoryProps {
  advisoryThreshold: number;
  date: DateTime;
  setDate: React.Dispatch<React.SetStateAction<DateTime>>;
  selectedFireCenter: FireCenter | undefined;
  setSelectedFireCenter: React.Dispatch<
    React.SetStateAction<FireCenter | undefined>
  >;
  selectedFireZoneUnit: FireShape | undefined;
  setSelectedFireZoneUnit: React.Dispatch<
    React.SetStateAction<FireShape | undefined>
  >;
}

const Advisory = ({
  advisoryThreshold,
  date,
  setDate,
  selectedFireCenter,
  setSelectedFireCenter,
  selectedFireZoneUnit,
  setSelectedFireZoneUnit,
}: AdvisoryProps) => {
  const { fireCenters } = useSelector(selectFireCenters);
  const theme = useTheme();
  return (
    <Box
      data-testid="asa-go-advisory"
      sx={{
        display: "flex",
        flex: 1,
        flexDirection: "column",
        height: "100%",
        overflowY: "hidden",
      }}
    >
      <Box
        data-testid="advisory-control-container"
        sx={{
          alignItems: "center",
          backgroundColor: "white",
          display: "flex",
          padding: theme.spacing(1),
        }}
      >
        <Box
          sx={{ alignItems: "center", display: "flex", pr: theme.spacing(1) }}
        >
          <TodayTomorrowSwitch border={true} date={date} setDate={setDate} />
        </Box>
        <Box sx={{ display: "flex", flexGrow: 1 }}>
          <FormControl
            sx={{
              backgroundColor: "white",
              margin: 1,
              maxWidth: 300,
              minWidth: 250,
              flexGrow: 1,
            }}
          >
            <FireCenterDropdown
              fireCenterOptions={fireCenters ?? []}
              selectedFireCenter={selectedFireCenter}
              setSelectedFireCenter={setSelectedFireCenter}
              setSelectedFireShape={setSelectedFireZoneUnit}
            />
          </FormControl>
        </Box>
      </Box>
      <Box
        sx={{
          alignItems: "center",
          backgroundColor: HEADER_GREY,
          display: "flex",
          p: theme.spacing(1),
        }}
      >
        <TextSnippet />
        <Typography
          sx={{ fontWeight: "bold", pl: theme.spacing(1) }}
          variant="h5"
        >
          Advisory Report
        </Typography>
      </Box>
      <Box
        id="advisory-content-container"
        sx={{
          backgroundColor: INFO_PANEL_CONTENT_BACKGROUND,
          display: "flex",
          flexGrow: 1,
          padding: theme.spacing(1),
          overflowY: "hidden",
        }}
      >
        <FireZoneUnitTabs
          advisoryThreshold={advisoryThreshold}
          selectedFireCenter={selectedFireCenter}
          selectedFireZoneUnit={selectedFireZoneUnit}
          setSelectedFireZoneUnit={setSelectedFireZoneUnit}
        >
          <AdvisoryText
            advisoryThreshold={advisoryThreshold}
            selectedFireCenter={selectedFireCenter}
            selectedFireZoneUnit={selectedFireZoneUnit}
          />
        </FireZoneUnitTabs>
      </Box>
    </Box>
  );
};

export default Advisory;
