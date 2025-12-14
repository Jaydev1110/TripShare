# TripShare Backend

FastAPI backend for the TripShare application, configured with Supabase integration.

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy the `.env.example` file to `.env` and fill in your Supabase credentials:

```bash
cp .env.example .env
```

Update `.env` with your actual Supabase credentials:
```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
```

### 3. Run the Server

Start the development server:

```bash
uvicorn app.main:app --reload
```

The server will run on `http://localhost:8000` by default.

## API Endpoints

- `GET /` - Root endpoint returning project information
- `GET /ping` - Health check endpoint

## Deployment on Render

This backend is configured for deployment on Render:

1. Set environment variables in Render dashboard:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`

2. Build command:
   ```bash
   pip install -r requirements.txt
   ```

3. Start command:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── routes/              # API route handlers
│   │   └── ping.py         # Test/health check endpoint
│   ├── database/            # Database configuration
│   │   └── supabase_client.py  # Supabase client setup
│   ├── utils/               # Utility functions
│   ├── models/              # Data models
│   └── __init__.py
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
└── README.md               # This file
```

## Group Lifecycle & Expiry (Phase 4)

TripShare implements time-limited groups. Groups have an `expires_at` timestamp.

### Automatic Expiry
- Groups expire automatically after the configured duration (default 7 days).
- **Expired Groups**:
    - Cannot accept new members (`POST /groups/join` returns 410).
    - Cannot accept photo uploads (`POST /photos/upload` returns 403).
    - Cannot generate signed URLs for downloads.

### Extension
- **Owners** can extend a group using:
  `POST /groups/{group_id}/extend`
  Body: `{"extend_days": 3}`

### Automation Scripts (`backend/scripts/`)
These scripts should be scheduled (e.g., via cron or GitHub Actions).

1.  **`send_expiry_warnings.py`**
    - Checks for groups expiring in the next 24 hours.
    - Adds an entry to `group_warnings` table (setup via `supabase/migrations/20251214_group_warnings.sql`).
    - *Note: Does not send actual emails yet (Backend logic only).*

2.  **`cleanup_expired_groups.py`**
    - Permanently deletes groups that have passed their `expires_at` time.
    - Deletes all associated photos from Supabase Storage.
    - Deletes database records (Group, Members, Photos, Warnings).
    - **Danger:** This is destructive and irreversible.
