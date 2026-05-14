#!/bin/bash
set -e

source env/.env.local

AUDIENCE="$ENTRA_APP_CLIENT_ID"
ISSUER="https://login.microsoftonline.com/$ENTRA_APP_TENANT_ID/v2.0"

for file in .devproxy/dishes-api.json .devproxy/orders-api.json; do
  sed -i '' "s|\"audience\": \".*\"|\"audience\": \"$AUDIENCE\"|" "$file"
  sed -i '' "s|\"issuer\": \".*\"|\"issuer\": \"$ISSUER\"|" "$file"
done
