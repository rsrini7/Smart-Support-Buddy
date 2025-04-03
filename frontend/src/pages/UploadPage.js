import React, { useState, useEffect } from 'react';
import { 
  Typography, 
  Box, 
  Paper, 
  Button, 
  TextField, 
  CircularProgress, 
  Alert, 
  Stepper, 
  Step, 
  StepLabel,
  Card,
  CardContent
} from '@mui/material';
import { useNavigate, useLocation } from 'react-router-dom';

const UploadPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [activeStep, setActiveStep] = useState(0);
  const [file, setFile] = useState(null);
  const [jiraTicketId, setJiraTicketId] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  
  // Check for tab parameter in URL to determine initial step
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const tab = params.get('tab');
    
    if (tab === 'jira') {
      // If coming from Jira integration link, go directly to Jira ticket step
      setActiveStep(1);
    }
  }, [location]);

  const steps = ['Select MSG File (Optional)', 'Enter Jira Ticket ID (Optional)', 'Upload & Process'];

  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];
    if (selectedFile && selectedFile.name.endsWith('.msg')) {
      setFile(selectedFile);
      setError('');
    } else {
      setFile(null);
      setError('Please select a valid MSG file');
    }
  };

  const handleJiraTicketChange = (event) => {
    setJiraTicketId(event.target.value);
  };

  const handleNext = () => {
    // Allow proceeding without a file since Jira ticket ID alone is valid
    setActiveStep((prevStep) => prevStep + 1);
  };

  const handleBack = () => {
    setActiveStep((prevStep) => prevStep - 1);
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError('');
    
    // Validate that at least one of file or jiraTicketId is provided
    if (!file && !jiraTicketId) {
      setError('Please provide either an MSG file or a Jira ticket ID');
      setLoading(false);
      return;
    }
    
    try {
      const formData = new FormData();
      if (file) {
        formData.append('file', file);
      }
      
      if (jiraTicketId) {
        formData.append('jira_ticket_id', jiraTicketId);
      }
      
      const response = await fetch('http://localhost:9000/api/upload-msg', {
        method: 'POST',
        body: formData,
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to upload file');
      }
      
      setSuccess(true);
      setUploadResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleViewIssue = () => {
    if (uploadResult && uploadResult.issue_id) {
      navigate(`/issues/${uploadResult.issue_id}`);
    }
  };

  const renderStepContent = (step) => {
    switch (step) {
      case 0:
        return (
          <Box sx={{ mt: 3 }}>
            <Typography variant="body1" gutterBottom>
              Select a Microsoft Outlook MSG file containing production issue details or proceed to enter a Jira ticket ID. You can provide either one or both.
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              At least one of MSG file or Jira ticket ID is required to proceed.
            </Typography>
            <Button
              variant="contained"
              component="label"
              sx={{ mt: 2 }}
            >
              Select MSG File
              <input
                type="file"
                accept=".msg"
                hidden
                onChange={handleFileChange}
              />
            </Button>
            {file && (
              <Typography variant="body2" sx={{ mt: 2 }}>
                Selected file: {file.name}
              </Typography>
            )}
          </Box>
        );
      case 1:
        return (
          <Box sx={{ mt: 3 }}>
            <Typography variant="body1" gutterBottom>
              Optionally link this issue to a Jira ticket for better tracking.
            </Typography>
            <TextField
              fullWidth
              label="Jira Ticket ID"
              variant="outlined"
              value={jiraTicketId}
              onChange={handleJiraTicketChange}
              placeholder="e.g., PROD-123"
              sx={{ mt: 2 }}
            />
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Leave blank if you don't want to link to a Jira ticket.
            </Typography>
          </Box>
        );
      case 2:
        return (
          <Box sx={{ mt: 3 }}>
            <Typography variant="body1" gutterBottom>
              Review your information and upload the file.
            </Typography>
            <Card variant="outlined" sx={{ mt: 2, mb: 3 }}>
              <CardContent>
                <Typography variant="body2">
                  <strong>File:</strong> {file ? file.name : 'No file selected'}
                </Typography>
                <Typography variant="body2">
                  <strong>Jira Ticket:</strong> {jiraTicketId || 'None'}
                </Typography>
              </CardContent>
            </Card>
            {!loading && !success && (
              <Button
                variant="contained"
                color="primary"
                onClick={handleSubmit}
                disabled={!file && !jiraTicketId}
              >
                Upload and Process
              </Button>
            )}
            {loading && <CircularProgress />}
            {success && (
              <Box>
                <Alert severity="success" sx={{ mb: 2 }}>
                  File uploaded and processed successfully!
                </Alert>
                <Button
                  variant="contained"
                  color="primary"
                  onClick={handleViewIssue}
                >
                  View Issue Details
                </Button>
              </Box>
            )}
          </Box>
        );
      default:
        return null;
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Upload Production Issue
      </Typography>
      <Paper sx={{ p: 3, mb: 4 }}>
        <Stepper activeStep={activeStep}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>
        
        {error && (
          <Alert severity="error" sx={{ mt: 3 }}>
            {error}
          </Alert>
        )}
        
        {renderStepContent(activeStep)}
        
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
          <Button
            disabled={activeStep === 0 || loading || success}
            onClick={handleBack}
          >
            Back
          </Button>
          <Button
            variant="contained"
            onClick={handleNext}
            disabled={activeStep === steps.length - 1 || loading || success}
          >
            Next
          </Button>
        </Box>
      </Paper>
    </Box>
  );
};

export default UploadPage;