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

// Login screen göster
function showLoginScreen() {
    document.getElementById('loginScreen').classList.remove('hidden');
    document.getElementById('adminPanel').classList.add('hidden');
}

// Admin panel göster
function showAdminPanel() {
    document.getElementById('loginScreen').classList.add('hidden');
    document.getElementById('adminPanel').classList.remove('hidden');
}

// Logout
function logout() {
    localStorage.removeItem('adminToken');
    authToken = null;
    showLoginScreen();
}

// Section göster
function showSection(section) {
    // Tüm section'ları gizle
    document.querySelectorAll('.section').forEach(s => s.classList.add('hidden'));
    // Tüm nav link'leri deaktif et
    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
    // Seçilen section'ı göster
    document.getElementById(section + 'Section').classList.remove('hidden');
    // Seçilen nav link'i aktif et
    event.target.classList.add('active');
    
    // Section'a göre veri yükle
    if (section === 'dashboard') {
        loadDashboard();
    } else if (section === 'users') {
        loadUsers(1);
    } else if (section === 'foods') {
        loadFoods(1);
    } else if (section === 'logs') {
        loadLogs(1);
    }
}

// Login handler
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

// Dashboard yükle
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
        document.getElementById('totalUsers').textContent = data.total_users || 0;
        document.getElementById('totalFoods').textContent = data.total_foods || 0;
        document.getElementById('todayLogs').textContent = data.today_logs || 0;
        document.getElementById('activeUsers').textContent = data.active_users || 0;
        drawActivityChart(data.activity_data || []);
    })
    .catch(error => {
        console.error('Dashboard yükleme hatası:', error);
    });
}

// Activity chart çiz
function drawActivityChart(data) {
    const ctx = document.getElementById('activityChart');
    if (!ctx) return;
    
    if (activityChart) {
        activityChart.destroy();
    }
    
    const labels = data.map(d => {
        const date = new Date(d.date);
        return date.toLocaleDateString('tr-TR', { day: 'numeric', month: 'short' });
    });
    const counts = data.map(d => d.count);
    
    activityChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Aktif Kullanıcı Sayısı',
                data: counts,
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
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

// Kullanıcıları yükle
function loadUsers(page = 1) {
    const search = document.getElementById('userSearch')?.value || '';
    const url = `${API_BASE_URL}/admin/users?page=${page}&limit=20${search ? `&search=${encodeURIComponent(search)}` : ''}`;
    
    document.getElementById('usersTable').innerHTML = '<div class="loading"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Yükleniyor...</span></div></div>';
    
    fetch(url, {
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
        displayUsers(data.users || []);
        displayUsersPagination(data.total || 0, data.page || 1, data.limit || 20);
    })
    .catch(error => {
        console.error('Kullanıcı yükleme hatası:', error);
        document.getElementById('usersTable').innerHTML = '<div class="alert alert-danger">Kullanıcılar yüklenirken hata oluştu.</div>';
    });
}

// Kullanıcıları göster
function displayUsers(users) {
    if (users.length === 0) {
        document.getElementById('usersTable').innerHTML = '<div class="alert alert-info">Kullanıcı bulunamadı.</div>';
        return;
    }
    
    const table = `
        <table class="table table-striped table-hover">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Ad</th>
                    <th>Email</th>
                    <th>Yaş</th>
                    <th>Cinsiyet</th>
                    <th>Kilo</th>
                    <th>Hedef</th>
                    <th>Kayıt Tarihi</th>
                    <th>İşlemler</th>
                </tr>
            </thead>
            <tbody>
                ${users.map(user => `
                    <tr>
                        <td>${user.id}</td>
                        <td>${user.name || '-'}</td>
                        <td>${user.email}</td>
                        <td>${user.age || '-'}</td>
                        <td>${user.gender || '-'}</td>
                        <td>${user.weight || '-'}</td>
                        <td>${user.goal || '-'}</td>
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
                `).join('')}
            </tbody>
        </table>
    `;
    document.getElementById('usersTable').innerHTML = table;
}

// Kullanıcı pagination göster
function displayUsersPagination(total, page, limit) {
    const totalPages = Math.ceil(total / limit);
    const pagination = document.getElementById('usersPagination');
    
    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }
    
    let html = '<nav><ul class="pagination">';
    for (let i = 1; i <= totalPages; i++) {
        html += `<li class="page-item ${i === page ? 'active' : ''}">
            <a class="page-link" href="#" onclick="loadUsers(${i}); return false;">${i}</a>
        </li>`;
    }
    html += '</ul></nav>';
    pagination.innerHTML = html;
}

