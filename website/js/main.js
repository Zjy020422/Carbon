/**
 * ContrailTracker Website - Main JavaScript
 * Interactive functionality and animations
 */

// ==================== Initialization ====================
document.addEventListener('DOMContentLoaded', function() {
    initializeAOS();
    initializeNavigation();
    initializeHeroAnimations();
    initializeDemoTabs();
    initializeContactForm();
    initializeParticles();
});

// ==================== AOS Animation ====================
function initializeAOS() {
    AOS.init({
        duration: 800,
        easing: 'ease-out-cubic',
        once: true,
        offset: 100
    });
}

// ==================== Navigation ====================
function initializeNavigation() {
    const navbar = document.getElementById('navbar');
    const hamburger = document.getElementById('hamburger');
    const navMenu = document.getElementById('nav-menu');
    const navLinks = document.querySelectorAll('.nav-link');

    // Scroll effect
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    });

    // Mobile menu toggle
    hamburger.addEventListener('click', () => {
        navMenu.classList.toggle('active');
        hamburger.classList.toggle('active');
    });

    // Close mobile menu on link click
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            navMenu.classList.remove('active');
            hamburger.classList.remove('active');
        });
    });

    // Smooth scroll
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const targetSection = document.querySelector(targetId);

            if (targetSection) {
                const offsetTop = targetSection.offsetTop - 80;
                window.scrollTo({
                    top: offsetTop,
                    behavior: 'smooth'
                });
            }
        });
    });

    // Active nav link highlight
    window.addEventListener('scroll', () => {
        let current = '';
        const sections = document.querySelectorAll('section');

        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.clientHeight;
            if (window.scrollY >= (sectionTop - 200)) {
                current = section.getAttribute('id');
            }
        });

        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === `#${current}`) {
                link.classList.add('active');
            }
        });
    });
}

// ==================== Hero Animations ====================
function initializeHeroAnimations() {
    // Animated counter
    const stats = document.querySelectorAll('.stat-number');

    const animateValue = (element, start, end, duration) => {
        const range = end - start;
        const increment = end > start ? 1 : -1;
        const stepTime = Math.abs(Math.floor(duration / range));
        let current = start;

        const timer = setInterval(() => {
            current += increment;
            element.textContent = current;
            if (current === end) {
                clearInterval(timer);
                // Add decimal for the 98.9% stat
                if (end === 98.9) {
                    element.textContent = '98.9';
                }
            }
        }, stepTime);
    };

    // Observer for stats animation
    const statsObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const target = parseFloat(entry.target.dataset.target);
                const isDecimal = target % 1 !== 0;

                if (isDecimal) {
                    // For 98.9, animate to 98 then set to 98.9
                    animateValue(entry.target, 0, 98, 2000);
                    setTimeout(() => {
                        entry.target.textContent = '98.9';
                    }, 2000);
                } else {
                    animateValue(entry.target, 0, target, 2000);
                }

                statsObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.5 });

    stats.forEach(stat => {
        statsObserver.observe(stat);
    });
}

// ==================== Demo Tabs ====================
function initializeDemoTabs() {
    const demoTabs = document.querySelectorAll('.demo-tab');
    const demoContents = document.querySelectorAll('.demo-content');

    demoTabs.forEach((tab, index) => {
        tab.addEventListener('click', () => {
            // Remove active class from all tabs and contents
            demoTabs.forEach(t => t.classList.remove('active'));
            demoContents.forEach(c => c.classList.remove('active'));

            // Add active class to clicked tab and corresponding content
            tab.classList.add('active');
            const tabName = tab.dataset.tab;
            document.getElementById(`${tabName}-tab`).classList.add('active');
        });
    });

    // Run Analysis button
    const runAnalysisBtn = document.getElementById('run-analysis');
    if (runAnalysisBtn) {
        runAnalysisBtn.addEventListener('click', function() {
            // Show loading state
            const originalText = this.innerHTML;
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analyzing...';
            this.disabled = true;

            // Simulate API call
            setTimeout(() => {
                this.innerHTML = '<i class="fas fa-check"></i> Analysis Complete';
                setTimeout(() => {
                    this.innerHTML = originalText;
                    this.disabled = false;
                }, 2000);
            }, 3000);
        });
    }

    // File upload handlers
    const satelliteUpload = document.getElementById('satellite-upload');
    const flightUpload = document.getElementById('flight-upload');

    if (satelliteUpload) {
        satelliteUpload.addEventListener('change', function(e) {
            const fileName = e.target.files[0]?.name;
            if (fileName) {
                const label = this.nextElementSibling;
                const span = label.querySelector('span');
                span.textContent = fileName;
            }
        });
    }

    if (flightUpload) {
        flightUpload.addEventListener('change', function(e) {
            const fileName = e.target.files[0]?.name;
            if (fileName) {
                const label = this.nextElementSibling;
                const span = label.querySelector('span');
                span.textContent = fileName;
            }
        });
    }
}

