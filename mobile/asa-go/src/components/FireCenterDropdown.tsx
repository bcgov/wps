import { MAP_BUTTON_GREY } from "@/theme";
import {
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  SelectChangeEvent,
} from "@mui/material";
import { FireShape } from "api/fbaAPI";
import type { FireCentre } from "@/types/fireCentre";
import React from "react";

export interface FireCenterDropdownProps {
  selectedFireCentre?: FireCentre;
  fireCentreOptions: FireCentre[];
  setSelectedFireCentre: React.Dispatch<
    React.SetStateAction<FireCentre | undefined>
  >;
  setSelectedFireShape: React.Dispatch<
    React.SetStateAction<FireShape | undefined>
  >;
}

const FireCenterDropdown = ({
  fireCentreOptions,
  selectedFireCentre,
  setSelectedFireCentre,
  setSelectedFireShape,
}: FireCenterDropdownProps) => {
  const getDisplayName = (name: string): string =>
    name.replace("Fire Centre", "").trim();

  const handleChange = (event: SelectChangeEvent<string>): void => {
    const selectedName = event.target.value;
    const selected = fireCentreOptions.find((fc) => fc.name === selectedName);
    setSelectedFireShape(undefined);
    setSelectedFireCentre(selected ?? undefined);
  };

  return (
    <FormControl variant="outlined" size="small" sx={{ minWidth: 175 }}>
      <InputLabel id="fire-center-label" shrink>
        Centre
      </InputLabel>

      <Select
        data-testid="fire-center-dropdown"
        labelId="fire-center-label"
        id="fire-center-select"
        value={selectedFireCentre?.name ?? ""}
        onChange={handleChange}
        label="Centre"
        displayEmpty
        renderValue={(value) => (value ? getDisplayName(value) : "")}
        sx={{ fontWeight: "bold", color: MAP_BUTTON_GREY }}
      >
        {fireCentreOptions.map((option) => {
          const displayName = getDisplayName(option.name);

          return (
            <MenuItem
              key={option.name}
              value={option.name}
              sx={{ fontWeight: "bold", color: MAP_BUTTON_GREY }}
            >
              {displayName}
            </MenuItem>
          );
        })}
      </Select>
    </FormControl>
  );
};

export default React.memo(FireCenterDropdown);
