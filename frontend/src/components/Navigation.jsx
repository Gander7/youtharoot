import React from 'react';
import { UserButton } from '@clerk/astro/react';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  Container,
  useMediaQuery,
  useTheme,
  BottomNavigation,
  BottomNavigationAction,
  Paper
} from '@mui/material';
import {
  Event as EventIcon,
  People as PeopleIcon,
  Home as HomeIcon,
  Message as MessageIcon
} from '@mui/icons-material';

export default function Navigation({ currentPath: currentPathProp = null, userButtonKey = 0 }) {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const [value, setValue] = React.useState(0);
  const [currentPath, setCurrentPath] = React.useState(currentPathProp ?? (typeof window !== 'undefined' ? window.location.pathname : '/'));

  React.useEffect(() => {
    if (currentPathProp !== null) setCurrentPath(currentPathProp);
  }, [currentPathProp]);

  React.useEffect(() => {
    if (currentPath.includes('/Events')) setValue(1);
    else if (currentPath.includes('/People')) setValue(2);
    else if (currentPath.includes('/Messaging')) setValue(3);
    else setValue(0);
  }, [currentPath]);

  if (isMobile) {
    const paths = ['/', '/Events', '/People', '/Messaging'];
    return (
      <Paper
        sx={{
          position: 'fixed',
          bottom: 0,
          left: 0,
          right: 0,
          zIndex: 1000,
          bgcolor: 'background.paper',
          borderTop: 1,
          borderColor: 'divider'
        }}
        elevation={3}
      >
        <BottomNavigation value={value} showLabels>
          <BottomNavigationAction component="a" href="/" label="Home" icon={<HomeIcon />} />
          <BottomNavigationAction component="a" href="/Events" label="Events" icon={<EventIcon />} />
          <BottomNavigationAction component="a" href="/People" label="People" icon={<PeopleIcon />} />
          <BottomNavigationAction component="a" href="/Messaging" label="Messages" icon={<MessageIcon />} />
        </BottomNavigation>
      </Paper>
    );
  }

  return (
    <AppBar position="static" sx={{ bgcolor: 'background.paper', color: 'text.primary' }}>
      <Container maxWidth="lg">
        <Toolbar>
          <Typography
            variant="h6"
            component="div"
            sx={{ flexGrow: 1, fontWeight: 'bold', color: 'primary.main' }}
          >
            Youtharoot
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            <Button
              component="a"
              href="/"
              color="inherit"
              variant={currentPath === '/' ? 'contained' : 'text'}
              sx={{ borderRadius: 2, minWidth: 100, px: 2 }}
            >
              Home
            </Button>
            <Button
              component="a"
              href="/Events"
              color="inherit"
              variant={currentPath.includes('/Events') ? 'contained' : 'text'}
              sx={{ borderRadius: 2, minWidth: 100, px: 2 }}
            >
              Events
            </Button>
            <Button
              component="a"
              href="/People"
              color="inherit"
              variant={currentPath.includes('/People') ? 'contained' : 'text'}
              sx={{ borderRadius: 2, minWidth: 100, px: 2 }}
            >
              People
            </Button>
            <Button
              component="a"
              href="/Messaging"
              color="inherit"
              variant={currentPath.includes('/Messaging') ? 'contained' : 'text'}
              sx={{ borderRadius: 2, minWidth: 100, px: 2 }}
            >
              Messages
            </Button>
            
            {/* Clerk User Button */}
            <Box sx={{ ml: 2 }} key={userButtonKey}>
              <UserButton />
            </Box>
          </Box>
        </Toolbar>
      </Container>
    </AppBar>
  );
}