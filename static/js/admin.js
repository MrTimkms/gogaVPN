let adminTelegramId = null;

// Вход в админ-панель
async function adminLogin() {
    const telegramId = document.getElementById('adminTelegramId').value;
    if (!telegramId) {
        alert('Введите Telegram ID');
        return;
    }
    
    adminTelegramId = parseInt(telegramId);
    
    // Проверяем, является ли пользователь админом
    try {
        const checkResponse = await fetch(`/api/users/me/${adminTelegramId}/is-admin`);
        if (checkResponse.ok) {
            const adminData = await checkResponse.json();
            if (!adminData.is_admin) {
                alert('❌ Этот Telegram ID не является администратором!\n\nПроверьте настройки ADMIN_TELEGRAM_IDS в файле .env');
                return;
            }
        }
    } catch (error) {
        console.error('Ошибка проверки админа:', error);
    }
    
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
        tbody.innerHTML = users.map(user => {
            const billingDate = user.next_billing_date ? new Date(user.next_billing_date).toLocaleDateString('ru-RU') : '-';
            const notifyStatus = user.enable_billing_notifications 
                ? `<span class="badge bg-info" title="Уведомления за ${user.notify_before_billing_days} дн.">🔔</span>` 
                : '<span class="badge bg-secondary" title="Уведомления отключены">🔕</span>';
            return `
            <tr>
                <td>${user.id}</td>
                <td>${user.name}</td>
                <td>${user.telegram_id || '-'}</td>
                <td>${user.balance.toFixed(2)} ₽</td>
                <td>${billingDate} ${notifyStatus}</td>
                <td>${getStatusBadge(user.status)}</td>
                <td>
                    <button class="btn btn-sm btn-primary" onclick="openUserModal(${user.id})">Управление</button>
                </td>
            </tr>
        `;
        }).join('');
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
        
        // Загрузка СБП информации
        const sbpResponse = await fetch(`/api/admin/sbp-info?telegram_id=${adminTelegramId}`);
        if (sbpResponse.ok) {
            const sbpInfo = await sbpResponse.json();
            if (sbpInfo.phone) {
                document.getElementById('sbpPhoneInput').value = sbpInfo.phone;
            }
            if (sbpInfo.account) {
                document.getElementById('sbpAccountInput').value = sbpInfo.account;
            }
            if (sbpInfo.qr_code_path) {
                const qrContainer = document.getElementById('currentQrCode');
                // Формируем правильный URL для QR-кода
                let qrUrl = sbpInfo.qr_code_path;
                // Если это только имя файла (без директории), добавляем static/uploads/
                if (!qrUrl.includes('/') && !qrUrl.includes('\\')) {
                    qrUrl = `/static/uploads/${qrUrl}`;
                } else if (!qrUrl.startsWith('/')) {
                    qrUrl = `/${qrUrl}`;
                }
                qrContainer.innerHTML = `
                    <label class="form-label">Текущий QR-код:</label>
                    <img src="${qrUrl}" alt="QR Code" class="img-thumbnail" style="max-width: 200px;" onerror="this.style.display='none'; this.nextElementSibling.style.display='block';">
                    <p style="display:none; color: red;">Файл не найден: ${sbpInfo.qr_code_path}</p>
                `;
            }
        }
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

// Обновление СБП информации
async function updateSBPInfo() {
    const phone = document.getElementById('sbpPhoneInput').value;
    const account = document.getElementById('sbpAccountInput').value;
    
    try {
        const response = await fetch(`/api/admin/sbp-info?telegram_id=${adminTelegramId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                phone: phone,
                account: account
            })
        });
        
        if (!response.ok) throw new Error('Ошибка обновления');
        
        alert('Настройки СБП сохранены');
        loadSettings(); // Перезагружаем для отображения QR-кода
    } catch (error) {
        alert('Ошибка: ' + error.message);
    }
}

// Загрузка QR-кода
async function uploadQRCode() {
    const fileInput = document.getElementById('sbpQrFile');
    const file = fileInput.files[0];
    
    if (!file) {
        alert('Выберите файл QR-кода');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('telegram_id', adminTelegramId);
    
    try {
        const response = await fetch('/api/admin/upload-qr', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) throw new Error('Ошибка загрузки');
        
        const result = await response.json();
        alert('QR-код загружен успешно!');
        loadSettings(); // Перезагружаем для отображения
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
        
        // Заполняем дату следующего списания
        if (user.next_billing_date) {
            const date = new Date(user.next_billing_date);
            const dateStr = date.toISOString().split('T')[0];
            document.getElementById('modalUserNextBillingDate').value = dateStr;
        }
        
        // Заполняем настройки уведомлений
        document.getElementById('modalUserEnableNotifications').checked = user.enable_billing_notifications !== false;
        document.getElementById('modalUserNotifyDays').value = user.notify_before_billing_days || 2;
        
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

// Обновление даты следующего списания
async function updateBillingDate() {
    const userId = parseInt(document.getElementById('modalUserId').value);
    const nextBillingDate = document.getElementById('modalUserNextBillingDate').value;
    
    if (!nextBillingDate) {
        alert('Выберите дату');
        return;
    }
    
    try {
        const response = await fetch(`/api/admin/users/${userId}?telegram_id=${adminTelegramId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                next_billing_date: nextBillingDate
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Ошибка обновления');
        }
        
        alert('Дата списания обновлена');
        loadUsers();
    } catch (error) {
        alert('Ошибка: ' + error.message);
    }
}

// Обновление настроек уведомлений
async function updateNotificationSettings() {
    const userId = parseInt(document.getElementById('modalUserId').value);
    const enableNotifications = document.getElementById('modalUserEnableNotifications').checked;
    const notifyDays = parseInt(document.getElementById('modalUserNotifyDays').value);
    
    if (isNaN(notifyDays) || notifyDays < 0 || notifyDays > 30) {
        alert('Количество дней должно быть от 0 до 30');
        return;
    }
    
    try {
        const response = await fetch(`/api/admin/users/${userId}?telegram_id=${adminTelegramId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                enable_billing_notifications: enableNotifications,
                notify_before_billing_days: notifyDays
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Ошибка обновления');
        }
        
        alert('Настройки уведомлений обновлены');
        loadUsers();
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

