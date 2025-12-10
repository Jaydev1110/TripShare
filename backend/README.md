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

