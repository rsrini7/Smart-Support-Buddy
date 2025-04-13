import React from 'react';
import { AppBar, Toolbar, Typography, Button, Box, Menu, MenuItem } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';

const Header = () => {
  const [anchorEl, setAnchorEl] = React.useState(null);

  const handleToolsClick = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };


  return (
    <AppBar position="static">
      <Toolbar>
        <Box
          sx={{ display: 'flex', alignItems: 'center', flexGrow: 1, textDecoration: 'none', color: 'white' }}
          component={RouterLink}
          to="/"
        >
          <img
            src={`${process.env.PUBLIC_URL}/logo192.png`}
            alt="Logo"
            style={{ height: 40, marginRight: 8 }}
          />
          <Typography variant="h6" component="div">
            Support Buddy
          </Typography>
        </Box>
        <Box>
          <Button color="inherit" component={RouterLink} to="/">
            Home
          </Button>
          <Button color="inherit" component={RouterLink} to="/search">
            Search
          </Button>
          <Button color="inherit" onClick={handleToolsClick}>
            Tools
          </Button>
          <Menu
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={handleClose}
          >
            <MenuItem component={RouterLink} to="/clear-chroma" onClick={handleClose}>
              Clear ChromaDB Collections
            </MenuItem>
          </Menu>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Header;