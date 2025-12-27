// Main JavaScript file for the application

document.addEventListener('DOMContentLoaded', function() {
    console.log('Application loaded successfully');

    // Add active class to current navigation item
    setActiveNavItem();

    // Add smooth scrolling for anchor links
    addSmoothScrolling();
});

/**
 * Highlight the current page in navigation
 */
function setActiveNavItem() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-menu a');

    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.style.fontWeight = 'bold';
            link.style.textDecoration = 'underline';
        }
    });
}

/**
 * Add smooth scrolling behavior to anchor links
 */
function addSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
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
}

/**
 * Check application health
 */
async function checkHealth() {
    try {
        const response = await fetch('/api/health');
        const data = await response.json();
        console.log('Health check:', data);
        return data;
    } catch (error) {
        console.error('Health check failed:', error);
        return null;
    }
}

// Export functions for use in other scripts
window.app = {
    checkHealth
};
