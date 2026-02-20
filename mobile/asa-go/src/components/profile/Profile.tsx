import { FireCenter, FireShape } from "@/api/fbaAPI";
import FireCenterDropdown from "@/components/FireCenterDropdown";
import FireZoneUnitSummary from "@/components/profile/FireZoneUnitSummary";
import { DefaultText } from "@/components/report/DefaultText";
import FireZoneUnitTabs from "@/components/report/FireZoneUnitTabs";
import TodayTomorrowSwitch from "@/components/TodayTomorrowSwitch";
import { selectFireCenters } from "@/store";
import { Box, useTheme } from "@mui/material";
import { DateTime } from "luxon";
import { useSelector } from "react-redux";

export interface ProfileProps {
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

const Profile = ({
  date,
  setDate,
  selectedFireCenter,
  setSelectedFireCenter,
  selectedFireZoneUnit,
  setSelectedFireZoneUnit,
}: ProfileProps) => {
  const { fireCenters } = useSelector(selectFireCenters);
  const theme = useTheme();
  return (
    <Box
      data-testid="asa-go-profile"
      sx={{
        display: "flex",
        flex: 1,
        flexDirection: "column",
        height: "100%",
        overflowY: "hidden",
      }}
    >
      <Box
        data-testid="profile-control-container"
        sx={{
          alignItems: "end",
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
        <Box sx={{ display: "flex", flexGrow: 1, pt: theme.spacing(1) }}>
          <FireCenterDropdown
            fireCenterOptions={fireCenters ?? []}
            selectedFireCenter={selectedFireCenter}
            setSelectedFireCenter={setSelectedFireCenter}
            setSelectedFireShape={setSelectedFireZoneUnit}
          />
        </Box>
      </Box>

      <Box
        id="profile-content-container"
        sx={{
          backgroundColor: "#FFFFFF",
          display: "flex",
          flexGrow: 1,
          paddingTop: theme.spacing(1),
          overflowY: "hidden",
        }}
      >
        {!selectedFireCenter ? (
          <DefaultText />
        ) : (
          <FireZoneUnitTabs
            selectedFireCenter={selectedFireCenter}
            selectedFireZoneUnit={selectedFireZoneUnit}
            setSelectedFireZoneUnit={setSelectedFireZoneUnit}
            date={date}
          >
            <FireZoneUnitSummary
              selectedFireCenter={selectedFireCenter}
              selectedFireZoneUnit={selectedFireZoneUnit}
              date={date}
            />
          </FireZoneUnitTabs>
        )}
      </Box>
    </Box>
  );
};

export default Profile;
