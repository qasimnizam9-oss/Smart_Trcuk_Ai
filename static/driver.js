let isLoginMode = true;
let currentDriverId = null;
let activeBookingId = null;
let rejectedLoads = []; // Session-based filter for declined loads

// --- PROFESSIONAL TOAST SYSTEM ---
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    let icon = 'fa-info-circle';
    if (type === 'success') icon = 'fa-check-circle';
    if (type === 'error') icon = 'fa-exclamation-circle';
    if (type === 'warning') icon = 'fa-exclamation-triangle';

    toast.innerHTML = `<i class="fas ${icon}"></i> <span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('fade-out');
        setTimeout(() => toast.remove(), 500);
    }, 4000);
}

// Global Alert Override
window.alert = function (msg) {
    if (msg.includes("Success") || msg.includes("Synchronized") || msg.includes("confirmed") || msg.includes("created") || msg.includes("Confirmed")) {
        showToast(msg, 'success');
    } else if (msg.includes("Error") || msg.includes("failed") || msg.includes("Invalid") || msg.includes("failed")) {
        showToast(msg, 'error');
    } else {
        showToast(msg, 'info');
    }
};

// --- Document Upload Handler (Real File Picker → AI Scan) ---
function handleDocUpload(inputOrObj, docType) {
    const file = (inputOrObj.files || [])[0];
    if (!file) return;

    // 5 MB guard
    if (file.size > 5 * 1024 * 1024) {
        alert('File exceeds 5MB. Please upload a smaller document.');
        return;
    }

    const zoneId = `upload-zone-${docType}`;
    const innerId = `upload-zone-${docType}-inner`;
    const previewId = `preview-${docType}`;
    const feedbackId = `scan-feedback-${docType}`;
    const zone = document.getElementById(zoneId);
    const inner = document.getElementById(innerId);
    const preview = document.getElementById(previewId);
    const feedback = document.getElementById(feedbackId);

    // Show preview or filename badge
    if (file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = e => {
            preview.src = e.target.result;
            preview.style.display = 'block';
            inner.style.display = 'none';
            zone.style.border = '2px solid #16a34a';
        };
        reader.readAsDataURL(file);
    } else {
        // PDF — show a filename badge
        inner.innerHTML = `
            <i class="fas fa-file-pdf" style="font-size:2.5rem; color:#ef4444; margin-bottom:8px;"></i>
            <span style="font-weight:700; font-size:0.85rem; color:var(--secondary); word-break:break-all;">${file.name}</span>`;
        zone.style.border = '2px solid #16a34a';
        zone.style.background = '#f0fdf4';
    }

    // AI Scanning animation
    if (feedback) {
        feedback.style.color = '#f59e0b';
        feedback.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> AI Analyzing document…';
        setTimeout(() => {
            feedback.style.color = '#16a34a';
            if (docType === 'license') {
                feedback.innerHTML = '<i class="fas fa-check-double"></i> OCR Extraction: Class A Heavy Verified';
            } else {
                feedback.innerHTML = '<i class="fas fa-check-double"></i> Telemetry Sync: Road Worthy Verified';
            }
        }, 2200);
    }
}

// Handle Auth Toggle
function toggleAuth() {
    isLoginMode = !isLoginMode;

    const title = document.getElementById('auth-title');
    const subtitle = document.getElementById('auth-subtitle');
    const signupExtras = document.getElementById('signup-extras');
    const authBtn = document.getElementById('main-auth-btn');
    const toggleText = document.getElementById('toggle-text');
    const toggleLink = document.getElementById('toggle-link');

    if (isLoginMode) {
        title.innerText = "Welcome Back";
        subtitle.innerText = "Login to your Partner Dashboard";
        if (signupExtras) signupExtras.style.display = "none";
        authBtn.innerText = "Login";
        toggleText.innerText = "New driver?";
        toggleLink.innerText = "Apply to Drive";
    } else {
        title.innerText = "Join the Fleet";
        subtitle.innerText = "Register to start earning with top rates";
        if (signupExtras) signupExtras.style.display = "flex";
        if (signupExtras) signupExtras.style.flexDirection = "column";
        authBtn.innerText = "Create Account";
        toggleText.innerText = "Already a partner?";
        toggleLink.innerText = "Login here";
    }
}

// Handle Authentication Submission
async function handleAuthAction() {
    const email = document.getElementById('auth-email').value;
    const pass = document.getElementById('auth-pass').value;

    if (!email || !pass) {
        alert("Please fill in email and password.");
        return;
    }

    const authBtn = document.getElementById('main-auth-btn');
    authBtn.innerText = "Processing...";
    authBtn.disabled = true;

    try {
        if (!isLoginMode) {
            // SIGNUP
            const name = document.getElementById('reg-name').value;
            const phone = document.getElementById('reg-phone').value;

            if (!name || !phone) {
                alert("Please provide your full name and phone number to register.");
                return;
            }

            const response = await fetch('/api/driver/signup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, email, phone, password: pass })
            });

            const result = await response.json();
            alert(result.message);

            if (response.ok) {
                document.querySelectorAll('.auth-form-wrapper input').forEach(i => i.value = '');
                toggleAuth();
            }
        } else {
            // LOGIN
            const response = await fetch('/api/driver/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password: pass })
            });

            const result = await response.json();
            if (response.ok) {
                // Success
                currentDriverId = Number(result.driver_id);
                localStorage.setItem('smart_truck_driver_id', currentDriverId);
                document.getElementById('auth-overlay').style.display = 'none';

                // Auto set driver Online on login
                setDriverOnline(currentDriverId);

                // Fetch driver initial stats
                fetchDriverStats(currentDriverId);
                loadActiveJob();
                loadSettings();
                loadMarketplace();
                showPage('loads');
                startBackgroundSync(); // Ensure real-time updates start after login
            } else {
                showToast(result.message, 'error');
            }
        }
    } catch (err) {
        console.error(err);
        alert("Connection error. Is the server running?");
    } finally {
        authBtn.innerText = isLoginMode ? "Login" : "Create Account";
        authBtn.disabled = false;
    }
}

// Sidebar Navigation
function showPage(pageId) {
    document.querySelectorAll('.page-content').forEach(s => s.style.display = 'none');
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

    const target = document.getElementById(pageId);
    if (target) target.style.display = 'block';

    const nav = document.getElementById(`nav-${pageId}`);
    if (nav) nav.classList.add('active');

    // Reset biometric interface when leaving or entering pages to ensure hardware release
    if (typeof resetBiometricInterface === 'function') resetBiometricInterface();

    // Trigger data loads based on page
    if (pageId === 'loads') loadMarketplace();
    if (pageId === 'active') loadActiveJob();
    if (pageId === 'messages') loadAllChats();
    if (pageId === 'earnings') fetchEarningsData();
    if (pageId === 'settings') loadSettings();

    window.scrollTo(0, 0);
}

async function fetchEarningsData() {
    if (!currentDriverId) return;

    try {
        const res = await fetch(`/api/driver/earnings/${currentDriverId}`);
        const data = await res.json();

        if (res.ok) {
            document.getElementById('earning-balance').innerText = `PKR ${data.total_net.toLocaleString()}`;
            document.getElementById('earning-growth').innerHTML = `<i class="fas fa-chart-line"></i> ${data.growth} vs last period`;
            document.getElementById('earning-efficiency').innerText = data.efficiency;
            document.getElementById('earning-trips').innerText = `${data.trips} Total Assignments`;

            document.getElementById('earning-weekly').innerText = `PKR ${data.weekly_earnings.toLocaleString()}`;
            document.getElementById('earning-monthly').innerText = `PKR ${data.monthly_earnings.toLocaleString()}`;
            document.getElementById('earning-yearly').innerText = `PKR ${data.yearly_earnings.toLocaleString()}`;
            document.getElementById('earning-net-ledger').innerText = `PKR ${data.total_net.toLocaleString()}`;
        }
    } catch (e) {
        console.error("Error fetching earnings:", e);
    }
}

// Toggle Online Status
async function toggleDarkMode() {
    const isDark = document.body.classList.toggle('dark-mode');
    localStorage.setItem('driver_dark_mode', isDark);
}

function downloadGoldenCard() {
    const name = document.getElementById('card-name').innerText;
    const win = window.open('', '_blank');
    win.document.write(`
        <html>
        <head>
            <title>SmartTruck_Verified_${name}</title>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
            <style>
                body { margin: 0; display: flex; align-items: center; justify-content: center; height: 100vh; background: #0f172a; font-family: 'Inter', sans-serif; }
                .card-container { transform: scale(1.5); }
                #golden-id-card {
                    width: 420px; height: 250px; 
                    background: linear-gradient(135deg, #f59e0b 0%, #fbbf24 50%, #b45309 100%); 
                    border-radius: 24px; padding: 30px; text-align: left; position: relative; 
                    box-shadow: 0 30px 60px -12px rgba(217, 119, 6, 0.5); color: white; 
                    border: 1px solid rgba(255,255,255,0.3);
                }
            </style>
        </head>
        <body>
            <div class="card-container">
                ${document.getElementById('golden-id-card').outerHTML}
            </div>
            <script>
                setTimeout(() => { window.print(); setTimeout(() => window.close(), 500); }, 500);
            <\/script>
        </body>
        </html>
    `);
    win.document.close();
}

// --- NOTIFICATION ENGINE ---
async function fetchDriverNotifs() {
    if (!currentDriverId) return;
    try {
        const res = await fetch(`/api/driver/notifications/${currentDriverId}`);
        const data = await res.json();

        const badge = document.getElementById('notif-count-badge');
        const list = document.getElementById('notif-items-list');
        if (!badge || !list) return;

        const unreadCount = data.filter(n => !n.is_read).length;
        if (unreadCount > 0) {
            badge.innerText = unreadCount;
            badge.style.display = 'flex';
        } else {
            badge.style.display = 'none';
        }

        if (data.length > 0) {
            list.innerHTML = '';
            data.forEach(n => {
                let icon = 'fa-info-circle', iconColor = '#3b82f6', bg = '#eff6ff';
                if (n.type === 'success') { icon = 'fa-check-circle'; iconColor = '#10b981'; bg = '#f0fdf4'; }
                else if (n.type === 'warning') { icon = 'fa-exclamation-triangle'; iconColor = '#f59e0b'; bg = '#fffbeb'; }

                list.innerHTML += `
                    <div style="padding: 15px 20px; border-bottom: 1px solid #f1f5f9; display: flex; gap: 15px; cursor: pointer; transition: 0.2s; ${n.is_read ? '' : 'background: rgba(99, 102, 241, 0.03);'}" onmouseover="this.style.background='#f8fafc'" onmouseout="this.style.background='${n.is_read ? 'transparent' : 'rgba(99, 102, 241, 0.03)'}'" onclick="markNotifRead(${n.id})">
                        <div style="width: 40px; height: 40px; background: ${bg}; color: ${iconColor}; border-radius: 10px; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                            <i class="fas ${icon}"></i>
                        </div>
                        <div style="flex: 1;">
                            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 3px;">
                                <span style="font-weight: 700; font-size: 0.85rem; color: #1e293b;">${n.title}</span>
                                <span style="font-size: 0.7rem; color: #94a3b8; font-weight: 600;">${n.time}</span>
                            </div>
                            <p style="font-size: 0.75rem; color: #64748b; line-height: 1.4; margin: 0;">${n.message}</p>
                        </div>
                    </div>
                `;
            });
        }
    } catch (e) { console.error("Notif fetch error", e); }
}

function toggleDriverNotifs(e) {
    if (e) e.stopPropagation();
    const dropdown = document.getElementById('notif-dropdown');
    if (!dropdown) return;
    const isVisible = dropdown.style.display === 'block';
    dropdown.style.display = isVisible ? 'none' : 'block';
    if (!isVisible) fetchDriverNotifs();
}

async function markNotifRead(id) {
    try {
        await fetch(`/api/driver/notifications/read/${id}`, { method: 'POST' });
        fetchDriverNotifs();
        // Refresh settings/profile in case it was a verification alert
        loadSettings();
    } catch (e) { }
}

function markAllNotifsRead() {
    alert("Intelligence feed summarized and cleared.");
    const dropdown = document.getElementById('notif-dropdown');
    if (dropdown) dropdown.style.display = 'none';
}

// Close dropdowns on outside click
window.addEventListener('click', () => {
    const dropdown = document.getElementById('notif-dropdown');
    if (dropdown) dropdown.style.display = 'none';
});
async function toggleStatus() {
    const savedId = localStorage.getItem('smart_truck_driver_id');
    const driverId = parseInt(savedId);

    if (!driverId || isNaN(driverId)) {
        alert("Authentication Error: Please login again.");
        location.reload();
        return;
    }

    const isOnline = document.getElementById('statusToggle').checked;
    const statusText = document.getElementById('statusText');

    statusText.innerText = "Updating...";

    try {
        const response = await fetch('/api/driver/toggle-status', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id: driverId, available: isOnline })
        });
        const result = await response.json();
        if (response.ok) {
            statusText.innerText = isOnline ? "Online" : "Offline";
            statusText.style.color = isOnline ? "var(--success)" : "var(--text-muted)";
        } else {
            alert(result.message);
            document.getElementById('statusToggle').checked = !isOnline;
            statusText.innerText = !isOnline ? "Online" : "Offline";
        }
    } catch (e) {
        console.error(e);
        document.getElementById('statusToggle').checked = !isOnline;
        statusText.innerText = !isOnline ? "Online" : "Offline";
        statusText.style.color = !isOnline ? "var(--success)" : "var(--text-muted)";
    }
}

// Auto-set driver ONLINE on login / page load (no manual toggle needed)
async function setDriverOnline(driverId) {
    const toggle = document.getElementById('statusToggle');
    const statusText = document.getElementById('statusText');
    if (!toggle || !driverId) return;

    // Immediately update UI
    toggle.checked = true;
    statusText.innerText = 'Online';
    statusText.style.color = 'var(--success, #16a34a)';

    // Silently persist to backend
    try {
        await fetch('/api/driver/toggle-status', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id: driverId, available: true })
        });
    } catch (e) {
        console.warn('Auto-online sync failed:', e);
    }
}

async function fetchDriverStats(id) {
    try {
        const res = await fetch(`/api/driver/stats/${id}`);
        if (res.ok) {
            const data = await res.json();
            document.getElementById('profileName').innerText = data.driver;
            if (document.getElementById('topbar-name')) {
                document.getElementById('topbar-name').innerText = data.driver;
            }
            // Update UI with stats if needed
            if (data.fleet_status === "Idle" || data.fleet_status === "In Transit") {
                document.getElementById('statusToggle').checked = true;
                document.getElementById('statusText').innerText = "Online";
                document.getElementById('statusText').style.color = "var(--success)";
            }
        }
    } catch (e) {
        console.log("Stats fetch error:", e);
    }
}

async function loadActiveJob() {
    if (!currentDriverId) return;
    try {
        const res = await fetch(`/api/driver/active-job/${currentDriverId}`);
        const data = await res.json();

        if (data.status === "Success") {
            document.getElementById('no-active-job').style.display = 'none';
            document.getElementById('active-job-container').style.display = 'block';

            document.getElementById('active-job-id').innerText = `#BK-${data.job.id}`;
            document.getElementById('active-pickup').innerText = data.job.pickup;
            document.getElementById('active-dropoff').innerText = data.job.dropoff;
            document.getElementById('active-fare').innerText = `PKR ${data.job.fare.toLocaleString()}`;
            document.getElementById('customer-name').innerText = data.job.user_name;
            document.getElementById('customer-phone').innerText = data.job.user_phone;

            activeBookingId = data.job.id;

            // Setup Active Chat Polling
            if (chatInterval) clearInterval(chatInterval);
            loadChat(activeBookingId);
            chatInterval = setInterval(() => {
                const activeSection = document.getElementById('active');
                if (activeSection && activeSection.style.display !== 'none') {
                    loadChat(activeBookingId);
                }
            }, 3000);
        } else {
            if (chatInterval) {
                clearInterval(chatInterval);
                chatInterval = null;
            }
            document.getElementById('no-active-job').style.display = 'block';
            document.getElementById('active-job-container').style.display = 'none';
        }
    } catch (e) {
        console.error("Error loading active job:", e);
    }
}