// Kullanıcı düzenle
function editUser(userId) {
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
        const user = data.user || data;
        // Modal aç ve kullanıcı bilgilerini göster
        const modal = new bootstrap.Modal(document.getElementById('editUserModal'));
        document.getElementById('editUserId').value = user.id;
        document.getElementById('editUserName').value = user.name || '';
        document.getElementById('editUserEmail').value = user.email || '';
        document.getElementById('editUserAge').value = user.age || '';
        document.getElementById('editUserGender').value = user.gender || '';
        document.getElementById('editUserHeight').value = user.height || '';
        document.getElementById('editUserWeight').value = user.weight || '';
        document.getElementById('editUserTargetWeight').value = user.target_weight || '';
        document.getElementById('editUserActivityLevel').value = user.activity_level || '';
        document.getElementById('editUserGoal').value = user.goal || '';
        
        // Şifre modal için user ID'yi sakla
        document.getElementById('changePasswordUserId').value = user.id;
        
        // Hata mesajını temizle
        document.getElementById('editUserError').classList.add('hidden');
        document.getElementById('editUserError').textContent = '';
        
        modal.show();
    })
    .catch(error => {
        console.error('Kullanıcı detay hatası:', error);
        alert('Kullanıcı bilgileri yüklenirken hata oluştu.');
    });
}

// Kullanıcı kaydet
function saveUserEdit() {
    const userId = document.getElementById('editUserId').value;
    const errorDiv = document.getElementById('editUserError');
    
    // Validation
    const email = document.getElementById('editUserEmail').value.trim();
    if (!email || !email.includes('@')) {
        errorDiv.textContent = 'Geçerli bir email adresi giriniz';
        errorDiv.classList.remove('hidden');
        return;
    }
    
    const userData = {
        name: document.getElementById('editUserName').value.trim() || null,
        email: email,
        age: document.getElementById('editUserAge').value ? parseInt(document.getElementById('editUserAge').value) : null,
        gender: document.getElementById('editUserGender').value || null,
        height: document.getElementById('editUserHeight').value ? parseFloat(document.getElementById('editUserHeight').value) : null,
        weight: document.getElementById('editUserWeight').value ? parseFloat(document.getElementById('editUserWeight').value) : null,
        target_weight: document.getElementById('editUserTargetWeight').value ? parseFloat(document.getElementById('editUserTargetWeight').value) : null,
        activity_level: document.getElementById('editUserActivityLevel').value || null,
        goal: document.getElementById('editUserGoal').value || null
    };
    
    // Loading göster
    const saveBtn = document.querySelector('#editUserModal .btn-primary');
    const originalText = saveBtn.innerHTML;
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Kaydediliyor...';
    
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
            errorDiv.textContent = data.error;
            errorDiv.classList.remove('hidden');
            saveBtn.disabled = false;
            saveBtn.innerHTML = originalText;
        } else {
            alert('Kullanıcı güncellendi!');
            bootstrap.Modal.getInstance(document.getElementById('editUserModal')).hide();
            loadUsers(1);
            loadDashboard();
        }
    })
    .catch(error => {
        console.error('Kullanıcı güncelleme hatası:', error);
        errorDiv.textContent = 'Kullanıcı güncellenirken hata oluştu: ' + error.message;
        errorDiv.classList.remove('hidden');
        saveBtn.disabled = false;
        saveBtn.innerHTML = originalText;
    });
}

// Şifre değiştir modal'ını göster
function showChangePasswordModal() {
    const userId = document.getElementById('editUserId').value;
    if (!userId) {
        alert('Kullanıcı seçilmedi!');
        return;
    }
    
    // Kullanıcı düzenleme modal'ını kapat
    const editModal = bootstrap.Modal.getInstance(document.getElementById('editUserModal'));
    if (editModal) {
        editModal.hide();
    }
    
    // Şifre değiştir modal'ını aç
    document.getElementById('changePasswordUserId').value = userId;
    document.getElementById('changePasswordNew').value = '';
    document.getElementById('changePasswordConfirm').value = '';
    document.getElementById('changePasswordError').classList.add('hidden');
    document.getElementById('changePasswordError').textContent = '';
    
    const passwordModal = new bootstrap.Modal(document.getElementById('changePasswordModal'));
    passwordModal.show();
}

