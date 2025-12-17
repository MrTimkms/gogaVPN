let adminTelegramId = null;

// Вход в админ-панель
async function adminLogin() {
    const telegramId = document.getElementById('adminTelegramId').value;
    if (!telegramId) {
        alert('Введите Telegram ID');
        return;
    }
    
    adminTelegramId = parseInt(telegramId);
    document.getElementById('loginSection').style.display = 'none';
    document.getElementById('adminPanel').style.display = 'block';
    
    // Загружаем данные
    loadUsers();
    loadGhostUsers();
    loadDebtors();
    loadSettings();
}

// Импорт CSV
async function importCSV() {
    const fileInput = document.getElementById('csvFile');
    const file = fileInput.files[0];
    
    if (!file) {
        alert('Выберите CSV файл');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('telegram_id', adminTelegramId);
    
    try {
        const response = await fetch('/api/admin/import-csv', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Ошибка импорта');
        }
        
        const result = await response.json();
        const resultDiv = document.getElementById('importResult');
        resultDiv.innerHTML = `
            <div class="alert alert-success">
                <strong>Импорт завершен!</strong><br>
                Импортировано: ${result.imported}<br>
                Спящих профилей: ${result.ghost_users}<br>
                Ошибок: ${result.errors.length}
            </div>
        `;
        
        if (result.errors.length > 0) {
            const errorsList = result.errors.map(e => `Строка ${e.row}: ${e.error}`).join('<br>');
            resultDiv.innerHTML += `<div class="alert alert-warning">${errorsList}</div>`;
        }
        
        // Обновляем списки
        loadUsers();
        loadGhostUsers();
    } catch (error) {
        alert('Ошибка импорта: ' + error.message);
    }
}

// Загрузка пользователей
async function loadUsers() {
    try {
        const response = await fetch(`/api/admin/users?telegram_id=${adminTelegramId}`);
        if (!response.ok) throw new Error('Ошибка загрузки');
        
        const users = await response.json();
        const tbody = document.getElementById('usersTableBody');
        tbody.innerHTML = users.map(user => `
            <tr>
                <td>${user.id}</td>
                <td>${user.name}</td>
                <td>${user.telegram_id || '-'}</td>
                <td>${user.balance.toFixed(2)} ₽</td>
                <td>${getStatusBadge(user.status)}</td>
                <td>
                    <button class="btn btn-sm btn-primary" onclick="openUserModal(${user.id})">Управление</button>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error loading users:', error);
    }
}

// Загрузка спящих профилей
async function loadGhostUsers() {
    try {
        const response = await fetch(`/api/admin/ghost-users?telegram_id=${adminTelegramId}`);
        if (!response.ok) throw new Error('Ошибка загрузки');
        
        const users = await response.json();
        const tbody = document.getElementById('ghostTableBody');
        tbody.innerHTML = users.map(user => `
            <tr>
                <td>${user.id}</td>
                <td>${user.name}</td>
                <td>${user.balance.toFixed(2)} ₽</td>
                <td>
                    <button class="btn btn-sm btn-success" onclick="mapGhostUser(${user.id})">Привязать</button>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error loading ghost users:', error);
    }
}

// Загрузка должников
async function loadDebtors() {
    try {
        const response = await fetch(`/api/admin/debtors?telegram_id=${adminTelegramId}`);
        if (!response.ok) throw new Error('Ошибка загрузки');
        
        const debtors = await response.json();
        const tbody = document.getElementById('debtorsTableBody');
        tbody.innerHTML = debtors.map(user => `
            <tr>
                <td>${user.id}</td>
                <td>${user.name}</td>
                <td>${user.telegram_id || '-'}</td>
                <td>${user.balance.toFixed(2)} ₽</td>
                <td>
                    <button class="btn btn-sm btn-primary" onclick="openUserModal(${user.id})">Управление</button>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error loading debtors:', error);
    }
}

// Загрузка настроек
async function loadSettings() {
    try {
        const response = await fetch(`/api/admin/settings?telegram_id=${adminTelegramId}`);
        if (!response.ok) throw new Error('Ошибка загрузки');
        
        const settings = await response.json();
        document.getElementById('subscriptionPriceInput').value = settings.subscription_price;
    } catch (error) {
        console.error('Error loading settings:', error);
    }
}

// Обновление настроек
async function updateSettings() {
    const price = parseFloat(document.getElementById('subscriptionPriceInput').value);
    
    try {
        const response = await fetch(`/api/admin/settings?telegram_id=${adminTelegramId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ subscription_price: price })
        });
        
        if (!response.ok) throw new Error('Ошибка обновления');
        
        alert('Настройки сохранены');
    } catch (error) {
        alert('Ошибка: ' + error.message);
    }
}

