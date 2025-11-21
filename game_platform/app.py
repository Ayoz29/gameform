from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, send_from_directory
import json
import os
import re
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.environ.get('SECRET_KEY', 'game-platform-secret-key-2025')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Для Netlify - используем абсолютные пути
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')

USERS_FILE = os.path.join(DATA_DIR, 'users.json')
GAMES_FILE = os.path.join(DATA_DIR, 'games.json')

# Создаем необходимые директории
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs('static/games', exist_ok=True)
os.makedirs('static/images', exist_ok=True)
os.makedirs('templates', exist_ok=True)

# Категории игр
CATEGORIES = [
    'Аркады',
    'Головоломки',
    'Стратегии',
    'Экшен',
    'Приключения',
    'Гонки',
    'Спортивные',
    'Симуляторы',
    'Хоррор',
    'РПГ',
    'Казуальные',
    'Образовательные',
    'Другие'
]

# Запрещенные слова для проверки контента
FORBIDDEN_WORDS = [
    'porn', 'porno', 'xxx', 'sex', 'nude', 'naked', 'erotic', 'adult', '18+',
    'drugs', 'violence', 'hate', 'racism', 'extremism', 'terrorism',
    'порно', 'секс', 'голый', 'обнаженный', 'эротика', 'наркотики',
    'насилие', 'ненависть', 'расизм', 'экстремизм'
]

# Создаем необходимые директории
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs('static/games', exist_ok=True)
os.makedirs('static/images', exist_ok=True)
os.makedirs('templates', exist_ok=True)


def load_json(filename):
    """Загружает JSON из файла с обработкой ошибок"""
    try:
        if not os.path.exists(filename):
            print(f"Создаем новый файл: {filename}")
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)
            return []

        if os.path.getsize(filename) == 0:
            return []

        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                return []
            return json.loads(content)

    except (json.JSONDecodeError, Exception) as e:
        print(f"Ошибка загрузки {filename}: {e}")
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=2)
        return []


def save_json(filename, data):
    """Сохраняет данные в JSON файл"""
    try:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Ошибка сохранения {filename}: {e}")
        return False


def check_content_safety(html_content):
    """Проверяет HTML контент на запрещенные слова"""
    content_lower = html_content.lower()

    # Проверяем наличие запрещенных слов
    for word in FORBIDDEN_WORDS:
        if word in content_lower:
            return False, f"Обнаружено запрещенное слово: {word}"

    # Проверяем наличие подозрительных паттернов
    suspicious_patterns = [
        r'porn', r'xxx', r'sex', r'adult', r'18\+',
        r'нарко', r'насилие', r'порно'
    ]

    for pattern in suspicious_patterns:
        if re.search(pattern, content_lower):
            return False, "Обнаружен запрещенный контент"

    return True, "Контент прошел проверку"


def init_data():
    """Инициализирует данные при запуске"""
    users = load_json(USERS_FILE)
    games = load_json(GAMES_FILE)
    print(f"Инициализировано: {len(users)} пользователей, {len(games)} игр")


@app.route('/')
def index():
    games = load_json(GAMES_FILE)
    category = request.args.get('category', '')

    # Фильтрация по категории
    if category:
        games = [game for game in games if game.get('category') == category]

    games.sort(key=lambda x: x.get('likes', 0), reverse=True)
    active_users = len(load_json(USERS_FILE))

    return render_template('index.html',
                           games=games,
                           active_users=active_users,
                           categories=CATEGORIES,
                           current_category=category)


