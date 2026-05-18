// User Dashboard JavaScript - Complete Multi-Driver Instant Booking Implementation

let userId = localStorage.getItem('smart_truck_user_id');
let userName = localStorage.getItem('smart_truck_user_name');
let selectedDriverId = null;
let currentBookingData = null;

// ==================== AUTH & INIT ====================
document.addEventListener('DOMContentLoaded', function() {
    if (!userId) {
        window.location.href = '/user/auth';
        return;
    }
    
    initDashboard();
});

function initDashboard() {
    // Set user info
    if (userName) {
        const nameEl = document.getElementById('userNameDisplay');
        const profileCardNameEl = document.getElementById('profileCardName');
        const settingsUserNameEl = document.getElementById('settingsUserName');
        const userInitialEl = document.getElementById('userInitial');
        const editNameEl = document.getElementById('edit-name');
        
        if (nameEl) nameEl.innerText = userName;
        if (profileCardNameEl) profileCardNameEl.innerText = userName;
        if (settingsUserNameEl) settingsUserNameEl.innerText = userName;
        if (userInitialEl) userInitialEl.innerText = userName.charAt(0).toUpperCase();
        if (editNameEl) editNameEl.value = userName;
    }

    // Load profile pic
    const storedPic = localStorage.getItem(`user_profile_pic_${userId}`);
    if (storedPic) {
        const picElements = ['userProfilePic', 'sidebarProfilePic', 'settingsProfilePic'];
        picElements.forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                el.src = storedPic;
                el.style.display = 'block';
            }
        });
        const userInitialEl = document.getElementById('userInitial');
        if (userInitialEl) userInitialEl.style.display = 'none';
    }

    loadDashboardData();
    loadConversations();
}

// ==================== SIDEBAR NAVIGATION ====================
function showSection(sectionId, el) {
    // Hide all sections
    document.querySelectorAll('.dashboard-section').forEach(s => {
        s.style.display = 'none';
        s.classList.remove('active');
    });
    
    // Show target section
    const target = document.getElementById(`section-${sectionId}`);
    if (target) {
        if (sectionId === 'control' || sectionId === 'messages') {
            target.style.display = 'grid';
        } else {
            target.style.display = 'block';
        }
        target.classList.add('active');
    }
    
    // Update sidebar active state
    document.querySelectorAll('.sidebar-link').forEach(link => link.classList.remove('active'));
    if (el) el.classList.add('active');

    // Mobile sidebar close
    if (window.innerWidth <= 1024) toggleSidebar(false);

    // Load section-specific data
    switch(sectionId) {
        case 'control': loadDashboardData(); break;
        case 'messages': loadConversations(); break;
        case 'instant-booking': resetInstantBooking(); break;
    }
}

function toggleSidebar(open = null) {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.querySelector('.sidebar-overlay');
    
    if (!sidebar) return;
    
    if (open === null) {
        sidebar.classList.toggle('active');
        if (overlay) overlay.classList.toggle('active');
        document.body.classList.toggle('sidebar-open');
    } else {
        sidebar.classList.toggle('active', open);
        if (overlay) overlay.classList.toggle('active', open);
        document.body.classList.toggle('sidebar-open', open);
    }
    
    if (overlay) {
        overlay.onclick = () => toggleSidebar(false);
    }
}

