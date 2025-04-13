import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Box, Container } from '@mui/material';

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

function App() {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <Header />
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
          </Routes>
      </Container>
      <Footer />
    </Box>
  );
}

export default App;