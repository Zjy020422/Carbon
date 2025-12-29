"""
ContrailTracker Backend API
Flask server connecting frontend to core analysis functions
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
import traceback

# Add parent directory to path to import project modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data_processing.data_fusion import DataFusionPipeline
from src.emission.emission_calculator import BatchEmissionCalculator
# from src.emission.carbon_trading import CarbonMarket  # Not used, commented out

# Initialize Flask app
app = Flask(__name__, static_folder='..', static_url_path='')
CORS(app)  # Enable CORS for frontend-backend communication

# Configuration
UPLOAD_FOLDER = Path(__file__).parent / 'uploads'
UPLOAD_FOLDER.mkdir(exist_ok=True)
ALLOWED_EXTENSIONS = {'csv', 'nc', 'npy', 'json'}

app.config['UPLOAD_FOLDER'] = str(UPLOAD_FOLDER)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

# ==================== Helper Functions ====================

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_upload_file(file):
    """Save uploaded file and return path"""
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = UPLOAD_FOLDER / filename
        file.save(str(filepath))
        return filepath
    return None


# ==================== Routes ====================

@app.route('/')
def index():
    """Serve main page"""
    return send_from_directory('..', 'index.html')


@app.route('/api/health', methods=['GET'])
def health_check():
    """API health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'ContrailTracker API',
        'version': '1.0.0'
    })