// ==================== INSTANT BOOKING - FULL MULTI-DRIVER IMPLEMENTATION ====================
const instantBookingForm = document.getElementById('instantBookingForm');
if (instantBookingForm) {
    instantBookingForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const pickupSelect = document.getElementById('ib-pickup');
        const weightEl = document.getElementById('ib-weight');
        const dropoffEl = document.getElementById('ib-dropoff');
        const loadingEl = document.getElementById('ib-loading');
        const driversGrid = document.getElementById('ib-drivers-grid');
        const noDriversEl = document.getElementById('ib-no-drivers');
        
        if (!pickupSelect || !weightEl || !dropoffEl) return;
        
        const [pickup_lat, pickup_lon] = pickupSelect.value.split(',').slice(0, 2).map(parseFloat);
        const weight = parseFloat(weightEl.value);
        const dropoff = dropoffEl.value;
        
        // Show loading, hide form
        instantBookingForm.style.display = 'none';
        if (loadingEl) loadingEl.style.display = 'block';
        if (driversGrid) driversGrid.style.display = 'none';
        if (noDriversEl) noDriversEl.style.display = 'none';
        
        try {
            const response = await fetch('/api/drivers/nearby', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    pickup_lat: pickup_lat,
                    pickup_lon: pickup_lon,
                    weight: weight
                })
            });
            
            const data = await response.json();
            if (loadingEl) loadingEl.style.display = 'none';
            
            if (data.status === 'Success' && data.drivers && data.drivers.length > 0) {
                renderDriverCards(data.drivers, pickup_lat, pickup_lon, weight, dropoff);
            } else {
                if (noDriversEl) {
                    noDriversEl.style.display = 'block';
                    noDriversEl.innerHTML = `
                        <div style="text-align: center; padding: 40px; background: #f8fafc; border-radius: 16px; border: 1px solid #e2e8f0;">
                            <i class="fas fa-truck" style="font-size: 3rem; color: #94a3b8; margin-bottom: 15px;"></i>
                            <p style="font-weight: 600; color: #475569;">No drivers available nearby</p>
                            <p style="font-size: 0.85rem; color: #64748b;">Try adjusting your pickup location or weight.</p>
                            <button onclick="resetInstantBooking()" style="margin-top: 20px; background: var(--primary); color: white; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer; font-weight: 600;">Try Again</button>
                        </div>
                    `;
                }
                instantBookingForm.style.display = 'block';
            }
            
        } catch (error) {
            console.error('Error fetching drivers:', error);
            if (loadingEl) loadingEl.style.display = 'none';
            if (noDriversEl) {
                noDriversEl.style.display = 'block';
                noDriversEl.innerHTML = `
                    <div style="text-align: center; padding: 40px; background: #fef2f2; border-radius: 16px; border-left: 4px solid #ef4444;">
                        <i class="fas fa-exclamation-triangle" style="font-size: 3rem; color: #ef4444; margin-bottom: 15px;"></i>
                        <p style="font-weight: 600; color: #991b1b;">Service temporarily unavailable</p>
                        <p style="font-size: 0.85rem; color: #64748b;">Server error. Please try again later.</p>
                        <button onclick="resetInstantBooking()" style="margin-top: 20px; background: var(--primary); color: white; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer; font-weight: 600;">Try Again</button>
                    </div>
                `;
            }
            instantBookingForm.style.display = 'block';
        }
    });
}

