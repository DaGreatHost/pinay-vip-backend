# Pinay VIP Backend

This is a simple Flask backend for managing access codes for the Pinay VIP app.
Deploy-ready on Railway with Gunicorn.

## Endpoints

- `POST /generate_code` - Generate a new 6-digit access code
- `GET /access_codes.json` - View all stored codes
- `POST /verify_code` - Mark a code as used
