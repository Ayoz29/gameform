// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    console.log('🎮 Game Platform initialized');
    initializeEventListeners();
    initializeAnimations();

    // Добавляем данные пользователя в body для использования в JS
    document.body.dataset.userId = "{{ session.user_id }}";
    document.body.dataset.username = "{{ session.username }}";
});

function initializeEventListeners() {
    // Лайки
    document.querySelectorAll('.like-btn').forEach(button => {
        button.addEventListener('click', handleLike);
    });

    // Комментарии
    document.querySelectorAll('.comment-btn').forEach(button => {
        button.addEventListener('click', handleCommentClick);
    });

    // Поделиться
    document.querySelectorAll('.share-btn').forEach(button => {
        button.addEventListener('click', handleShare);
    });

    // Форма комментариев
    const commentForm = document.getElementById('commentForm');
    if (commentForm) {
        commentForm.addEventListener('submit', handleCommentSubmit);
    }

    // Анимация карточек при скролле
    initializeScrollAnimations();
}

function initializeAnimations() {
    // Добавляем анимацию появления элементов
    const animatedElements = document.querySelectorAll('.game-card, .card, .hero-section');
    animatedElements.forEach((element, index) => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(30px)';
        setTimeout(() => {
            element.style.transition = 'all 0.6s ease';
            element.style.opacity = '1';
            element.style.transform = 'translateY(0)';
        }, index * 100);
    });
}

function initializeScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);

    // Наблюдаем за всеми карточками игр
    document.querySelectorAll('.game-card').forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(30px)';
        card.style.transition = 'all 0.6s ease';
        observer.observe(card);
    });
}