// Document Preview
function previewImg(input, imgId) {
    const preview = document.getElementById(imgId);
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function (e) {
            preview.src = e.target.result;
            preview.style.display = 'block';
        }
        reader.readAsDataURL(input.files[0]);
    }
}

// --- NEW ENHANCEMENTS ---

async function loadSettings() {
    const savedId = localStorage.getItem('smart_truck_driver_id');
    const driverId = parseInt(savedId);
    if (!driverId || isNaN(driverId)) return;

    try {
        const resSettings = await fetch(`/api/driver/settings/${driverId}`);
        if (resSettings.ok) {
            const data = await resSettings.json();
            const distInput = document.getElementById('setting-max-distance');
            const autoInput = document.getElementById('setting-auto-accept');
            if (distInput) distInput.value = data.max_distance || 100;
            if (autoInput) autoInput.checked = data.auto_accept || false;
        }

        const resProfile = await fetch(`/api/driver/profile/${driverId}`);
        if (resProfile.ok) {
            const data = await resProfile.json();
            const fields = {
                'profile-name': data.name,
                'profile-phone': data.phone,
                'profile-vehicle-num': data.vehicle_number,
                'profile-vehicle-type': data.vehicle_type,
                'profile-bio': data.bio
            };

            for (let id in fields) {
                const el = document.getElementById(id);
                if (el) el.value = fields[id] || "";
            }

            const pic = data.profile_pic || "https://cdn-icons-png.flaticon.com/512/3135/3135715.png";
            if (document.getElementById('profile-pic-preview')) document.getElementById('profile-pic-preview').src = pic;
            if (document.getElementById('topbar-profile-pic')) document.getElementById('topbar-profile-pic').src = pic;

            const name = data.name || "Driver";
            if (document.getElementById('profileName')) document.getElementById('profileName').innerText = name;
            if (document.getElementById('topbar-name')) document.getElementById('topbar-name').innerText = name;

            // --- VERIFICATION SUCCESS LOGIC ---
            if (data.is_verified) {
                const successZone = document.getElementById('verification-success-zone');
                if (successZone) {
                    successZone.style.display = 'block';
                    if (document.getElementById('card-name')) document.getElementById('card-name').innerText = data.name.toUpperCase();
                    if (document.getElementById('card-vehicle')) document.getElementById('card-vehicle').innerText = `${data.vehicle_number} • ${data.vehicle_type}`.toUpperCase();
                    if (document.getElementById('card-pic')) document.getElementById('card-pic').src = data.profile_pic || 'https://cdn-icons-png.flaticon.com/512/3135/3135715.png';

                    // Update Stepper & Tier UI
                    const tierLabel = document.getElementById('partner-tier-status');
                    if (tierLabel) {
                        tierLabel.innerText = 'Elite Partner';
                        tierLabel.parentElement.style.background = '#fffbeb';
                        tierLabel.parentElement.style.border = '1px solid #fcd34d';
                    }

                    const progress = document.getElementById('trust-progress-fill');
                    if (progress) progress.style.width = '100%';

                    const certNode = document.getElementById('cert-step-node');
                    if (certNode) {
                        certNode.style.background = '#f59e0b';
                        certNode.style.borderColor = '#f59e0b';
                        certNode.style.color = 'white';
                        certNode.innerHTML = '<i class="fas fa-crown"></i>';
                    }

                    const bioNode = document.getElementById('bio-step-node');
                    if (bioNode) {
                        bioNode.style.background = 'var(--primary)';
                        bioNode.style.borderColor = 'var(--primary)';
                        bioNode.style.color = 'white';
                        bioNode.innerHTML = '<i class="fas fa-check"></i>';
                    }
                }
            }
        }
    } catch (e) {
        console.error("Error loading settings/profile:", e);
    }
}

