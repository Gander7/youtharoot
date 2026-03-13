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
  const [userButtonKey, setUserButtonKey] = useState(0);

  useEffect(() => {
    const refresh = () => {
      setCurrentPath(window.location.pathname);
      setUserButtonKey(k => k + 1);
    };
    document.addEventListener('astro:after-swap', refresh);
    return () => document.removeEventListener('astro:after-swap', refresh);
  }, []);

  return (
    <ThemeProvider theme={darkTheme}>
      <Navigation currentPath={currentPath} userButtonKey={userButtonKey} />
    </ThemeProvider>
  );
}
