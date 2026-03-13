import { useState, useEffect } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import Navigation from './Navigation.jsx';

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
  },
});

export default function NavigationIsland() {
  const [currentPath, setCurrentPath] = useState(
    typeof window !== 'undefined' ? window.location.pathname : '/'
  );

  useEffect(() => {
    const refresh = () => setCurrentPath(window.location.pathname);
    document.addEventListener('astro:after-swap', refresh);
    return () => document.removeEventListener('astro:after-swap', refresh);
  }, []);

  return (
    <ThemeProvider theme={darkTheme}>
      <Navigation currentPath={currentPath} />
    </ThemeProvider>
  );
}
