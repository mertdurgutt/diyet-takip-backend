// Admin Panel JavaScript
// API URL'ini otomatik olarak belirle (hosting veya localhost)
const getApiBaseUrl = () => {
    // Eğer localhost'ta çalışıyorsak, localhost API'yi kullan
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        return 'http://localhost:5000/api';
    }
    // Aksi halde, mevcut domain'in API'sini kullan
    return `${window.location.origin}/api`;
};

const API_BASE_URL = getApiBaseUrl();
let authToken = localStorage.getItem('adminToken');
let activityChart = null;

// Sayfa yüklendiğinde
document.addEventListener('DOMContentLoaded', function() {
    console.log('Admin paneli yüklendi');
    console.log('API Base URL:', API_BASE_URL);
    console.log('Current Origin:', window.location.origin);
    console.log('Auth token:', authToken ? 'Mevcut' : 'Yok');
    
    if (authToken) {
        showAdminPanel();
        loadDashboard();
    } else {
        showLoginScreen();
    }

    // Login form
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
        console.log('Login form event listener eklendi');
    } else {
        console.error('Login form bulunamadı!');
    }
    
    // Search handlers (sadece admin panel açıksa)
    const userSearch = document.getElementById('userSearch');
    if (userSearch) {
        userSearch.addEventListener('input', debounce(() => {
            loadUsers(1);
        }, 500));
    }
    
    const foodSearch = document.getElementById('foodSearch');
    if (foodSearch) {
        foodSearch.addEventListener('input', debounce(() => {
            loadFoods(1);
        }, 500));
    }

    // Add food form
    const addFoodForm = document.getElementById('addFoodForm');
    if (addFoodForm) {
        addFoodForm.addEventListener('submit', handleAddFood);
    }
    
    // Log filters
    const logTypeFilter = document.getElementById('logTypeFilter');
    if (logTypeFilter) {
        logTypeFilter.addEventListener('change', () => {
            loadLogs(1);
        });
    }
});

function showLoginScreen() {
    document.getElementById('loginScreen').classList.remove('hidden');
    document.getElementById('adminPanel').classList.add('hidden');
}

function showAdminPanel() {
    document.getElementById('loginScreen').classList.add('hidden');
    document.getElementById('adminPanel').classList.remove('hidden');
}

