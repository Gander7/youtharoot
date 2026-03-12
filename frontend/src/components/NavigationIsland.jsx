import React from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import Navigation from './Navigation.jsx';

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
  },
});

export default function NavigationIsland() {
  return (
    <ThemeProvider theme={darkTheme}>
      <Navigation />
    </ThemeProvider>
  );
}
