# Railway Deployment Instructions

## Automatic Deployment (Recommended)

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Add configurable database support"
   git push origin main
   ```

2. **Connect to Railway:**
   - Go to [railway.app](https://railway.app)
   - Click "Start a New Project"
   - Choose "Deploy from GitHub repo"
   - Select your `youth-attendance` repository

3. **Add PostgreSQL Database:**
   - In Railway dashboard, click "Add Plugin"
   - Select "PostgreSQL"
   - Railway will automatically set `DATABASE_URL`

4. **Set Environment Variables:**
   ```
   DATABASE_TYPE=postgresql
   DEBUG=false
   ```

5. **Deploy:**
   - Railway will automatically deploy
   - Your API will be available at: `https://yourapp.railway.app`

## Frontend Deployment (Separate)

Deploy the frontend to Vercel/Netlify:

1. **Vercel (Recommended):**
   - Connect your GitHub repo
   - Set build directory to `web/`
   - Set build command: `npm run build`
   - Update API calls to use your Railway backend URL

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