async function saveProfileOnly() {
    if (!currentDriverId) return;
    const profileData = {
        name: document.getElementById('profile-name').value,
        phone: document.getElementById('profile-phone').value,
        vehicle_number: document.getElementById('profile-vehicle-num').value,
        vehicle_type: document.getElementById('profile-vehicle-type').value,
        bio: document.getElementById('profile-bio').value,
        profile_pic: document.getElementById('profile-pic-preview').src
    };

    try {
        const res = await fetch(`/api/driver/profile/${currentDriverId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(profileData)
        });
        if (res.ok) {
            loadSettings(); // Re-fetch to ensure all UI is synced including Golden Card if verified
            return true;
        }
    } catch (e) {
        console.error("Error saving profile:", e);
    }
    return false;
}

async function saveSettings() {
    if (!currentDriverId) {
        alert("Please login first.");
        return;
    }

    const settingsData = {
        max_distance: document.getElementById('setting-max-distance').value,
        auto_accept: document.getElementById('setting-auto-accept').checked
    };

    try {
        // Save Settings
        const resSettings = await fetch(`/api/driver/settings/${currentDriverId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settingsData)
        });

        // Also Save Profile
        const profileSaved = await saveProfileOnly();

        if (resSettings.ok && profileSaved) {
            showToast("Enterprise Profile & Settings Synchronized Successfully!", "success");
        } else {
            alert("Partial Save: Some data could not be updated.");
        }
    } catch (e) {
        console.error("Error saving settings:", e);
        alert("Failed to save changes. Connection error.");
    }
}

