import React from 'react';
import { AppBar, Toolbar, Typography, Button, Box, Menu, MenuItem, IconButton, Tooltip } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import HomeIcon from '@mui/icons-material/Home';
import SearchIcon from '@mui/icons-material/Search';
import BuildIcon from '@mui/icons-material/Build';
import DeleteSweepIcon from '@mui/icons-material/DeleteSweep';
import SettingsIcon from '@mui/icons-material/Settings';
import Brightness7Icon from '@mui/icons-material/Brightness7';
import Brightness4Icon from '@mui/icons-material/Brightness4';

const Header = ({ mode, toggleTheme }) => {
  const [anchorEl, setAnchorEl] = React.useState(null);

  const handleToolsClick = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };


  return (
    <AppBar
      position="static"
      sx={{
        background: 'linear-gradient(90deg, #6a11cb 0%, #2575fc 100%)',
        boxShadow: '0 4px 18px 0 rgba(40, 80, 200, 0.15)'
      }}
      className="custom-appbar"
    >
      <Toolbar>
        <Box
          sx={{ display: 'flex', alignItems: 'center', flexGrow: 1, textDecoration: 'none', color: 'white' }}
          component={RouterLink}
          to="/"
        >
          <img
            src={`${process.env.PUBLIC_URL}/logo192.png`}
            alt="Logo"
            style={{ height: 40, marginRight: 8, borderRadius: 8, boxShadow: '0 2px 8px rgba(40,80,200,0.10)' }}
          />
          <Typography variant="h6" component="div" sx={{ fontWeight: 700, letterSpacing: '0.04em' }}>
            Support Buddy
          </Typography>
        </Box>
        <Box>
          <Button
            color="inherit"
            component={RouterLink}
            to="/"
            startIcon={<HomeIcon />}
            sx={{
              borderRadius: 2,
              mx: 0.5,
              px: 2,
              fontWeight: 600,
              textTransform: 'none',
              transition: 'background 0.2s, box-shadow 0.2s',
              '&:hover': {
                background: 'rgba(255,255,255,0.10)',
                boxShadow: '0 2px 8px rgba(40,80,200,0.10)'
              }
            }}
          >
            Home
          </Button>
          <Button
            color="inherit"
            component={RouterLink}
            to="/search"
            startIcon={<SearchIcon />}
            sx={{
              borderRadius: 2,
              mx: 0.5,
              px: 2,
              fontWeight: 600,
              textTransform: 'none',
              transition: 'background 0.2s, box-shadow 0.2s',
              '&:hover': {
                background: 'rgba(255,255,255,0.10)',
                boxShadow: '0 2px 8px rgba(40,80,200,0.10)'
              }
            }}
          >
            Search
          </Button>
          <Button
            color="inherit"
            onClick={handleToolsClick}
            startIcon={<BuildIcon />}
            sx={{
              borderRadius: 2,
              mx: 0.5,
              px: 2,
              fontWeight: 600,
              textTransform: 'none',
              transition: 'background 0.2s, box-shadow 0.2s',
              '&:hover': {
                background: 'rgba(255,255,255,0.10)',
                boxShadow: '0 2px 8px rgba(40,80,200,0.10)'
              }
            }}
          >
            Tools
          </Button>
          <Menu
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={handleClose}
            PaperProps={{
              sx: (theme) => ({
                borderRadius: 2,
                minWidth: 220,
                boxShadow: theme.shadows[8],
                backgroundColor: theme.palette.background.paper,
                color: theme.palette.text.primary,
                border: `1px solid ${theme.palette.divider}`,
                backdropFilter: 'blur(8px)'
              })
            }}
            MenuListProps={{
              sx: {
                py: 1
              }
            }}
          >
            <MenuItem
              component={RouterLink}
              to="/clear-chroma"
              onClick={handleClose}
              sx={{
                borderRadius: 1.5,
                fontWeight: 500,
                gap: 1,
                px: 2,
                my: 0.5,
                transition: 'background 0.2s',
                '&:hover': {
                  background: 'linear-gradient(90deg, #6a11cb22 0%, #2575fc22 100%)'
                }
              }}
              startIcon={<DeleteSweepIcon sx={{ color: '#6a11cb' }} />}
            >
              Clear ChromaDB Collections
            </MenuItem>
            <MenuItem
              component={RouterLink}
              to="/config"
              onClick={handleClose}
              sx={{
                borderRadius: 1.5,
                fontWeight: 500,
                gap: 1,
                px: 2,
                my: 0.5,
                transition: 'background 0.2s',
                '&:hover': {
                  background: 'linear-gradient(90deg, #6a11cb22 0%, #2575fc22 100%)'
                }
              }}
              startIcon={<SettingsIcon sx={{ color: '#2575fc' }} />}
            >
              Config
            </MenuItem>
          </Menu>
        </Box>
        <Box sx={{ ml: 2 }}>
          <Tooltip title={mode === 'light' ? 'Switch to dark mode' : 'Switch to light mode'}>
            <IconButton color="inherit" onClick={toggleTheme} size="large">
              {mode === 'light' ? <Brightness4Icon /> : <Brightness7Icon />}
            </IconButton>
          </Tooltip>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Header;