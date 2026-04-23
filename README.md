# Expense Tracker

A full-stack expense tracking application with a Django REST API backend and a React frontend. Features idempotent expense creation, real-time backend health monitoring, and a responsive mobile-friendly UI.

**Live Demo**: [Frontend URL] | **API**: [Backend URL]

## Backend (Django + DRF)

### Run locally

From `backend/`:

```bash
python manage.py migrate
python manage.py runserver
```

Run tests:

```bash
python manage.py test expenses
```

### API

`GET /expenses`
- Returns a list of expenses.
- Optional query params:
  - `category=<value>`
  - `sort=date_desc` (default newest first, `date_asc` also supported)

`POST /expenses`
- Creates a new expense from:
  - `amount`
  - `category`
  - `description`
  - `date`
- Requires `Idempotency-Key` request header.
- If the same `Idempotency-Key` is retried, the API returns the previously created expense instead of inserting a duplicate.

`GET /health`
- Health check endpoint for monitoring backend availability.
- Returns `200 OK` with `{"status": "healthy"}` if backend is operational.
- Returns `503 Service Unavailable` if database is unreachable.
- Frontend polls this every 30 seconds to display backend status.

### Data model

Expense fields:
- `id` (UUID)
- `amount` (`DecimalField`, 2 decimal places)
- `category`
- `description`
- `date`
- `created_at`
- `idempotency_key` (unique)

### Database

**Development**: SQLite (default)  
**Production**: PostgreSQL (via Render)

The application automatically detects the `DATABASE_URL` environment variable and uses PostgreSQL if available, otherwise falls back to SQLite for local development.

### Key Design Decisions

1. **Idempotent POST with unique constraint**: Uses `idempotency_key` field with unique database constraint to safely handle retries without duplicates. Simpler than distributed locking.

2. **Decimal for currency**: Stores amounts as `DecimalField` instead of float to avoid precision errors in financial calculations.

3. **Server-side filtering & sorting**: Category filter and date sort happen on the backend for consistency and to reduce data transfer.

4. **Health check endpoint**: Dedicated `/health` endpoint allows frontend to monitor backend availability without creating side effects, critical for handling inactivity periods on Render.

5. **Function-based DRF views**: Chose simpler function-based views over class-based views for clarity and minimal boilerplate.

6. **Environment-based database selection**: Automatically switches between SQLite (dev) and PostgreSQL (production) based on `DATABASE_URL` env var.

7. **WhiteNoise for static files**: Simplifies deployment by serving static files directly from the application without needing a separate CDN.

### Trade-offs Made (Timebox)

- **No authentication**: Focused on core expense tracking logic. Auth would require user model, JWT tokens, and frontend login flow.
- **No pagination**: Assumes reasonable dataset size. Large datasets would need cursor-based pagination for performance.
- **Limited error handling**: API returns basic error messages. Production would benefit from structured error codes and detailed logging.
- **No rate limiting**: Could add rate limiting per IP or user for production robustness.
- **Minimal test coverage**: Tests cover idempotency and filtering. Edge cases (concurrent requests, large amounts) not fully tested.

### Intentionally Not Implemented

- **User authentication & authorization**: Out of scope for this assignment.
- **Expense editing/deletion**: Only create and read operations implemented.
- **Recurring expenses**: Single-entry expenses only.
- **Multi-currency support**: Fixed to single currency (INR).
- **Advanced analytics**: No spending trends or category breakdowns.
- **Offline support**: No service worker or local caching.
- **Real-time updates**: No WebSocket support for live expense updates.

## Frontend (React + Vite)

### Run locally

From `frontend/`:

```bash
npm install
npm run dev
```

Build for production:

```bash
npm run build
```

### Features

- **Create expense form**: Add amount, category, description, and date.
- **Idempotent submission**: Automatically generates and reuses `Idempotency-Key` header to prevent duplicate submissions on retry/refresh.
- **Expense list**: View all expenses with date, category, description, and amount.
- **Category filter**: Filter expenses by category (all categories, or select one).
- **Date sort**: Sort by newest first (default) or oldest first.
- **Total calculation**: Shows total of currently visible expenses (after filters/sort).
- **Loading & error states**: User-friendly feedback for network issues and validation errors.
- **Responsive design**: Fully mobile-friendly with optimized layouts for phones, tablets, and desktops.
- **Backend health monitoring**: Real-time status indicator showing if backend is online/offline. Polls health endpoint every 30 seconds.

### Design

- Modern, clean UI with a professional color palette (sky blue accent).
- Smooth transitions and hover effects for better interactivity.
- Accessible form inputs with focus states and proper labels.
- Dark mode support via system preference.
- Mobile-first responsive design with breakpoints at 768px and 640px.
- Gradient header and styled cards with subtle shadows.
- Error and success states with color-coded feedback.