function renderDriverCards(drivers, pickupLat, pickupLon, weight, dropoff) {
    const container = document.getElementById('ib-drivers-list');
    const driverCountEl = document.getElementById('ib-driver-count');
    const driversGrid = document.getElementById('ib-drivers-grid');
    
    if (!container) return;
    
    if (driverCountEl) driverCountEl.textContent = drivers.length;
    if (driversGrid) driversGrid.style.display = 'block';
    
    container.innerHTML = drivers.map(driver => `
        <div class="driver-card" data-driver-id="${driver.driver_id}" style="border: 2px solid transparent; box-shadow: 0 4px 12px rgba(0,0,0,0.1); transition: all 0.3s ease; border-radius: 16px; padding: 20px; background: white; margin-bottom: 15px; position: relative;">
            <div style="display: flex; align-items: center; gap: 15px;">
                <div style="position: relative; flex-shrink: 0;">
                    <img src="${driver.profile_pic || '/static/images/default-driver.png'}" alt="${driver.driver_name}" style="width: 70px; height: 70px; border-radius: 16px; object-fit: cover; border: 3px solid white; box-shadow: 0 8px 20px rgba(0,0,0,0.15);">
                    ${driver.is_verified ? '<div style="position: absolute; bottom: -5px; right: -5px; width: 24px; height: 24px; background: #16a34a; border-radius: 50%; border: 3px solid white; display: flex; align-items: center; justify-content: center;"><i class="fas fa-check" style="color: white; font-size: 0.8rem;"></i></div>' : ''}
                </div>
                <div style="flex: 1; min-width: 0;">
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 5px; flex-wrap: wrap;">
                        <h4 style="margin: 0; font-weight: 700; font-size: 1.1rem; color: #1e293b;">${driver.driver_name}</h4>
                        ${driver.is_verified ? '<span style="background: #dcfce7; color: #166534; padding: 4px 10px; border-radius: 20px; font-size: 0.7rem; font-weight: 800;">Verified</span>' : ''}
                    </div>
                    <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 8px; font-size: 0.85rem; color: #64748b; flex-wrap: wrap;">
                        <span><i class="fas fa-star" style="color: #f59e0b;"></i> ${driver.rating || '4.5'}/5</span>
                        <span><i class="fas fa-route" style="color: #64748b;"></i> ${driver.distance_km} km away</span>
                        <span><i class="fas fa-truck" style="color: #64748b;"></i> ${driver.vehicle || 'Standard Truck'}</span>
                    </div>
                    <div style="display: flex; gap: 10px; margin-bottom: 10px; flex-wrap: wrap;">
                        <div style="font-size: 0.75rem; color: #64748b;">
                            ${driver.trips_completed || 0} trips completed
                        </div>
                        <div style="font-size: 0.75rem; color: #16a34a; font-weight: 600;">
                            AI Score: ${Math.round(driver.ai_match_score || 85)}%
                        </div>
                    </div>
                    <div style="padding: 8px 12px; background: #f8fafc; border-radius: 8px; font-size: 0.8rem; color: #475569; line-height: 1.4;">
                        ${driver.bio || 'Professional driver ready for your shipment.'}
                    </div>
                </div>
                <div style="text-align: right; flex-shrink: 0; padding-left: 10px;">
                    <div style="font-size: 1.8rem; font-weight: 800; color: #16a34a; margin-bottom: 5px;">PKR ${(driver.estimated_fare || 0).toLocaleString()}</div>
                    <div style="font-size: 0.75rem; color: #64748b;">Contract rate</div>
                </div>
            </div>
            <label class="driver-select-label" style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; cursor: pointer; z-index: 2; margin: 0;">
                <input type="radio" name="selected-driver" value="${driver.driver_id}" style="position: absolute; opacity: 0; width: 0; height: 0;" onchange="selectDriver(${driver.driver_id}, ${driver.estimated_fare || 0}, '${dropoff.replace(/'/g, "\\'")}', ${weight}, this)">
                <div style="position: absolute; top: 20px; right: 20px; width: 24px; height: 24px; border: 2px solid #e2e8f0; border-radius: 50%; background: white; display: flex; align-items: center; justify-content: center; transition: all 0.2s ease; z-index: 3; pointer-events: none;">
                    <div class="radio-inner" style="width: 10px; height: 10px; border-radius: 50%; background: var(--primary); opacity: 0; transition: opacity 0.2s ease;"></div>
                </div>
            </label>
        </div>
    `).join('');
    
    // Add professional styling for radio buttons via event delegation
    container.addEventListener('change', function(e) {
        if (e.target.name === 'selected-driver') {
            // Reset all cards
            container.querySelectorAll('.driver-card').forEach(card => {
                card.style.border = '2px solid transparent';
                card.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)';
                const radioInner = card.querySelector('.radio-inner');
                if (radioInner) radioInner.style.opacity = '0';
            });
            // Highlight selected card
            const selectedCard = e.target.closest('.driver-card');
            if (selectedCard) {
                selectedCard.style.border = '2px solid var(--primary)';
                selectedCard.style.boxShadow = '0 8px 25px rgba(37,99,235,0.2)';
                const radioInner = selectedCard.querySelector('.radio-inner');
                if (radioInner) radioInner.style.opacity = '1';
            }
        }
    });
}

function selectDriver(driverId, fare, dropoff, weight, radioEl) {
    selectedDriverId = driverId;
    const pickupSelect = document.getElementById('ib-pickup');
    
    currentBookingData = {
        pickup_loc: pickupSelect ? pickupSelect.value.split(',')[2] : '',
        dropoff_loc: dropoff,
        weight: weight,
        fare: fare,
        driver_id: driverId
    };
    
    // Update confirm button
    const confirmBtn = document.getElementById('ib-confirm-btn');
    if (confirmBtn) {
        confirmBtn.disabled = false;
        confirmBtn.innerHTML = `
            <i class="fas fa-check-circle"></i> 
            Confirm Booking with Selected Driver (PKR ${fare.toLocaleString()})
        `;
    }
}

