let currentUser = null;
let userKey = null;

// Инициализация Telegram Widget
async function initTelegramWidget() {
    // Получаем имя бота с сервера (можно добавить API endpoint)
    const botName = 'YOUR_BOT_NAME'; // Замените на имя вашего бота или получите через API
    const script = document.createElement('script');
    script.src = `https://telegram.org/js/telegram-widget.js?22`;
    script.setAttribute('data-telegram-login', botName);
    script.setAttribute('data-size', 'large');
    script.setAttribute('data-onauth', 'onTelegramAuth(user)');
    script.setAttribute('data-request-access', 'write');
    document.getElementById('telegram-login-container').appendChild(script);
}

// Обработка авторизации через Telegram
function onTelegramAuth(user) {
    console.log('Telegram auth:', user);
    loadUserProfile(user.id);
}

// Вход по ID
async function loginById() {
    const telegramId = document.getElementById('telegramIdInput').value;
    if (!telegramId) {
        alert('Введите Telegram ID');
        return;
    }
    await loadUserProfile(parseInt(telegramId));
}

// Загрузка профиля пользователя
async function loadUserProfile(telegramId) {
    try {
        const response = await fetch(`/api/users/me/${telegramId}`);
        if (!response.ok) {
            if (response.status === 404) {
                alert('Пользователь не найден. Используйте /start в боте для регистрации.');
                return;
            }
            throw new Error('Ошибка загрузки профиля');
        }
        
        currentUser = await response.json();
        userKey = currentUser.key_data;
        
        // Проверяем, является ли пользователь админом
        const adminCheck = await fetch(`/api/users/me/${telegramId}/is-admin`);
        if (adminCheck.ok) {
            const adminData = await adminCheck.json();
            currentUser.is_admin = adminData.is_admin;
        }
        
        displayDashboard();
    } catch (error) {
        console.error('Error:', error);
        alert('Ошибка загрузки данных: ' + error.message);
    }
}

// Отображение дашборда
function displayDashboard() {
    document.getElementById('loginSection').style.display = 'none';
    document.getElementById('dashboardSection').style.display = 'block';
    
    // Заполняем данные
    document.getElementById('userBalance').textContent = currentUser.balance.toFixed(2) + ' ₽';
    document.getElementById('userName').textContent = currentUser.name;
    document.getElementById('userStatus').textContent = getStatusText(currentUser.status);
    document.getElementById('nextBilling').textContent = formatDate(currentUser.next_billing_date);
    
    // Статус
    const statusBadge = document.getElementById('statusBadge');
    if (currentUser.status === 'active') {
        statusBadge.className = 'status-badge status-active';
        statusBadge.textContent = 'Оплачено';
    } else {
        statusBadge.className = 'status-badge status-debt';
        statusBadge.textContent = 'Не оплачено';
    }
    
    // Показываем кнопку админ-панели если пользователь админ
    if (currentUser.is_admin) {
        document.getElementById('adminLink').style.display = 'inline-block';
        document.getElementById('userInfo').textContent = '🔑 Администратор';
    }
    
    // Загружаем цену подписки
    loadSubscriptionPrice();
}

// Загрузка цены подписки
async function loadSubscriptionPrice() {
    // Здесь можно добавить API для получения цены
    document.getElementById('subscriptionPrice').textContent = '100';
}

// Загрузка информации о СБП
async function loadSBPInfo() {
    try {
        const response = await fetch('/api/users/sbp-info');
        if (!response.ok) {
            throw new Error('Не удалось загрузить информацию о СБП');
        }
        const sbpInfo = await response.json();
        
        const sbpContainer = document.getElementById('sbpPaymentInfo');
        if (sbpContainer) {
            let html = '<div class="sbp-info">';
            
            if (sbpInfo.phone) {
                html += `<p><i class="bi bi-phone"></i> Телефон: <code>${sbpInfo.phone}</code></p>`;
            }
            
            if (sbpInfo.account) {
                html += `<p><i class="bi bi-bank"></i> Счет: <code>${sbpInfo.account}</code></p>`;
            }
            
            if (sbpInfo.qr_code_url) {
                html += `<div class="mt-2">
                    <img src="${sbpInfo.qr_code_url}" alt="QR-код СБП" class="img-fluid" style="max-width: 200px; cursor: pointer;" onclick="showSBPQR('${sbpInfo.qr_code_url}')">
                    <p class="small text-muted mt-1">Нажмите на QR-код для увеличения</p>
                </div>`;
            }
            
            if (!sbpInfo.phone && !sbpInfo.account && !sbpInfo.qr_code_url) {
                html += '<p class="text-muted">Информация о СБП пока не настроена</p>';
            }
            
            html += '</div>';
            sbpContainer.innerHTML = html;
        }
    } catch (error) {
        console.error('Error loading SBP info:', error);
        const sbpContainer = document.getElementById('sbpPaymentInfo');
        if (sbpContainer) {
            sbpContainer.innerHTML = '<p class="text-muted">Не удалось загрузить информацию о СБП</p>';
        }
    }
}