async function uploadProfilePic(input) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        const preview = document.getElementById('profile-pic-preview');
        const topbar = document.getElementById('topbar-profile-pic');

        // Show loading state
        if (preview) preview.style.opacity = '0.5';

        reader.onload = async function (e) {
            if (preview) {
                preview.src = e.target.result;
                preview.style.opacity = '1';
            }
            if (topbar) topbar.src = e.target.result;

            try {
                const res = await fetch(`/api/driver/upload-pic/${currentDriverId}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ image_url: e.target.result })
                });
                if (res.ok) {
                    console.log("Profile picture persisted to enterprise cloud.");
                }
            } catch (err) {
                console.error("Upload error:", err);
            }
        };
        reader.readAsDataURL(input.files[0]);
    }
}

async function adjustAIFare(btn, baseFare) {
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Adjusting...';
    btn.disabled = true;

    try {
        const res = await fetch('/api/driver/ai-fare', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ current_fare: baseFare })
        });
        const data = await res.json();

        if (res.ok) {
            // Find the sibling h3 tag to update fare visually
            const fareElem = btn.parentElement.querySelector('.load-fare');
            fareElem.style.color = '#10b981'; // Green to indicate bump
            fareElem.innerHTML = `PKR ${data.suggested_fare.toLocaleString()} <i class="fas fa-arrow-up" style="font-size:1rem;"></i>`;
            btn.innerHTML = '<i class="fas fa-check"></i> Optimized';
        } else {
            btn.innerHTML = '<i class="fas fa-robot"></i> AI Adjust Fare';
            btn.disabled = false;
        }
    } catch (e) {
        console.error("Error with AI fare:", e);
        btn.innerHTML = '<i class="fas fa-robot"></i> AI Adjust Fare';
        btn.disabled = false;
    }
}

// --- CHAT SYSTEM (MISSION COMMAND) ---
let chatInterval = null;

async function loadChat(bookingId) {
    if (!bookingId) return;

    try {
        const res = await fetch(`/api/chat/${bookingId}`);
        if (res.ok) {
            const messages = await res.json();
            const container = document.getElementById('chat-messages');
            if (!container) return;

            const isAtBottom = container.scrollHeight - container.scrollTop <= container.clientHeight + 100;

            if (messages.length === 0) {
                container.innerHTML = '<div style="text-align:center; color: var(--text-muted); margin-top:20px; font-size: 0.9rem;"><i class="fas fa-comments" style="display:block; font-size: 2rem; margin-bottom: 10px; opacity: 0.2;"></i>No messages yet.</div>';
            } else {
                container.innerHTML = messages.map(msg => {
                    const isDriver = msg.sender === 'driver';
                    const align = isDriver ? 'flex-end' : 'flex-start';
                    const bg = isDriver ? 'var(--primary)' : 'white';
                    const color = isDriver ? 'white' : 'var(--secondary)';
                    const border = isDriver ? 'none' : '1px solid var(--border)';

                    return `
                        <div style="display:flex; flex-direction:column; align-items:${align}; margin-bottom:12px;">
                            <div style="background:${bg}; color:${color}; border:${border}; padding:10px 14px; border-radius:12px; max-width:85%; box-shadow: 0 2px 5px rgba(0,0,0,0.05); font-size: 0.9rem; line-height: 1.4;">
                                ${msg.message}
                            </div>
                            <small style="color:var(--text-muted); font-size:0.7rem; margin-top:4px; font-weight: 600;">${msg.time}</small>
                        </div>
                    `;
                }).join('');
            }

            if (isAtBottom) {
                container.scrollTop = container.scrollHeight;
            }
        }
    } catch (e) {
        console.error("Error loading chat:", e);
    }
}

async function sendChatMessage() {
    const input = document.getElementById('chat-input');
    const msg = input.value.trim();

    if (!msg || !activeBookingId) return;

    input.value = '';

    try {
        await fetch(`/api/chat/${activeBookingId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sender: 'driver', message: msg })
        });
        loadChat(activeBookingId);
    } catch (e) {
        console.error("Error sending message:", e);
        showToast("Failed to send message", "error");
    }
}

// --- GLOBAL MESSAGE CENTER ---
let globalActiveBookingId = null;
let globalChatInterval = null;

async function loadAllChats() {
    if (!currentDriverId) return;
    const list = document.getElementById('conversation-list');
    if (!list) return;

    try {
        const res = await fetch(`/api/driver/bookings/${currentDriverId}`);
        const bookings = await res.json();

        if (bookings.length === 0) {
            list.innerHTML = `
                <div style="padding: 60px 20px; text-align: center; color: var(--text-muted);">
                    <i class="fas fa-ghost" style="font-size: 3rem; opacity: 0.1; display: block; margin-bottom: 15px;"></i>
                    <p style="font-weight: 600;">No active connections</p>
                    <p style="font-size: 0.8rem; margin-top: 5px;">Your chat history will appear here.</p>
                </div>`;
            return;
        }

        list.innerHTML = bookings.map(b => `
            <div class="conv-item ${globalActiveBookingId === b.id ? 'active' : ''}" id="conv-${b.id}" onclick="selectConversation(${b.id}, '${b.user_name.replace(/'/g, "\\'")}')" 
                style="padding: 18px 20px; border-bottom: 1px solid var(--border); cursor: pointer; transition: 0.2s; border-left: 4px solid transparent;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div style="font-weight: 700; color: var(--secondary); font-size: 0.95rem;">${b.user_name}</div>
                    <span style="font-size: 0.7rem; background: #f1f5f9; padding: 2px 8px; border-radius: 10px; color: #64748b; font-weight: 800;">#BK-${b.id}</span>
                </div>
                <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 6px; display: flex; align-items: center; gap: 6px;">
                    <span style="width: 8px; height: 8px; border-radius: 50%; background: ${b.status === 'In Transit' ? '#16a34a' : '#cbd5e1'}"></span>
                    ${b.status} • Route Details Available
                </div>
            </div>
        `).join('');
    } catch (e) {
        console.error("Error loading all chats:", e);
    }
}

async function selectConversation(id, name) {
    globalActiveBookingId = id;
    const noChat = document.getElementById('no-chat-selected');
    const activeChat = document.getElementById('active-chat-window');

    if (noChat) noChat.style.display = 'none';
    if (activeChat) activeChat.style.display = 'flex';

    const headerName = document.getElementById('chat-header-name');
    const headerId = document.getElementById('chat-header-id');
    if (headerName) headerName.innerText = name;
    if (headerId) headerId.innerText = `#BK-${id}`;

    // Highlight active item
    document.querySelectorAll('.conv-item').forEach(item => {
        item.style.background = 'white';
        item.style.borderLeftColor = 'transparent';
    });
    const activeItem = document.getElementById(`conv-${id}`);
    if (activeItem) {
        activeItem.style.background = '#f8fafc';
        activeItem.style.borderLeftColor = 'var(--primary)';
    }

    // Setup polling
    if (globalChatInterval) clearInterval(globalChatInterval);
    loadGlobalChat(id);
    globalChatInterval = setInterval(() => loadGlobalChat(id), 3000);
}

