import { MAP_BUTTON_GREY } from "@/theme";
import {
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  SelectChangeEvent,
} from "@mui/material";
import { FireCenter, FireShape } from "api/fbaAPI";
import React from "react";

export interface FireCenterDropdownProps {
  selectedFireCenter?: FireCenter;
  fireCenterOptions: FireCenter[];
  setSelectedFireCenter: React.Dispatch<
    React.SetStateAction<FireCenter | undefined>
  >;
  setSelectedFireShape: React.Dispatch<
    React.SetStateAction<FireShape | undefined>
  >;
}

const FireCenterDropdown = ({
  fireCenterOptions,
  selectedFireCenter,
  setSelectedFireCenter,
  setSelectedFireShape,
}: FireCenterDropdownProps) => {
  const handleChange = (event: SelectChangeEvent<string>): void => {
    const selectedName = event.target.value;
    const selected = fireCenterOptions.find((fc) => fc.name === selectedName);
    setSelectedFireShape(undefined);
    setSelectedFireCenter(selected ?? undefined);
  };

  return (
    <FormControl variant="outlined" size="small" sx={{ minWidth: 175 }}>
      <InputLabel id="fire-center-label" shrink={!!selectedFireCenter}>
        Centre
      </InputLabel>

      <Select
        data-testid="fire-center-dropdown"
        labelId="fire-center-label"
        id="fire-center-select"
        value={selectedFireCenter?.name ?? ""}
        onChange={handleChange}
        label="Centre"
        sx={{ fontWeight: "bold", color: MAP_BUTTON_GREY }}
      >
        {fireCenterOptions.map((option) => {
          const displayName = option.name.replace("Fire Centre", "");

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
