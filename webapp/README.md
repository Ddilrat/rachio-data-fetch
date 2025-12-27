# Azure Web App - Python 3.14

A basic Flask web application configured for deployment on Azure Web Apps using Python 3.14 runtime stack.

## Project Structure

```
webapp/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── startup.txt           # Azure startup command
├── .env.example          # Environment variables template
├── templates/            # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── about.html
│   ├── 404.html
│   └── 500.html
└── static/              # Static files
    ├── css/
    │   └── style.css
    └── js/
        └── main.js
```

## Features

- Flask web framework
- Responsive design
- Health check endpoint (`/api/health`)
- Custom error pages (404, 500)
- Production-ready with Gunicorn
- Azure Web Apps optimized

## Local Development

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Run the application:
```bash
python app.py
```

Visit `http://localhost:8000` in your browser.

## Azure Deployment

### Prerequisites
- Azure account
- Azure CLI installed

### Deployment Steps

1. **Create Azure Web App**:
```bash
az webapp up --name your-app-name --resource-group your-resource-group --runtime "PYTHON:3.14" --sku B1
```

2. **Configure Startup Command** (in Azure Portal):
   - Go to Configuration > General Settings
   - Set Startup Command: `gunicorn --bind=0.0.0.0:8000 --timeout 600 app:app`

3. **Set Environment Variables** (in Azure Portal):
   - Go to Configuration > Application Settings
   - Add `SECRET_KEY` with a secure random value

4. **Deploy via Git**:
```bash
# Initialize git if not already done
git init
git add .
git commit -m "Initial commit"

# Add Azure remote
git remote add azure <deployment-git-url>

# Push to Azure
git push azure main
```

5. **Alternative: Deploy via ZIP**:
```bash
# Create ZIP file
zip -r webapp.zip .

# Deploy ZIP
az webapp deployment source config-zip --resource-group your-resource-group --name your-app-name --src webapp.zip
```

### Configuration Settings in Azure Portal

Go to Configuration > Application Settings and add:

- `SCM_DO_BUILD_DURING_DEPLOYMENT`: `true`
- `SECRET_KEY`: `your-secure-secret-key`

## API Endpoints

- `GET /` - Home page
- `GET /about` - About page
- `GET /api/health` - Health check endpoint (returns JSON)

## Testing

Test the health endpoint:
```bash
curl https://your-app-name.azurewebsites.net/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "message": "Application is running"
}
```

## Monitoring

- View logs: Azure Portal > App Service > Log stream
- Application Insights: Can be enabled in Azure Portal for detailed monitoring

## Troubleshooting

1. **Application doesn't start**:
   - Check startup command in Configuration
   - Review logs in Log stream

2. **Static files not loading**:
   - Verify static file paths in templates
   - Check build process completed successfully

3. **Import errors**:
   - Ensure all dependencies are in requirements.txt
   - Verify Python version matches (3.14)

## Production Checklist

- [ ] Set strong `SECRET_KEY` in App Settings
- [ ] Set `FLASK_ENV=production`
- [ ] Enable HTTPS only
- [ ] Configure custom domain (if needed)
- [ ] Enable Application Insights
- [ ] Set up backup strategy
- [ ] Configure scaling rules
- [ ] Review security settings

## License

MIT License - feel free to use this template for your projects.