// Şifre değiştir
function savePasswordChange() {
    const userId = document.getElementById('changePasswordUserId').value;
    const newPassword = document.getElementById('changePasswordNew').value;
    const confirmPassword = document.getElementById('changePasswordConfirm').value;
    const errorDiv = document.getElementById('changePasswordError');
    
    // Validation
    if (!newPassword) {
        errorDiv.textContent = 'Yeni şifre gerekli';
        errorDiv.classList.remove('hidden');
        return;
    }
    
    if (newPassword.length < 6) {
        errorDiv.textContent = 'Şifre en az 6 karakter olmalıdır';
        errorDiv.classList.remove('hidden');
        return;
    }
    
    if (newPassword !== confirmPassword) {
        errorDiv.textContent = 'Şifreler eşleşmiyor';
        errorDiv.classList.remove('hidden');
        return;
    }
    
    // Loading göster
    const saveBtn = document.querySelector('#changePasswordModal .btn-primary');
    const originalText = saveBtn.innerHTML;
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Değiştiriliyor...';
    
    fetch(`${API_BASE_URL}/admin/users/${userId}/password`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({ password: newPassword })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            errorDiv.textContent = data.error;
            errorDiv.classList.remove('hidden');
            saveBtn.disabled = false;
            saveBtn.innerHTML = originalText;
        } else {
            alert('Şifre değiştirildi!');
            bootstrap.Modal.getInstance(document.getElementById('changePasswordModal')).hide();
        }
    })
    .catch(error => {
        console.error('Şifre değiştirme hatası:', error);
        errorDiv.textContent = 'Şifre değiştirilirken hata oluştu: ' + error.message;
        errorDiv.classList.remove('hidden');
        saveBtn.disabled = false;
        saveBtn.innerHTML = originalText;
    });
}

// Kullanıcı sil
function deleteUser(userId) {
    if (!confirm('Bu kullanıcıyı silmek istediğinizden emin misiniz?')) {
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
            alert('Kullanıcı silindi!');
            loadUsers(1);
            loadDashboard();
        }
    })
    .catch(error => {
        console.error('Kullanıcı silme hatası:', error);
        alert('Kullanıcı silinirken hata oluştu.');
    });
}

// Besinleri yükle
function loadFoods(page = 1) {
    const search = document.getElementById('foodSearch')?.value || '';
    const url = `${API_BASE_URL}/admin/foods?page=${page}&limit=50${search ? `&search=${encodeURIComponent(search)}` : ''}`;
    
    document.getElementById('foodsTable').innerHTML = '<div class="loading"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Yükleniyor...</span></div></div>';
    
    fetch(url, {
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
        displayFoods(data.foods || []);
        displayFoodsPagination(data.total || 0, data.page || 1, data.limit || 50);
    })
    .catch(error => {
        console.error('Besin yükleme hatası:', error);
        document.getElementById('foodsTable').innerHTML = '<div class="alert alert-danger">Besinler yüklenirken hata oluştu.</div>';
    });
}

// Besinleri göster
function displayFoods(foods) {
    if (foods.length === 0) {
        document.getElementById('foodsTable').innerHTML = '<div class="alert alert-info">Besin bulunamadı.</div>';
        return;
    }
    
    const table = `
        <table class="table table-striped table-hover">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Ad</th>
                    <th>Kalori</th>
                    <th>Protein (g)</th>
                    <th>Karbonhidrat (g)</th>
                    <th>Yağ (g)</th>
                    <th>Porsiyon</th>
                    <th>Kategori</th>
                    <th>İşlemler</th>
                </tr>
            </thead>
            <tbody>
                ${foods.map(food => `
                    <tr>
                        <td>${food.id}</td>
                        <td>${food.name}</td>
                        <td>${food.calories || 0}</td>
                        <td>${food.protein || 0}</td>
                        <td>${food.carbs || 0}</td>
                        <td>${food.fat || 0}</td>
                        <td>${food.serving_size || '-'}</td>
                        <td>${food.category || '-'}</td>
                        <td>
                            <button class="btn btn-sm btn-danger" onclick="deleteFood(${food.id})" title="Sil">
                                <i class="fas fa-trash"></i>
                            </button>
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
    document.getElementById('foodsTable').innerHTML = table;
}