function handleLogin(e) {
    e.preventDefault();
    console.log('Giriş butonu tıklandı');
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const errorDiv = document.getElementById('loginError');
    
    console.log('Email:', email);
    console.log('API URL:', `${API_BASE_URL}/admin/login`);

    // Loading göster
    const submitBtn = e.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Giriş yapılıyor...';

    fetch(`${API_BASE_URL}/admin/login`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email, password })
    })
    .then(response => {
        console.log('Response status:', response.status);
        console.log('Response URL:', response.url);
        
        // Response'u text olarak al (JSON parse hatası için)
        return response.text().then(text => {
            try {
                const data = JSON.parse(text);
                if (!response.ok) {
                    throw new Error(data.error || `HTTP ${response.status}: ${response.statusText}`);
                }
                return data;
            } catch (e) {
                // JSON parse hatası
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText} - ${text}`);
                }
                throw new Error('Geçersiz yanıt: ' + text.substring(0, 100));
            }
        });
    })
    .then(data => {
        console.log('Response data:', data);
        if (data.token) {
            authToken = data.token;
            localStorage.setItem('adminToken', authToken);
            errorDiv.classList.add('hidden');
            showAdminPanel();
            loadDashboard();
        } else {
            errorDiv.textContent = data.error || 'Giriş başarısız';
            errorDiv.classList.remove('hidden');
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
        }
    })
    .catch(error => {
        console.error('Giriş hatası:', error);
        console.error('Error details:', {
            message: error.message,
            stack: error.stack,
            apiUrl: `${API_BASE_URL}/admin/login`
        });
        errorDiv.textContent = 'Hata: ' + error.message;
        errorDiv.classList.remove('hidden');
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
    });
}

function logout() {
    authToken = null;
    localStorage.removeItem('adminToken');
    showLoginScreen();
}

function showSection(section) {
    console.log('Section değiştiriliyor:', section);
    // Hide all sections
    document.querySelectorAll('.section').forEach(s => s.classList.add('hidden'));
    document.querySelectorAll('.nav-link').forEach(link => link.classList.remove('active'));
    
    // Show selected section
    const sectionElement = document.getElementById(section + 'Section');
    if (sectionElement) {
        sectionElement.classList.remove('hidden');
        
        // Section'a göre veri yükle
        if (section === 'users') {
            console.log('Kullanıcılar yükleniyor...');
            loadUsers(1);
        } else if (section === 'foods') {
            console.log('Besinler yükleniyor...');
            loadFoods(1);
        } else if (section === 'logs') {
            console.log('Loglar yükleniyor...');
            loadLogs(1);
        }
    } else {
        console.error('Section bulunamadı:', section + 'Section');
    }
    
    // Active nav link'i bul ve işaretle
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        if (link.getAttribute('onclick') && link.getAttribute('onclick').includes(`'${section}'`)) {
            link.classList.add('active');
        }
    });
}

// Dashboard
function loadDashboard() {
    fetch(`${API_BASE_URL}/admin/stats`, {
        headers: {
            'Authorization': `Bearer ${authToken}`
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            if (data.error === 'Yetkisiz erişim') {
                logout();
            }
            return;
        }
        displayStats(data);
        drawActivityChart(data.activity_data);
    })
    .catch(error => {
        console.error('Dashboard yükleme hatası:', error);
    });
}

function displayStats(data) {
    const statsContainer = document.getElementById('statsContainer');
    statsContainer.innerHTML = `
        <div class="col-md-3">
            <div class="stat-card">
                <div class="icon users">
                    <i class="fas fa-users"></i>
                </div>
                <h3>${data.total_users}</h3>
                <p>Toplam Kullanıcı</p>
            </div>
        </div>
        <div class="col-md-3">
            <div class="stat-card">
                <div class="icon active">
                    <i class="fas fa-user-check"></i>
                </div>
                <h3>${data.active_users}</h3>
                <p>Aktif Kullanıcı (30 gün)</p>
            </div>
        </div>
        <div class="col-md-3">
            <div class="stat-card">
                <div class="icon foods">
                    <i class="fas fa-utensils"></i>
                </div>
                <h3>${data.total_foods}</h3>
                <p>Toplam Besin</p>
            </div>
        </div>
        <div class="col-md-3">
            <div class="stat-card">
                <div class="icon logs">
                    <i class="fas fa-list"></i>
                </div>
                <h3>${data.today_logs}</h3>
                <p>Bugünkü Log</p>
            </div>
        </div>
    `;
}

function drawActivityChart(activityData) {
    const ctx = document.getElementById('activityChart').getContext('2d');
    
    if (activityChart) {
        activityChart.destroy();
    }

    const labels = activityData.map(item => {
        const date = new Date(item.date);
        return date.toLocaleDateString('tr-TR', { day: 'numeric', month: 'short' });
    });
    const data = activityData.map(item => item.count);

    activityChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Aktif Kullanıcı Sayısı',
                data: data,
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: true
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// Users
let currentUsersPage = 1;
function loadUsers(page = 1) {
    console.log('loadUsers çağrıldı, sayfa:', page);
    currentUsersPage = page;
    const search = document.getElementById('userSearch')?.value || '';
    
    const tbody = document.getElementById('usersTableBody');
    if (tbody) {
        tbody.innerHTML = '<tr><td colspan="9" class="text-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Yükleniyor...</span></div></td></tr>';
    }
    
    fetch(`${API_BASE_URL}/admin/users?page=${page}&limit=20`, {
        headers: {
            'Authorization': `Bearer ${authToken}`
        }
    })
    .then(response => {
        console.log('Kullanıcılar response status:', response.status);
        if (!response.ok) {
            return response.json().then(err => {
                throw new Error(err.error || 'Kullanıcılar yüklenemedi');
            });
        }
        return response.json();
    })
    .then(data => {
        console.log('Kullanıcılar data:', data);
        if (data.error) {
            if (data.error === 'Yetkisiz erişim') {
                logout();
                return;
            }
            alert('Hata: ' + data.error);
            return;
        }
        if (data.users) {
            displayUsers(data.users);
            displayUsersPagination(data.total, data.page, data.limit);
        } else {
            console.error('Kullanıcılar data.users yok:', data);
        }
    })
    .catch(error => {
        console.error('Kullanıcı yükleme hatası:', error);
        if (tbody) {
            tbody.innerHTML = `<tr><td colspan="9" class="text-center text-danger">Hata: ${error.message}</td></tr>`;
        }
    });
}

function displayUsers(users) {
    const tbody = document.getElementById('usersTableBody');
    const search = document.getElementById('userSearch').value.toLowerCase();
    
    let filteredUsers = users;
    if (search) {
        filteredUsers = users.filter(user => 
            user.email.toLowerCase().includes(search) ||
            (user.name && user.name.toLowerCase().includes(search))
        );
    }

    if (filteredUsers.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="text-center">Kullanıcı bulunamadı</td></tr>';
        return;
    }

    tbody.innerHTML = filteredUsers.map(user => `
        <tr>
            <td>${user.id}</td>
            <td>${user.email}</td>
            <td>${user.name || '-'}</td>
            <td>${user.age || '-'}</td>
            <td>${user.gender || '-'}</td>
            <td>${user.weight || '-'}</td>
            <td>${user.target_weight || '-'}</td>
            <td>${new Date(user.created_at).toLocaleDateString('tr-TR')}</td>
            <td>
                <button class="btn btn-sm btn-primary me-1" onclick="editUser(${user.id})" title="Düzenle">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-sm btn-danger" onclick="deleteUser(${user.id})" title="Sil">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

function displayUsersPagination(total, page, limit) {
    const totalPages = Math.ceil(total / limit);
    const pagination = document.getElementById('usersPagination');
    
    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }

    let html = '';
    for (let i = 1; i <= totalPages; i++) {
        html += `
            <li class="page-item ${i === page ? 'active' : ''}">
                <a class="page-link" href="#" onclick="loadUsers(${i}); return false;">${i}</a>
            </li>
        `;
    }
    pagination.innerHTML = html;
}

function editUser(userId) {
    console.log('Kullanıcı düzenleniyor:', userId);
    
    // Kullanıcı detaylarını getir
    fetch(`${API_BASE_URL}/admin/users/${userId}`, {
        headers: {
            'Authorization': `Bearer ${authToken}`
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert('Hata: ' + data.error);
            return;
        }
        
        const user = data.user;
        
        // Modal'ı doldur
        document.getElementById('editUserId').value = user.id;
        document.getElementById('editUserEmail').value = user.email || '';
        document.getElementById('editUserName').value = user.name || '';
        document.getElementById('editUserAge').value = user.age || '';
        document.getElementById('editUserGender').value = user.gender || '';
        document.getElementById('editUserHeight').value = user.height || '';
        document.getElementById('editUserWeight').value = user.weight || '';
        document.getElementById('editUserTargetWeight').value = user.target_weight || '';
        document.getElementById('editUserActivityLevel').value = user.activity_level || 'sedentary';
        document.getElementById('editUserGoal').value = user.goal || 'Kilo Koruma';
        
        // Modal'ı göster
        const modal = new bootstrap.Modal(document.getElementById('userEditModal'));
        modal.show();
    })
    .catch(error => {
        console.error('Kullanıcı detay hatası:', error);
        alert('Hata: ' + error.message);
    });
}

function saveUserEdit() {
    const userId = document.getElementById('editUserId').value;
    const userData = {
        name: document.getElementById('editUserName').value,
        age: parseInt(document.getElementById('editUserAge').value) || null,
        gender: document.getElementById('editUserGender').value || null,
        height: parseFloat(document.getElementById('editUserHeight').value) || null,
        weight: parseFloat(document.getElementById('editUserWeight').value) || null,
        target_weight: parseFloat(document.getElementById('editUserTargetWeight').value) || null,
        activity_level: document.getElementById('editUserActivityLevel').value,
        goal: document.getElementById('editUserGoal').value
    };
    
    console.log('Kullanıcı güncelleniyor:', userId, userData);
    
    fetch(`${API_BASE_URL}/admin/users/${userId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify(userData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert('Hata: ' + data.error);
        } else {
            alert('Kullanıcı güncellendi');
            // Modal'ı kapat
            const modal = bootstrap.Modal.getInstance(document.getElementById('userEditModal'));
            modal.hide();
            // Kullanıcı listesini yenile
            loadUsers(currentUsersPage);
            loadDashboard();
        }
    })
    .catch(error => {
        console.error('Kullanıcı güncelleme hatası:', error);
        alert('Hata: ' + error.message);
    });
}

function deleteUser(userId) {
    if (!confirm('Bu kullanıcıyı silmek istediğinize emin misiniz?')) {
        return;
    }

    fetch(`${API_BASE_URL}/admin/users/${userId}`, {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${authToken}`
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert('Hata: ' + data.error);
        } else {
            alert('Kullanıcı silindi');
            loadUsers(currentUsersPage);
            loadDashboard();
        }
    })
    .catch(error => {
        alert('Hata: ' + error.message);
    });
}

// Foods
let currentFoodsPage = 1;
function loadFoods(page = 1) {
    console.log('loadFoods çağrıldı, sayfa:', page);
    currentFoodsPage = page;
    const search = document.getElementById('foodSearch')?.value || '';
    
    const tbody = document.getElementById('foodsTableBody');
    if (tbody) {
        tbody.innerHTML = '<tr><td colspan="9" class="text-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Yükleniyor...</span></div></td></tr>';
    }
    
    fetch(`${API_BASE_URL}/admin/foods?page=${page}&limit=50`, {
        headers: {
            'Authorization': `Bearer ${authToken}`
        }
    })
    .then(response => {
        console.log('Besinler response status:', response.status);
        if (!response.ok) {
            return response.json().then(err => {
                throw new Error(err.error || 'Besinler yüklenemedi');
            });
        }
        return response.json();
    })
    .then(data => {
        console.log('Besinler data:', data);
        if (data.error) {
            if (data.error === 'Yetkisiz erişim') {
                logout();
                return;
            }
            alert('Hata: ' + data.error);
            return;
        }
        if (data.foods) {
            displayFoods(data.foods);
            displayFoodsPagination(data.total, data.page, data.limit);
        } else {
            console.error('Besinler data.foods yok:', data);
        }
    })
    .catch(error => {
        console.error('Besin yükleme hatası:', error);
        if (tbody) {
            tbody.innerHTML = `<tr><td colspan="9" class="text-center text-danger">Hata: ${error.message}</td></tr>`;
        }
    });
}

function displayFoods(foods) {
    const tbody = document.getElementById('foodsTableBody');
    const search = document.getElementById('foodSearch').value.toLowerCase();
    
    let filteredFoods = foods;
    if (search) {
        filteredFoods = foods.filter(food => 
            food.name.toLowerCase().includes(search)
        );
    }

    if (filteredFoods.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="text-center">Besin bulunamadı</td></tr>';
        return;
    }

    tbody.innerHTML = filteredFoods.map(food => `
        <tr>
            <td>${food.id}</td>
            <td>${food.name}</td>
            <td>${food.calories}</td>
            <td>${food.protein || '-'}</td>
            <td>${food.carbs || '-'}</td>
            <td>${food.fat || '-'}</td>
            <td>${food.serving_size || '-'}</td>
            <td>${food.category || '-'}</td>
            <td>
                <button class="btn btn-sm btn-danger" onclick="deleteFood(${food.id})">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

function displayFoodsPagination(total, page, limit) {
    const totalPages = Math.ceil(total / limit);
    const pagination = document.getElementById('foodsPagination');
    
    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }

    let html = '';
    for (let i = 1; i <= totalPages; i++) {
        html += `
            <li class="page-item ${i === page ? 'active' : ''}">
                <a class="page-link" href="#" onclick="loadFoods(${i}); return false;">${i}</a>
            </li>
        `;
    }
    pagination.innerHTML = html;
}

function handleAddFood(e) {
    e.preventDefault();
    
    const foodData = {
        name: document.getElementById('foodName').value,
        calories: parseFloat(document.getElementById('foodCalories').value),
        protein: parseFloat(document.getElementById('foodProtein').value) || 0,
        carbs: parseFloat(document.getElementById('foodCarbs').value) || 0,
        fat: parseFloat(document.getElementById('foodFat').value) || 0,
        serving_size: document.getElementById('foodServing').value || null,
        category: document.getElementById('foodCategory').value || 'Diğer',
        barcode: document.getElementById('foodBarcode').value || null
    };

    fetch(`${API_BASE_URL}/admin/foods`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify(foodData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert('Hata: ' + data.error);
        } else {
            alert('Besin eklendi');
            document.getElementById('addFoodForm').reset();
            loadFoods(currentFoodsPage);
            loadDashboard();
        }
    })
    .catch(error => {
        alert('Hata: ' + error.message);
    });
}

function deleteFood(foodId) {
    if (!confirm('Bu besini silmek istediğinize emin misiniz?')) {
        return;
    }

    fetch(`${API_BASE_URL}/admin/foods/${foodId}`, {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${authToken}`
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert('Hata: ' + data.error);
        } else {
            alert('Besin silindi');
            loadFoods(currentFoodsPage);
            loadDashboard();
        }
    })
    .catch(error => {
        alert('Hata: ' + error.message);
    });
}