// Показать QR-код СБП в модальном окне
function showSBPQR(qrCodeUrl) {
    const modal = document.getElementById('sbpQRModal');
    if (modal) {
        const img = document.getElementById('sbpQRImage');
        if (img) {
            img.src = qrCodeUrl;
        }
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
    }
}

// Загрузка информации об оплате в модальное окно
async function loadPaymentInfo() {
    try {
        const response = await fetch('/api/users/sbp-info');
        if (!response.ok) {
            throw new Error('Не удалось загрузить информацию о СБП');
        }
        const sbpInfo = await response.json();
        
        const content = document.getElementById('paymentInfoContent');
        if (content) {
            let html = '';
            
            if (sbpInfo.phone) {
                html += `<p><i class="bi bi-phone"></i> Телефон: <code>${sbpInfo.phone}</code></p>`;
            }
            
            if (sbpInfo.account) {
                html += `<p><i class="bi bi-bank"></i> Счет: <code>${sbpInfo.account}</code></p>`;
            }
            
            if (sbpInfo.qr_code_url) {
                html += `<div class="text-center mt-3">
                    <img src="${sbpInfo.qr_code_url}" alt="QR-код СБП" class="img-fluid" style="max-width: 250px; cursor: pointer;" onclick="showSBPQR('${sbpInfo.qr_code_url}')">
                    <p class="small text-muted mt-2">Нажмите на QR-код для увеличения</p>
                </div>`;
            }
            
            if (!sbpInfo.phone && !sbpInfo.account && !sbpInfo.qr_code_url) {
                html = '<p class="text-muted">Информация о СБП пока не настроена администратором</p>';
            }
            
            content.innerHTML = html;
        }
    } catch (error) {
        console.error('Error loading payment info:', error);
        const content = document.getElementById('paymentInfoContent');
        if (content) {
            content.innerHTML = '<p class="text-danger">Не удалось загрузить информацию о СБП</p>';
        }
    }
}

// Копирование ключа
function copyKey() {
    if (!userKey) {
        alert('Ключ еще не загружен администратором');
        return;
    }
    navigator.clipboard.writeText(userKey).then(() => {
        alert('Ключ скопирован в буфер обмена');
    });
}

// Скачивание ключа
function downloadKey() {
    if (!userKey) {
        alert('Ключ еще не загружен администратором');
        return;
    }
    const blob = new Blob([userKey], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'vpn_config.vpn';
    a.click();
    URL.revokeObjectURL(url);
}

// Показать QR-код
function showQR() {
    if (!userKey) {
        alert('Ключ еще не загружен администратором');
        return;
    }
    
    const qrContainer = document.getElementById('qrCodeImage');
    qrContainer.innerHTML = '';
    
    QRCode.toCanvas(qrContainer, userKey, {
        width: 300,
        margin: 2
    }, (error) => {
        if (error) {
            console.error('QR Code error:', error);
            alert('Ошибка генерации QR-кода');
        } else {
            const modal = new bootstrap.Modal(document.getElementById('qrModal'));
            modal.show();
        }
    });
}

// Информация об оплате
function showPaymentInfo() {
    const modal = document.getElementById('paymentInfoModal');
    if (modal) {
        // Загружаем актуальную информацию о СБП
        loadPaymentInfo();
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
    } else {
        // Fallback на alert если модальное окно не найдено
        alert('Оплата через СБП:\n\n1. Откройте приложение вашего банка\n2. Выберите "Оплата по QR-коду" или "Перевод по номеру телефона"\n3. Отсканируйте QR-код или введите номер телефона\n4. Укажите сумму пополнения\n5. После оплаты отправьте скриншот чека в бот для подтверждения.\n\nИли используйте автоплатеж для автоматического пополнения.');
    }
}

// Выход
function logout() {
    currentUser = null;
    userKey = null;
    document.getElementById('loginSection').style.display = 'block';
    document.getElementById('dashboardSection').style.display = 'none';
    document.getElementById('telegramIdInput').value = '';
}

// Вспомогательные функции
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU');
}

function getStatusText(status) {
    const statusMap = {
        'active': 'Активен',
        'blocked': 'Заблокирован',
        'debt': 'Задолженность'
    };
    return statusMap[status] || status;
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    // Инициализируем Telegram Widget (опционально)
    // initTelegramWidget();
    
    // Проверяем, есть ли сохраненный пользователь
    const savedUserId = localStorage.getItem('telegramId');
    if (savedUserId) {
        loadUserProfile(parseInt(savedUserId));
    }
});