const ibConfirmBtn = document.getElementById('ib-confirm-btn');
if (ibConfirmBtn) {
    ibConfirmBtn.addEventListener('click', async () => {
        if (!selectedDriverId) {
            showToast('Please select a driver first', '', 'error');
            return;
        }
        
        const originalText = ibConfirmBtn.innerHTML;
        ibConfirmBtn.disabled = true;
        ibConfirmBtn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Processing...';
        
        try {
            const response = await fetch('/api/user/book', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(currentBookingData)
            });
            
            const data = await response.json();
            
            if (response.ok) {
                showToast('Booking Confirmed!', `Driver notified. Shipment #BK-${data.booking_id} created.`, 'success');
                resetInstantBooking();
                loadDashboardData();
            } else {
                showToast('Error', data.message || 'Booking failed', 'error');
            }
        } catch (error) {
            console.error('Booking error:', error);
            showToast('Server Error', 'Please try again', 'error');
        } finally {
            ibConfirmBtn.disabled = false;
            ibConfirmBtn.innerHTML = originalText;
        }
    });
}

function resetInstantBooking() {
    const form = document.getElementById('instantBookingForm');
    const driversGrid = document.getElementById('ib-drivers-grid');
    const noDrivers = document.getElementById('ib-no-drivers');
    const loading = document.getElementById('ib-loading');
    const confirmBtn = document.getElementById('ib-confirm-btn');
    
    if (form) form.style.display = 'block';
    if (driversGrid) driversGrid.style.display = 'none';
    if (noDrivers) noDrivers.style.display = 'none';
    if (loading) loading.style.display = 'none';
    if (form) form.reset();
    
    selectedDriverId = null;
    currentBookingData = null;
    
    if (confirmBtn) {
        confirmBtn.disabled = true;
        confirmBtn.innerHTML = '<i class="fas fa-check-circle"></i> Select a Driver to Confirm';
    }
}

// ==================== CONTROL CENTER ====================
async function loadDashboardData() {
    try {
        const res = await fetch(`/api/user/${userId}/bookings`);
        const bookings = await res.json();
        
        const totalBookingsEl = document.getElementById('totalBookings');
        const activeShipmentsEl = document.getElementById('activeShipments');
        const totalSpentEl = document.getElementById('totalSpent');
        const tbody = document.getElementById('bookingsTableBody');
        
        if (totalBookingsEl) totalBookingsEl.innerText = bookings.length;
        
        let active = 0, spent = 0;
        
        if (tbody) {
            tbody.innerHTML = bookings.length === 0 ? 
                '<tr><td colspan="6" style="text-align: center; padding: 60px; color: #64748b;">No bookings found. <a href="#" onclick="event.preventDefault(); showSection(\'instant-booking\', document.querySelector(\'[data-section=&quot;instant-booking&quot;]\'));" style="color: var(--primary); font-weight: 600;">Book now</a></td></tr>' :
                bookings.map(b => {
                    if (['Pending', 'Confirmed', 'In Transit'].includes(b.status)) active++;
                    spent += b.fare || 0;
                    
                    const badgeClass = b.status === 'Completed' ? 'badge-success' : 'badge-pending';
                    const actionBtn = b.status === 'Completed' ? 
                        '<span class="badge badge-success"><i class="fas fa-check-double"></i> Delivered</span>' :
                        `<a href="/user/track/${b.id}" class="btn btn-primary" style="padding: 6px 12px; font-size: 0.75rem;"><i class="fas fa-map"></i> Track</a>`;
                    
                    return `
                        <tr style="border-bottom: 1px solid #f1f5f9; transition: background 0.2s;">
                            <td style="padding: 20px 30px;"><strong style="color: #1e293b;">#BK-${b.id}</strong><br><small style="color: #64748b;">${b.date || 'N/A'}</small></td>
                            <td style="padding: 20px 15px; color: #475569;">${b.pickup ? b.pickup.substring(0,25) : 'N/A'}... → ${b.dropoff ? b.dropoff.substring(0,25) : 'N/A'}...</td>
                            <td style="padding: 20px 15px; color: #475569;">${b.driver || 'AI Matching'}</td>
                            <td style="padding: 20px 15px;"><span class="badge ${badgeClass}">${b.status}</span></td>
                            <td style="padding: 20px 15px;"><i class="fas fa-brain" style="color: var(--primary);"></i> 96% Match</td>
                            <td style="padding: 20px 30px; white-space: nowrap;">${actionBtn}</td>
                        </tr>
                    `;
                }).join('');
        }
        
        if (activeShipmentsEl) activeShipmentsEl.innerText = active;
        if (totalSpentEl) totalSpentEl.innerText = spent.toLocaleString();
        
    } catch (err) {
        console.error('Dashboard load error:', err);
    }
}

