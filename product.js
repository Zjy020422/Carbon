// Product Platform JavaScript
// TrailSyncPioneers - Contrail Detection Platform

// Global state
let uploadedFiles = {
    band11: null,
    band14: null,
    band15: null
};

let analysisResults = null;
let currentStep = 1;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeFileUploads();
    initializeThresholdSlider();
    setDefaultDateTime();
});

// ==================== File Upload Handling ====================

function initializeFileUploads() {
    const fileInputs = ['band11', 'band14', 'band15'];

    fileInputs.forEach(bandId => {
        const input = document.getElementById(bandId);
        const status = document.getElementById(`status-${bandId}`);

        input.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                // Validate file
                if (!file.name.endsWith('.npy')) {
                    status.textContent = '❌ Invalid file type. Please upload .npy file';
                    status.className = 'file-status error';
                    uploadedFiles[bandId] = null;
                    return;
                }

                if (file.size > 50 * 1024 * 1024) { // 50MB limit
                    status.textContent = '❌ File too large (max 50MB)';
                    status.className = 'file-status error';
                    uploadedFiles[bandId] = null;
                    return;
                }

                // File is valid
                uploadedFiles[bandId] = file;
                status.textContent = `✅ ${file.name} (${formatFileSize(file.size)})`;
                status.className = 'file-status success';

                // Update button label
                const label = input.nextElementSibling;
                label.querySelector('.upload-text').textContent = 'Change file';

                // Check if all files uploaded
                checkAllFilesUploaded();
            }
        });
    });
}