@app.route('/api/analyze/contrail', methods=['POST'])
def analyze_contrail():
    """
    Endpoint: Analyze contrail detection
    Input: satellite data file, flight data file
    Output: Fusion results with contrail detection
    """
    try:
        # Check if files are present
        if 'satellite_data' not in request.files or 'flight_data' not in request.files:
            return jsonify({
                'error': 'Missing required files (satellite_data, flight_data)'
            }), 400

        # Save uploaded files
        satellite_file = save_upload_file(request.files['satellite_data'])
        flight_file = save_upload_file(request.files['flight_data'])

        if not satellite_file or not flight_file:
            return jsonify({'error': 'Invalid file format'}), 400

        # Initialize data fusion pipeline
        pipeline = DataFusionPipeline(
            satellite_data_dir=str(satellite_file.parent),
            flight_data_path=str(flight_file),
            output_dir=str(UPLOAD_FOLDER / 'processed')
        )

        # Run fusion
        fused_data = pipeline.run_fusion(
            satellite_metadata_file=str(satellite_file),
            output_file='fusion_results.csv'
        )

        # Calculate statistics
        stats = {
            'total_matches': len(fused_data),
            'unique_satellites': int(fused_data['record_id'].nunique()) if 'record_id' in fused_data.columns else 0,
            'unique_flights': int(fused_data['icao24'].nunique()) if 'icao24' in fused_data.columns else 0,
            'avg_time_diff': float(fused_data['time_diff_seconds'].mean()) if 'time_diff_seconds' in fused_data.columns else 0,
            'bbox_match_rate': float(fused_data['in_bbox'].mean()) if 'in_bbox' in fused_data.columns else 0
        }

        return jsonify({
            'success': True,
            'message': 'Contrail analysis completed',
            'stats': stats,
            'results_file': 'fusion_results.csv'
        })

    except Exception as e:
        print(f"Error in contrail analysis: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@app.route('/api/analyze/emissions', methods=['POST'])
def analyze_emissions():
    """
    Endpoint: Calculate carbon emissions
    Input: flight data (CSV or JSON), carbon market
    Output: Emission statistics and costs
    """
    try:
        data = request.json
        carbon_market = data.get('carbon_market', 'EU_ETS')

        # Check if flight data is provided
        if 'flight_data_file' in data:
            flight_data_path = UPLOAD_FOLDER / data['flight_data_file']
            if not flight_data_path.exists():
                return jsonify({'error': 'Flight data file not found'}), 404

            # Initialize emission calculator
            calculator = BatchEmissionCalculator(carbon_market=carbon_market)

            # Process flight data
            results = calculator.process_flight_csv(
                input_csv=str(flight_data_path),
                output_csv=str(UPLOAD_FOLDER / 'emission_results.csv')
            )

            # Calculate summary statistics
            total_co2_kg = results['co2_total_kg'].sum()
            total_co2_tonnes = total_co2_kg / 1000.0
            total_fuel_kg = results['fuel_burn_kg'].sum()
            avg_emission_factor = results['emission_factor_kg_per_km'].mean()
            total_carbon_cost = results['carbon_cost_usd'].sum()

            stats = {
                'total_flights': len(results),
                'total_co2_kg': float(total_co2_kg),
                'total_co2_tonnes': float(total_co2_tonnes),
                'total_fuel_kg': float(total_fuel_kg),
                'avg_emission_factor': float(avg_emission_factor),
                'carbon_market': carbon_market,
                'total_carbon_cost_usd': float(total_carbon_cost),
                'avg_cost_per_flight': float(total_carbon_cost / len(results)) if len(results) > 0 else 0
            }

            # Get top 10 emitters
            top10 = results.nlargest(10, 'co2_total_kg')[
                ['callsign', 'typecode', 'flight_distance_km', 'co2_total_kg', 'carbon_cost_usd']
            ].to_dict('records')

            return jsonify({
                'success': True,
                'message': 'Emission calculation completed',
                'stats': stats,
                'top_emitters': top10,
                'results_file': 'emission_results.csv'
            })

        elif 'flight_data' in data:
            # Direct flight data provided
            flight_data = pd.DataFrame(data['flight_data'])

            # Save to temp file
            temp_file = UPLOAD_FOLDER / 'temp_flights.csv'
            flight_data.to_csv(temp_file, index=False)

            # Calculate emissions
            calculator = BatchEmissionCalculator(carbon_market=carbon_market)
            results = calculator.process_flight_csv(
                input_csv=str(temp_file),
                output_csv=str(UPLOAD_FOLDER / 'emission_results.csv')
            )

            # Similar statistics calculation as above
            total_co2_kg = results['co2_total_kg'].sum()
            total_co2_tonnes = total_co2_kg / 1000.0

            return jsonify({
                'success': True,
                'total_co2_tonnes': float(total_co2_tonnes),
                'results': results.to_dict('records')
            })

        else:
            return jsonify({'error': 'No flight data provided'}), 400

    except Exception as e:
        print(f"Error in emission analysis: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@app.route('/api/analyze/carbon-markets', methods=['POST'])
def compare_carbon_markets():
    """
    Endpoint: Compare costs across different carbon markets
    Input: emissions data
    Output: Cost comparison across 5 carbon markets
    """
    try:
        data = request.json

        # Get emission results file or data
        if 'results_file' in data:
            results_file = UPLOAD_FOLDER / data['results_file']
            df = pd.read_csv(results_file)
        elif 'emissions' in data:
            df = pd.DataFrame(data['emissions'])
        else:
            return jsonify({'error': 'No emission data provided'}), 400

        # Define carbon markets
        markets = {
            'EU_ETS': {'name': 'EU Emissions Trading System', 'price': 95},
            'CORSIA': {'name': 'ICAO CORSIA', 'price': 20},
            'CHINA': {'name': 'China Carbon Market', 'price': 11},
            'CALIFORNIA': {'name': 'California Cap-and-Trade', 'price': 30},
            'RGGI': {'name': 'Regional Greenhouse Gas Initiative', 'price': 15}
        }

        # Calculate costs for each market
        results = []
        total_co2_tonnes = df['co2_total_kg'].sum() / 1000.0

        for market_code, market_info in markets.items():
            total_cost = total_co2_tonnes * market_info['price']
            avg_cost_per_flight = total_cost / len(df) if len(df) > 0 else 0

            results.append({
                'carbon_market': market_code,
                'market_name': market_info['name'],
                'price_per_tonne_usd': market_info['price'],
                'total_cost_usd': float(total_cost),
                'avg_cost_per_flight_usd': float(avg_cost_per_flight)
            })

        # Sort by total cost descending
        results.sort(key=lambda x: x['total_cost_usd'], reverse=True)

        # Calculate cost variance
        max_cost = results[0]['total_cost_usd']
        min_cost = results[-1]['total_cost_usd']
        cost_ratio = max_cost / min_cost if min_cost > 0 else 0

        return jsonify({
            'success': True,
            'message': 'Carbon market comparison completed',
            'markets': results,
            'analysis': {
                'highest_market': results[0]['market_name'],
                'highest_cost': float(max_cost),
                'lowest_market': results[-1]['market_name'],
                'lowest_cost': float(min_cost),
                'cost_difference': float(max_cost - min_cost),
                'cost_ratio': float(cost_ratio)
            }
        })

    except Exception as e:
        print(f"Error in market comparison: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """
    Generic file upload endpoint
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        filepath = save_upload_file(file)
        if filepath:
            return jsonify({
                'success': True,
                'filename': filepath.name,
                'path': str(filepath.relative_to(UPLOAD_FOLDER))
            })
        else:
            return jsonify({'error': 'Invalid file format'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/contact', methods=['POST'])
def contact():
    """
    Contact form submission endpoint
    """
    try:
        data = request.json

        # Validate required fields
        required_fields = ['name', 'email', 'message']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        # In production, this would send an email or save to database
        # For now, just log the submission
        print("=" * 70)
        print("New Contact Form Submission")
        print("=" * 70)
        print(f"Name: {data['name']}")
        print(f"Email: {data['email']}")
        print(f"Company: {data.get('company', 'N/A')}")
        print(f"Interest: {data.get('interest', 'N/A')}")
        print(f"Message: {data['message']}")
        print("=" * 70)

        # Save to log file
        log_file = UPLOAD_FOLDER / 'contact_submissions.log'
        with open(log_file, 'a') as f:
            f.write(f"\n{'='*70}\n")
            f.write(f"Submission Time: {pd.Timestamp.now()}\n")
            f.write(f"Name: {data['name']}\n")
            f.write(f"Email: {data['email']}\n")
            f.write(f"Company: {data.get('company', 'N/A')}\n")
            f.write(f"Interest: {data.get('interest', 'N/A')}\n")
            f.write(f"Message: {data['message']}\n")

        return jsonify({
            'success': True,
            'message': 'Thank you for your message. We will get back to you soon!'
        })

    except Exception as e:
        print(f"Error in contact form: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """
    Get current platform statistics
    """
    try:
        # In production, these would come from database
        stats = {
            'total_flights_analyzed': 65,
            'total_co2_tracked_tonnes': 2196.9,
            'model_accuracy': 98.9,
            'contrail_coverage_pct': 0.47,
            'active_users': 127,
            'api_calls_today': 1453
        }

        return jsonify({
            'success': True,
            'stats': stats
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== Error Handlers ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


# ==================== Run Server ====================

if __name__ == '__main__':
    print("="*70)
    print("ContrailTracker Backend API Server")
    print("="*70)
    print(f"Upload folder: {UPLOAD_FOLDER}")
    print(f"Allowed extensions: {ALLOWED_EXTENSIONS}")
    print("="*70)
    print("\nServer starting on http://localhost:5000")
    print("API endpoints:")
    print("  - GET  /api/health")
    print("  - POST /api/analyze/contrail")
    print("  - POST /api/analyze/emissions")
    print("  - POST /api/analyze/carbon-markets")
    print("  - POST /api/upload")
    print("  - POST /api/contact")
    print("  - GET  /api/stats")
    print("="*70)

    app.run(debug=True, host='0.0.0.0', port=5000)