@app.route('/about')
def about():
    """Страница 'О нас' с информацией о платформе и команде"""
    team_members = [
        {
            'name': 'Бобоев Аёзбек',
            'role': 'Главный создатель и разработчик',
            'description': 'Основатель платформы, full-stack разработчик с более чем 5-летним опытом создания веб-приложений. Отвечает за архитектуру платформы и разработку ключевых функций.',
            'email': 'ayozbek94@gmail.com',
            'phone': '+998945865577'
        },
        {
            'name': 'Команда энтузиастов',
            'role': 'Разработчики и тестировщики',
            'description': 'Группа талантливых разработчиков, дизайнеров и тестировщиков, работающих вместе для создания лучшей игровой платформы.'
        }
    ]

    platform_info = {
        'name': 'Game Platform',
        'launch_year': 2024,
        'mission': 'Создать открытую и безопасную платформу для разработчиков игр и игроков со всего мира.',
        'vision': 'Стать ведущей платформой для indie-разработчиков и любителей игр, предоставляя инструменты для создания, распространения и открытия удивительных игр.'
    }

    stats = {
        'total_games': len(load_json(GAMES_FILE)),
        'total_users': len(load_json(USERS_FILE)),
        'total_plays': sum(game.get('plays', 0) for game in load_json(GAMES_FILE))
    }

    return render_template('about.html',
                           team_members=team_members,
                           platform_info=platform_info,
                           stats=stats)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash('Заполните все поля!')
            return redirect(url_for('register'))

        users = load_json(USERS_FILE)

        if any(user.get('username') == username for user in users):
            flash('Пользователь уже существует!')
            return redirect(url_for('register'))

        new_user = {
            'id': len(users) + 1,
            'username': username,
            'password': password,
            'created_at': datetime.now().isoformat(),
            'last_login': datetime.now().isoformat()
        }

        users.append(new_user)
        if save_json(USERS_FILE, users):
            session['username'] = username
            session['user_id'] = new_user['id']
            flash('Регистрация успешна!')
            return redirect(url_for('index'))
        else:
            flash('Ошибка сохранения данных!')

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        users = load_json(USERS_FILE)
        user = next((u for u in users if u.get('username') == username and u.get('password') == password), None)

        if user:
            session['username'] = username
            session['user_id'] = user['id']
            user['last_login'] = datetime.now().isoformat()
            save_json(USERS_FILE, users)
            flash('Вход успешен!')
            return redirect(url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль!')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы!')
    return redirect(url_for('index'))


@app.route('/upload', methods=['GET', 'POST'])
def upload_game():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        category = request.form.get('category', '')
        html_file = request.files.get('html_file')
        cover_image = request.files.get('cover_image')

        if not title or not html_file or not cover_image or not category:
            flash('Заполните все обязательные поля!')
            return redirect(url_for('upload_game'))

        if category not in CATEGORIES:
            flash('Выберите корректную категорию!')
            return redirect(url_for('upload_game'))

        if not html_file.filename.lower().endswith(('.html', '.htm')):
            flash('Файл игры должен быть в формате HTML!')
            return redirect(url_for('upload_game'))

        # Проверка содержимого HTML файла
        try:
            html_content = html_file.read().decode('utf-8')
            html_file.seek(0)  # Сбрасываем позицию чтения файла

            is_safe, message = check_content_safety(html_content)
            if not is_safe:
                flash(f'Файл не прошел проверку безопасности: {message}')
                return redirect(url_for('upload_game'))

        except Exception as e:
            flash(f'Ошибка при проверке файла: {e}')
            return redirect(url_for('upload_game'))

        # Создаем уникальные имена файлов
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        html_filename = secure_filename(f"{session['username']}_{timestamp}_{html_file.filename}")
        cover_filename = secure_filename(f"{session['username']}_{timestamp}_{cover_image.filename}")

        # Сохраняем файлы
        html_path = f"games/{html_filename}"
        cover_path = f"images/{cover_filename}"

        full_html_path = os.path.join('static', html_path)
        full_cover_path = os.path.join('static', cover_path)

        try:
            html_file.save(full_html_path)
            cover_image.save(full_cover_path)

            if not os.path.exists(full_html_path):
                flash('Ошибка: HTML файл не был сохранен!')
                return redirect(url_for('upload_game'))

        except Exception as e:
            flash(f'Ошибка при сохранении файлов: {e}')
            return redirect(url_for('upload_game'))

        # Добавляем игру в базу
        games = load_json(GAMES_FILE)
        game_id = len(games) + 1

        new_game = {
            'id': game_id,
            'title': title,
            'creator': session['username'],
            'creator_id': session['user_id'],
            'description': description,
            'category': category,
            'html_file': html_path,
            'cover_image': cover_path,
            'likes': 0,
            'plays': 0,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'comments': [],
            'liked_by': []
        }

        games.append(new_game)
        if save_json(GAMES_FILE, games):
            flash('Игра успешно загружена!')
            return redirect(url_for('index'))
        else:
            flash('Ошибка при сохранении данных игры!')

    return render_template('upload.html', categories=CATEGORIES)