function checkAllFilesUploaded() {
    const allUploaded = uploadedFiles.band11 && uploadedFiles.band14 && uploadedFiles.band15;
    const nextBtn = document.getElementById('upload-next-btn');

    if (allUploaded) {
        nextBtn.disabled = false;
        nextBtn.classList.add('pulse');
    } else {
        nextBtn.disabled = true;
        nextBtn.classList.remove('pulse');
    }
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

// ==================== Form Configuration ====================

function initializeThresholdSlider() {
    const slider = document.getElementById('threshold');
    const output = document.getElementById('threshold-value');

    slider.addEventListener('input', (e) => {
        output.textContent = e.target.value;
    });
}

function setDefaultDateTime() {
    const now = new Date();
    now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
    document.getElementById('detection-time').value = now.toISOString().slice(0, 16);
}

// ==================== Step Navigation ====================

function goToStep(stepNumber) {
    // Validate current step before proceeding
    if (stepNumber > currentStep) {
        if (currentStep === 1 && !validateStep1()) return;
        if (currentStep === 2 && !validateStep2()) return;
    }

    // Hide all sections
    document.querySelectorAll('.section-panel').forEach(panel => {
        panel.classList.remove('active');
    });

    // Show target section
    document.getElementById(`step${stepNumber}`).classList.add('active');

    // Update step indicator
    document.querySelectorAll('.step').forEach((step, index) => {
        if (index < stepNumber) {
            step.classList.add('completed');
            step.classList.remove('active');
        } else if (index + 1 === stepNumber) {
            step.classList.add('active');
            step.classList.remove('completed');
        } else {
            step.classList.remove('active', 'completed');
        }
    });

    currentStep = stepNumber;

    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function validateStep1() {
    if (!uploadedFiles.band11 || !uploadedFiles.band14 || !uploadedFiles.band15) {
        alert('Please upload all three band files before proceeding.');
        return false;
    }
    return true;
}

function validateStep2() {
    const minLat = document.getElementById('min-lat').value;
    const maxLat = document.getElementById('max-lat').value;
    const minLon = document.getElementById('min-lon').value;
    const maxLon = document.getElementById('max-lon').value;

    if (!minLat || !maxLat || !minLon || !maxLon) {
        alert('Please fill in all geographic bounds.');
        return false;
    }

    if (parseFloat(minLat) >= parseFloat(maxLat)) {
        alert('Max latitude must be greater than min latitude.');
        return false;
    }

    if (parseFloat(minLon) >= parseFloat(maxLon)) {
        alert('Max longitude must be greater than min longitude.');
        return false;
    }

    return true;
}

// ==================== Analysis Processing ====================

async function startAnalysis() {
    if (!validateStep2()) return;

    // Go to processing step
    goToStep(3);

    // Collect form data
    const formData = new FormData();
    formData.append('band11', uploadedFiles.band11);
    formData.append('band14', uploadedFiles.band14);
    formData.append('band15', uploadedFiles.band15);

    const config = {
        detection_time: document.getElementById('detection-time').value,
        flight_callsign: document.getElementById('flight-callsign').value || 'UNKNOWN',
        min_lat: parseFloat(document.getElementById('min-lat').value),
        max_lat: parseFloat(document.getElementById('max-lat').value),
        min_lon: parseFloat(document.getElementById('min-lon').value),
        max_lon: parseFloat(document.getElementById('max-lon').value),
        threshold: parseFloat(document.getElementById('threshold').value),
        carbon_market: document.getElementById('carbon-market').value
    };

    formData.append('config', JSON.stringify(config));

    try {
        // Start processing animation
        const processingPromise = simulateProcessing();

        // Make actual API call to backend
        const API_URL = '/api/analyze';

        addLog('Connecting to backend server...');

        const response = await fetch(API_URL, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Analysis failed');
        }

        const results = await response.json();

        // Wait for processing animation to complete
        await processingPromise;

        analysisResults = results;

        // Go to results step first, then display results
        goToStep(4);

        // Use setTimeout to ensure DOM is ready
        setTimeout(() => {
            displayResults(results);
        }, 100);

    } catch (error) {
        console.error('Analysis error:', error);

        // Check if backend is unreachable
        if (error.message.includes('Failed to fetch')) {
            alert('Cannot connect to server.\n\nPlease ensure the server is running:\npython web/app.py');
        } else {
            alert('Analysis failed: ' + error.message);
        }

        goToStep(2);
    }
}

async function simulateProcessing() {
    const steps = [
        { id: 'proc-upload', duration: 1000 },
        { id: 'proc-detect', duration: 2000 },
        { id: 'proc-emission', duration: 1500 },
        { id: 'proc-carbon', duration: 1000 },
        { id: 'proc-report', duration: 1000 }
    ];

    for (const step of steps) {
        await processStep(step.id, step.duration);
    }
}

function processStep(stepId, duration) {
    return new Promise((resolve) => {
        const stepEl = document.getElementById(stepId);
        const icon = stepEl.querySelector('.proc-icon');
        const progressBar = stepEl.querySelector('.progress-fill');

        // Add log entry
        addLog(`Starting: ${stepEl.querySelector('h4').textContent}`);

        // Animate progress
        let progress = 0;
        const interval = setInterval(() => {
            progress += 100 / (duration / 50);
            progressBar.style.width = Math.min(progress, 100) + '%';
        }, 50);

        setTimeout(() => {
            clearInterval(interval);
            progressBar.style.width = '100%';
            icon.textContent = '✅';
            stepEl.classList.add('completed');
            addLog(`Completed: ${stepEl.querySelector('h4').textContent}`);
            resolve();
        }, duration);
    });
}

function addLog(message) {
    const logContent = document.getElementById('log-content');
    const timestamp = new Date().toLocaleTimeString();
    logContent.textContent += `\n[${timestamp}] ${message}`;
    logContent.scrollTop = logContent.scrollHeight;
}

// ==================== Results Display ====================

function generateMockResults(config) {
    // Generate realistic mock data
    const contrailPixels = Math.floor(Math.random() * 5000) + 100;
    const contrailCoverage = (contrailPixels / (256 * 256) * 100).toFixed(2);
    const contrailArea = (contrailPixels * 4).toFixed(1); // Assume 2km per pixel

    const flightDistance = Math.random() * 2000 + 500;
    const fuelBurn = flightDistance * (2.5 + Math.random() * 2);
    const co2Direct = fuelBurn * 3.16;
    const co2Contrail = contrailPixels * 100 + Math.random() * 10000;
    const co2Total = co2Direct + co2Contrail;

    const marketPrices = {
        'EU_ETS': 95,
        'CORSIA': 20,
        'CHINA': 11,
        'UK_ETS': 55,
        'CALIFORNIA': 32
    };

    const carbonPrice = marketPrices[config.carbon_market];
    const carbonCost = (co2Total / 1000) * carbonPrice;

    return {
        contrail: {
            pixels: contrailPixels,
            coverage: contrailCoverage,
            area: contrailArea,
            intensity: (0.5 + Math.random() * 0.5).toFixed(2)
        },
        emission: {
            distance: flightDistance.toFixed(1),
            fuel: fuelBurn.toFixed(1),
            co2_direct: co2Direct.toFixed(1),
            co2_contrail: co2Contrail.toFixed(1),
            co2_total: co2Total.toFixed(1)
        },
        carbon: {
            market: config.carbon_market,
            price: carbonPrice,
            cost_total: carbonCost.toFixed(2),
            cost_per_km: (carbonCost / flightDistance).toFixed(4)
        },
        flight: {
            callsign: config.flight_callsign,
            aircraft: ['A320', 'B737', 'A330', 'B777'][Math.floor(Math.random() * 4)],
            time: config.detection_time
        }
    };
}

function displayResults(results) {
    // Summary cards
    document.getElementById('result-coverage').textContent = results.contrail.coverage + '%';
    document.getElementById('result-co2').textContent = formatNumber(results.emission.co2_total) + ' kg';
    document.getElementById('result-cost').textContent = '$' + formatNumber(results.carbon.cost_total);
    document.getElementById('result-area').textContent = results.contrail.area + ' km²';

    // Flight information
    document.getElementById('data-callsign').textContent = results.flight.callsign;
    document.getElementById('data-aircraft').textContent = results.flight.aircraft;
    document.getElementById('data-distance').textContent = results.emission.distance + ' km';
    document.getElementById('data-time').textContent = new Date(results.flight.time).toLocaleString();

    // Emission data
    document.getElementById('data-fuel').textContent = formatNumber(results.emission.fuel) + ' kg';
    document.getElementById('data-co2-direct').textContent = formatNumber(results.emission.co2_direct) + ' kg';
    document.getElementById('data-co2-contrail').textContent = formatNumber(results.emission.co2_contrail) + ' kg';
    document.getElementById('data-co2-total').textContent = formatNumber(results.emission.co2_total) + ' kg';

    // Carbon data
    const marketNames = {
        'EU_ETS': 'EU ETS',
        'CORSIA': 'CORSIA',
        'CHINA': 'China ETS',
        'UK_ETS': 'UK ETS',
        'CALIFORNIA': 'California'
    };
    document.getElementById('data-market').textContent = marketNames[results.carbon.market];
    document.getElementById('data-price').textContent = '$' + results.carbon.price + '/tCO₂';
    document.getElementById('data-cost-km').textContent = '$' + results.carbon.cost_per_km + '/km';
    document.getElementById('data-cost-total').textContent = '$' + formatNumber(results.carbon.cost_total);

    // Always generate detailed report
    generateReport(results);

    // Display individual visualization images with error handling
    try {
        if (results.images) {
            console.log('Received images:', Object.keys(results.images));
            const imgElements = {
                'img-input': results.images.input,
                'img-probability': results.images.probability,
                'img-binary': results.images.binary,
                'img-fusion': results.images.fusion
            };

            for (const [id, data] of Object.entries(imgElements)) {
                const element = document.getElementById(id);
                if (element && data) {
                    element.src = 'data:image/png;base64,' + data;
                    console.log(`Set image for ${id}, data length: ${data.length}`);
                } else if (!element) {
                    console.warn(`Element with id '${id}' not found`);
                } else if (!data) {
                    console.warn(`No data for ${id}`);
                }
            }
        } else {
            console.warn('No images in results, using placeholders');
            setPlaceholderImages();
        }
    } catch (error) {
        console.error('Error displaying images:', error);
        setPlaceholderImages();
    }

    // Generate interactive charts
    try {
        generateCharts(results);
    } catch (error) {
        console.error('Error generating charts:', error);
    }

    // Generate strategy charts
    try {
        if (results.strategies) {
            generateStrategyCharts(results.strategies);
        }
    } catch (error) {
        console.error('Error generating strategy charts:', error);
    }
}

function generateReport(results) {
    const report = `
================================================================================
                  CONTRAIL DETECTION & EMISSION ANALYSIS REPORT
================================================================================

Analysis Date: ${new Date().toLocaleString()}
Flight: ${results.flight.callsign} (${results.flight.aircraft})

================================================================================
CONTRAIL DETECTION RESULTS
================================================================================

Coverage:           ${results.contrail.coverage}% of image
Contrail Area:      ${results.contrail.area} km²
Detection Pixels:   ${results.contrail.pixels}
Intensity:          ${results.contrail.intensity}

================================================================================
EMISSION ANALYSIS
================================================================================

Flight Distance:    ${results.emission.distance} km
Fuel Consumption:   ${formatNumber(results.emission.fuel)} kg

CO₂ Emissions:
  - Direct CO₂:     ${formatNumber(results.emission.co2_direct)} kg
  - Contrail CO₂eq: ${formatNumber(results.emission.co2_contrail)} kg
  - TOTAL CO₂eq:    ${formatNumber(results.emission.co2_total)} kg

================================================================================
CARBON TRADING ANALYSIS
================================================================================

Carbon Market:      ${results.carbon.market}
Carbon Price:       $${results.carbon.price}/tCO₂

Trading Costs:
  - Total Cost:     $${formatNumber(results.carbon.cost_total)}
  - Cost per km:    $${results.carbon.cost_per_km}/km

Environmental Equivalent:
  - Trees to offset: ${Math.floor(results.emission.co2_total / 21)} trees/year
  - Car miles equiv: ${Math.floor(results.emission.co2_total / 0.404)} miles

================================================================================
RECOMMENDATIONS
================================================================================

1. Route Optimization: Consider alternative flight paths to reduce contrail
   formation in high-impact regions.

2. Carbon Offsetting: Purchase ${(results.emission.co2_total / 1000).toFixed(2)} tonnes of carbon credits
   at estimated cost of $${formatNumber(results.carbon.cost_total)}.

3. Operational Efficiency: Fuel consumption can be optimized through altitude
   adjustments and speed optimization.

================================================================================
Generated by TrailSyncPioneers AI Platform
© 2025 TrailSyncPioneers. All rights reserved.
================================================================================
    `;

    document.getElementById('report-content').textContent = report.trim();
}

function setPlaceholderImages() {
    // In production, these would be actual analysis result images
    const placeholder = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400"><rect fill="%23f0f0f0" width="400" height="400"/><text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" font-family="Arial" font-size="20" fill="%23999">Analysis Result Image</text></svg>';

    const imageIds = ['img-input', 'img-probability', 'img-binary', 'img-fusion'];

    imageIds.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.src = placeholder;
        }
    });
}

