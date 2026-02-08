"""
TrailSyncPioneers - Simple Web Application
Run: python app.py
Visit: http://localhost:5000
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import sys
import numpy as np
import torch
import torch.nn as nn
from pathlib import Path
from datetime import datetime
import json
import base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

# Add parent directory
sys.path.append(str(Path(__file__).parent.parent))

from yige_code.src.emission.emission_calculator import EmissionCalculator, EmissionReportGenerator
from yige_code.src.emission.carbon_trading import CarbonTradingCalculator, CarbonTradingReportGenerator

# Flask app
app = Flask(__name__)
CORS(app)

# Folders
UPLOAD_FOLDER = Path('backend/uploads')
RESULTS_FOLDER = Path('backend/results')
MODEL_PATH = Path('../yige_code/model/model_checkpoint_e39.pt')

UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
RESULTS_FOLDER.mkdir(parents=True, exist_ok=True)

app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

# Model classes
class DoubleConv(nn.Module):
    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.double_conv = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True)
        )
    def forward(self, x):
        return self.double_conv(x)

class Down(nn.Module):
    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.maxpool_conv = nn.Sequential(nn.MaxPool2d(2), DoubleConv(in_channels, out_channels))
    def forward(self, x):
        return self.maxpool_conv(x)

class Up(nn.Module):
    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.up = nn.Upsample(scale_factor=2, mode='bilinear', align_corners=True)
        self.conv = DoubleConv(in_channels, out_channels)
    def forward(self, x, skip):
        x = self.up(x)
        diff_y = skip.size()[2] - x.size()[2]
        diff_x = skip.size()[3] - x.size()[3]
        if diff_y != 0 or diff_x != 0:
            x = nn.functional.pad(x, [diff_x // 2, diff_x - diff_x // 2, diff_y // 2, diff_y - diff_y // 2])
        x = torch.cat([skip, x], dim=1)
        return self.conv(x)

class OutConv(nn.Module):
    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.conv = nn.Conv2d(in_channels, out_channels, kernel_size=1)
    def forward(self, x):
        return self.conv(x)

class UNet(nn.Module):
    def __init__(self, in_channels=24, out_channels=1, base_classes=32):
        super(UNet, self).__init__()
        self.inc = DoubleConv(in_channels, base_classes)
        self.down1 = Down(base_classes, base_classes * 2)
        self.down2 = Down(base_classes * 2, base_classes * 4)
        self.down3 = Down(base_classes * 4, base_classes * 8)
        self.down4 = Down(base_classes * 8, base_classes * 8)
        self.up1 = Up(base_classes * 16, base_classes * 4)
        self.up2 = Up(base_classes * 8, base_classes * 2)
        self.up3 = Up(base_classes * 4, base_classes)
        self.up4 = Up(base_classes * 2, base_classes)
        self.outc = OutConv(base_classes, out_channels)

    def forward(self, x):
        x1 = self.inc(x)
        x2 = self.down1(x1)
        x3 = self.down2(x2)
        x4 = self.down3(x3)
        x5 = self.down4(x4)
        x = self.up1(x5, x4)
        x = self.up2(x, x3)
        x = self.up3(x, x2)
        x = self.up4(x, x1)
        return self.outc(x)

# Load model
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = UNet(in_channels=24, out_channels=1, base_classes=32)
checkpoint = torch.load(MODEL_PATH, map_location=device)
model.load_state_dict(checkpoint)
model.to(device)
model.eval()
emission_calc = EmissionCalculator()

print(f"Model loaded on {device}")
print("="*60)
print("MODIFIED VERSION with FIX - Images and Strategies support")
print("="*60)

# Helper functions
def process_data(b11, b14, b15):
    _T11 = (243, 303)
    _CLOUD = (-4, 5)
    _TDIFF = (-4, 2)
    norm = lambda d, b: (d - b[0]) / (b[1] - b[0])
    r = norm(b15 - b14, _TDIFF)
    g = norm(b14 - b11, _CLOUD)
    b = norm(b14, _T11)
    fc = np.clip(np.concatenate([r, g, b], axis=2), 0, 1)
    return torch.tensor(fc).float().permute(2, 0, 1), fc

def detect(img, thresh=0.5):
    with torch.no_grad():
        img = img.unsqueeze(0).to(device) if img.dim() == 3 else img.to(device)
        out = model(img)
        prob = torch.sigmoid(out).cpu().numpy()[0, 0]
        binary = (prob > thresh).astype(np.uint8)
    return prob, binary

def save_single_image(data, path, title, cmap=None):
    """Save a single visualization image"""
    fig, ax = plt.subplots(1, 1, figsize=(8, 8))
    if cmap:
        im = ax.imshow(data, cmap=cmap)
        plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    else:
        ax.imshow(data)
    ax.set_title(title, fontsize=16, fontweight='bold', pad=15)
    ax.axis('off')
    plt.tight_layout()
    plt.savefig(path, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()

def visualize(fc, prob, binary, folder):
    """Generate individual visualization images"""
    t = 3
    rgb = np.stack([fc[:, :, t], fc[:, :, 8 + t], fc[:, :, 16 + t]], axis=2)

    # Save individual images
    save_single_image(rgb, folder / 'input.png', 'Satellite Input Image')
    save_single_image(prob, folder / 'probability.png', 'Contrail Probability Map', cmap='hot')
    save_single_image(binary, folder / 'binary.png', 'Binary Detection Result', cmap='gray')

def visualize_fusion(fc, binary, config, path):
    """Generate fusion visualization of contrail detection and flight track"""
    t = 3
    rgb = np.stack([fc[:, :, t], fc[:, :, 8 + t], fc[:, :, 16 + t]], axis=2)

    fig, ax = plt.subplots(1, 1, figsize=(10, 10))

    # Show satellite image
    ax.imshow(rgb, alpha=0.8)

    # Overlay contrail detection (red transparent)
    contrail_overlay = np.zeros((*binary.shape, 4))
    contrail_overlay[binary > 0] = [1, 0, 0, 0.5]  # Red with 50% transparency
    ax.imshow(contrail_overlay)

    # Generate mock flight path based on config
    min_lat, max_lat = config['min_lat'], config['max_lat']
    min_lon, max_lon = config['min_lon'], config['max_lon']

    # Create flight path (diagonal across the image)
    H, W = binary.shape
    num_points = 50
    x_path = np.linspace(W * 0.1, W * 0.9, num_points)
    y_path = np.linspace(H * 0.2, H * 0.8, num_points)

    # Add some variation to make it look realistic
    y_path += np.sin(np.linspace(0, 2*np.pi, num_points)) * H * 0.05

    # Plot flight path
    ax.plot(x_path, y_path, 'b-', linewidth=3, label='Flight Track', alpha=0.8)
    ax.plot(x_path, y_path, 'b.', markersize=8, alpha=0.6)

    # Mark start and end
    ax.plot(x_path[0], y_path[0], 'go', markersize=15, label='Start', markeredgecolor='white', markeredgewidth=2)
    ax.plot(x_path[-1], y_path[-1], 'rs', markersize=15, label='End', markeredgecolor='white', markeredgewidth=2)

    # Add annotations
    ax.text(x_path[0], y_path[0] - 20, 'START', fontsize=12, color='white',
            bbox=dict(boxstyle='round', facecolor='green', alpha=0.7), ha='center')
    ax.text(x_path[-1], y_path[-1] + 30, 'END', fontsize=12, color='white',
            bbox=dict(boxstyle='round', facecolor='red', alpha=0.7), ha='center')

    # Add legend
    ax.legend(loc='upper left', fontsize=12, framealpha=0.9)

    # Title with flight info
    callsign = config.get('flight_callsign', 'UNKNOWN')
    ax.set_title(f'Contrail-Flight Fusion Analysis\nFlight: {callsign}',
                 fontsize=16, fontweight='bold', pad=20)
    ax.axis('off')

    plt.tight_layout()
    plt.savefig(path, dpi=200, bbox_inches='tight')
    plt.close()

def calc_emission(config, mask):
    track = pd.DataFrame({
        'latitude': [config['min_lat'], config['max_lat']],
        'longitude': [config['min_lon'], config['max_lon']],
        'baro_altitude': [10000, 10500],
        'velocity': [230, 235],
        'callsign': [config.get('flight_callsign', 'UNKNOWN')] * 2
    })
    em = emission_calc.calculate_flight_emissions(track, mask, 'A320')
    ct = CarbonTradingCalculator(config.get('carbon_market', 'EU_ETS'))
    cb = ct.calculate_flight_carbon_cost(em.co2_total, em.flight_distance, 180)
    return em, cb

# Routes
@app.route('/')
def home():
    with open('index.html', 'r', encoding='utf-8') as f:
        return f.read()

@app.route('/product.html')
def product():
    with open('product.html', 'r', encoding='utf-8') as f:
        return f.read()

@app.route('/api/health')
def health():
    return jsonify({'status': 'ok', 'device': str(device)})

@app.route('/<path:path>')
def static_files(path):
    if os.path.exists(path):
        return send_file(path)
    return '', 404

@app.route('/api/analyze', methods=['POST'])
def analyze():
    try:
        b11 = request.files['band11']
        b14 = request.files['band14']
        b15 = request.files['band15']
        config = json.loads(request.form['config'])

        sid = datetime.now().strftime('%Y%m%d_%H%M%S')
        folder = UPLOAD_FOLDER / sid
        folder.mkdir(exist_ok=True)

        p11 = folder / 'band_11.npy'
        p14 = folder / 'band_14.npy'
        p15 = folder / 'band_15.npy'
        b11.save(p11)
        b14.save(p14)
        b15.save(p15)

        img, fc = process_data(np.load(p11), np.load(p14), np.load(p15))
        prob, binary = detect(img, config.get('threshold', 0.5))

        pixels = int(np.sum(binary))
        coverage = float(pixels / (256 * 256) * 100)
        area = float(pixels * 4)
        intensity = float(np.mean(prob[binary > 0])) if pixels > 0 else 0.0

        # Generate individual visualization images
        visualize(fc, prob, binary, folder)

        # Generate fusion visualization
        fusion_path = folder / 'fusion.png'
        visualize_fusion(fc, binary, config, fusion_path)

        # Calculate emissions
        em, cb = calc_emission(config, binary)

        # Encode images to base64
        def encode_image(path):
            with open(path, 'rb') as f:
                return base64.b64encode(f.read()).decode()

        print(f"DEBUG: Encoding images from {folder}")
        img_input = encode_image(folder / 'input.png')
        print(f"DEBUG: img_input encoded: {len(img_input)} chars")
        img_prob = encode_image(folder / 'probability.png')
        print(f"DEBUG: img_prob encoded: {len(img_prob)} chars")
        img_binary = encode_image(folder / 'binary.png')
        print(f"DEBUG: img_binary encoded: {len(img_binary)} chars")
        img_fusion = encode_image(fusion_path)
        print(f"DEBUG: img_fusion encoded: {len(img_fusion)} chars")

        # Calculate carbon trading strategies for different markets and altitudes
        print("DEBUG: Starting strategy calculation...")
        markets = ['EU_ETS', 'CORSIA', 'CHINA', 'UK_ETS', 'CALIFORNIA']
        altitudes = [8000, 9000, 10000, 11000, 12000]  # meters

        strategies = []
        try:
            for market in markets:
                print(f"DEBUG: Processing market {market}...")
                ct = CarbonTradingCalculator(market)
                print(f"DEBUG: Created CarbonTradingCalculator for {market}, price={ct.carbon_price}")
                market_data = {'market': market, 'price': ct.carbon_price, 'altitudes': []}

                for alt in altitudes:
                    # Simulate altitude impact (higher altitude = more contrail, more CO2eq)
                    altitude_factor = 1.0 + (alt - 10000) / 10000 * 0.3
                    adjusted_co2 = em.co2_total * altitude_factor
                    cost_result = ct.calculate_flight_carbon_cost(adjusted_co2, em.flight_distance, 180)

                    market_data['altitudes'].append({
                        'altitude': alt,
                        'co2_total': round(adjusted_co2, 1),
                        'cost_total': round(cost_result.carbon_cost_total, 2),
                        'cost_per_km': round(cost_result.carbon_cost_per_km, 4)
                    })

                strategies.append(market_data)
                print(f"DEBUG: Completed market {market}")
        except Exception as e:
            print(f"DEBUG ERROR in strategy calculation: {e}")
            import traceback
            traceback.print_exc()
            raise

        print(f"DEBUG: Prepared {len(strategies)} strategies")
        print(f"DEBUG: Returning response with images and strategies")

        return jsonify({
            'session_id': sid,
            'contrail': {'pixels': pixels, 'coverage': round(coverage, 2), 'area': round(area, 1), 'intensity': round(intensity, 2)},
            'emission': {'distance': round(em.flight_distance, 1), 'fuel': round(em.fuel_burn, 1),
                        'co2_direct': round(em.co2_direct, 1), 'co2_contrail': round(em.co2_contrail, 1),
                        'co2_total': round(em.co2_total, 1)},
            'carbon': {'market': config.get('carbon_market', 'EU_ETS'), 'price': cb.carbon_price_per_tonne,
                      'cost_total': round(cb.carbon_cost_total, 2), 'cost_per_km': round(cb.carbon_cost_per_km, 4),
                      'cost_per_passenger': round(cb.carbon_cost_per_passenger, 2)},
            'flight': {'callsign': config.get('flight_callsign', 'UNKNOWN'), 'aircraft': 'A320',
                      'time': config.get('detection_time', datetime.now().isoformat())},
            'images': {
                'input': img_input,
                'probability': img_prob,
                'binary': img_binary,
                'fusion': img_fusion
            },
            'strategies': strategies,
            'report': f'Analysis completed for {sid}'
        })
    except Exception as e:
        import traceback
        print("="*60)
        print("ERROR in /api/analyze:")
        print(str(e))
        print("="*60)
        traceback.print_exc()
        print("="*60)
        return jsonify({'error': str(e)}), 500

@app.route('/api/download/<sid>')
def download(sid):
    import zipfile
    folder = UPLOAD_FOLDER / sid
    if not folder.exists():
        return jsonify({'error': 'Not found'}), 404
    zp = RESULTS_FOLDER / f'{sid}.zip'
    with zipfile.ZipFile(zp, 'w') as z:
        for f in folder.iterdir():
            z.write(f, f.name)
    return send_file(zp, as_attachment=True, download_name=f'results_{sid}.zip')

if __name__ == '__main__':
    print("\n" + "="*60)
    print("  TrailSyncPioneers Platform")
    print("="*60)
    print(f"\n  Homepage: http://localhost:5000/")
    print(f"  Product:  http://localhost:5000/product.html")
    print("\n" + "="*60 + "\n")
    app.run(host='0.0.0.0', port=5000, debug=False)