// ==================== TOASTS, PROFILE, MISC ====================
function showToast(title, message, type = 'success') {
    const container = document.getElementById('toast-container');
    if (!container) return;
    
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.style.cssText = `
        display: flex; align-items: flex-start; gap: 12px; padding: 16px 20px;
        background: ${type === 'success' ? '#f0fdf4' : '#fef2f2'};
        border-left: 4px solid ${type === 'success' ? '#16a34a' : '#ef4444'};
        border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        margin-bottom: 12px; animation: slideIn 0.3s ease; min-width: 300px;
    `;
    toast.innerHTML = `
        <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'}" style="color: ${type === 'success' ? '#16a34a' : '#ef4444'}; font-size: 1.2rem; margin-top: 2px;"></i>
        <div style="flex: 1;">
            <strong style="display: block; margin-bottom: 2px; color: ${type === 'success' ? '#166534' : '#991b1b'}; font-size: 0.95rem;">${title}</strong>
            <small style="color: #64748b; font-size: 0.85rem;">${message}</small>
        </div>
        <button onclick="this.parentElement.remove()" style="background: none; border: none; color: #94a3b8; cursor: pointer; font-size: 1rem; padding: 0; line-height: 1;"><i class="fas fa-times"></i></button>
    `;
    
    container.appendChild(toast);
    setTimeout(() => {
        if (toast.parentElement) toast.remove();
    }, 4000);
}

function saveProfileChanges() {
    const nameInput = document.getElementById('edit-name');
    if (nameInput && nameInput.value.trim()) {
        localStorage.setItem('smart_truck_user_name', nameInput.value.trim());
        showToast('Saved', 'Profile updated successfully');
    }
}

function logout() {
    Object.keys(localStorage).forEach(key => {
        if (key.startsWith('smart_truck_') || key.startsWith('user_')) {
            localStorage.removeItem(key);
        }
    });
    window.location.href = '/user/auth';
}

// ==================== MESSAGING SYSTEM ====================
let activeChatBookingId = null;
let chatInterval = null;

async function loadConversations() {
    const listContainer = document.getElementById('conversationsList');
    if (!listContainer) return;

    try {
        const res = await fetch(`/api/user/${userId}/bookings`);
        const data = await res.json();
        const bookings = data.bookings || [];

        if (bookings.length === 0) {
            listContainer.innerHTML = '<div style="padding: 40px; text-align: center; color: #64748b; font-size: 0.9rem;"><i class="fas fa-ghost" style="display: block; font-size: 2rem; margin-bottom: 10px; opacity: 0.3;"></i>No active connections found.</div>';
            return;
        }

        // Group by driver to show unique conversations
        const uniqueDrivers = {};
        bookings.forEach(b => {
            if (b.driver !== 'Unknown' && b.driver !== 'AI Matching') {
                if (!uniqueDrivers[b.driver]) {
                    uniqueDrivers[b.driver] = b;
                }
            }
        });

        const drivers = Object.values(uniqueDrivers);
        if (drivers.length === 0) {
            listContainer.innerHTML = '<div style="padding: 40px; text-align: center; color: #64748b; font-size: 0.9rem;">No drivers assigned to your shipments yet.</div>';
            return;
        }

        listContainer.innerHTML = drivers.map(d => `
            <div class="conversation-item ${activeChatBookingId === d.id ? 'active' : ''}" onclick="openChat(${d.id}, '${d.driver.replace(/'/g, "\\'")}')">
                <div class="conversation-avatar">
                    <i class="fas fa-user-truck"></i>
                </div>
                <div class="conversation-info">
                    <div class="conversation-name">
                        <span>${d.driver}</span>
                        <span class="conversation-time">#BK-${d.id}</span>
                    </div>
                    <div class="conversation-preview">${d.status} • ${d.pickup.split(',')[0]} → ${d.dropoff.split(',')[0]}</div>
                </div>
            </div>
        `).join('');

    } catch (err) {
        console.error('Error loading conversations:', err);
    }
}