// ==================== Tab Management ====================

function showTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');

    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`tab-${tabName}`).classList.add('active');

    // If switching to strategy tab, regenerate charts to ensure proper rendering
    if (tabName === 'strategy' && strategyData) {
        console.log('Strategy tab activated, regenerating charts...');
        setTimeout(() => {
            updateStrategyChart();
        }, 100);
    }
}

// ==================== Download Functions ====================

function downloadReport() {
    const reportText = document.getElementById('report-content').textContent;
    const blob = new Blob([reportText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `contrail-analysis-report-${Date.now()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function downloadAllResults() {
    if (!analysisResults || !analysisResults.session_id) {
        alert('No analysis results available to download.');
        return;
    }

    // Download ZIP from backend
    const API_URL = `/api/download/${analysisResults.session_id}`;
    window.open(API_URL, '_blank');
}

// ==================== Reset ====================

function resetAnalysis() {
    if (confirm('Start a new analysis? This will clear all current results.')) {
        // Reset uploaded files
        uploadedFiles = {
            band11: null,
            band14: null,
            band15: null
        };

        // Reset file inputs
        document.querySelectorAll('.file-input').forEach(input => {
            input.value = '';
        });

        // Reset file statuses
        document.querySelectorAll('.file-status').forEach(status => {
            status.textContent = 'No file selected';
            status.className = 'file-status';
        });

        // Reset labels
        document.querySelectorAll('.upload-text').forEach(text => {
            text.textContent = 'Choose file';
        });

        // Reset form
        document.getElementById('flight-callsign').value = '';
        document.getElementById('min-lat').value = '';
        document.getElementById('max-lat').value = '';
        document.getElementById('min-lon').value = '';
        document.getElementById('max-lon').value = '';
        document.getElementById('threshold').value = '0.5';
        document.getElementById('threshold-value').textContent = '0.5';
        setDefaultDateTime();

        // Reset results
        analysisResults = null;

        // Go back to step 1
        goToStep(1);
    }
}

// ==================== Utility Functions ====================

function formatNumber(num) {
    return parseFloat(num).toLocaleString('en-US', { maximumFractionDigits: 1 });
}

// ==================== Charts ====================

let chartInstances = {};

function generateCharts(results) {
    console.log('generateCharts called');

    // Check if Chart.js is loaded
    if (typeof Chart === 'undefined') {
        console.error('Chart.js library is not loaded. Charts will not be displayed.');
        // Hide charts section and show error message
        const chartsSection = document.querySelector('.charts-section');
        if (chartsSection) {
            chartsSection.innerHTML = '<div style="padding: 20px; background: #fff3cd; border: 1px solid #ffc107; border-radius: 8px; text-align: center;">' +
                '<h3 style="color: #856404;">Chart library loading failed</h3>' +
                '<p style="color: #856404;">Interactive charts are temporarily unavailable. All data is still available in the tables above.</p>' +
                '<p style="color: #856404; font-size: 0.9em;">Tip: Check your internet connection or try refreshing the page.</p>' +
                '</div>';
        }
        return;
    }

    console.log('Chart.js is loaded, version:', Chart.version);
    console.log('ChartDataLabels plugin:', typeof ChartDataLabels !== 'undefined' ? 'loaded' : 'NOT loaded');

    // Destroy existing charts
    Object.values(chartInstances).forEach(chart => chart.destroy());
    chartInstances = {};

    console.log('Creating charts...');

    // Chart 1: Emission Breakdown Pie Chart
    const emissionCtx = document.getElementById('emissionChart');
    if (!emissionCtx) {
        console.error('emissionChart canvas not found');
        return;
    }

    chartInstances.emission = new Chart(emissionCtx.getContext('2d'), {
        type: 'pie',
        data: {
            labels: ['Direct CO₂', 'Contrail CO₂eq'],
            datasets: [{
                data: [
                    parseFloat(results.emission.co2_direct),
                    parseFloat(results.emission.co2_contrail)
                ],
                backgroundColor: ['#667eea', '#f56565'],
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        font: { size: 13 },
                        padding: 15
                    }
                },
                title: {
                    display: true,
                    text: `Total: ${formatNumber(results.emission.co2_total)} kg CO₂eq`,
                    font: { size: 16, weight: 'bold' },
                    color: '#2d3748',
                    padding: { bottom: 15 }
                },
                datalabels: {
                    color: '#fff',
                    font: {
                        size: 14,
                        weight: 'bold'
                    },
                    formatter: function(value, context) {
                        const total = context.dataset.data.reduce((a, b) => a + b, 0);
                        const percentage = ((value / total) * 100).toFixed(1);
                        return percentage + '%';
                    }
                }
            }
        },
        plugins: [ChartDataLabels]
    });
    console.log('Emission chart created');

    // Chart 2: Carbon Cost Analysis Bar Chart
    const carbonCanvas = document.getElementById('carbonChart');
    if (!carbonCanvas) {
        console.error('carbonChart canvas not found');
        return;
    }
    const carbonCtx = carbonCanvas.getContext('2d');
    const gradient3 = carbonCtx.createLinearGradient(0, 0, 0, 400);
    gradient3.addColorStop(0, '#4facfe');
    gradient3.addColorStop(1, '#00f2fe');
    const gradient4 = carbonCtx.createLinearGradient(0, 0, 0, 400);
    gradient4.addColorStop(0, '#fa709a');
    gradient4.addColorStop(1, '#fee140');
    const gradient5 = carbonCtx.createLinearGradient(0, 0, 0, 400);
    gradient5.addColorStop(0, '#a8edea');
    gradient5.addColorStop(1, '#fed6e3');

    chartInstances.carbon = new Chart(carbonCtx, {
        type: 'bar',
        data: {
            labels: ['Total Cost', 'Cost per km × 100', 'Cost per Passenger'],
            datasets: [{
                label: 'USD ($)',
                data: [
                    parseFloat(results.carbon.cost_total),
                    parseFloat(results.carbon.cost_per_km) * 100,
                    parseFloat(results.carbon.cost_per_passenger)
                ],
                backgroundColor: [gradient3, gradient4, gradient5],
                borderWidth: 0,
                borderRadius: 8,
                borderSkipped: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                title: {
                    display: true,
                    text: `Market: ${results.carbon.market} @ $${results.carbon.price}/tCO₂`,
                    font: { size: 16, weight: 'bold' },
                    color: '#2d3748',
                    padding: { bottom: 20 }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    titleFont: { size: 14, weight: 'bold' },
                    bodyFont: { size: 13 },
                    cornerRadius: 8
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    },
                    ticks: {
                        font: { size: 12 },
                        callback: function(value) {
                            return '$' + value.toFixed(2);
                        }
                    }
                },
                x: {
                    grid: { display: false },
                    ticks: { font: { size: 12, weight: '600' } }
                }
            }
        }
    });

    // Chart 3: Contrail Coverage Pie Chart
    const contrailCtx = document.getElementById('contrailChart');
    if (!contrailCtx) {
        console.error('contrailChart canvas not found');
        return;
    }
    const coverage = parseFloat(results.contrail.coverage);

    chartInstances.contrail = new Chart(contrailCtx.getContext('2d'), {
        type: 'pie',
        data: {
            labels: ['Contrail Coverage', 'Clear Sky'],
            datasets: [{
                data: [coverage, 100 - coverage],
                backgroundColor: ['#ff6b6b', '#e2e8f0'],
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        font: { size: 13 },
                        padding: 15
                    }
                },
                title: {
                    display: true,
                    text: `Coverage: ${results.contrail.area} km²`,
                    font: { size: 16, weight: 'bold' },
                    color: '#2d3748',
                    padding: { bottom: 15 }
                },
                datalabels: {
                    color: '#fff',
                    font: {
                        size: 14,
                        weight: 'bold'
                    },
                    formatter: function(value) {
                        return value.toFixed(2) + '%';
                    }
                }
            }
        },
        plugins: [ChartDataLabels]
    });
    console.log('Contrail chart created');

    // Chart 4: Environmental Impact (Horizontal Bar with gradient)
    const treesNeeded = Math.floor(parseFloat(results.emission.co2_total) / 21);
    const carMiles = Math.floor(parseFloat(results.emission.co2_total) / 0.404);

    const impactCanvas = document.getElementById('impactChart');
    if (!impactCanvas) {
        console.error('impactChart canvas not found');
        return;
    }
    const impactCtx = impactCanvas.getContext('2d');
    const gradient7 = impactCtx.createLinearGradient(0, 0, 400, 0);
    gradient7.addColorStop(0, '#56ab2f');
    gradient7.addColorStop(1, '#a8e063');
    const gradient8 = impactCtx.createLinearGradient(0, 0, 400, 0);
    gradient8.addColorStop(0, '#ff512f');
    gradient8.addColorStop(1, '#f09819');

    chartInstances.impact = new Chart(impactCtx, {
        type: 'bar',
        data: {
            labels: ['🌳 Trees (annual)', '🚗 Car Miles ÷ 100'],
            datasets: [{
                label: 'Environmental Equivalent',
                data: [treesNeeded, carMiles / 100],
                backgroundColor: [gradient7, gradient8],
                borderWidth: 0,
                borderRadius: 8,
                borderSkipped: false
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                title: {
                    display: true,
                    text: 'Environmental Impact Equivalents',
                    font: { size: 16, weight: 'bold' },
                    color: '#2d3748',
                    padding: { bottom: 20 }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    titleFont: { size: 14, weight: 'bold' },
                    bodyFont: { size: 13 },
                    cornerRadius: 8,
                    callbacks: {
                        label: function(context) {
                            const label = context.label.includes('Trees') ?
                                treesNeeded + ' trees/year to offset' :
                                carMiles + ' car miles equivalent';
                            return label;
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    },
                    ticks: { font: { size: 12 } }
                },
                y: {
                    grid: { display: false },
                    ticks: { font: { size: 13, weight: '600' } }
                }
            }
        }
    });
    console.log('Impact chart created');
    console.log('All 4 charts created successfully!');
}

// ==================== Strategy Charts ====================

let strategyData = null;

function generateStrategyCharts(strategies) {
    console.log('generateStrategyCharts called with', strategies ? strategies.length : 0, 'markets');
    strategyData = strategies;

    // Initialize strategy controls
    const marketSelect = document.getElementById('strategy-market');
    const altitudeSlider = document.getElementById('strategy-altitude');

    if (!marketSelect || !altitudeSlider) {
        console.warn('Strategy controls not found in DOM');
        return;
    }

    updateStrategyChart();
}

function updateAltitudeDisplay(value) {
    const element = document.getElementById('altitude-value');
    if (element) {
        element.textContent = value;
    }
}

function updateStrategyChart() {
    if (!strategyData) {
        console.warn('No strategy data available');
        return;
    }

    if (typeof Chart === 'undefined') {
        console.error('Chart.js not loaded');
        return;
    }

    console.log('Updating strategy charts...');

    const selectedMarket = document.getElementById('strategy-market').value;
    const selectedAltitude = parseInt(document.getElementById('strategy-altitude').value);

    const marketData = strategyData.find(s => s.market === selectedMarket);
    if (!marketData) return;

    // Chart 1: Cost vs Altitude for selected market
    const altitudeCostCtx = document.getElementById('altitudeCostChart');
    if (altitudeCostCtx) {
        if (chartInstances.altitudeCost) chartInstances.altitudeCost.destroy();

        const ctx = altitudeCostCtx.getContext('2d');
        const gradient9 = ctx.createLinearGradient(0, 0, 0, 400);
        gradient9.addColorStop(0, '#667eea');
        gradient9.addColorStop(1, '#764ba2');

        chartInstances.altitudeCost = new Chart(ctx, {
            type: 'line',
            data: {
                labels: marketData.altitudes.map(a => a.altitude + 'm'),
                datasets: [{
                    label: 'Carbon Cost (USD)',
                    data: marketData.altitudes.map(a => a.cost_total),
                    borderColor: '#667eea',
                    backgroundColor: gradient9,
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 6,
                    pointHoverRadius: 8,
                    pointBackgroundColor: '#fff',
                    pointBorderWidth: 3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    title: {
                        display: true,
                        text: `${selectedMarket} - Cost Impact by Altitude`,
                        font: { size: 16, weight: 'bold' },
                        color: '#2d3748'
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        padding: 12,
                        cornerRadius: 8
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(0, 0, 0, 0.05)' },
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toFixed(0);
                            }
                        }
                    },
                    x: {
                        grid: { display: false }
                    }
                }
            }
        });
    }

    // Chart 2: Market Comparison at selected altitude
    const marketCompCtx = document.getElementById('marketComparisonChart');
    if (marketCompCtx) {
        if (chartInstances.marketComp) chartInstances.marketComp.destroy();

        const altIndex = marketData.altitudes.findIndex(a => a.altitude === selectedAltitude);
        const costs = strategyData.map(m => m.altitudes[altIndex]?.cost_total || 0);
        const labels = strategyData.map(m => m.market);

        const ctx = marketCompCtx.getContext('2d');
        chartInstances.marketComp = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Carbon Cost (USD)',
                    data: costs,
                    backgroundColor: [
                        '#667eea', '#f093fb', '#4facfe', '#fa709a', '#a8edea'
                    ],
                    borderWidth: 0,
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    title: {
                        display: true,
                        text: `Market Comparison at ${selectedAltitude}m`,
                        font: { size: 16, weight: 'bold' },
                        color: '#2d3748'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(0, 0, 0, 0.05)' },
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toFixed(0);
                            }
                        }
                    },
                    x: { grid: { display: false } }
                }
            }
        });
    }

    // Chart 3: CO2 vs Altitude
    const co2AltCtx = document.getElementById('co2AltitudeChart');
    if (co2AltCtx) {
        if (chartInstances.co2Alt) chartInstances.co2Alt.destroy();

        const ctx = co2AltCtx.getContext('2d');
        const gradient10 = ctx.createLinearGradient(0, 0, 0, 400);
        gradient10.addColorStop(0, '#f093fb');
        gradient10.addColorStop(1, '#f5576c');

        chartInstances.co2Alt = new Chart(ctx, {
            type: 'line',
            data: {
                labels: marketData.altitudes.map(a => a.altitude + 'm'),
                datasets: [{
                    label: 'CO₂ Emissions (kg)',
                    data: marketData.altitudes.map(a => a.co2_total),
                    borderColor: '#f5576c',
                    backgroundColor: gradient10,
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 6,
                    pointHoverRadius: 8,
                    pointBackgroundColor: '#fff',
                    pointBorderWidth: 3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    title: {
                        display: true,
                        text: 'CO₂ Emissions by Flight Altitude',
                        font: { size: 16, weight: 'bold' },
                        color: '#2d3748'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(0, 0, 0, 0.05)' },
                        ticks: {
                            callback: function(value) {
                                return value.toLocaleString() + ' kg';
                            }
                        }
                    },
                    x: { grid: { display: false } }
                }
            }
        });
    }

    // Chart 4: Heatmap (simulate with bar chart)
    const heatmapCtx = document.getElementById('heatmapChart');
    if (heatmapCtx) {
        if (chartInstances.heatmap) chartInstances.heatmap.destroy();

        // Find optimal (lowest cost) market
        const altIndex = marketData.altitudes.findIndex(a => a.altitude === selectedAltitude);
        const costs = strategyData.map(m => ({
            market: m.market,
            cost: m.altitudes[altIndex]?.cost_total || 0
        }));
        costs.sort((a, b) => a.cost - b.cost);

        chartInstances.heatmap = new Chart(heatmapCtx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: costs.map(c => c.market),
                datasets: [{
                    label: 'Cost Ranking (Low to High)',
                    data: costs.map(c => c.cost),
                    backgroundColor: costs.map((_, i) => {
                        const ratio = i / (costs.length - 1);
                        return `rgba(${255 * ratio}, ${255 * (1 - ratio)}, 100, 0.8)`;
                    }),
                    borderWidth: 0,
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    title: {
                        display: true,
                        text: 'Cost Ranking by Market',
                        font: { size: 16, weight: 'bold' },
                        color: '#2d3748'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(0, 0, 0, 0.05)' },
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toFixed(0);
                            }
                        }
                    },
                    x: { grid: { display: false } }
                }
            }
        });
    }

    // Update recommendations
    updateStrategyRecommendations(strategyData, selectedMarket, selectedAltitude);
}

function updateStrategyRecommendations(strategies, selectedMarket, selectedAlt) {
    const container = document.getElementById('strategy-recommendations-content');
    if (!container) return;

    // Find optimal altitude for selected market
    const marketData = strategies.find(s => s.market === selectedMarket);
    if (!marketData) return;

    const minCost = Math.min(...marketData.altitudes.map(a => a.cost_total));
    const optimalAlt = marketData.altitudes.find(a => a.cost_total === minCost);

    // Find optimal market at selected altitude
    const altIndex = marketData.altitudes.findIndex(a => a.altitude === selectedAlt);
    const allCosts = strategies.map(s => ({
        market: s.market,
        cost: s.altitudes[altIndex]?.cost_total || Infinity
    }));
    const optimalMarket = allCosts.reduce((min, curr) => curr.cost < min.cost ? curr : min);

    const currentAltData = marketData.altitudes.find(a => a.altitude === selectedAlt);

    container.innerHTML = `
        <p><strong>📊 Current Configuration:</strong> ${selectedMarket} at ${selectedAlt}m altitude</p>
        <p><strong>💰 Current Cost:</strong> $${currentAltData.cost_total.toFixed(2)} (CO₂: ${currentAltData.co2_total.toLocaleString()} kg)</p>
        <hr style="border: 1px solid rgba(255,255,255,0.3); margin: 15px 0;">
        <p><strong>✅ Optimal Altitude for ${selectedMarket}:</strong> ${optimalAlt.altitude}m</p>
        <p style="margin-left: 20px;">Estimated Cost: $${minCost.toFixed(2)} (Savings: $${(currentAltData.cost_total - minCost).toFixed(2)})</p>
        <p><strong>✅ Optimal Market at ${selectedAlt}m:</strong> ${optimalMarket.market}</p>
        <p style="margin-left: 20px;">Estimated Cost: $${optimalMarket.cost.toFixed(2)} (Savings: $${(currentAltData.cost_total - optimalMarket.cost).toFixed(2)})</p>
        <hr style="border: 1px solid rgba(255,255,255,0.3); margin: 15px 0;">
        <p><strong>💡 Recommendations:</strong></p>
        <ul style="margin-left: 20px; line-height: 1.8;">
            <li>${selectedAlt > optimalAlt.altitude ? 'Consider flying at lower altitude to reduce contrail formation' : 'Current altitude is optimal for minimizing costs'}</li>
            <li>${optimalMarket.market !== selectedMarket ? `Consider ${optimalMarket.market} market for better carbon pricing` : 'Current market selection is optimal'}</li>
            <li>Monitor weather conditions for ice supersaturation to avoid contrail-prone regions</li>
        </ul>
    `;
}

// ==================== Image Modal ====================

function openImageModal(src) {
    const modal = document.getElementById('imageModal');
    const modalImg = document.getElementById('modalImage');
    modal.classList.add('active');
    modalImg.src = src;
}

function closeImageModal() {
    const modal = document.getElementById('imageModal');
    modal.classList.remove('active');
}