### API Integration

- Connects to Django backend at `http://127.0.0.1:8000` (configurable via `VITE_API_BASE_URL` env var).
- Handles retries gracefully with idempotency keys.
- Cancels in-flight requests when filters/sort change to avoid race conditions.
- CORS-enabled for cross-origin requests from frontend.
- Monitors backend health every 30 seconds and displays status in header.

## Deployment on Render

### Prerequisites

- GitHub account with this repository pushed
- Render account (https://render.com)
- PostgreSQL database (Render provides this)

### Step 1: Create PostgreSQL Database on Render

1. Go to https://dashboard.render.com
2. Click **New +** → **PostgreSQL**
3. Configure:
   - **Name**: `expense-tracker-db` (or your choice)
   - **Database**: `expense_tracker`
   - **User**: `postgres` (default)
   - **Region**: Choose closest to you
   - **PostgreSQL Version**: 15 (or latest)
4. Click **Create Database**
5. Copy the **Internal Database URL** (you'll need this for the backend)

### Step 2: Deploy Backend on Render

1. Go to https://dashboard.render.com
2. Click **New +** → **Web Service**
3. Connect your GitHub repository
4. Configure:
   - **Name**: `expense-tracker-api`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput`
   - **Start Command**: `gunicorn backend.wsgi:application`
   - **Instance Type**: Free (or Starter)
5. Click **Advanced** and add environment variables:
   ```
   SECRET_KEY=<generate-a-secure-key>
   DEBUG=False
   ALLOWED_HOSTS=<your-backend-url>.onrender.com
   DATABASE_URL=<paste-internal-database-url-from-step-1>
   CORS_ALLOWED_ORIGINS=https://<your-frontend-url>.onrender.com
   ```
6. Click **Create Web Service**
7. Wait for deployment (5-10 minutes)
8. Copy the backend URL (e.g., `https://expense-tracker-api.onrender.com`)

### Step 3: Deploy Frontend on Render

1. Go to https://dashboard.render.com
2. Click **New +** → **Static Site**
3. Connect your GitHub repository
4. Configure:
   - **Name**: `expense-tracker-web`
   - **Build Command**: `cd frontend && npm install && npm run build`
   - **Publish Directory**: `frontend/dist`
5. Click **Advanced** and add environment variables:
   ```
   VITE_API_BASE_URL=https://<your-backend-url>.onrender.com
   ```
6. Click **Create Static Site**
7. Wait for deployment (2-5 minutes)
8. Your frontend will be available at the provided URL

### Step 4: Update Backend CORS Settings

After frontend is deployed, update the backend environment variable:

1. Go to backend service in Render dashboard
2. Click **Environment**
3. Update `CORS_ALLOWED_ORIGINS` to include your frontend URL:
   ```
   https://<your-frontend-url>.onrender.com
   ```
4. Click **Save** (this will trigger a redeploy)

### Step 5: Verify Deployment

1. Visit your frontend URL
2. Check that the "Backend Online" status appears in the header
3. Try creating an expense
4. Verify it appears in the list
5. Test filtering and sorting

### Environment Variables Reference

**Backend (.env or Render dashboard)**:
- `SECRET_KEY`: Django secret key (generate with `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`)
- `DEBUG`: Set to `False` in production
- `ALLOWED_HOSTS`: Comma-separated list of allowed domains
- `DATABASE_URL`: PostgreSQL connection string (auto-provided by Render)
- `CORS_ALLOWED_ORIGINS`: Comma-separated list of frontend URLs

**Frontend (.env or Render dashboard)**:
- `VITE_API_BASE_URL`: Backend API URL (e.g., `https://expense-tracker-api.onrender.com`)

### Handling Inactivity on Render

Render's free tier spins down services after 15 minutes of inactivity. The application handles this gracefully:

- Frontend displays "Backend Offline" status when backend is unavailable
- Health check endpoint (`/health`) is polled every 30 seconds
- When backend wakes up, status automatically updates to "Online"
- Users can retry their actions once backend is available

### Troubleshooting

**Backend shows "Offline"**:
- Check that `CORS_ALLOWED_ORIGINS` includes your frontend URL
- Verify `DATABASE_URL` is set correctly in environment variables
- Check Render logs: Dashboard → Service → Logs

**Database migration fails**:
- Ensure `DATABASE_URL` is set before deployment
- Check that the database exists and is accessible
- Manually run migrations: `python manage.py migrate` in Render shell

**Frontend can't reach backend**:
- Verify `VITE_API_BASE_URL` matches your backend URL exactly
- Check browser console for CORS errors
- Ensure backend `CORS_ALLOWED_ORIGINS` includes frontend URL

### Local Development

To test locally before deploying:

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

# Frontend (in another terminal)
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5174` and set `VITE_API_BASE_URL=http://127.0.0.1:8000`