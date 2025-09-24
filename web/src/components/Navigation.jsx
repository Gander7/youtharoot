import React from 'react';
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
  Home as HomeIcon
} from '@mui/icons-material';

export default function Navigation() {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const [value, setValue] = React.useState(0);

  // Get current page from URL
  const currentPath = typeof window !== 'undefined' ? window.location.pathname : '/';
  
  React.useEffect(() => {
    if (currentPath.includes('/Events')) setValue(1);
    else if (currentPath.includes('/People')) setValue(2);
    else setValue(0);
  }, [currentPath]);

  const navigate = (path) => {
    if (typeof window !== 'undefined') {
      window.location.href = path;
    }
  };

  if (isMobile) {
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
        <BottomNavigation
          value={value}
          onChange={(event, newValue) => {
            setValue(newValue);
            const paths = ['/', '/Events', '/People'];
            navigate(paths[newValue]);
          }}
          showLabels
        >
          <BottomNavigationAction 
            label="Home" 
            icon={<HomeIcon />} 
          />
          <BottomNavigationAction 
            label="Events" 
            icon={<EventIcon />} 
          />
          <BottomNavigationAction 
            label="People" 
            icon={<PeopleIcon />} 
          />
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
            Youth Attendance
          </Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button 
              color="inherit" 
              onClick={() => navigate('/')}
              variant={currentPath === '/' ? 'contained' : 'text'}
              sx={{ borderRadius: 2 }}
            >
              Home
            </Button>
            <Button 
              color="inherit" 
              onClick={() => navigate('/Events')}
              variant={currentPath.includes('/Events') ? 'contained' : 'text'}
              sx={{ borderRadius: 2 }}
            >
              Events
            </Button>
            <Button 
              color="inherit" 
              onClick={() => navigate('/People')}
              variant={currentPath.includes('/People') ? 'contained' : 'text'}
              sx={{ borderRadius: 2 }}
            >
              People
            </Button>
          </Box>
        </Toolbar>
      </Container>
    </AppBar>
  );
}