// Открытие модального окна пользователя
async function openUserModal(userId) {
    try {
        const response = await fetch(`/api/users/${userId}`);
        if (!response.ok) throw new Error('Ошибка загрузки');
        
        const user = await response.json();
        document.getElementById('modalUserId').value = user.id;
        document.getElementById('modalUserName').value = user.name;
        document.getElementById('modalUserBalance').value = user.balance;
        document.getElementById('modalUserKey').value = user.key_data || '';
        
        const modal = new bootstrap.Modal(document.getElementById('userModal'));
        modal.show();
    } catch (error) {
        alert('Ошибка: ' + error.message);
    }
}

// Корректировка баланса
async function adjustBalance() {
    const userId = parseInt(document.getElementById('modalUserId').value);
    const amount = parseFloat(document.getElementById('balanceAdjustment').value);
    const description = document.getElementById('balanceDescription').value;
    
    if (!amount || !description) {
        alert('Заполните все поля');
        return;
    }
    
    try {
        const response = await fetch(`/api/admin/adjust-balance?telegram_id=${adminTelegramId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: userId,
                amount: amount,
                description: description
            })
        });
        
        if (!response.ok) throw new Error('Ошибка корректировки');
        
        const result = await response.json();
        document.getElementById('modalUserBalance').value = result.new_balance;
        document.getElementById('balanceAdjustment').value = '';
        document.getElementById('balanceDescription').value = '';
        
        alert('Баланс обновлен');
        loadUsers();
        loadDebtors();
    } catch (error) {
        alert('Ошибка: ' + error.message);
    }
}

// Обновление ключа
async function updateKey() {
    const userId = parseInt(document.getElementById('modalUserId').value);
    const keyData = document.getElementById('modalUserKey').value;
    
    if (!keyData) {
        alert('Введите ключ');
        return;
    }
    
    try {
        const response = await fetch(`/api/admin/update-key?telegram_id=${adminTelegramId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: userId,
                key_data: keyData
            })
        });
        
        if (!response.ok) throw new Error('Ошибка обновления');
        
        alert('Ключ обновлен');
    } catch (error) {
        alert('Ошибка: ' + error.message);
    }
}

// Привязка спящего профиля
async function mapGhostUser(ghostUserId) {
    const telegramId = prompt('Введите Telegram ID пользователя для привязки:');
    if (!telegramId) return;
    
    try {
        const response = await fetch(`/api/admin/map-user?telegram_id=${adminTelegramId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                ghost_user_id: ghostUserId,
                telegram_id: parseInt(telegramId)
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Ошибка привязки');
        }
        
        alert('Пользователь привязан');
        loadGhostUsers();
        loadUsers();
    } catch (error) {
        alert('Ошибка: ' + error.message);
    }
}

// Выход
function logout() {
    adminTelegramId = null;
    document.getElementById('loginSection').style.display = 'block';
    document.getElementById('adminPanel').style.display = 'none';
}

// Вспомогательные функции
function getStatusBadge(status) {
    const badges = {
        'active': '<span class="badge bg-success">Активен</span>',
        'blocked': '<span class="badge bg-secondary">Заблокирован</span>',
        'debt': '<span class="badge bg-danger">Задолженность</span>'
    };
    return badges[status] || status;
}

