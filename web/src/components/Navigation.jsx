import React from 'react';
import { useStore } from '@nanostores/react';
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
  Paper,
  IconButton,
  Menu,
  MenuItem
} from '@mui/material';
import {
  Event as EventIcon,
  People as PeopleIcon,
  Home as HomeIcon,
  AccountCircle,
  Logout
} from '@mui/icons-material';
import { authStore, logout } from '../stores/auth';

export default function Navigation() {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const [value, setValue] = React.useState(0);
  const [currentPath, setCurrentPath] = React.useState('/');
  const [anchorEl, setAnchorEl] = React.useState(null);
  
  const auth = useStore(authStore);
  
  React.useEffect(() => {
    // Update current path on client side only
    if (typeof window !== 'undefined') {
      setCurrentPath(window.location.pathname);
    }
  }, []);

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

  const handleMenu = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    logout();
    handleClose();
    navigate('/login');
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
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
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
            
            {/* User Menu */}
            <Box sx={{ ml: 2 }}>
              <IconButton
                size="large"
                aria-label="account of current user"
                aria-controls="menu-appbar"
                aria-haspopup="true"
                onClick={handleMenu}
                color="inherit"
              >
                <AccountCircle />
              </IconButton>
              <Menu
                id="menu-appbar"
                anchorEl={anchorEl}
                anchorOrigin={{
                  vertical: 'top',
                  horizontal: 'right',
                }}
                keepMounted
                transformOrigin={{
                  vertical: 'top',
                  horizontal: 'right',
                }}
                open={Boolean(anchorEl)}
                onClose={handleClose}
              >
                <MenuItem disabled>
                  {auth.user?.username} ({auth.user?.role})
                </MenuItem>
                <MenuItem onClick={handleLogout}>
                  <Logout sx={{ mr: 1 }} />
                  Logout
                </MenuItem>
              </Menu>
            </Box>
          </Box>
        </Toolbar>
      </Container>
    </AppBar>
  );
}