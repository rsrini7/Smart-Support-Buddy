import React, { useEffect, useState } from "react";
import { Box, Typography, TextField, Button, Alert, Paper } from "@mui/material";

const API_URL = "/api/config/similarity-threshold";
const LLM_API_URL = "/api/config/llm-top-results-count";

const ConfigPage = () => {
  const [threshold, setThreshold] = useState("");
  const [llmCount, setLlmCount] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    setLoading(true);
    Promise.all([
      fetch(API_URL)
        .then((res) => {
          if (!res.ok) throw new Error("Failed to fetch");
          return res.json();
        })
        .then((data) => setThreshold(data.similarity_threshold?.toString() ?? "")),
      fetch(LLM_API_URL)
        .then((res) => {
          if (!res.ok) throw new Error("Failed to fetch");
          return res.json();
        })
        .then((data) => setLlmCount(data.llm_top_results_count?.toString() ?? ""))
    ])
      .catch(() => {
        setError("Failed to load config values.");
      })
      .finally(() => setLoading(false));
  }, []);

  const handleChange = (e) => {
    setThreshold(e.target.value);
    setError("");
    setSuccess("");
  };

  const handleLlmChange = (e) => {
    setLlmCount(e.target.value);
    setError("");
    setSuccess("");
  };

  const handleUnifiedSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError("");
    setSuccess("");
    // Validate both fields
    const simValue = parseFloat(threshold);
    const llmValue = parseInt(llmCount, 10);
    if (isNaN(simValue) || simValue <= 0 || simValue >= 1) {
      setError("Please enter a value between 0 and 1 (exclusive) for Similarity Threshold.");
      setSaving(false);
      return;
    }
    if (isNaN(llmValue) || llmValue < 1 || llmValue > 20) {
      setError("Please enter a value between 1 and 20 for LLM Top Results Count.");
      setSaving(false);
      return;
    }
    try {
      // Save both in parallel, but only show one success message
      const [simRes, llmRes] = await Promise.all([
        fetch(API_URL, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ similarity_threshold: simValue }),
        }),
        fetch(LLM_API_URL, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ llm_top_results_count: llmValue }),
        })
      ]);
      if (!simRes.ok || !llmRes.ok) {
        const simData = await simRes.json().catch(() => ({}));
        const llmData = await llmRes.json().catch(() => ({}));
        throw new Error(simData.detail || llmData.detail || "Failed to save");
      }
      setSuccess("Configuration updated successfully.");
    } catch (err) {
      setError(err.message || "Failed to save.");
    }
    setSaving(false);
  };

  return (
    <Box maxWidth={500} mx="auto" mt={4}>
      <Paper elevation={3} sx={{ p: 3 }}>
        <Button variant="outlined" onClick={() => window.history.back()} sx={{ mb: 2 }}>
          Back
        </Button>
        <Typography variant="h5" gutterBottom>
          Config
        </Typography>
        <Typography variant="body1" gutterBottom>
          Set the similarity threshold for search results. Default is used if not set. Value must be between 0 and 1 (exclusive).
        </Typography>
        <Typography variant="body1" gutterBottom>
          Set how many top search results are passed to the LLM for summary generation (1-20).
        </Typography>
        <form onSubmit={handleUnifiedSave}>
          <TextField
            label="Similarity Threshold"
            type="number"
            inputProps={{ step: 0.01, min: 0, max: 1 }}
            value={threshold}
            onChange={handleChange}
            fullWidth
            required
            disabled={loading || saving}
            sx={{ mb: 2 }}
          />
          <TextField
            label="LLM Top Results Count"
            type="number"
            inputProps={{ step: 1, min: 1, max: 20 }}
            value={llmCount}
            onChange={handleLlmChange}
            fullWidth
            required
            disabled={loading || saving}
            sx={{ mb: 2 }}
          />
          <Button
            type="submit"
            variant="contained"
            color="primary"
            disabled={loading || saving}
            sx={{ mb: 2 }}
          >
            {saving ? "Saving..." : "Save"}
          </Button>
        </form>
        {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
        {success && <Alert severity="success" sx={{ mt: 2 }}>{success}</Alert>}
      </Paper>
    </Box>
  );
};

export default ConfigPage;