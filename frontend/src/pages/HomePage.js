import React from 'react';
import { Typography, Box, Paper, Grid, Button, Card, CardContent, CardActions } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import SearchIcon from '@mui/icons-material/Search';
import MailIcon from '@mui/icons-material/Mail';
import BugReportIcon from '@mui/icons-material/BugReport';
import LibraryBooksIcon from '@mui/icons-material/LibraryBooks';
import CodeIcon from '@mui/icons-material/Code';

const HomePage = () => {
  return (
    <Box>
      <Paper sx={{ p: 4, mb: 4, backgroundColor: 'primary.light', color: 'white' }}>
        <Typography variant="h4" gutterBottom>
          Support Buddy
        </Typography>
        <Typography variant="subtitle1">
          Easily manage, search, and analyze support issues / queries using below features
        </Typography>
        <Box sx={{ mt: 3, display: 'flex', justifyContent: 'center', gap: 3 }}>
          <Button
            variant="contained"
            color="secondary"
            size="large"
            component={RouterLink}
            to="/ingest-msg-files"
            startIcon={<MailIcon />}
            className="search-issues-btn"
          >
            Ingest MSG
          </Button>
          <Button
            variant="contained"
            color="secondary"
            size="large"
            component={RouterLink}
            to="/ingest-jira"
            startIcon={<BugReportIcon />}
            className="search-issues-btn"
          >
            Ingest Jira
          </Button>
          <Button
            variant="contained"
            color="secondary"
            size="large"
            component={RouterLink}
            to="/ingest-confluence"
            startIcon={<LibraryBooksIcon />}
            className="search-issues-btn"
          >
            Ingest Confluence
          </Button>
          <Button
            variant="contained"
            color="secondary"
            size="large"
            component={RouterLink}
            to="/ingest-stackoverflow"
            startIcon={<CodeIcon />}
            className="search-issues-btn"
          >
            Ingest Stack Overflow
          </Button>
          <Button
            variant="contained"
            color="secondary"
            size="large"
            component={RouterLink}
            to="/search"
            startIcon={<SearchIcon />}
            className="search-issues-btn"
          >
            Search Issues
          </Button>
        </Box>
      </Paper>

      <Typography variant="h5" gutterBottom>
        Features
      </Typography>
      
      <Grid container spacing={3} alignItems="stretch">
        <Grid item xs={12} md={4}>
          <Card
            className="feature-card"
            sx={{
              background: (theme) =>
                theme.palette.mode === 'dark'
                  ? 'linear-gradient(135deg, #23272a 0%, #181a1b 100%)'
                  : 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
              color: (theme) => theme.palette.text.primary,
              transition: 'background 0.3s, color 0.3s',
              '&:hover, &:focus-within': {
                background: (theme) =>
                  theme.palette.mode === 'dark'
                    ? 'linear-gradient(135deg, #181a1b 0%, #23272a 100%)'
                    : 'linear-gradient(135deg, #e0eafc 0%, #cfdef3 100%)',
                color: (theme) => theme.palette.text.primary,
              },
            }}
          >
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <MailIcon sx={{ fontSize: 28 }} />
                MSG File Ingest
              </Typography>
              <Typography variant="body2">
                Ingest Microsoft Outlook MSG files and parse them to extract RCA details and save them into the vector database.
              </Typography>
            </CardContent>
            <CardActions>
              <Button
                size="large"
                component={RouterLink}
                to="/ingest-msg-files"
                className="search-issues-btn"
                startIcon={<MailIcon />}
              >
                Try It
              </Button>
            </CardActions>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card
            className="feature-card"
            sx={{
              background: (theme) =>
                theme.palette.mode === 'dark'
                  ? 'linear-gradient(135deg, #23272a 0%, #181a1b 100%)'
                  : 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
              color: (theme) => theme.palette.text.primary,
              transition: 'background 0.3s, color 0.3s',
              '&:hover, &:focus-within': {
                background: (theme) =>
                  theme.palette.mode === 'dark'
                    ? 'linear-gradient(135deg, #181a1b 0%, #23272a 100%)'
                    : 'linear-gradient(135deg, #e0eafc 0%, #cfdef3 100%)',
                color: (theme) => theme.palette.text.primary,
              },
            }}
          >
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <BugReportIcon sx={{ fontSize: 28 }} />
                Jira Details Ingest
              </Typography>
              <Typography variant="body2">
                Ingest Jira ticket details into the vector database by providing either the Jira ID or Jira URL to enable information correlation and resolution tracking.
              </Typography>
            </CardContent>
            <CardActions>
              <Button
                size="large"
                component={RouterLink}
                to="/ingest-jira"
                className="search-issues-btn"
                startIcon={<BugReportIcon />}
              >
                Try It
              </Button>
            </CardActions>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card
            className="feature-card"
            sx={{
              background: (theme) =>
                theme.palette.mode === 'dark'
                  ? 'linear-gradient(135deg, #23272a 0%, #181a1b 100%)'
                  : 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
              color: (theme) => theme.palette.text.primary,
              transition: 'background 0.3s, color 0.3s',
              '&:hover, &:focus-within': {
                background: (theme) =>
                  theme.palette.mode === 'dark'
                    ? 'linear-gradient(135deg, #181a1b 0%, #23272a 100%)'
                    : 'linear-gradient(135deg, #e0eafc 0%, #cfdef3 100%)',
                color: (theme) => theme.palette.text.primary,
              },
            }}
          >
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <SearchIcon sx={{ fontSize: 28 }} />
                Semantic Search
              </Typography>
              <Typography variant="body2">
                Find similar content from the msg file content, jira, confluence and stackoverflow using vector search to quickly identify solutions
              </Typography>
            </CardContent>
            <CardActions>
              <Button
                size="large"
                component={RouterLink}
                to="/search"
                className="search-issues-btn"
                startIcon={<SearchIcon />}
              >
                Try It
              </Button>
            </CardActions>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card
            className="feature-card"
            sx={{
              background: (theme) =>
                theme.palette.mode === 'dark'
                  ? 'linear-gradient(135deg, #23272a 0%, #181a1b 100%)'
                  : 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
              color: (theme) => theme.palette.text.primary,
              transition: 'background 0.3s, color 0.3s',
              '&:hover, &:focus-within': {
                background: (theme) =>
                  theme.palette.mode === 'dark'
                    ? 'linear-gradient(135deg, #181a1b 0%, #23272a 100%)'
                    : 'linear-gradient(135deg, #e0eafc 0%, #cfdef3 100%)',
                color: (theme) => theme.palette.text.primary,
              },
            }}
          >
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <LibraryBooksIcon sx={{ fontSize: 28 }} />
                Confluence Ingest
              </Typography>
              <Typography variant="body2">
                Ingest and analyze Confluence pages by providing a page URL. Integrate documentation and knowledge base content into the system for enhanced search and context.
              </Typography>
            </CardContent>
            <CardActions>
              <Button
                size="large"
                component={RouterLink}
                to="/ingest-confluence"
                className="search-issues-btn"
                startIcon={<LibraryBooksIcon />}
              >
                Try It
              </Button>
            </CardActions>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card
            className="feature-card"
            sx={{
              background: (theme) =>
                theme.palette.mode === 'dark'
                  ? 'linear-gradient(135deg, #23272a 0%, #181a1b 100%)'
                  : 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
              color: (theme) => theme.palette.text.primary,
              transition: 'background 0.3s, color 0.3s',
              '&:hover, &:focus-within': {
                background: (theme) =>
                  theme.palette.mode === 'dark'
                    ? 'linear-gradient(135deg, #181a1b 0%, #23272a 100%)'
                    : 'linear-gradient(135deg, #e0eafc 0%, #cfdef3 100%)',
                color: (theme) => theme.palette.text.primary,
              },
            }}
          >
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <CodeIcon sx={{ fontSize: 28 }} />
                Stack Overflow Ingest
              </Typography>
              <Typography variant="body2">
                Ingest and analyze Stack Overflow questions and answers by providing a question URL. Integrate community Q&amp;A into the system for enhanced search and context.
              </Typography>
            </CardContent>
            <CardActions>
              <Button
                size="large"
                component={RouterLink}
                to="/ingest-stackoverflow"
                className="search-issues-btn"
                startIcon={<CodeIcon />}
              >
                Try It
              </Button>
            </CardActions>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default HomePage;