// ==================== Contact Form ====================
function initializeContactForm() {
    const contactForm = document.getElementById('contact-form');

    if (contactForm) {
        contactForm.addEventListener('submit', async function(e) {
            e.preventDefault();

            const submitBtn = this.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;

            // Show loading state
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';
            submitBtn.disabled = true;

            // Get form data
            const formData = new FormData(this);
            const data = {
                name: this.querySelector('input[type="text"]').value,
                email: this.querySelector('input[type="email"]').value,
                company: this.querySelectorAll('input[type="text"]')[1].value,
                interest: this.querySelector('select').value,
                message: this.querySelector('textarea').value
            };

            try {
                // Send to backend API
                const response = await fetch('/api/contact', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                });

                if (response.ok) {
                    submitBtn.innerHTML = '<i class="fas fa-check"></i> Message Sent!';
                    submitBtn.style.background = '#00cc66';

                    // Reset form
                    this.reset();

                    // Show success message
                    showNotification('Thank you! We will get back to you soon.', 'success');
                } else {
                    throw new Error('Failed to send message');
                }
            } catch (error) {
                submitBtn.innerHTML = '<i class="fas fa-exclamation-circle"></i> Error';
                submitBtn.style.background = '#ff3333';
                showNotification('Failed to send message. Please try again.', 'error');
            }

            // Reset button after 3 seconds
            setTimeout(() => {
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
                submitBtn.style.background = '';
            }, 3000);
        });
    }
}

// ==================== Notification System ====================
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.style.cssText = `
        position: fixed;
        top: 100px;
        right: 20px;
        background: ${type === 'success' ? '#00cc66' : '#ff3333'};
        color: white;
        padding: 16px 24px;
        border-radius: 8px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.3);
        z-index: 10000;
        animation: slideIn 0.3s ease;
    `;
    notification.textContent = message;

    // Add to page
    document.body.appendChild(notification);

    // Remove after 5 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 5000);
}

// ==================== Particles Background ====================
function initializeParticles() {
    const particlesContainer = document.getElementById('particles');

    if (particlesContainer) {
        const particleCount = 50;

        for (let i = 0; i < particleCount; i++) {
            const particle = document.createElement('div');
            particle.className = 'particle';

            const size = Math.random() * 4 + 1;
            const x = Math.random() * 100;
            const y = Math.random() * 100;
            const duration = Math.random() * 20 + 10;
            const delay = Math.random() * 5;

            particle.style.cssText = `
                position: absolute;
                width: ${size}px;
                height: ${size}px;
                background: rgba(0, 204, 102, ${Math.random() * 0.5 + 0.2});
                border-radius: 50%;
                left: ${x}%;
                top: ${y}%;
                animation: float ${duration}s ${delay}s infinite ease-in-out;
            `;

            particlesContainer.appendChild(particle);
        }
    }
}

// ==================== API Integration ====================
class ContrailTrackerAPI {
    constructor(baseURL = 'http://localhost:5000/api') {
        this.baseURL = baseURL;
    }

    async analyzeContrail(satelliteFile, flightFile) {
        const formData = new FormData();
        formData.append('satellite_data', satelliteFile);
        formData.append('flight_data', flightFile);

        try {
            const response = await fetch(`${this.baseURL}/analyze/contrail`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) throw new Error('Analysis failed');
            return await response.json();
        } catch (error) {
            console.error('Contrail analysis error:', error);
            throw error;
        }
    }

    async calculateEmissions(flightData, carbonMarket = 'EU_ETS') {
        try {
            const response = await fetch(`${this.baseURL}/analyze/emissions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    flight_data: flightData,
                    carbon_market: carbonMarket
                })
            });

            if (!response.ok) throw new Error('Emission calculation failed');
            return await response.json();
        } catch (error) {
            console.error('Emission calculation error:', error);
            throw error;
        }
    }

    async compareCarbonMarkets(emissions) {
        try {
            const response = await fetch(`${this.baseURL}/analyze/carbon-markets`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ emissions })
            });

            if (!response.ok) throw new Error('Market comparison failed');
            return await response.json();
        } catch (error) {
            console.error('Market comparison error:', error);
            throw error;
        }
    }
}

// Initialize API client
const api = new ContrailTrackerAPI();

// ==================== CSS Animations ====================
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }

    @keyframes float {
        0%, 100% {
            transform: translateY(0) translateX(0);
        }
        25% {
            transform: translateY(-20px) translateX(10px);
        }
        50% {
            transform: translateY(0) translateX(20px);
        }
        75% {
            transform: translateY(20px) translateX(10px);
        }
    }

    @keyframes pulse {
        0%, 100% {
            opacity: 1;
        }
        50% {
            opacity: 0.5;
        }
    }
`;
document.head.appendChild(style);

// ==================== Utility Functions ====================
function formatNumber(num) {
    return new Intl.NumberFormat('en-US').format(num);
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

function formatDate(date) {
    return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    }).format(new Date(date));
}

// ==================== Export for use in other scripts ====================
window.ContrailTracker = {
    api,
    showNotification,
    formatNumber,
    formatCurrency,
    formatDate
};
