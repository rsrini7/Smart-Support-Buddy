# Windows PowerShell script to start ChromaDB server using only the YAML config file (now named config.yaml)
# Usage: .\start_chromadb.ps1

chroma run .\chroma-config.yaml
