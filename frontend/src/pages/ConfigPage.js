import React, { useEffect, useState } from "react";
import { Box, Typography, TextField, Button, Alert, Paper } from "@mui/material";

const API_URL = "/api/config/similarity-threshold";

const ConfigPage = () => {
  const [threshold, setThreshold] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    setLoading(true);
    fetch(API_URL)
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch");
        return res.json();
      })
      .then((data) => {
        setThreshold(data.similarity_threshold?.toString() ?? "");
        setLoading(false);
      })
      .catch(() => {
        setError("Failed to load current threshold.");
        setLoading(false);
      });
  }, []);

  const handleChange = (e) => {
    setThreshold(e.target.value);
    setError("");
    setSuccess("");
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError("");
    setSuccess("");
    const value = parseFloat(threshold);
    if (isNaN(value) || value <= 0 || value >= 1) {
      setError("Please enter a value between 0 and 1 (exclusive).");
      setSaving(false);
      return;
    }
    try {
      const res = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ similarity_threshold: value }),
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Failed to save");
      }
      setSuccess("Threshold updated successfully.");
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
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}
        <form onSubmit={handleSave}>
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
          <Button
            type="submit"
            variant="contained"
            color="primary"
            disabled={loading || saving}
          >
            {saving ? "Saving..." : "Save"}
          </Button>
        </form>
      </Paper>
    </Box>
  );
};

export default ConfigPage;