// Hero Background Slideshow
function initHeroSlideshow() {
    const bgImages = document.querySelectorAll('.hero-bg-image');
    let currentIndex = 0;

    function changeBackground() {
        // Remove active class from current image
        bgImages[currentIndex].classList.remove('active');

        // Move to next image
        currentIndex = (currentIndex + 1) % bgImages.length;

        // Add active class to next image
        bgImages[currentIndex].classList.add('active');
    }

    // Change background every 5 seconds
    setInterval(changeBackground, 5000);
}

// Initialize slideshow and set loading state when page loads
window.addEventListener('load', () => {
    initHeroSlideshow();
    document.body.style.opacity = '1';
});

// Smooth scrolling for navigation links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Add active state to navigation links on scroll
window.addEventListener('scroll', () => {
    let current = '';
    const sections = document.querySelectorAll('section');
    const navLinks = document.querySelectorAll('.nav-menu a');

    sections.forEach(section => {
        const sectionTop = section.offsetTop;
        const sectionHeight = section.clientHeight;
        if (scrollY >= (sectionTop - 100)) {
            current = section.getAttribute('id');
        }
    });

    navLinks.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href').substring(1) === current) {
            link.classList.add('active');
        }
    });
});

// Add scroll effect to navbar
let lastScroll = 0;
const navbar = document.querySelector('.navbar');

window.addEventListener('scroll', () => {
    const currentScroll = window.pageYOffset;

    if (currentScroll > 100) {
        navbar.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.15)';
    } else {
        navbar.style.boxShadow = '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)';
    }

    lastScroll = currentScroll;
});

// Intersection Observer for fade-in animations
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

// Observe all cards and sections
document.querySelectorAll('.business-card, .team-member, .research-phase, .research-summary').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(30px)';
    el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
    observer.observe(el);
});

// Business Model Tabs Functionality
const tabButtons = document.querySelectorAll('.tab-button');
const tabContents = document.querySelectorAll('.tab-content');

tabButtons.forEach(button => {
    button.addEventListener('click', () => {
        const targetTab = button.getAttribute('data-tab');

        // Remove active class from all buttons and contents
        tabButtons.forEach(btn => btn.classList.remove('active'));
        tabContents.forEach(content => content.classList.remove('active'));

        // Add active class to clicked button and corresponding content
        button.classList.add('active');
        document.getElementById(targetTab).classList.add('active');
    });
});

// Consolidate loading state with slideshow initialization
// (Already handled in the earlier window load event)

// ========== Pricing Calculator Functionality ==========

// Service selection handler
const serviceRadios = document.querySelectorAll('input[name="service"]');
const pricingSections = document.querySelectorAll('.pricing-section');

serviceRadios.forEach(radio => {
    radio.addEventListener('change', function() {
        // Hide all pricing sections
        pricingSections.forEach(section => {
            section.classList.remove('active');
        });

        // Show selected pricing section
        const selectedService = this.value;
        document.getElementById(`${selectedService}-pricing`).classList.add('active');
    });
});

// SaaS Subscription Pricing Calculator
const fleetSizeSlider = document.getElementById('fleet-size');
const fleetSizeValue = document.getElementById('fleet-size-value');
const saasPrice = document.getElementById('saas-price');

function calculateSaaSPrice() {
    const fleetSize = parseInt(fleetSizeSlider.value);
    fleetSizeValue.textContent = fleetSize;

    // Price calculation: 50,000 base + (fleet size - 10) * 300
    // This gives a range from 50,000 (10 aircraft) to 200,000 (500 aircraft)
    const basePrice = 50000;
    const pricePerAircraft = 300;
    const calculatedPrice = basePrice + (fleetSize - 10) * pricePerAircraft;

    // Format price with thousand separators
    saasPrice.textContent = calculatedPrice.toLocaleString('zh-CN') + ' CNY';
}

if (fleetSizeSlider) {
    fleetSizeSlider.addEventListener('input', calculateSaaSPrice);
    calculateSaaSPrice(); // Initial calculation
}

// Professional Consulting Pricing
const projectComplexity = document.getElementById('project-complexity');
const consultingPrice = document.getElementById('consulting-price');

function updateConsultingPrice() {
    const prices = {
        'basic': 20000,
        'standard': 35000,
        'advanced': 50000
    };

    const selectedComplexity = projectComplexity.value;
    const price = prices[selectedComplexity];

    consultingPrice.textContent = price.toLocaleString('zh-CN') + ' CNY';
}

if (projectComplexity) {
    projectComplexity.addEventListener('change', updateConsultingPrice);
    updateConsultingPrice(); // Initial price
}

// API Data Access Pricing Calculator
const apiTier = document.getElementById('api-tier');
const tokenUsage = document.getElementById('token-usage');
const apiBaseFee = document.getElementById('api-base-fee');
const apiTokenCost = document.getElementById('api-token-cost');
const apiTotalPrice = document.getElementById('api-total-price');

function calculateAPIPrice() {
    const tierPrices = {
        'basic': 500,
        'professional': 2000,
        'enterprise': 5000
    };

    const selectedTier = apiTier.value;
    const baseFee = tierPrices[selectedTier];
    const tokens = parseInt(tokenUsage.value) || 0;

    // Token pricing: 0.75 CNY per token (average of 0.5-1 CNY)
    const tokenRate = 0.75;
    const tokenCost = tokens * tokenRate;
    const totalCost = baseFee + tokenCost;

    apiBaseFee.textContent = baseFee.toLocaleString('zh-CN') + ' CNY';
    apiTokenCost.textContent = tokenCost.toLocaleString('zh-CN') + ' CNY';
    apiTotalPrice.textContent = totalCost.toLocaleString('zh-CN') + ' CNY';
}

if (apiTier && tokenUsage) {
    apiTier.addEventListener('change', calculateAPIPrice);
    tokenUsage.addEventListener('input', calculateAPIPrice);
    calculateAPIPrice(); // Initial calculation
}

// ========== Interactive Data Table Functionality ==========

// Table tab switching
const tableTabButtons = document.querySelectorAll('.table-tab-btn');
const dataTableContainers = document.querySelectorAll('.data-table-container');

tableTabButtons.forEach(button => {
    button.addEventListener('click', function() {
        const targetTable = this.getAttribute('data-table');

        // Remove active class from all buttons and containers
        tableTabButtons.forEach(btn => btn.classList.remove('active'));
        dataTableContainers.forEach(container => container.classList.remove('active'));

        // Add active class to clicked button and corresponding container
        this.classList.add('active');
        document.getElementById(`${targetTable}-table`).classList.add('active');
    });
});