// Besin pagination göster
function displayFoodsPagination(total, page, limit) {
    const totalPages = Math.ceil(total / limit);
    const pagination = document.getElementById('foodsPagination');
    
    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }
    
    let html = '<nav><ul class="pagination">';
    for (let i = 1; i <= totalPages; i++) {
        html += `<li class="page-item ${i === page ? 'active' : ''}">
            <a class="page-link" href="#" onclick="loadFoods(${i}); return false;">${i}</a>
        </li>`;
    }
    html += '</ul></nav>';
    pagination.innerHTML = html;
}

// Besin ekle
function handleAddFood(e) {
    e.preventDefault();
    
    const foodData = {
        name: document.getElementById('foodName').value.trim(),
        calories: parseFloat(document.getElementById('foodCalories').value) || 0,
        protein: parseFloat(document.getElementById('foodProtein').value) || 0,
        carbs: parseFloat(document.getElementById('foodCarbs').value) || 0,
        fat: parseFloat(document.getElementById('foodFat').value) || 0,
        serving_size: document.getElementById('foodServing').value.trim() || null,
        category: document.getElementById('foodCategory').value.trim() || 'Diğer',
        barcode: document.getElementById('foodBarcode').value.trim() || null
    };
    
    // Loading göster
    const submitBtn = e.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    
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
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
        } else {
            alert('Besin eklendi!');
            document.getElementById('addFoodForm').reset();
            loadFoods(1);
            loadDashboard();
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
        }
    })
    .catch(error => {
        console.error('Besin ekleme hatası:', error);
        alert('Besin eklenirken hata oluştu: ' + error.message);
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
    });
}

// Besin sil
function deleteFood(foodId) {
    if (!confirm('Bu besini silmek istediğinizden emin misiniz?')) {
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
            alert('Besin silindi!');
            loadFoods(1);
            loadDashboard();
        }
    })
    .catch(error => {
        console.error('Besin silme hatası:', error);
        alert('Besin silinirken hata oluştu.');
    });
}

// Logları yükle
function loadLogs(page = 1) {
    const logType = document.getElementById('logTypeFilter')?.value || 'all';
    const dateFrom = document.getElementById('logDateFrom')?.value || null;
    const dateTo = document.getElementById('logDateTo')?.value || null;
    
    let url = `${API_BASE_URL}/admin/logs?page=${page}&limit=50&type=${logType}`;
    if (dateFrom) url += `&date_from=${dateFrom}`;
    if (dateTo) url += `&date_to=${dateTo}`;
    
    document.getElementById('logsTable').innerHTML = '<div class="loading"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Yükleniyor...</span></div></div>';
    
    fetch(url, {
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
        displayLogs(data.logs || []);
        displayLogsPagination(data.total || 0, data.page || 1, data.limit || 50);
    })
    .catch(error => {
        console.error('Log yükleme hatası:', error);
        document.getElementById('logsTable').innerHTML = '<div class="alert alert-danger">Loglar yüklenirken hata oluştu.</div>';
    });
}

// Logları göster
function displayLogs(logs) {
    if (logs.length === 0) {
        document.getElementById('logsTable').innerHTML = '<div class="alert alert-info">Log bulunamadı.</div>';
        return;
    }
    
    const rows = logs.map(log => {
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
    
    const table = `
        <table class="table table-striped table-hover">
            <thead>
                <tr>
                    <th>Tür</th>
                    <th>Kullanıcı</th>
                    <th>Tarih</th>
                    <th>Detay</th>
                    <th>Oluşturma</th>
                </tr>
            </thead>
            <tbody>
                ${rows}
            </tbody>
        </table>
    `;
    document.getElementById('logsTable').innerHTML = table;
}

// Log pagination göster
function displayLogsPagination(total, page, limit) {
    const totalPages = Math.ceil(total / limit);
    const pagination = document.getElementById('logsPagination');
    
    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }
    
    let html = '<nav><ul class="pagination">';
    for (let i = 1; i <= totalPages; i++) {
        html += `<li class="page-item ${i === page ? 'active' : ''}">
            <a class="page-link" href="#" onclick="loadLogs(${i}); return false;">${i}</a>
        </li>`;
    }
    html += '</ul></nav>';
    pagination.innerHTML = html;
}

// Debounce helper
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

// Make functions global
window.showSection = showSection;
window.loadUsers = loadUsers;
window.loadFoods = loadFoods;
window.loadLogs = loadLogs;
window.editUser = editUser;
window.saveUserEdit = saveUserEdit;
window.showChangePasswordModal = showChangePasswordModal;
window.savePasswordChange = savePasswordChange;
window.deleteUser = deleteUser;
window.deleteFood = deleteFood;
