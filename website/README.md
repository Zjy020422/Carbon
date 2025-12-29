# ContrailTracker Website

Professional commercial website for ContrailTracker - AI-Powered Aviation Carbon Intelligence Platform

## 🎨 Design Features

### Theme
- **Energy & Environment Focus**: Deep blue (#0066cc) and green (#00cc66) color scheme
- **Commercial Grade**: Professional, data-driven, enterprise-level design
- **Modern UI**: Glassmorphism, gradients, smooth animations
- **Responsive**: Fully mobile-optimized

### Sections

1. **Hero** - Impactful introduction with animated statistics
2. **About** - Project overview with key capabilities
3. **Features** - 6 core features with detailed descriptions
4. **Technology** - Tech stack and system architecture
5. **Live Demo** - Interactive analysis platform
6. **Team** - High school student team showcase
7. **Contact** - Enterprise inquiry form

## 🚀 Quick Start

### Frontend Only

Simply open `index.html` in a modern web browser:

```bash
cd website
# Windows
start index.html

# Mac/Linux
open index.html
# or
python -m http.server 8000
```

Then visit: http://localhost:8000

### Full Stack (Frontend + Backend)

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Start Backend Server**
```bash
cd website/backend
python app.py
```

Backend will run on: http://localhost:5000

3. **Access Website**

Open your browser and navigate to: http://localhost:5000

## 📁 Directory Structure

```
website/
├── index.html              # Main HTML page
├── css/
│   └── style.css          # Styling (energy theme)
├── js/
│   └── main.js            # Interactive functionality
├── backend/
│   ├── app.py             # Flask API server
│   └── uploads/           # Upload directory (auto-created)
├── images/                # Image assets
├── assets/                # Other assets
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## 🔌 Backend API Endpoints

### Base URL: `http://localhost:5000/api`

#### Health Check
```
GET /api/health
```

#### Contrail Analysis
```
POST /api/analyze/contrail
Content-Type: multipart/form-data

Body:
- satellite_data: File (NetCDF, NPY)
- flight_data: File (CSV)

Response:
{
    "success": true,
    "stats": {
        "total_matches": 48,
        "unique_satellites": 1,
        "unique_flights": 48,
        "avg_time_diff": 850.5,
        "bbox_match_rate": 1.0
    }
}
```

#### Emission Calculation
```
POST /api/analyze/emissions
Content-Type: application/json

Body:
{
    "flight_data_file": "flights.csv",
    "carbon_market": "EU_ETS"
}

Response:
{
    "success": true,
    "stats": {
        "total_flights": 65,
        "total_co2_tonnes": 2196.9,
        "total_carbon_cost_usd": 208707.48,
        "avg_emission_factor": 10.80
    },
    "top_emitters": [...]
}
```

#### Carbon Market Comparison
```
POST /api/analyze/carbon-markets
Content-Type: application/json

Body:
{
    "results_file": "emission_results.csv"
}

Response:
{
    "success": true,
    "markets": [
        {
            "carbon_market": "EU_ETS",
            "market_name": "EU Emissions Trading System",
            "price_per_tonne_usd": 95,
            "total_cost_usd": 208707.48
        },
        ...
    ],
    "analysis": {
        "cost_ratio": 8.64,
        "cost_difference": 184541.0
    }
}
```

#### Contact Form
```
POST /api/contact
Content-Type: application/json

Body:
{
    "name": "John Doe",
    "email": "john@example.com",
    "company": "Aviation Inc",
    "interest": "Enterprise License",
    "message": "I'm interested in..."
}
```

## 🎯 Features Integration

### Connecting to Existing Code

The backend API (`backend/app.py`) integrates with existing ContrailTracker modules:

```python
# Data Fusion
from src.data_processing.data_fusion import DataFusionPipeline

# Emission Calculation
from src.emission.emission_calculator import BatchEmissionCalculator

# Carbon Markets
from src.emission.carbon_trading import CarbonMarket
```

### Demo Tab Functionality

The **Live Demo** section has three tabs:

1. **Contrail Detection** - Shows satellite-flight fusion results
2. **Emission Analysis** - Displays emission calculations
3. **Carbon Markets** - Compares 5 global carbon markets

### File Upload

Users can upload:
- Satellite data (NetCDF, NPY files)
- Flight data (CSV files)

Files are processed through the backend API and results are displayed.

## 🎨 Customization

### Colors

Edit `css/style.css` to change theme colors:

```css
:root {
    --primary-blue: #0066cc;      /* Main brand color */
    --secondary-green: #00cc66;   /* Accent color */
    --dark-bg: #0a1628;           /* Background */
    /* ... more variables */
}
```

### Content

- **Team Members**: Edit team cards in `index.html` section `#team`
- **Statistics**: Update hero stats in `index.html` section `#home`
- **Features**: Modify feature cards in `#features` section

### Images

Replace demo images:
- Place your visualization images in `../visualizations_en/`
- Update image paths in `index.html`

## 📊 Production Deployment

### Environment Variables

Create `.env` file:

```env
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
MAX_CONTENT_LENGTH=104857600
UPLOAD_FOLDER=/var/www/uploads
DATABASE_URL=postgresql://user:pass@localhost/contrailtracker
```

### WSGI Server

Use Gunicorn for production:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 backend.app:app
```

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name contrailtracker.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static {
        alias /var/www/contrailtracker/website;
    }
}
```

### Docker Deployment

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "backend.app:app"]
```

## 🛡️ Security

- File upload validation (type, size)
- CORS configuration
- Input sanitization
- SQL injection prevention
- XSS protection

## 📈 Performance Optimization

- Lazy loading images
- CSS/JS minification
- CDN for external libraries
- Gzip compression
- Browser caching

## 🐛 Troubleshooting

### Backend Won't Start

```bash
# Check Python version
python --version  # Should be 3.8+

# Install dependencies
pip install -r requirements.txt

# Check port availability
netstat -an | grep 5000
```

### File Upload Fails

```bash
# Check upload folder permissions
mkdir -p website/backend/uploads
chmod 755 website/backend/uploads
```

### CORS Errors

Enable CORS in `backend/app.py`:
```python
CORS(app, resources={r"/api/*": {"origins": "*"}})
```

## 📞 Support

For issues or questions:
- Email: support@contrailtracker.com
- GitHub: https://github.com/contrailtracker/website
- Documentation: https://docs.contrailtracker.com

## 📄 License

Copyright © 2025 ContrailTracker Team. All rights reserved.

---

**Built with** ❤️ **by high school students passionate about climate action**