@app.route('/play/<int:game_id>')
def play_game(game_id):
    games = load_json(GAMES_FILE)
    game = next((g for g in games if g.get('id') == game_id), None)

    if game:
        # Проверяем существование файла
        html_full_path = os.path.join('static', game['html_file'])
        if not os.path.exists(html_full_path):
            flash('Файл игры не найден!')
            return redirect(url_for('index'))

        # Увеличиваем счетчик игр
        game['plays'] = game.get('plays', 0) + 1
        game['updated_at'] = datetime.now().isoformat()
        save_json(GAMES_FILE, games)

        return render_template('play.html', game=game)

    flash('Игра не найдена!')
    return redirect(url_for('index'))


@app.route('/like/<int:game_id>')
def like_game(game_id):
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Войдите в систему!'})

    games = load_json(GAMES_FILE)
    game = next((g for g in games if g.get('id') == game_id), None)

    if not game:
        return jsonify({'success': False, 'error': 'Игра не найдена!'})

    user_id = session['user_id']
    liked_by = game.get('liked_by', [])

    if user_id in liked_by:
        liked_by.remove(user_id)
        game['likes'] = max(0, game.get('likes', 0) - 1)
    else:
        liked_by.append(user_id)
        game['likes'] = game.get('likes', 0) + 1

    game['liked_by'] = liked_by
    game['updated_at'] = datetime.now().isoformat()

    if save_json(GAMES_FILE, games):
        return jsonify({
            'success': True,
            'likes': game['likes'],
            'is_liked': user_id in liked_by
        })
    else:
        return jsonify({'success': False, 'error': 'Ошибка сохранения!'})


@app.route('/comment/<int:game_id>', methods=['POST'])
def add_comment(game_id):
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Войдите в систему!'})

    comment_text = request.form.get('comment', '').strip()
    if not comment_text:
        return jsonify({'success': False, 'error': 'Комментарий не может быть пустым!'})

    games = load_json(GAMES_FILE)
    game = next((g for g in games if g.get('id') == game_id), None)

    if not game:
        return jsonify({'success': False, 'error': 'Игра не найдена!'})

    if 'comments' not in game:
        game['comments'] = []

    new_comment = {
        'id': len(game['comments']) + 1,
        'user': session['username'],
        'user_id': session['user_id'],
        'text': comment_text,
        'timestamp': datetime.now().isoformat()
    }

    game['comments'].append(new_comment)
    game['updated_at'] = datetime.now().isoformat()

    if save_json(GAMES_FILE, games):
        return jsonify({'success': True, 'comment': new_comment})
    else:
        return jsonify({'success': False, 'error': 'Ошибка сохранения!'})


@app.route('/delete_comment/<int:game_id>/<int:comment_id>')
def delete_comment(game_id, comment_id):
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Войдите в систему!'})

    games = load_json(GAMES_FILE)
    game = next((g for g in games if g.get('id') == game_id), None)

    if not game:
        return jsonify({'success': False, 'error': 'Игра не найдена!'})

    comment = next((c for c in game.get('comments', []) if c.get('id') == comment_id), None)
    if not comment:
        return jsonify({'success': False, 'error': 'Комментарий не найден!'})

    if comment.get('user_id') != session['user_id'] and game.get('creator_id') != session['user_id']:
        return jsonify({'success': False, 'error': 'Нет прав для удаления!'})

    game['comments'] = [c for c in game.get('comments', []) if c.get('id') != comment_id]
    game['updated_at'] = datetime.now().isoformat()

    if save_json(GAMES_FILE, games):
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Ошибка сохранения!'})


