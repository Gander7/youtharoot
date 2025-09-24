# Railway Deployment Instructions

## Updated Railway Process (2024+)

Railway has simplified their deployment process. Here's the current workflow:

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Add configurable database support"
   git push origin main
   ```

2. **Create Railway Project:**
   - Go to [railway.app](https://railway.app)
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your `youth-attendance` repository
   - Railway will automatically detect it's a Python app

3. **Add PostgreSQL Database:**
   - In your Railway project dashboard
   - Click "New Service" 
   - Select "Database"
   - Choose "PostgreSQL"
   - Railway creates the database and automatically connects it to your app

4. **Configure Environment Variables:**
   - Go to your app service (not the database)
   - Click on "Variables" tab
   - Add these environment variables:
   ```
   DATABASE_TYPE=postgresql
   DEBUG=false
   PORT=8000
   ```
   - `DATABASE_URL` is automatically provided by Railway when you add PostgreSQL

5. **Deploy:**
   - Railway automatically builds and deploys your app
   - Your API will be available at: `https://your-app-name.up.railway.app`
   - Check the deployment logs for any issues

## Alternative: Railway CLI (Advanced)

If you prefer command-line deployment:

1. **Install Railway CLI:**
   ```bash
   npm install -g @railway/cli
   ```

2. **Login and Deploy:**
   ```bash
   railway login
   railway link  # Link to existing project or create new
   railway up    # Deploy
   ```

## Frontend + Backend Deployment

### **Option 1: Separate Services (Recommended)**

**Backend on Railway:**
1. Follow the Railway steps above for the API
2. Note your Railway app URL: `https://your-app-name.up.railway.app`

**Frontend on Vercel:**
1. **Connect Vercel to GitHub:**
   - Go to [vercel.com](https://vercel.com)
   - Import your GitHub repository
   - Set the **Root Directory** to `web/`

2. **Environment Variables in Vercel:**
   ```
   PUBLIC_API_URL=https://your-app-name.up.railway.app
   ```

3. **Deploy:**
   - Vercel auto-deploys on every push
   - Your frontend will be at: `https://your-project.vercel.app`

### **Option 2: Railway Monorepo (Advanced)**

Deploy both frontend and backend on Railway using multiple services:

1. **Create Railway Project** (as above for backend)

2. **Add Frontend Service:**
   - In Railway dashboard: "New Service" → "GitHub Repo"
   - **Same repository** but set:
     - **Root Directory**: `web/`
     - **Build Command**: `npm run build`
     - **Start Command**: `npm run preview`

3. **Environment Variables:**
   - Backend service: `DATABASE_TYPE=postgresql`, `DEBUG=false`
   - Frontend service: `PUBLIC_API_URL=https://[backend-service].up.railway.app`

### **Option 3: Single Railway Service (Not Recommended)**

You could serve the frontend from FastAPI, but this adds complexity and isn't optimal for static sites.

## Local Development with PostgreSQL

If you want to test PostgreSQL locally:

1. **Install PostgreSQL:**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install postgresql postgresql-contrib
   
   # macOS
   brew install postgresql
   ```

2. **Create Database:**
   ```bash
   createdb youth_attendance_dev
   ```

3. **Set Environment Variables:**
   Create `.env` file:
   ```
   DATABASE_TYPE=postgresql
   DEV_DATABASE_URL=postgresql://username:password@localhost/youth_attendance_dev
   DEBUG=true
   ```

4. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run:**
   ```bash
   uvicorn app.main:app --reload
   ```

## Environment Variables Reference

### Development (In-Memory)
```
DATABASE_TYPE=memory
DEBUG=true
```

### Development (Local PostgreSQL)
```
DATABASE_TYPE=postgresql
DEV_DATABASE_URL=postgresql://user:pass@localhost/youth_attendance_dev
DEBUG=true
```

### Production (Railway)
```
DATABASE_TYPE=postgresql
DEBUG=false
# DATABASE_URL is automatically set by Railway
```