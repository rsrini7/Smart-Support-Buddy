#!/bin/bash

# Start a ChromaDB server using the YAML config file (config.yaml)
# For ChromaDB v0.4.x+, pass the config file as a positional argument, not with --config
exec chroma run ./chroma-config.yaml