@app.route('/delete_game/<int:game_id>')
def delete_game(game_id):
    if 'username' not in session:
        flash('Войдите в систему!')
        return redirect(url_for('login'))

    games = load_json(GAMES_FILE)
    game = next((g for g in games if g.get('id') == game_id), None)

    if game and game.get('creator_id') == session['user_id']:
        # Удаляем файлы
        try:
            html_path = os.path.join('static', game['html_file'])
            cover_path = os.path.join('static', game['cover_image'])
            if os.path.exists(html_path):
                os.remove(html_path)
            if os.path.exists(cover_path):
                os.remove(cover_path)
        except Exception as e:
            print(f"Ошибка удаления файлов: {e}")

        games = [g for g in games if g.get('id') != game_id]
        if save_json(GAMES_FILE, games):
            flash('Игра успешно удалена!')
        else:
            flash('Ошибка при удалении игры!')
    else:
        flash('Игра не найдена или нет прав для удаления!')

    return redirect(url_for('index'))


@app.route('/update_game/<int:game_id>', methods=['GET', 'POST'])
def update_game(game_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    games = load_json(GAMES_FILE)
    game = next((g for g in games if g.get('id') == game_id), None)

    if not game or game.get('creator_id') != session['user_id']:
        flash('Игра не найдена или нет прав для редактирования!')
        return redirect(url_for('index'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        category = request.form.get('category', '')
        html_file = request.files.get('html_file')
        cover_image = request.files.get('cover_image')

        if not title or not category:
            flash('Название игры и категория обязательны!')
            return redirect(url_for('update_game', game_id=game_id))

        if category not in CATEGORIES:
            flash('Выберите корректную категорию!')
            return redirect(url_for('update_game', game_id=game_id))

        game['title'] = title
        game['description'] = description
        game['category'] = category
        game['updated_at'] = datetime.now().isoformat()

        # Обновляем файлы если загружены новые
        if html_file and html_file.filename:
            if html_file.filename.lower().endswith(('.html', '.htm')):
                # Проверка содержимого
                try:
                    html_content = html_file.read().decode('utf-8')
                    html_file.seek(0)

                    is_safe, message = check_content_safety(html_content)
                    if not is_safe:
                        flash(f'Файл не прошел проверку безопасности: {message}')
                        return redirect(url_for('update_game', game_id=game_id))

                except Exception as e:
                    flash(f'Ошибка при проверке файла: {e}')
                    return redirect(url_for('update_game', game_id=game_id))

                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                html_filename = secure_filename(f"{session['username']}_{timestamp}_{html_file.filename}")
                html_path = f"games/{html_filename}"
                full_html_path = os.path.join('static', html_path)
                html_file.save(full_html_path)
                game['html_file'] = html_path

        if cover_image and cover_image.filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            cover_filename = secure_filename(f"{session['username']}_{timestamp}_{cover_image.filename}")
            cover_path = f"images/{cover_filename}"
            full_cover_path = os.path.join('static', cover_path)
            cover_image.save(full_cover_path)
            game['cover_image'] = cover_path

        if save_json(GAMES_FILE, games):
            flash('Игра успешно обновлена!')
            return redirect(url_for('index'))
        else:
            flash('Ошибка при обновлении игры!')

    return render_template('update_game.html', game=game, categories=CATEGORIES)


@app.route('/api/games')
def api_games():
    games = load_json(GAMES_FILE)
    return jsonify(games)


# Маршруты для статических файлов
@app.route('/games/<path:filename>')
def serve_game(filename):
    return send_from_directory('static/games', filename)


@app.route('/images/<path:filename>')
def serve_image(filename):
    return send_from_directory('static/images', filename)


@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)


# Инициализация при запуске
with app.app_context():
    init_data()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)