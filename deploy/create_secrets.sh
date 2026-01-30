#!/bin/bash
# Script to create docker secrets for Base_Costos (Swarm mode)
# Edit values below or pass via env when calling.

: ${SECRET_KEY_VALUE:="change-me-super-secret"}
: ${DB_PASSWORD_VALUE:="change-me-db-pass"}

set -euo pipefail

echo "Creating docker secrets (will fail if secret already exists)"

echo "$SECRET_KEY_VALUE" | docker secret create base_costos_secret_key - || echo "Secret base_costos_secret_key may already exist"
echo "$DB_PASSWORD_VALUE" | docker secret create base_costos_db_password - || echo "Secret base_costos_db_password may already exist"

echo "Done. Verify with: docker secret ls" 
