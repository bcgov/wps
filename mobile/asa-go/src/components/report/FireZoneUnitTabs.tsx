import { FireCenter, FireShape } from "@/api/fbaAPI";
import AdvisoryText from "@/components/report/AdvisoryText";
import { useFireCentreDetails } from "@/hooks/useFireCentreDetails";
import { calculateStatusColour } from "@/utils/calculateZoneStatus";
import { Tab, Tabs, Typography } from "@mui/material";
import { Box, useTheme } from "@mui/system";
import { isEmpty, isUndefined } from "lodash";
import { useEffect, useState } from "react";

interface FireZoneUnitTabsProps {
  advisoryThreshold: number;
  selectedFireCenter: FireCenter | undefined;
  selectedFireZoneUnit: FireShape | undefined;
  setSelectedFireZoneUnit: React.Dispatch<
    React.SetStateAction<FireShape | undefined>
  >;
}

const FireZoneUnitTabs = ({
  advisoryThreshold,
  selectedFireCenter,
  selectedFireZoneUnit,
  setSelectedFireZoneUnit,
}: FireZoneUnitTabsProps) => {
  const [tabNumber, setTabNumber] = useState(0);
  const sortedGroupedFireZoneUnits = useFireCentreDetails(selectedFireCenter);
  const theme = useTheme();

  const getTabFireShape = (tabNumber: number): FireShape | undefined => {
    if (sortedGroupedFireZoneUnits.length > 0) {
      const selectedTabZone = sortedGroupedFireZoneUnits[tabNumber];

      const fireShape: FireShape = {
        fire_shape_id: selectedTabZone.fire_shape_id,
        mof_fire_centre_name: selectedTabZone.fire_centre_name,
        mof_fire_zone_name: selectedTabZone.fire_shape_name,
      };

      return fireShape;
    }
  };

  useEffect(() => {
    if (selectedFireZoneUnit) {
      const newIndex = sortedGroupedFireZoneUnits.findIndex(
        (zone) => zone.fire_shape_id === selectedFireZoneUnit.fire_shape_id
      );
      if (newIndex !== -1) {
        setTabNumber(newIndex);
      }
    } else {
      setTabNumber(0);
      setSelectedFireZoneUnit(getTabFireShape(0)); // if no selected FireShape, select the first one in the sorted tabs
    }
  }, [selectedFireZoneUnit, sortedGroupedFireZoneUnits]);

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setTabNumber(newValue);

    const fireShape = getTabFireShape(newValue);
    setSelectedFireZoneUnit(fireShape);
  };

  if (isUndefined(selectedFireCenter)) {
    return <div data-testid="fire-zone-unit-tabs-empty"></div>;
  }

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        width: "100%",
      }}
    >
      {isEmpty(sortedGroupedFireZoneUnits) && (
        <Typography sx={{ paddingLeft: "1rem", paddingTop: "1rem" }}>
          No advisory data available for the selected date.
        </Typography>
      )}
      <Tabs
        value={tabNumber}
        onChange={handleTabChange}
        sx={{
          mx: theme.spacing(1),
          maxWidth: `calc(100% - ${theme.spacing(1)})`,
          "& .MuiTab-root": {
            flex: 1,
            minWidth: 0,
          },
          ".MuiTabs-indicator": {
            height: "4px",
          },
        }}
      >
        {sortedGroupedFireZoneUnits.map((zone, index) => {
          const isActive = tabNumber === index;
          const key = zone.fire_shape_id;
          return (
            <Tab
              key={key}
              data-testid={`zone-${key}-tab`}
              sx={{
                backgroundColor: calculateStatusColour(
                  zone.fireShapeDetails,
                  advisoryThreshold,
                  "#FFFFFF"
                ),
                fontWeight: "bold",
                color: isActive ? "black" : "grey",
                minHeight: "30px",
              }}
              label={zone.fire_shape_name.split("-")[0]}
              aria-label={`zone-${key}-tab`}
            />
          );
        })}
      </Tabs>
      <Box
        sx={{
          display: "flex",

          flexGrow: 1,
          maxWidth: `calc(100% - ${theme.spacing(1)})`,
          mb: theme.spacing(1),
          mx: theme.spacing(1),
        }}
      >
        <AdvisoryText
          advisoryThreshold={advisoryThreshold}
          selectedFireCenter={selectedFireCenter}
          selectedFireZoneUnit={selectedFireZoneUnit}
        />
      </Box>
    </Box>
  );
};

export default FireZoneUnitTabs;
