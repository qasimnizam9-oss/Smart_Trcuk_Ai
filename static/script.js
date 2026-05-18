/**
 * Smart Truck AI - Main Application Script
 * Handles: Sidebar Navigation, Tab Switching, Booking, Truck Matching
 * Version: Professional
 */

'use strict';

/* ============================
   GLOBAL STATE
   ============================ */
let currentBookingData = null;

/* ============================
   DOM UTILITIES
   ============================ */
const DOM = {
    get: (id) => document.getElementById(id),
    query: (sel) => document.querySelector(sel),
    queryAll: (sel) => document.querySelectorAll(sel),
    show: (el) => { if (el) el.style.display = 'block'; },
    hide: (el) => { if (el) el.style.display = 'none'; },
    setText: (id, text) => {
        const el = document.getElementById(id);
        if (el) el.innerText = text;
    }
};

/* ============================
   SIDEBAR & TAB NAVIGATION
   ============================ */
function initSidebar() {
    const toggleBtn = DOM.query('.sidebar-toggle, #sidebarToggle, .menu-toggle');
    const sidebar = DOM.query('.sidebar, #sidebar');
    const navLinks = DOM.queryAll('.nav-link[data-tab], .sidebar-link[data-tab], .tab-link');
    const contents = DOM.queryAll('.tab-content, .dashboard-tab');

    // Mobile sidebar toggle (hamburger menu)
    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', (e) => {
            e.preventDefault();
            sidebar.classList.toggle('active');
            sidebar.classList.toggle('open');
            document.body.classList.toggle('sidebar-open');
        });
    }

    // Tab switching logic
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            const tabId = link.getAttribute('data-tab') || link.getAttribute('href')?.replace('#', '');
            if (!tabId) return;
            
            e.preventDefault();

            // Update active link state
            navLinks.forEach(l => {
                l.classList.remove('active');
                if (l.parentElement) l.parentElement.classList.remove('active');
            });
            link.classList.add('active');
            if (link.parentElement) link.parentElement.classList.add('active');

            // Switch content panels
            contents.forEach(content => {
                if (content.id === tabId || content.getAttribute('data-tab') === tabId) {
                    content.classList.add('active');
                    content.style.display = 'block';
                    content.style.opacity = '0';
                    requestAnimationFrame(() => {
                        content.style.transition = 'opacity 0.3s ease';
                        content.style.opacity = '1';
                    });
                } else {
                    content.classList.remove('active');
                    content.style.display = 'none';
                }
            });

            // Update URL hash without page jump
            history.pushState(null, null, `#${tabId}`);

            // Auto-close sidebar on mobile after selection
            if (window.innerWidth < 992 && sidebar) {
                sidebar.classList.remove('active', 'open');
                document.body.classList.remove('sidebar-open');
            }
        });
    });

    // Activate tab from URL hash on page load
    const hash = window.location.hash.replace('#', '');
    if (hash) {
        const activeLink = DOM.query(`.nav-link[data-tab="${hash}"], .sidebar-link[data-tab="${hash}"]`);
        if (activeLink) {
            activeLink.click();
            return;
        }
    }

    // Default: activate first tab if none is currently active
    const anyActive = DOM.query('.tab-content.active, .dashboard-tab.active');
    if (!anyActive && navLinks.length > 0) {
        navLinks[0].click();
    }
}

/* ============================
   BOOKING FORM
   ============================ */
function initBookingForm() {
    const form = DOM.get('bookingForm');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const pickupSelect = DOM.get('pickup').value;
        const [pickup_lat, pickup_lon, pickup_name] = pickupSelect.split(',');
        const weight = DOM.get('weight').value;
        const dropoff = DOM.get('dropoff').value;
        
        const resultBox = DOM.get('result');
        const errorBox = DOM.get('errorMessage');
        const loadingBox = DOM.get('loading');
        const submitBtn = DOM.get('submitBtn');
        
        // Reset view
        DOM.hide(resultBox);
        DOM.hide(errorBox);
        DOM.hide(form);
        DOM.show(loadingBox);

        try {
            // Simulate network delay for effect
            await new Promise(r => setTimeout(r, 1200));

            const response = await fetch('/match-truck', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    weight: parseFloat(weight),
                    pickup_lat: parseFloat(pickup_lat),
                    pickup_lon: parseFloat(pickup_lon)
                })
            });

            const data = await response.json();

            DOM.hide(loadingBox);

            if (response.ok && data.status === "Success") {
                DOM.setText('driverName', data.driver_name);
                DOM.setText('distance', data.distance_km);
                const score = data.ai_match_score || 95;
                DOM.setText('aiScore', score);
                DOM.setText('fare', data.estimated_fare);
                
                // Animate score bar
                setTimeout(() => {
                    const bar = DOM.get('scoreBar');
                    if (bar) bar.style.width = score + '%';
                }, 100);
                
                currentBookingData = {
                    pickup_loc: pickup_name || 'Lahore',
                    dropoff_loc: dropoff,
                    weight: parseFloat(weight),
                    fare: data.estimated_fare,
                    driver_name: data.driver_name
                };

                DOM.show(resultBox);
            } else {
                DOM.setText('errorText', data.message || "No suitable truck found.");
                DOM.show(errorBox);
                DOM.show(form); // Allow retry
            }
        } catch (error) {
            console.error("Error:", error);
            DOM.hide(loadingBox);
            DOM.setText('errorText', "Backend server offline! Please start app.py.");
            DOM.show(errorBox);
            DOM.show(form);
        }
    });
}

/* ============================
   CONFIRM BOOKING
   ============================ */
function initConfirmBooking() {
    const confirmBtn = DOM.get('confirmBookingBtn');
    if (!confirmBtn) return;

    confirmBtn.addEventListener('click', async () => {
        const userId = localStorage.getItem('smart_truck_user_id');
        if (!userId) {
            alert('Please login or create an account to confirm your booking.');
            window.location.href = '/user/auth';
            return;
        }

        const originalText = confirmBtn.innerText;
        confirmBtn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Confirming...';
        confirmBtn.disabled = true;

        try {
            const payload = { ...currentBookingData, user_id: parseInt(userId) };
            
            const response = await fetch('/api/user/book', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            
            const data = await response.json();
            
            if (response.ok) {
                window.location.href = `/user/checkout?booking_id=${data.booking_id}`;
            } else {
                alert('Failed to confirm booking: ' + data.message);
                confirmBtn.innerHTML = originalText;
                confirmBtn.disabled = false;
            }
        } catch (err) {
            console.error("Error confirming booking:", err);
            alert('Server error while confirming booking.');
            confirmBtn.innerHTML = originalText;
            confirmBtn.disabled = false;
        }
    });
}

/* ============================
   APP INITIALIZATION
   ============================ */
document.addEventListener('DOMContentLoaded', () => {
    console.log('[Smart Truck AI] Dashboard initialized successfully.');
    
    initSidebar();
    initBookingForm();
    initConfirmBooking();
    
    // Responsive: reset sidebar when resizing to desktop
    window.addEventListener('resize', () => {
        if (window.innerWidth >= 992) {
            document.body.classList.remove('sidebar-open');
            const sidebar = DOM.query('.sidebar, #sidebar');
            if (sidebar) sidebar.classList.remove('active', 'open');
        }
    });
});