async function openChat(bookingId, driverName) {
    activeChatBookingId = bookingId;
    
    // Update active state in UI
    document.querySelectorAll('.conversation-item').forEach(item => item.classList.remove('active'));
    const activeItem = Array.from(document.querySelectorAll('.conversation-item')).find(item => item.innerHTML.includes(`#BK-${bookingId}`));
    if (activeItem) activeItem.classList.add('active');

    // Setup chat container
    const chatDisplay = document.getElementById('chatDisplay');
    const chatHeader = document.getElementById('chatHeader');
    
    if (chatHeader) {
        chatHeader.innerHTML = `
            <div class="chat-header-avatar">
                <i class="fas fa-user-truck"></i>
            </div>
            <div class="chat-header-info">
                <h4>${driverName}</h4>
                <p>Shipment #BK-${bookingId} • Active Connection</p>
            </div>
        `;
    }

    if (chatDisplay) {
        chatDisplay.innerHTML = '<div style="flex:1; display:flex; align-items:center; justify-content:center;"><i class="fas fa-spinner fa-spin" style="font-size: 2rem; color: var(--primary);"></i></div>';
    }

    // Clear previous interval
    if (chatInterval) clearInterval(chatInterval);
    
    // Initial fetch
    fetchMessages();
    
    // Set polling
    chatInterval = setInterval(fetchMessages, 3000);
}

async function fetchMessages() {
    if (!activeChatBookingId) return;
    
    try {
        const res = await fetch(`/api/chat/${activeChatBookingId}`);
        const messages = await res.json();
        
        const chatDisplay = document.getElementById('chatDisplay');
        if (!chatDisplay) return;

        if (messages.length === 0) {
            chatDisplay.innerHTML = `
                <div class="empty-chat">
                    <i class="fas fa-comments"></i>
                    <p>Start a conversation with your driver.</p>
                </div>
            `;
            return;
        }

        const isAtBottom = chatDisplay.scrollHeight - chatDisplay.scrollTop <= chatDisplay.clientHeight + 100;

        chatDisplay.innerHTML = messages.map(m => `
            <div class="chat-message ${m.sender === 'user' ? 'sent' : 'received'}">
                ${m.message}
                <div class="message-time">${m.time}</div>
            </div>
        `).join('');

        if (isAtBottom) {
            chatDisplay.scrollTop = chatDisplay.scrollHeight;
        }
    } catch (err) {
        console.error('Error fetching messages:', err);
    }
}

async function sendMessage() {
    const input = document.getElementById('chatInput');
    if (!activeChatBookingId || !input || !input.value.trim()) return;

    const message = input.value.trim();
    input.value = '';

    try {
        const res = await fetch(`/api/chat/${activeChatBookingId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                sender: 'user',
                message: message
            })
        });

        if (res.ok) {
            fetchMessages();
        } else {
            showToast('Message Failed', 'Could not send message', 'error');
        }
    } catch (err) {
        console.error('Send error:', err);
        showToast('Error', 'Connection lost', 'error');
    }
}

// Global enter key listener for chat
document.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && document.activeElement.id === 'chatInput') {
        sendMessage();
    }
});

// Add CSS animation for toasts
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { opacity: 0; transform: translateX(100%); }
        to { opacity: 1; transform: translateX(0); }
    }
    .dashboard-section { display: none; }
    .dashboard-section.active { display: block; }
`;
document.head.appendChild(style);