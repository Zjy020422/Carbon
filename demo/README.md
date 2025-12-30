# TrailSyncPioneers - Carbon Management Platform

## Overview

TrailSyncPioneers is an AI-driven carbon management platform designed for aviation's net-zero future. The platform empowers airlines to monitor, manage, and reduce contrail emissions through cutting-edge AI technology and comprehensive data integration.

## Features

- **AI-Powered Contrail Detection**: Custom U-Net deep learning model for precise contrail identification
- **Multi-Source Data Integration**: Seamless correlation of satellite data, flight tracking, and meteorological information
- **Climate Impact Quantification**: Advanced radiative forcing analysis and CO2-equivalent emissions calculation
- **Interactive Pricing Calculator**: Dynamic pricing models for SaaS subscriptions, consulting services, and API access
- **Comprehensive Research Results**: Detailed visualization of detection results, emission analysis, and market insights

## Technology Stack

- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **AI/ML**: U-Net Deep Learning Architecture
- **Data Sources**: GOES-16, Himawari-8 Satellite Imagery, ADS-B Flight Data
- **Deployment**: Railway (Static Site)

## Project Structure

```
demo/
├── index.html              # Main HTML file
├── styles.css              # Stylesheet
├── script.js               # JavaScript functionality
├── images/                 # Logo, backgrounds, team photos
├── assert/                 # Research result images
│   └── cropped/           # Cropped analysis charts
├── README.md              # This file
└── .gitignore             # Git ignore rules
```

## Local Development

1. Clone the repository:
```bash
git clone https://github.com/Zjy020422/carbon_web.git
cd carbon_web
```

2. Open `index.html` in your web browser:
```bash
# On Windows
start index.html

# On macOS
open index.html

# On Linux
xdg-open index.html
```

Or use a local development server:
```bash
# Python 3
python -m http.server 8000

# Python 2
python -m SimpleHTTPServer 8000
```

Then visit `http://localhost:8000`

## Deployment

This project is deployed on Railway. To deploy your own instance:

1. Fork this repository
2. Create a new project on [Railway](https://railway.app)
3. Connect your GitHub repository
4. Railway will automatically deploy the static site

## Features Breakdown

### Interactive Pricing Calculator
- **SaaS Subscription**: Dynamic pricing based on fleet size (50,000-200,000 CNY/year)
- **Professional Consulting**: Project complexity-based pricing (20,000-50,000 CNY)
- **API Data Access**: Tiered access with token-based billing (500-5,000 CNY/month)

### Research Results
1. **AI-Powered Detection**: Model training and validation metrics
2. **Climate Impact**: Radiative forcing distribution analysis
3. **Emission Analysis**: CO2 distribution and flight distance correlation
4. **Economic Impact**: Cost structure breakdown and market analysis

## Team

- **Gladys Liu** - CTO & CEO
- **Zoe Wang** - CFO

## Contact

For inquiries and partnership opportunities:
- Email: contact@trailsyncpioneers.com
- Partnerships: partnerships@trailsyncpioneers.com

## License

© 2025 TrailSyncPioneers. All rights reserved.

## Tagline

**Fly Cleaner. Spend Smarter.**