// Utility functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Logs
let currentLogsPage = 1;
function loadLogs(page = 1) {
    console.log('loadLogs çağrıldı, sayfa:', page);
    currentLogsPage = page;
    const logType = document.getElementById('logTypeFilter')?.value || 'all';
    const dateFrom = document.getElementById('logDateFrom')?.value || null;
    const dateTo = document.getElementById('logDateTo')?.value || null;
    
    const tbody = document.getElementById('logsTableBody');
    if (tbody) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Yükleniyor...</span></div></td></tr>';
    }
    
    let url = `${API_BASE_URL}/admin/logs?page=${page}&limit=50&type=${logType}`;
    if (dateFrom) url += `&date_from=${dateFrom}`;
    if (dateTo) url += `&date_to=${dateTo}`;
    
    fetch(url, {
        headers: {
            'Authorization': `Bearer ${authToken}`
        }
    })
    .then(response => {
        console.log('Loglar response status:', response.status);
        if (!response.ok) {
            return response.json().then(err => {
                throw new Error(err.error || 'Loglar yüklenemedi');
            });
        }
        return response.json();
    })
    .then(data => {
        console.log('Loglar data:', data);
        if (data.error) {
            if (data.error === 'Yetkisiz erişim') {
                logout();
                return;
            }
            alert('Hata: ' + data.error);
            return;
        }
        if (data.logs) {
            displayLogs(data.logs);
            displayLogsPagination(data.total, data.page, data.limit);
        } else {
            console.error('Loglar data.logs yok:', data);
        }
    })
    .catch(error => {
        console.error('Log yükleme hatası:', error);
        if (tbody) {
            tbody.innerHTML = `<tr><td colspan="5" class="text-center text-danger">Hata: ${error.message}</td></tr>`;
        }
    });
}

