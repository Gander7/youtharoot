import React from 'react';
import { TextField, InputAdornment } from '@mui/material';
import { Phone as PhoneIcon } from '@mui/icons-material';

/**
 * Simple phone input using HTML5 tel input type
 * Much simpler than custom validation, relies on browser native validation
 */
const SimplePhoneInput = ({
  label = "Phone Number",
  value = '',
  onChange,
  required = false,
  fullWidth = true,
  helperText = 'Format: (416) 555-1234 or +1-416-555-1234',
  ...props
}) => {
  return (
    <TextField
      {...props}
      type="tel"
      label={label}
      value={value}
      onChange={onChange}
      required={required}
      fullWidth={fullWidth}
      helperText={helperText}
      InputProps={{
        startAdornment: (
          <InputAdornment position="start">
            <PhoneIcon />
          </InputAdornment>
        ),
        ...props.InputProps
      }}
      placeholder="(416) 555-1234"
      // HTML5 pattern for North American phone numbers (optional)
      inputProps={{
        pattern: "^(\\+?1[\\-\\s]?)?\\(?[0-9]{3}\\)?[\\-\\s]?[0-9]{3}[\\-\\s]?[0-9]{4}$",
        title: "Please enter a valid phone number: (416) 555-1234 or +1-416-555-1234",
        ...props.inputProps
      }}
    />
  );
};

export default SimplePhoneInput;