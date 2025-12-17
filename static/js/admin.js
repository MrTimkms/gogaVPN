let adminTelegramId = null;
let allUsers = []; // Сохраняем всех пользователей для фильтрации

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
        allUsers = users; // Сохраняем для фильтрации
        displayUsers(users);
        updateUsersStats(users);
    } catch (error) {
        console.error('Error loading users:', error);
    }
}

// Отображение пользователей в таблице
function displayUsers(users) {
    const tbody = document.getElementById('usersTableBody');
    tbody.innerHTML = users.map(user => {
            const billingDate = user.next_billing_date ? new Date(user.next_billing_date).toLocaleDateString('ru-RU') : '-';
            const notifyStatus = user.enable_billing_notifications 
                ? `<span class="badge bg-info" title="Уведомления за ${user.notify_before_billing_days} дн.">🔔</span>` 
                : '<span class="badge bg-secondary" title="Уведомления отключены">🔕</span>';
            const telegramLink = user.telegram_id 
                ? `<a href="tg://user?id=${user.telegram_id}" class="text-decoration-none" title="Открыть диалог в Telegram">${user.telegram_id} <i class="bi bi-telegram"></i></a>`
                : '-';
            return `
            <tr>
                <td>${user.id}</td>
                <td>${user.name}</td>
                <td>${telegramLink}</td>
                <td>${user.balance.toFixed(2)} ₽</td>
                <td>${billingDate} ${notifyStatus}</td>
                <td>${getStatusBadge(user.status)}</td>
                <td>
                    <div class="btn-group" role="group">
                        <button class="btn btn-sm btn-primary" onclick="openUserModal(${user.id})" title="Управление">
                            <i class="bi bi-gear"></i>
                        </button>
                        ${user.status === 'active' 
                            ? `<button class="btn btn-sm btn-danger" onclick="quickBlockUser(${user.id})" title="Заблокировать">
                                <i class="bi bi-lock"></i>
                               </button>`
                            : `<button class="btn btn-sm btn-success" onclick="quickUnblockUser(${user.id})" title="Разблокировать">
                                <i class="bi bi-unlock"></i>
                               </button>`
                        }
                        <button class="btn btn-sm btn-info" onclick="showUserTransactions(${user.id})" title="Транзакции">
                            <i class="bi bi-list-ul"></i>
                        </button>
                    </div>
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
        tbody.innerHTML = debtors.map(user => {
            const telegramLink = user.telegram_id 
                ? `<a href="tg://user?id=${user.telegram_id}" class="text-decoration-none" title="Открыть диалог в Telegram">${user.telegram_id} <i class="bi bi-telegram"></i></a>`
                : '-';
            return `
            <tr>
                <td>${user.id}</td>
                <td>${user.name}</td>
                <td>${telegramLink}</td>
                <td>${user.balance.toFixed(2)} ₽</td>
                <td>
                    <button class="btn btn-sm btn-primary" onclick="openUserModal(${user.id})">Управление</button>
                </td>
            </tr>
        `;
        }).join('');
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
        document.getElementById('modalUserEnableNegativeBalanceNotifications').checked = user.enable_negative_balance_notifications !== false;
        document.getElementById('modalUserNotifyDays').value = user.notify_before_billing_days || 2;
        document.getElementById('notificationMessage').value = ''; // Очищаем поле уведомления
        
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

// Обновление имени пользователя
async function updateUserName() {
    const userId = parseInt(document.getElementById('modalUserId').value);
    const name = document.getElementById('modalUserName').value.trim();
    
    if (!name) {
        alert('Введите имя');
        return;
    }
    
    try {
        const response = await fetch(`/api/admin/users/${userId}?telegram_id=${adminTelegramId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: name
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Ошибка обновления');
        }
        
        alert('Имя обновлено');
        loadUsers();
        loadDebtors();
        loadGhostUsers();
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
    const enableNegativeBalanceNotifications = document.getElementById('modalUserEnableNegativeBalanceNotifications').checked;
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
                enable_negative_balance_notifications: enableNegativeBalanceNotifications,
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

// Отправка уведомления пользователю
async function sendNotificationToUser() {
    const userId = parseInt(document.getElementById('modalUserId').value);
    const message = document.getElementById('notificationMessage').value.trim();
    
    if (!message) {
        alert('Введите текст уведомления');
        return;
    }
    
    if (!confirm('Отправить уведомление пользователю?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/admin/send-notification?telegram_id=${adminTelegramId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: userId,
                message: message
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Ошибка отправки');
        }
        
        const result = await response.json();
        alert('✅ ' + result.message);
        document.getElementById('notificationMessage').value = ''; // Очищаем поле
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

// Поиск и фильтрация пользователей
function filterUsers() {
    const searchText = document.getElementById('userSearchInput')?.value.toLowerCase() || '';
    const statusFilter = document.getElementById('statusFilter')?.value || '';
    
    let filtered = allUsers.filter(user => {
        const matchesSearch = !searchText || 
            user.name.toLowerCase().includes(searchText) ||
            user.id.toString().includes(searchText) ||
            (user.telegram_id && user.telegram_id.toString().includes(searchText));
        
        const matchesStatus = !statusFilter || user.status === statusFilter;
        
        return matchesSearch && matchesStatus;
    });
    
    displayUsers(filtered);
    updateUsersStats(filtered);
}

// Обновление статистики пользователей
function updateUsersStats(users) {
    const statsDiv = document.getElementById('usersStats');
    if (!statsDiv) return;
    
    const total = users.length;
    const active = users.filter(u => u.status === 'active').length;
    const blocked = users.filter(u => u.status === 'blocked').length;
    const debt = users.filter(u => u.status === 'debt').length;
    const totalBalance = users.reduce((sum, u) => sum + u.balance, 0);
    
    statsDiv.innerHTML = `
        <div class="row g-2">
            <div class="col-md-2">
                <div class="card bg-primary text-white">
                    <div class="card-body p-2">
                        <small>Всего</small>
                        <h5 class="mb-0">${total}</h5>
                    </div>
                </div>
            </div>
            <div class="col-md-2">
                <div class="card bg-success text-white">
                    <div class="card-body p-2">
                        <small>Активных</small>
                        <h5 class="mb-0">${active}</h5>
                    </div>
                </div>
            </div>
            <div class="col-md-2">
                <div class="card bg-danger text-white">
                    <div class="card-body p-2">
                        <small>Должников</small>
                        <h5 class="mb-0">${debt}</h5>
                    </div>
                </div>
            </div>
            <div class="col-md-2">
                <div class="card bg-secondary text-white">
                    <div class="card-body p-2">
                        <small>Заблокированных</small>
                        <h5 class="mb-0">${blocked}</h5>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card bg-info text-white">
                    <div class="card-body p-2">
                        <small>Общий баланс</small>
                        <h5 class="mb-0">${totalBalance.toFixed(2)} ₽</h5>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Быстрая блокировка пользователя
async function quickBlockUser(userId) {
    if (!confirm('Заблокировать пользователя?')) return;
    
    try {
        const response = await fetch(`/api/admin/users/${userId}?telegram_id=${adminTelegramId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: 'blocked' })
        });
        
        if (!response.ok) throw new Error('Ошибка блокировки');
        
        alert('Пользователь заблокирован');
        loadUsers();
        loadDebtors();
    } catch (error) {
        alert('Ошибка: ' + error.message);
    }
}

// Быстрая разблокировка пользователя
async function quickUnblockUser(userId) {
    if (!confirm('Разблокировать пользователя?')) return;
    
    try {
        const response = await fetch(`/api/admin/users/${userId}?telegram_id=${adminTelegramId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: 'active' })
        });
        
        if (!response.ok) throw new Error('Ошибка разблокировки');
        
        alert('Пользователь разблокирован');
        loadUsers();
        loadDebtors();
    } catch (error) {
        alert('Ошибка: ' + error.message);
    }
}

// Просмотр транзакций пользователя
async function showUserTransactions(userId) {
    try {
        const response = await fetch(`/api/users/${userId}/transactions`);
        if (!response.ok) throw new Error('Ошибка загрузки');
        
        const transactions = await response.json();
        const user = allUsers.find(u => u.id === userId);
        
        let html = `
            <div class="modal fade" id="transactionsModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Транзакции: ${user ? user.name : 'Пользователь #' + userId}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <table class="table table-sm">
                                <thead>
                                    <tr>
                                        <th>Дата</th>
                                        <th>Тип</th>
                                        <th>Сумма</th>
                                        <th>Описание</th>
                                    </tr>
                                </thead>
                                <tbody>
        `;
        
        if (transactions.length === 0) {
            html += '<tr><td colspan="4" class="text-center">Транзакций нет</td></tr>';
        } else {
            transactions.forEach(t => {
                const date = new Date(t.created_at).toLocaleString('ru-RU');
                const typeBadge = t.transaction_type === 'deposit' 
                    ? '<span class="badge bg-success">Пополнение</span>'
                    : t.transaction_type === 'withdrawal'
                    ? '<span class="badge bg-danger">Списание</span>'
                    : '<span class="badge bg-warning">Корректировка</span>';
                const amountClass = t.amount >= 0 ? 'text-success' : 'text-danger';
                html += `
                    <tr>
                        <td>${date}</td>
                        <td>${typeBadge}</td>
                        <td class="${amountClass}">${t.amount >= 0 ? '+' : ''}${t.amount.toFixed(2)} ₽</td>
                        <td>${t.description || '-'}</td>
                    </tr>
                `;
            });
        }
        
        html += `
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Удаляем старый модал если есть
        const oldModal = document.getElementById('transactionsModal');
        if (oldModal) oldModal.remove();
        
        // Добавляем новый модал
        document.body.insertAdjacentHTML('beforeend', html);
        const modal = new bootstrap.Modal(document.getElementById('transactionsModal'));
        modal.show();
    } catch (error) {
        alert('Ошибка: ' + error.message);
    }
}

// Экспорт пользователей в CSV
function exportUsersToCSV() {
    if (allUsers.length === 0) {
        alert('Нет данных для экспорта');
        return;
    }
    
    const headers = ['ID', 'Имя', 'Telegram ID', 'Баланс', 'Статус', 'Дата списания'];
    const rows = allUsers.map(user => [
        user.id,
        user.name,
        user.telegram_id || '',
        user.balance.toFixed(2),
        user.status,
        user.next_billing_date || ''
    ]);
    
    const csvContent = [
        headers.join(';'),
        ...rows.map(row => row.join(';'))
    ].join('\n');
    
    const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `users_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
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