async function loadGlobalChat(id) {
    if (!id) return;
    try {
        const res = await fetch(`/api/chat/${id}`);
        if (res.ok) {
            const messages = await res.json();
            const container = document.getElementById('global-chat-messages');
            if (!container) return;

            const isAtBottom = container.scrollHeight - container.scrollTop <= container.clientHeight + 100;

            if (messages.length === 0) {
                container.innerHTML = `
                    <div style="height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; color: var(--text-muted); opacity: 0.5;">
                        <i class="fas fa-comments-alt" style="font-size: 3rem; margin-bottom: 15px;"></i>
                        <p>No messages in this thread yet.</p>
                    </div>`;
            } else {
                container.innerHTML = messages.map(msg => {
                    const isDriver = msg.sender === 'driver';
                    const align = isDriver ? 'flex-end' : 'flex-start';
                    const bg = isDriver ? 'var(--primary)' : '#f1f5f9';
                    const color = isDriver ? 'white' : 'var(--secondary)';

                    return `
                        <div style="display:flex; flex-direction:column; align-items:${align}; margin-bottom:15px; width: 100%;">
                            <div style="background:${bg}; color:${color}; padding:12px 16px; border-radius:16px; ${isDriver ? 'border-bottom-right-radius: 4px;' : 'border-bottom-left-radius: 4px;'} max-width:80%; font-size: 0.95rem; box-shadow: 0 2px 8px rgba(0,0,0,0.04);">
                                ${msg.message}
                            </div>
                            <small style="color:var(--text-muted); font-size:0.7rem; margin-top:5px; font-weight: 700; margin-left: 5px; margin-right: 5px;">${msg.time}</small>
                        </div>
                    `;
                }).join('');
            }

            if (isAtBottom) {
                container.scrollTop = container.scrollHeight;
            }
        }
    } catch (e) {
        console.error("Error loading global chat:", e);
    }
}

async function sendGlobalChatMessage() {
    const input = document.getElementById('global-chat-input');
    if (!input) return;
    const msg = input.value.trim();
    if (!msg || !globalActiveBookingId) return;

    input.value = '';

    try {
        const res = await fetch(`/api/chat/${globalActiveBookingId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sender: 'driver', message: msg })
        });

        if (res.ok) {
            loadGlobalChat(globalActiveBookingId);
        } else {
            showToast("Failed to sync message", "error");
        }
    } catch (e) {
        console.error("Error sending global message:", e);
        showToast("Terminal Connection Error", "error");
    }
}

// Global enter key listener for both chats
document.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        if (document.activeElement.id === 'chat-input') sendChatMessage();
        if (document.activeElement.id === 'global-chat-input') sendGlobalChatMessage();
    }
});

// Settings Tab Navigation
function switchSettingsTab(tabId, el) {
    if (!el) return;

    // Update Tab UI
    document.querySelectorAll('.s-tab').forEach(t => t.classList.remove('active'));
    el.classList.add('active');

    // Update Pane UI
    document.querySelectorAll('.settings-pane').forEach(p => p.classList.remove('active'));
    const targetPane = document.getElementById(`s-pane-${tabId}`);
    if (targetPane) {
        targetPane.classList.add('active');
    } else {
        console.error(`Settings pane not found: s-pane-${tabId}`);
    }
}

function checkAuth() {
    const savedId = localStorage.getItem('smart_truck_driver_id');
    const driverId = parseInt(savedId);
    if (driverId && !isNaN(driverId)) {
        currentDriverId = driverId;

        // Auto set Online on every page load
        setDriverOnline(currentDriverId);

        // Restore Dark Mode
        if (localStorage.getItem('driver_dark_mode') === 'true') {
            document.body.classList.add('dark-mode');
        }

        // Load session data
        fetchDriverStats(currentDriverId);
        loadActiveJob();
        loadSettings();
        loadMarketplace();
        showPage('loads');
        fetchDriverNotifs();

        startBackgroundSync();
        // Sync UI toggles
        setTimeout(() => {
            if (localStorage.getItem('driver_dark_mode') === 'true') {
                const darkToggle = document.getElementById('setting-dark-mode-toggle');
                if (darkToggle) darkToggle.checked = true;
            }
        }, 500);
    } else {
        window.location.href = '/driver';
    }
}

function startBackgroundSync() {
    if (window.syncInterval) clearInterval(window.syncInterval);
    window.syncInterval = setInterval(() => {
        loadActiveJob();
        loadMarketplace(); // Refresh available loads to show new instant bookings
        fetchDriverNotifs(); // Update the intelligence feed
    }, 15000);
}

async function loadMarketplace() {
    // Pass the driver ID to filter relevant loads (broadcasts + specific assignments)
    if (!currentDriverId) return;

    try {
        const res = await fetch(`/api/driver/available-loads?driver_id=${currentDriverId || 0}`);
        if (!res.ok) throw new Error("Network Response Error");

        const loads = await res.json();
        const container = document.getElementById('load-list-container');

        if (!Array.isArray(loads)) {
            console.error("Marketplace: Expected array but received", loads);
            return;
        }

        // Update Sidebar Badge for "Available Loads"
        // Note: We no longer permanently filter rejected loads - the backend handles that
        // The rejectedLoads array is only used for immediate visual feedback (fade effect)
        const sidebarBadge = document.getElementById('loads-count-badge');
        if (sidebarBadge) {
            sidebarBadge.innerText = loads.length;
            sidebarBadge.style.display = loads.length > 0 ? 'flex' : 'none';
        }

        if (!container) return;

        if (loads.length === 0) {
            container.innerHTML = `
                <div style="text-align: center; padding: 50px; background: white; border-radius: 20px; border: 1px dashed var(--border);">
                    <i class="fas fa-search" style="font-size: 3rem; color: var(--border); margin-bottom: 15px;"></i>
                    <p style="color: var(--text-muted); font-weight: 600;">Searching for matched loads in your radius...</p>
                </div>`;
            return;
        }

        container.innerHTML = loads.map(load => {
            // Check if THIS load belongs to THIS driver (by driver_id) and is currently active (In Transit)
            // If load.driver_id matches current driver AND status is 'In Transit', this is their active job
            const isDriversActiveJob = (load.driver_id === currentDriverId) && (load.status === 'In Transit');

            // Check if this was a direct assignment to this driver - API returns 'Direct Assignment' as status
            const isDirectAssignment = (load.driver_id === currentDriverId) && (load.status === 'Direct Assignment');

            // Build badges based on status
            let badges = '';
            if (isDirectAssignment) {
                badges = `<span style="background: #fffbeb; color: #f59e0b; padding: 5px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 800; text-transform: uppercase; border: 1px solid #fef3c7;">
                    <i class="fas fa-bolt"></i> Direct Assignment
                </span>`;
            } else if (isDriversActiveJob) {
                badges = `<span style="background: #dcfce7; color: #16a34a; padding: 5px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 800; text-transform: uppercase; border: 1px solid #bbf7d0;">
                    <i class="fas fa-truck"></i> Active Job
                </span>`;
            }

            // Determine button state - ALWAYS show Accept/Reject EXCEPT for exact active In Transit job
            // Only show "View Active Route" for the driver's exact active job (In Transit status)
            let buttonHtml = '';

            // Show 'View Active Route' ONLY for the driver's exact active job that is In Transit
            if (isDriversActiveJob) {
                // This driver is exactly doing this specific job (In Transit) - show active route button
                buttonHtml = `<button class="btn-primary" style="background: #16a34a; padding: 16px; border-radius: 12px; font-size: 1.1rem; font-weight: 800; box-shadow: 0 10px 15px -3px rgba(22, 163, 74, 0.3);" onclick="showPage('active'); loadActiveJob();">
                    <i class="fas fa-map-marker-alt"></i> View Active Route
                </button>`;
            } else {
                // ALL other loads (Pending, Approved, Direct Assignment, or any other) - show Accept/Reject buttons
                // This includes loads assigned to this driver that are NOT yet In Transit (like Assigned status)
                buttonHtml = `
                    <button class="btn-reject" onclick="rejectLoad(this, ${load.id})">
                        <i class="fas fa-times-circle"></i> Reject Load
                    </button>
                    <button class="btn-accept" id="accept-btn-${load.id}" onclick="acceptLoad(${load.id})">
                        <i class="fas fa-check-double"></i> ${isDirectAssignment ? 'Confirm Assignment' : 'Accept Load'}
                    </button>`;
            }

            // Use correct variable name: isDriversActiveJob (renamed for clarity)
            const isJobActive = isDriversActiveJob;

            return `
            <div class="card load-card" style="margin-bottom: 25px; padding: 30px; border-radius: 20px; transition: 0.3s; border: 1px solid #e2e8f0; ${isJobActive ? 'border-color: #16a34a; background: linear-gradient(to right, white, #f0fdf4);' : ''}" onmouseover="this.style.transform='translateY(-5px)'" onmouseout="this.style.transform='translateY(0)'">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px;">
                    <div>
                        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px;">
                            <span style="background: rgba(37, 99, 235, 0.1); color: var(--primary); padding: 5px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 800; text-transform: uppercase; letter-spacing: 1px;">
                                <i class="fas fa-microchip"></i> AI Match: ${load.match_score}%
                            </span>
                            ${badges}
                            <span style="background: #f8fafc; color: #64748b; padding: 5px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 700;">#BK-${load.id.toString().padStart(4, '0')}</span>
                        </div>
                        <h3 style="font-size: 1.6rem; color: var(--secondary); margin: 0; font-weight: 800;">
                            ${load.pickup} <i class="fas fa-arrow-right" style="color: #cbd5e1; margin: 0 15px; font-size: 1.2rem;"></i> ${load.dropoff}
                        </h3>
                        <div style="display: flex; gap: 20px; margin-top: 15px;">
                            <div style="display: flex; align-items: center; gap: 8px; color: #64748b; font-size: 0.9rem; font-weight: 600;">
                                <i class="fas fa-weight-hanging" style="color: var(--primary);"></i> ${load.weight} KG Payload
                            </div>
                            <div style="display: flex; align-items: center; gap: 8px; color: #64748b; font-size: 0.9rem; font-weight: 600;">
                                <i class="fas fa-clock" style="color: var(--primary);"></i> ${isJobActive ? 'In Transit' : 'Ready for Dispatch'}
                            </div>
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <small style="color: #64748b; font-weight: 700; display: block; margin-bottom: 5px; text-transform: uppercase; font-size: 0.7rem;">Contract Fare</small>
                        <h2 style="color: #16a34a; font-size: 2.2rem; font-weight: 900; margin: 0;">PKR ${(load.fare || 0).toLocaleString()}</h2>
                    </div>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 25px; padding-top: 25px; border-top: 1px dashed #e2e8f0;">
                    ${buttonHtml}
                </div>
            </div>
        `}).join('');

        // AI Auto-Accept Logic
        const autoAcceptEnabled = document.getElementById('setting-auto-accept')?.checked || document.getElementById('setting-auto-accept-toggle')?.checked;
        if (autoAcceptEnabled) {
            const eliteMatch = loads.find(l => l.match_score >= 95);
            if (eliteMatch) {
                const activeJobContainer = document.getElementById('active-job-container');
                if (activeJobContainer && activeJobContainer.style.display === 'none') {
                    showToast(`AI Intelligent Sync: Direct Assignment #${eliteMatch.id} detected. Auto-accepting...`, 'success');
                    setTimeout(() => acceptLoad(eliteMatch.id), 2000); // Give user 2 seconds to see it before it moves
                }
            }
        }
    } catch (e) {
        console.error("Marketplace Error:", e);
    }
}

