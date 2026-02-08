# TrailSyncPioneers - Contrail Detection & Carbon Trading Platform

AI-powered aviation emission monitoring and carbon trading analysis platform.

## Features

- 🛩️ Contrail Detection using UNet Deep Learning Model
- 📊 Real-time Emission Calculations
- 💰 Carbon Trading Cost Analysis (5 Markets)
- 📈 Interactive Data Visualization
- 🎯 Flight-Contrail Fusion Visualization
- 🌍 Multi-Market Strategy Comparison

## Tech Stack

- **Backend**: Flask, PyTorch
- **Frontend**: Vanilla JavaScript, Chart.js
- **ML Model**: UNet (24-channel input for satellite data)
- **Deployment**: Railway

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run server
python app.py
```

Visit: `http://localhost:5000`

### Railway Deployment

1. Push to GitHub
2. Connect Railway to your repository
3. Railway will auto-detect and deploy using:
   - `runtime.txt` - Python version
   - `requirements.txt` - Dependencies
   - `Procfile` - Start command

## Project Structure

```
web/
├── app.py                 # Flask backend
├── index.html            # Homepage
├── product.html          # Analysis platform
├── product.js            # Frontend logic
├── product.css           # Styling
├── styles.css            # Global styles
├── script.js             # Homepage scripts
├── images/               # Static images
├── backend/
│   ├── uploads/          # User uploaded data
│   └── results/          # Analysis results
├── requirements.txt      # Python dependencies
├── Procfile             # Railway start command
└── runtime.txt          # Python version

```

## API Endpoints

- `GET /` - Homepage
- `GET /product.html` - Analysis platform
- `GET /api/health` - Health check
- `POST /api/analyze` - Run contrail analysis
- `GET /api/download/<session_id>` - Download results

## Environment Variables

No environment variables required for basic operation.

## License

© 2025 TrailSyncPioneers. All rights reserved.

## Contact

For questions or support, please open an issue on GitHub.
