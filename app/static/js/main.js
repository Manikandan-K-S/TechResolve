// Main JavaScript file for TechResolve

// Mobile menu toggle
document.addEventListener('DOMContentLoaded', function() {
    const mobileMenuButton = document.getElementById('mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');

    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener('click', function() {
            mobileMenu.classList.toggle('hidden');
        });
    }

    // Flash message auto-dismiss
    const flashMessages = document.querySelectorAll('.alert');
    flashMessages.forEach(function(message) {
        setTimeout(function() {
            const closeButton = message.querySelector('.btn-close');
            if (closeButton) {
                closeButton.click();
            }
        }, 5000);
    });
});

// Helper function for tracking complaint form
function trackComplaint(event) {
    event.preventDefault();
    const form = event.target;
    const complaintId = form.querySelector('input[name="complaint_id"]').value;
    const email = form.querySelector('input[name="email"]').value;
    
    if (!complaintId && !email) {
        alert('Please enter either a complaint ID or your email address.');
        return;
    }
    
    form.submit();
}