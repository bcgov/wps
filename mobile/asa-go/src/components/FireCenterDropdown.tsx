import { Autocomplete, TextField } from "@mui/material";
import { FireCenter, FireShape } from "api/fbaAPI";
import { isEqual } from "lodash";
import React from "react";

interface FireCenterDropdownProps {
  selectedFireCenter?: FireCenter;
  fireCenterOptions: FireCenter[];
  setSelectedFireCenter: React.Dispatch<
    React.SetStateAction<FireCenter | undefined>
  >;
  setSelectedFireShape: React.Dispatch<
    React.SetStateAction<FireShape | undefined>
  >;
}

const FireCenterDropdown = (props: FireCenterDropdownProps) => {
  // eslint-disable-next-line
  const changeHandler = (_: React.ChangeEvent<{}>, value: any | null) => {
    if (!isEqual(props.selectedFireCenter, value)) {
      props.setSelectedFireShape(undefined);
      props.setSelectedFireCenter(value);
    }
  };

  return (
    <Autocomplete
      blurOnSelect
      data-testid={`fire-center-dropdown`}
      getOptionLabel={(option) => option?.name}
      onChange={changeHandler}
      options={props.fireCenterOptions}
      renderInput={(params) => (
        <TextField
          {...params}
          slotProps={{
            input: {
              ...params.InputProps,
              readOnly: true,
            },
          }}
        />
      )}
      value={props.selectedFireCenter || null}
    />
  );
};

export default React.memo(FireCenterDropdown);