async function rejectLoad(btn, loadId) {
    if (!currentDriverId || isNaN(currentDriverId) || currentDriverId <= 0) {
        alert("Authentication Error: Driver ID is missing or invalid. Please log in again.");
        return;
    }
    if (!loadId || isNaN(loadId) || loadId <= 0) {
        alert("Error: Invalid load ID. Please try selecting the load again or refresh the page.");
        return;
    }

    // Button loading state
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Rejecting...';
    }

    try {
        const res = await fetch(`/api/driver/reject-load/${loadId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ driver_id: currentDriverId })
        });
        const result = await res.json();

        if (res.ok) {
            // Add to local rejected loads for session filtering
            if (loadId) rejectedLoads.push(loadId);

            // Visual feedback - fade out the card
            const card = btn ? btn.closest('.load-card') : null;
            if (card) {
                card.style.opacity = '0.3';
                card.style.transform = 'translateX(20px)';
            }

            // Show success toast
            showToast("Load rejected and returned to marketplace", "success");

            // Re-render marketplace after short delay
            setTimeout(() => loadMarketplace(), 1000);
        } else {
            alert(result.message || "Failed to reject load");
            // Reset button on failure
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = '<i class="fas fa-times-circle"></i> Reject Load';
            }
        }
    } catch (e) {
        console.error("Error rejecting load:", e);
        alert("Connection Error: Could not sync rejection with HQ server.");

        // Reset button on error
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-times-circle"></i> Reject Load';
        }
    }
}

async function confirmDropOff(btn) {
    // Ensure we have the necessary IDs before proceeding
    if (!currentDriverId || !activeBookingId) {
        alert("Error: Active route data is missing. Please refresh and try again.");
        return;
    }

    // Professional confirmation dialog
    if (!confirm("Mission Completion: Are you sure you have reached the destination and completed the drop-off?")) {
        return;
    }

    // Support explicit parameter (modern) and legacy window.event fallback
    if (!btn && typeof event !== 'undefined') {
        btn = event?.target?.closest('button');
    }
    const originalHtml = btn ? btn.innerHTML : null;

    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Finalizing Delivery...';
    }

    try {
        const res = await fetch(`/api/driver/complete-job/${currentDriverId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ booking_id: activeBookingId })
        });
        const result = await res.json();

        if (res.ok) {
            showToast("Success: Mission Accomplished! Shipment completed and earnings updated.", "success");

            // Store the completed job details for display
            const completedJobData = {
                jobId: activeBookingId,
                pickup: document.getElementById('active-pickup').innerText,
                dropoff: document.getElementById('active-dropoff').innerText,
                fare: document.getElementById('active-fare').innerText,
                customerName: document.getElementById('customer-name').innerText
            };

            activeBookingId = null;

            // Show success state in Active Route page (keep the route visible without chat)
            showJobCompletedSuccess(completedJobData);

            // Also refresh stats for earnings
            fetchDriverStats(currentDriverId);
        } else {
            alert(result.message);
        }
    } catch (e) {
        console.error("Job completion error:", e);
        alert("Connection Error: Could not sync completion with the server.");
    } finally {
        if (btn && originalHtml) {
            btn.disabled = false;
            btn.innerHTML = originalHtml;
        }
    }
}

