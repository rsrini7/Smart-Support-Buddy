import React, { useState, useMemo } from 'react';
import { Routes, Route } from 'react-router-dom';
import { Box, Container } from '@mui/material';
import { ThemeProvider, createTheme } from '@mui/material/styles';
// Import components
import Header from './components/Header';
import Footer from './components/Footer';

// Import pages
import HomePage from './pages/HomePage';
import SearchPage from './pages/SearchPage';
import IssueDetailsPage from './pages/IssueDetailsPage';
import IngestMsgFilesPage from './pages/IngestMsgFilesPage';
import ConfluenceIngestPage from './pages/ConfluenceIngestPage';
import StackOverflowIngestPage from './pages/StackOverflowIngestPage';
import JiraIngestPage from './pages/JiraIngestPage';
import ClearChromaPage from './pages/ClearChromaPage';
import ConfigPage from './pages/ConfigPage';

function App() {
  const [mode, setMode] = useState('light');

  const toggleTheme = () => {
    setMode((prev) => (prev === 'light' ? 'dark' : 'light'));
  };

  const theme = useMemo(
    () =>
      createTheme({
        palette: {
          mode,
          ...(mode === 'light'
            ? {
                // custom light palette
                primary: { main: '#2575fc' },
                secondary: { main: '#6a11cb' },
                background: { default: '#f5f7fa', paper: '#fff' },
              }
            : {
                // custom dark palette
                primary: { main: '#90caf9' },
                secondary: { main: '#ce93d8' },
                background: { default: '#181a1b', paper: '#23272a' },
              }),
        },
      }),
    [mode]
  );

  return (
    <ThemeProvider theme={theme}>
      <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', bgcolor: 'background.default' }}>
        <Header mode={mode} toggleTheme={toggleTheme} />
        <Container component="main" sx={{ flexGrow: 1, py: 4 }}>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/search" element={<SearchPage />} />
            <Route path="/issues/:issueId" element={<IssueDetailsPage />} />
            <Route path="/ingest-msg-files" element={<IngestMsgFilesPage />} />
            <Route path="/ingest-confluence" element={<ConfluenceIngestPage />} />
            <Route path="/ingest-stackoverflow" element={<StackOverflowIngestPage />} />
            <Route path="/ingest-jira" element={<JiraIngestPage />} />
            <Route path="/clear-chroma" element={<ClearChromaPage />} />
            <Route path="/config" element={<ConfigPage />} />
          </Routes>
        </Container>
        <Footer />
      </Box>
    </ThemeProvider>
  );
}

export default App;