function displayLogs(logs) {
    const tbody = document.getElementById('logsTableBody');
    
    if (!logs || logs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center">Log bulunamadı</td></tr>';
        return;
    }
    
    tbody.innerHTML = logs.map(log => {
        let detail = '';
        let typeLabel = '';
        let typeIcon = '';
        let badgeClass = 'bg-primary';
        
        if (log.log_type === 'daily') {
            typeLabel = 'Besin';
            typeIcon = '🍽️';
            badgeClass = 'bg-success';
            detail = `<strong>${log.meal_type || 'Öğün'}:</strong> ${log.food_name || 'Bilinmeyen'} - ${log.calories || 0} kcal`;
            if (log.quantity && log.quantity > 1) {
                detail += ` <span class="badge bg-secondary">${log.quantity}x</span>`;
            }
            if (log.protein || log.carbs || log.fat) {
                detail += `<br><small class="text-muted">P: ${log.protein || 0}g, K: ${log.carbs || 0}g, Y: ${log.fat || 0}g</small>`;
            }
        } else if (log.log_type === 'water') {
            typeLabel = 'Su';
            typeIcon = '💧';
            badgeClass = 'bg-info';
            detail = `<strong>${log.amount || 0} ml</strong>`;
        } else if (log.log_type === 'exercise') {
            typeLabel = 'Egzersiz';
            typeIcon = '🏃';
            badgeClass = 'bg-warning';
            detail = `<strong>${log.exercise_name || 'Bilinmeyen'}</strong><br>`;
            if (log.duration) detail += `<small>Süre: ${log.duration} dakika</small><br>`;
            if (log.calories_burned) detail += `<small>Yakılan: ${log.calories_burned} kcal</small>`;
        } else if (log.log_type === 'weight') {
            typeLabel = 'Kilo';
            typeIcon = '⚖️';
            badgeClass = 'bg-danger';
            detail = `<strong>${log.weight || 0} kg</strong>`;
        }
        
        const userName = log.name || log.email || `Kullanıcı #${log.user_id}`;
        const logDate = log.date ? new Date(log.date).toLocaleDateString('tr-TR') : '-';
        const createdAt = log.created_at ? new Date(log.created_at).toLocaleString('tr-TR') : '-';
        
        return `
            <tr>
                <td><span class="badge ${badgeClass}">${typeIcon} ${typeLabel}</span></td>
                <td>${userName}<br><small class="text-muted">ID: ${log.user_id}</small></td>
                <td>${logDate}</td>
                <td>${detail}</td>
                <td><small>${createdAt}</small></td>
            </tr>
        `;
    }).join('');
}

function displayLogsPagination(total, page, limit) {
    const totalPages = Math.ceil(total / limit);
    const pagination = document.getElementById('logsPagination');
    
    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }

    let html = '';
    for (let i = 1; i <= totalPages; i++) {
        html += `
            <li class="page-item ${i === page ? 'active' : ''}">
                <a class="page-link" href="#" onclick="loadLogs(${i}); return false;">${i}</a>
            </li>
        `;
    }
    pagination.innerHTML = html;
}

// Make functions global
window.showSection = showSection;
window.loadUsers = loadUsers;
window.loadFoods = loadFoods;
window.loadLogs = loadLogs;
window.editUser = editUser;
window.saveUserEdit = saveUserEdit;
window.deleteUser = deleteUser;
window.deleteFood = deleteFood;