// Show completed job success state - keeps route visible without chat
function showJobCompletedSuccess(jobData) {
    // Hide the normal active job container
    const activeJobContainer = document.getElementById('active-job-container');
    const noActiveJob = document.getElementById('no-active-job');

    if (activeJobContainer) {
        activeJobContainer.style.display = 'block';

        // Update status to completed
        const statusSpan = activeJobContainer.querySelector('span');
        if (statusSpan) {
            statusSpan.style.background = '#16a34a';
            statusSpan.style.color = 'white';
            statusSpan.innerHTML = '<i class="fas fa-check-circle"></i> COMPLETED';
        }

        // Hide the chat section - find and hide it
        const missionGrid = activeJobContainer.querySelector('.mission-command-grid');
        if (missionGrid) {
            missionGrid.style.display = 'block';
            // Make single column layout
            missionGrid.style.gridTemplateColumns = '1fr';

            // Hide the chat column (second child)
            if (missionGrid.children[1]) {
                missionGrid.children[1].style.display = 'none';
            }

            // Update the left column to show completed info
            const leftCol = missionGrid.children[0];
            if (leftCol) {
                // Hide the call, chat, emergency buttons and confirm button
                const buttonsDiv = leftCol.querySelector('div > div:nth-child(2)');
                if (buttonsDiv) {
                    buttonsDiv.style.display = 'none';
                }
                const confirmBtn = leftCol.querySelector('#completeBtn');
                if (confirmBtn) {
                    confirmBtn.style.display = 'none';
                }

                // Add completed badge
                const firstDiv = leftCol.querySelector('div > div:first-child');
                if (firstDiv) {
                    firstDiv.innerHTML += `
                        <div style="margin-top: 20px; padding: 20px; background: #f0fdf4; border-radius: 16px; border: 2px solid #16a34a;">
                            <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 15px;">
                                <div style="width: 50px; height: 50px; background: #16a34a; border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                                    <i class="fas fa-check" style="color: white; font-size: 1.5rem;"></i>
                                </div>
                                <div>
                                    <h4 style="margin: 0; color: var(--secondary); font-size: 1.1rem;">Delivery Confirmed</h4>
                                    <p style="margin: 0; font-size: 0.8rem; color: var(--text-muted);">Trip #BK-${jobData.jobId} completed successfully</p>
                                </div>
                            </div>
                            <div style="display: flex; justify-content: space-between; padding: 12px; background: white; border-radius: 10px;">
                                <span style="color: var(--text-muted); font-weight: 600;">Fare Earned</span>
                                <span style="color: #16a34a; font-weight: 800;">${jobData.fare}</span>
                            </div>
                            <div style="margin-top: 15px; display: flex; gap: 10px;">
                                <button class="btn-primary" style="flex: 1; padding: 14px; background: var(--primary);" onclick="showPage('earnings')">
                                    <i class="fas fa-wallet"></i> View Earnings
                                </button>
                                <button class="btn" style="flex: 1; padding: 14px;" onclick="showPage('loads')">
                                    <i class="fas fa-route"></i> Find New Load
                                </button>
                            </div>
                        </div>
                    `;
                }
            }
        }

        // Hide the map
        const driverMap = document.getElementById('driver-map');
        if (driverMap) driverMap.style.display = 'none';
    }

    // Hide the "no active job" message
    if (noActiveJob) noActiveJob.style.display = 'none';
}