// Обработка лайков
async function handleLike(event) {
    event.preventDefault();
    const button = event.currentTarget;
    const gameId = button.dataset.gameId;

    if (!document.body.dataset.userId) {
        showNotification('Войдите в систему чтобы ставить лайки!', 'warning');
        return;
    }

    // Анимация нажатия
    button.style.transform = 'scale(0.95)';
    setTimeout(() => {
        button.style.transform = '';
    }, 150);

    try {
        const response = await fetch(`/like/${gameId}`);
        const data = await response.json();

        if (data.success) {
            // Обновляем счетчик лайков с анимацией
            const likesCount = button.querySelector('.likes-count');
            if (likesCount) {
                animateCounter(likesCount, data.likes);
            }

            // Обновляем состояние кнопки
            if (data.is_liked) {
                button.classList.add('liked');
                button.innerHTML = '<i class="fas fa-heart"></i> <span class="likes-count">' + data.likes + '</span>';
                showNotification('❤️ Вы поставили лайк!', 'success');
            } else {
                button.classList.remove('liked');
                button.innerHTML = '<i class="fas fa-heart"></i> <span class="likes-count">' + data.likes + '</span>';
                showNotification('💔 Вы убрали лайк', 'info');
            }

            // Обновляем все кнопки лайков для этой игры на странице
            document.querySelectorAll(`.like-btn[data-game-id="${gameId}"]`).forEach(btn => {
                const countSpan = btn.querySelector('.likes-count');
                if (countSpan) animateCounter(countSpan, data.likes);
                if (data.is_liked) {
                    btn.classList.add('liked');
                    btn.innerHTML = '<i class="fas fa-heart"></i> <span class="likes-count">' + data.likes + '</span>';
                } else {
                    btn.classList.remove('liked');
                    btn.innerHTML = '<i class="fas fa-heart"></i> <span class="likes-count">' + data.likes + '</span>';
                }
            });
        } else {
            showNotification(data.error, 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('Ошибка при обновлении лайка', 'error');
    }
}

// Анимация счетчика
function animateCounter(element, newValue) {
    element.style.transform = 'scale(1.5)';
    setTimeout(() => {
        element.textContent = newValue;
        element.style.transform = 'scale(1)';
    }, 150);
}

// Обработка клика по кнопке комментариев
function handleCommentClick(event) {
    event.preventDefault();
    const button = event.currentTarget;
    const gameId = button.dataset.gameId;

    // Анимация кнопки
    button.style.transform = 'scale(0.95)';
    setTimeout(() => {
        button.style.transform = '';
    }, 150);

    document.getElementById('currentGameId').value = gameId;
    loadComments(gameId);

    const modal = new bootstrap.Modal(document.getElementById('commentsModal'));
    modal.show();
}

// Загрузка комментариев
async function loadComments(gameId) {
    const commentsList = document.getElementById('commentsList');
    commentsList.innerHTML = `
        <div class="text-center py-4">
            <div class="spinner-border text-primary mb-3" role="status"></div>
            <p class="text-muted">Загрузка комментариев...</p>
        </div>
    `;

    try {
        const response = await fetch('/api/games');
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        const games = await response.json();
        const game = games.find(g => g.id == gameId);

        commentsList.innerHTML = '';

        if (!game || !game.comments || game.comments.length === 0) {
            commentsList.innerHTML = `
                <div class="text-center text-muted py-5">
                    <i class="fas fa-comments fa-3x mb-3 opacity-50"></i>
                    <p class="fs-5">Пока нет комментариев</p>
                    <p class="text-muted">Будьте первым, кто оставит комментарий!</p>
                </div>
            `;
        } else {
            game.comments.forEach((comment, index) => {
                setTimeout(() => {
                    const commentDiv = createCommentElement(comment, gameId);
                    commentsList.appendChild(commentDiv);
                }, index * 100);
            });
        }
    } catch (error) {
        console.error('Error loading comments:', error);
        commentsList.innerHTML = `
            <div class="alert alert-danger text-center">
                <i class="fas fa-exclamation-triangle me-2"></i>
                Ошибка загрузки комментариев
            </div>
        `;
    }
}

// Создание элемента комментария
function createCommentElement(comment, gameId) {
    const commentDiv = document.createElement('div');
    commentDiv.className = 'comment mb-3';
    commentDiv.id = `comment-${comment.id}`;
    commentDiv.style.opacity = '0';
    commentDiv.style.transform = 'translateX(-20px)';

    const currentUserId = parseInt(document.body.dataset.userId) || null;
    const canDelete = currentUserId && (currentUserId === comment.user_id);

    commentDiv.innerHTML = `
        <div class="d-flex justify-content-between align-items-start mb-2">
            <div>
                <strong class="user">${comment.user}</strong>
                <small class="timestamp ms-2">${formatDate(comment.timestamp)}</small>
            </div>
            ${canDelete ? `
            <button class="btn btn-sm btn-outline-danger delete-comment-btn" 
                    data-game-id="${gameId}" 
                    data-comment-id="${comment.id}">
                <i class="fas fa-trash"></i>
            </button>
            ` : ''}
        </div>
        <div class="text">${escapeHtml(comment.text)}</div>
    `;

    // Анимация появления
    setTimeout(() => {
        commentDiv.style.transition = 'all 0.4s ease';
        commentDiv.style.opacity = '1';
        commentDiv.style.transform = 'translateX(0)';
    }, 50);

    if (canDelete) {
        const deleteBtn = commentDiv.querySelector('.delete-comment-btn');
        deleteBtn.addEventListener('click', handleDeleteComment);
    }

    return commentDiv;
}

// Удаление комментария
async function handleDeleteComment(event) {
    const button = event.currentTarget;
    const gameId = button.dataset.gameId;
    const commentId = button.dataset.commentId;

    if (!confirm('Удалить этот комментарий?')) {
        return;
    }

    try {
        const response = await fetch(`/delete_comment/${gameId}/${commentId}`);
        const data = await response.json();

        if (data.success) {
            const commentElement = document.getElementById(`comment-${commentId}`);
            if (commentElement) {
                commentElement.style.transform = 'translateX(100px)';
                commentElement.style.opacity = '0';
                setTimeout(() => {
                    commentElement.remove();
                }, 400);
            }
            showNotification('🗑️ Комментарий удален', 'success');
            updateCommentsCount(gameId);
        } else {
            showNotification(data.error, 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('Ошибка при удалении комментария', 'error');
    }
}

// Отправка комментария
async function handleCommentSubmit(event) {
    event.preventDefault();

    const gameId = document.getElementById('currentGameId').value;
    const commentText = document.getElementById('commentText').value.trim();

    if (!commentText) {
        showNotification('Введите текст комментария', 'warning');
        return;
    }

    const formData = new FormData();
    formData.append('comment', commentText);

    // Блокируем форму на время отправки
    const submitBtn = document.querySelector('#commentForm button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Отправка...';
    submitBtn.disabled = true;

    try {
        const response = await fetch(`/comment/${gameId}`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            document.getElementById('commentText').value = '';

            const commentsList = document.getElementById('commentsList');
            const commentElement = createCommentElement(data.comment, gameId);

            // Если нет комментариев, очищаем сообщение
            if (commentsList.querySelector('.text-muted')) {
                commentsList.innerHTML = '';
            }

            commentsList.appendChild(commentElement);

            // Прокручиваем к новому комментарию
            setTimeout(() => {
                commentElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }, 100);

            // Обновляем счетчик комментариев
            updateCommentsCount(gameId);

            showNotification('💬 Комментарий добавлен', 'success');
        } else {
            showNotification(data.error, 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('Ошибка при отправке комментария', 'error');
    } finally {
        // Разблокируем форму
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }
}

// Обновление счетчика комментариев
function updateCommentsCount(gameId) {
    fetch('/api/games')
        .then(response => response.json())
        .then(games => {
            const game = games.find(g => g.id == gameId);
            if (game) {
                document.querySelectorAll(`.comment-btn[data-game-id="${gameId}"]`).forEach(btn => {
                    const countSpan = btn.querySelector('.comments-count');
                    if (countSpan) {
                        animateCounter(countSpan, game.comments.length);
                    }
                });
            }
        });
}

// Поделиться игрой
function handleShare(event) {
    event.preventDefault();
    const button = event.currentTarget;
    const gameId = button.dataset.gameId;
    const url = `${window.location.origin}/play/${gameId}`;

    // Анимация кнопки
    button.style.transform = 'scale(0.95)';
    setTimeout(() => {
        button.style.transform = '';
    }, 150);

    if (navigator.share) {
        navigator.share({
            title: 'Посмотри эту игру на Game Platform!',
            text: 'Я нашел крутую игру, посмотри!',
            url: url
        }).then(() => {
            showNotification('✅ Игра успешно опубликована!', 'success');
        }).catch(err => {
            console.log('Error sharing:', err);
            copyToClipboard(url);
        });
    } else {
        copyToClipboard(url);
    }
}

// Копирование в буфер обмена
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showNotification('📋 Ссылка скопирована в буфер обмена!', 'success');
    }).catch(err => {
        console.error('Failed to copy: ', err);
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        showNotification('📋 Ссылка скопирована!', 'success');
    });
}

// Уведомления
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = `
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        opacity: 0;
        transform: translateX(100px);
        transition: all 0.4s ease;
    `;
    notification.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="fas fa-${getNotificationIcon(type)} me-2"></i>
            <div class="flex-grow-1">${message}</div>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="alert"></button>
        </div>
    `;

    document.body.appendChild(notification);

    // Анимация появления
    setTimeout(() => {
        notification.style.opacity = '1';
        notification.style.transform = 'translateX(0)';
    }, 100);

    // Автоматически удаляем через 5 секунд
    setTimeout(() => {
        if (notification.parentNode) {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(100px)';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, 400);
        }
    }, 5000);
}

function getNotificationIcon(type) {
    const icons = {
        'success': 'check-circle',
        'error': 'exclamation-circle',
        'warning': 'exclamation-triangle',
        'info': 'info-circle'
    };
    return icons[type] || 'info-circle';
}

// Вспомогательные функции
function formatDate(isoString) {
    const date = new Date(isoString);
    const now = new Date();
    const diff = now - date;

    if (diff < 60000) { // Меньше минуты
        return 'только что';
    } else if (diff < 3600000) { // Меньше часа
        const minutes = Math.floor(diff / 60000);
        return `${minutes} мин. назад`;
    } else if (diff < 86400000) { // Меньше суток
        const hours = Math.floor(diff / 3600000);
        return `${hours} ч. назад`;
    } else {
        return date.toLocaleString('ru-RU', {
            day: 'numeric',
            month: 'short',
            year: 'numeric'
        });
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Параллакс эффект для фона
document.addEventListener('mousemove', function(e) {
    const shapes = document.querySelectorAll('.shape');
    const mouseX = e.clientX / window.innerWidth;
    const mouseY = e.clientY / window.innerHeight;

    shapes.forEach((shape, index) => {
        const speed = (index + 1) * 0.5;
        const x = (mouseX - 0.5) * speed * 50;
        const y = (mouseY - 0.5) * speed * 50;

        shape.style.transform = `translate(${x}px, ${y}px) rotate(${x}deg)`;
    });
});