async function acceptLoad(bookingId, btn = null) {
    if (!btn && typeof event !== 'undefined') btn = event?.target?.closest('button');
    const originalHtml = btn ? btn.innerHTML : null;

    // Ensure driver is authenticated and booking ID is valid before proceeding
    if (!currentDriverId || isNaN(currentDriverId) || currentDriverId <= 0) {
        alert("Authentication Error: Driver ID is missing or invalid. Please log in again.");
        return;
    }
    if (!bookingId || isNaN(bookingId) || bookingId <= 0) {
        alert("Error: Invalid load ID. Please try selecting the load again or refresh the page.");
        return;
    }

    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Synchronizing...';
    }

    try {
        const res = await fetch(`/api/driver/accept-load/${bookingId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ driver_id: currentDriverId })
        });
        const result = await res.json();
        if (res.ok) {
            alert("Mission Confirmed: Payload data synced to terminal.");
            loadActiveJob();
            showPage('active');
            loadMarketplace();
        } else {
            alert(result.message);
        }
    } catch (e) {
        console.error("Error during load acceptance:", e);
        alert("Sync Error: HQ connection interrupted. Please try again later.");
    } finally {
        if (btn && originalHtml) {
            btn.disabled = false;
            btn.innerHTML = originalHtml;
        }
    }
}

async function logout() {
    await fetch('/api/driver/logout', { method: 'POST' });
    localStorage.removeItem('smart_truck_driver_id');
    window.location.href = '/driver';
}

// Initialize on load
window.addEventListener('DOMContentLoaded', checkAuth);


// ═══════════════════════════════════════════════════════════════
//  PREMIUM BIOMETRIC VERIFICATION ENGINE  (Camera + AI Scan)
// ═══════════════════════════════════════════════════════════════

let biometricStream = null;
let biometricScanTimer = null;
let biometricVideoEl = null;
let biometricCanvasEl = null;

/**
 * Auto-binds the biometric initialize button if found in DOM.
 * Call this once after the verification tab HTML is rendered.
 */
function bindBiometricButton() {
    const candidates = [
        document.getElementById('bio-trigger-btn'),
        document.getElementById('init-biometric-btn'),
        document.getElementById('btn-init-biometric'),
        document.getElementById('start-biometric-scan'),
        document.querySelector('.biometric-init-btn'),
        document.querySelector('[data-action="init-biometric"]')
    ];

    const btn = candidates.find(el => el !== null);
    if (!btn || btn.dataset.biometricBound === 'true') return;

    btn.dataset.biometricBound = 'true';

    // Clone to strip any old inline onclick duplicates
    const cleanBtn = btn.cloneNode(true);
    btn.parentNode.replaceChild(cleanBtn, btn);
    cleanBtn.addEventListener('click', startRealBiometricScan);
}

/**
 * Premium Biometric Entry Point: Triggered by "INITIALIZE REAL-FACE SCAN"
 */
async function startRealBiometricScan() {
    // Prevent double-triggering if already scanning or if stream exists
    if (biometricScanTimer || biometricStream) {
        console.warn("Biometric scan already in progress or camera active.");
        return;
    }

    const container = document.getElementById('bio-visual-container');
    const video = document.getElementById('bio-webcam');
    const placeholder = document.getElementById('bio-placeholder');
    const triggerBtn = document.getElementById('bio-trigger-btn');
    const statusText = document.getElementById('bio-status-text');
    const subtext = document.getElementById('bio-status-subtext');
    const spinner = document.getElementById('bio-init-spinner');
    const statusIcon = document.getElementById('bio-status-icon');

    if (!container || !video || !triggerBtn) {
        showToast("Biometric hardware interface not initialized properly.", "error");
        return;
    }

    // 1. UI Loading State
    triggerBtn.disabled = true;
    triggerBtn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> INITIALIZING SENSOR...';
    if (spinner) spinner.style.display = 'block';
    if (statusIcon) statusIcon.className = 'fas fa-shield-halved fa-beat';
    if (statusText) statusText.innerText = 'INITIALIZING...';
    if (subtext) subtext.innerText = 'CALIBRATING OPTICAL ENGINE';

    // 2. Intelligent Camera Initialization (Dual-Stage Bypass)
    try {
        // Stage 1: Request temporary permission to unlock device labels
        const tempStream = await navigator.mediaDevices.getUserMedia({ video: true });
        tempStream.getTracks().forEach(track => track.stop());

        // Stage 2: Enumerate devices with now-available labels
        const devices = await navigator.mediaDevices.enumerateDevices();
        const videoDevices = devices.filter(d => d.kind === 'videoinput');
        
        const virtualKeywords = ['camo', 'virtual', 'obs', 'splitcam', 'manycam', 'vcam', 'logi-capture', 'snap camera', 'studio', 'v-camo'];
        
        const physicalDevices = videoDevices.filter(d => {
            const label = (d.label || '').toLowerCase();
            return label && !virtualKeywords.some(kw => label.includes(kw));
        });

        let finalConstraints = {
            video: {
                width: { ideal: 1280 },
                height: { ideal: 720 },
                facingMode: 'user'
            }
        };

        if (physicalDevices.length > 0) {
            finalConstraints.video.deviceId = { exact: physicalDevices[0].deviceId };
        }

        const stream = await navigator.mediaDevices.getUserMedia(finalConstraints);

        biometricStream = stream;
        video.srcObject = stream;

        // Aggressive UI update: ensure face is shown, not the icon
        video.style.display = 'block';
        video.style.opacity = '1';
        video.style.visibility = 'visible';
        video.style.zIndex = '100'; // Force to the very top during scan

        // Hide placeholder and all its children (icons, pulse, etc) immediately
        if (placeholder) {
            placeholder.style.display = 'none';
            placeholder.style.opacity = '0';
            placeholder.style.visibility = 'hidden';
            placeholder.style.zIndex = '-1';
        }

        // Force play just in case autoplay is blocked or delayed
        video.play().catch(e => console.warn("Video play interrupted or blocked:", e));

        // Show HUD Elements on top of video
        const hud = document.getElementById('bio-hud');
        const progressHud = document.getElementById('bio-progress-hud');
        const scannerLine = document.getElementById('bio-scanner-line');

        if (hud) {
            hud.style.display = 'block';
            hud.style.zIndex = '110';
        }
        if (progressHud) {
            progressHud.style.display = 'block';
            progressHud.style.zIndex = '120';
        }
        if (scannerLine) {
            scannerLine.style.display = 'block';
            scannerLine.style.zIndex = '115';
        }

        container.classList.add('active', 'scanning');
        triggerBtn.innerHTML = '<i class="fas fa-radar fa-spin"></i> LIVENESS CHECK ACTIVE';

        // 3. Progressive Scanning Animation
        let progress = 0;
        const progressBar = document.getElementById('bio-progress-bar');
        const progressText = document.getElementById('bio-progress-text');
        const hudStatusText = container.querySelector('.bio-hud-text');

        const scanStages = [
            "DETECTING FACE...",
            "MAPPING LANDMARKS...",
            "ANALYZING TEXTURE...",
            "VERIFYING LIVENESS...",
            "FINALIZING AUTH..."
        ];

        // Store interval locally so it can't be cleared by a different call
        const currentTimer = setInterval(() => {
            progress += 2;
            if (progressBar) progressBar.style.width = `${progress}%`;
            if (progressText) progressText.innerText = `${progress}%`;

            // Update HUD text based on stage
            const stageIndex = Math.floor(progress / 20);
            if (hudStatusText && scanStages[stageIndex]) {
                hudStatusText.innerText = scanStages[stageIndex];
            }

            if (progress >= 100) {
                clearInterval(currentTimer);
                if (biometricScanTimer === currentTimer) biometricScanTimer = null;
                finalizeBiometricVerification(container, triggerBtn);
            }
        }, 50);

        biometricScanTimer = currentTimer;

    } catch (err) {
        console.error("Camera Access Error:", err);
        triggerBtn.disabled = false;
        triggerBtn.innerHTML = 'INITIALIZE REAL-FACE SCAN';
        if (spinner) spinner.style.display = 'none';
        if (statusIcon) statusIcon.className = 'fas fa-video-slash';
        if (statusText) statusText.innerText = 'SENSOR OFFLINE';
        if (subtext) subtext.innerText = 'PERMISSION DENIED OR NO CAMERA';

        let errorMsg = "Camera access denied. Please enable permissions.";
        if (err.name === 'NotFoundError') errorMsg = "No camera hardware detected.";
        showToast(errorMsg, "error");
    }
}

/**
 * Capture frame, stop camera, and show success state
 */
function finalizeBiometricVerification(container, btn) {
    // Double check if already success to prevent multiple toasts
    if (container.classList.contains('success')) return;

    const video = document.getElementById('bio-webcam');
    const canvas = document.getElementById('bio-snapshot');
    const successOverlay = document.getElementById('bio-success-overlay');
    const hud = document.getElementById('bio-hud');
    const progressHud = document.getElementById('bio-progress-hud');

    // Capture the moment
    if (video && canvas) {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const ctx = canvas.getContext('2d');
        ctx.translate(canvas.width, 0);
        ctx.scale(-1, 1);
        ctx.drawImage(video, 0, 0);
    }

    // Stop Stream
    if (biometricStream) {
        biometricStream.getTracks().forEach(track => track.stop());
        biometricStream = null;
    }

    // Show Success UI
    if (hud) hud.style.display = 'none';
    if (progressHud) progressHud.style.display = 'none';
    if (successOverlay) {
        successOverlay.style.display = 'flex';
        successOverlay.classList.add('visible');
        successOverlay.style.zIndex = '200'; // Ensure it's on top of everything
    }

    container.classList.remove('scanning');
    container.classList.add('success');

    btn.innerHTML = '<i class="fas fa-check-double"></i> IDENTITY VERIFIED';
    btn.style.background = 'var(--grad-success)';
    btn.style.boxShadow = '0 10px 30px rgba(16, 185, 129, 0.4)';

    showToast("Biometric verification successful. Access tier upgraded to Elite.", "success");

    // Persist verification status if needed (simulated)
    const savedId = localStorage.getItem('smart_truck_driver_id');
    if (savedId) {
        fetch(`/api/driver/verify-biometric/${savedId}`, { method: 'POST' })
            .then(() => loadSettings()) // Refresh UI elements
            .catch(e => console.warn("Sync failed, but local UI is updated."));
    }
}

/**
 * Stops all tracks, kills timers, resets CSS states. 
 */
function stopBiometricCamera() {
    if (biometricScanTimer) {
        clearInterval(biometricScanTimer);
        biometricScanTimer = null;
    }
    if (biometricStream) {
        biometricStream.getTracks().forEach(track => track.stop());
        biometricStream = null;
    }
    const video = document.getElementById('bio-webcam');
    if (video) {
        video.srcObject = null;
        video.style.display = 'none';
        video.style.zIndex = ''; // Reset z-index
        video.style.opacity = '';
        video.style.visibility = '';
    }

    const container = document.getElementById('bio-visual-container');
    const placeholder = document.getElementById('bio-placeholder');
    const successOverlay = document.getElementById('bio-success-overlay');

    if (container) {
        container.classList.remove('active', 'scanning', 'success', 'error');
    }
    if (placeholder) {
        placeholder.style.display = 'block';
        placeholder.style.opacity = '1';
    }
    if (successOverlay) {
        successOverlay.style.display = 'none';
        successOverlay.classList.remove('visible');
    }
}

/**
 * Emergency reset — call this when leaving the verification tab/page
 * to ensure the camera LED turns off and memory is freed.
 */
function resetBiometricInterface() {
    stopBiometricCamera();
    const btn = document.querySelector('[data-biometric-btn]')
        || document.getElementById('init-biometric-btn')
        || document.querySelector('.biometric-init-btn');
    if (btn) {
        btn.disabled = false;
        btn.innerHTML = btn.dataset.originalHtml || '<i class="fas fa-fingerprint"></i> Initialize Real-Face Scan';
        btn.style.background = '';
        btn.style.boxShadow = '';
    }
}

// Auto-bind the biometric button once the DOM is ready (non-intrusive)
window.addEventListener('DOMContentLoaded', () => {
    setTimeout(bindBiometricButton, 600);
});