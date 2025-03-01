import os

def fix_dashboard_html():
    print("Исправление шаблона dashboard.html...")
    
    dashboard_path = os.path.join('templates', 'dashboard.html')
    
    # Проверяем, существует ли файл
    if not os.path.exists(dashboard_path):
        print(f"ОШИБКА: Файл {dashboard_path} не найден!")
        return False
    
    # Создаем простой и надежный шаблон dashboard
    with open(dashboard_path, 'w') as f:
        f.write('''{% extends "base.html" %}

{% block title %}Дашборд{% endblock %}

{% block content %}
<h1>Добро пожаловать в админ-панель!</h1>

<div class="row mt-4">
    <div class="col-md-3">
        <div class="card mb-4">
            <div class="card-body text-center">
                <h5>Стримы</h5>
                <h2>{{ stream_count }}</h2>
                <a href="{{ url_for('streams') }}" class="btn btn-primary">Управление</a>
            </div>
        </div>
    </div>
    
    <div class="col-md-3">
        <div class="card mb-4">
            <div class="card-body text-center">
                <h5>Контент</h5>
                <h2>{{ content_count }}</h2>
                <a href="{{ url_for('content') }}" class="btn btn-primary">Управление</a>
            </div>
        </div>
    </div>
    
    <div class="col-md-3">
        <div class="card mb-4">
            <div class="card-body text-center">
                <h5>Цепочки</h5>
                <h2>{{ sequence_count }}</h2>
                <a href="{{ url_for('sequences') }}" class="btn btn-primary">Управление</a>
            </div>
        </div>
    </div>
    
    <div class="col-md-3">
        <div class="card mb-4">
            <div class="card-body text-center">
                <h5>Пользователи</h5>
                <h2>{{ user_count }}</h2>
                <a href="{{ url_for('users') }}" class="btn btn-primary">Просмотр</a>
            </div>
        </div>
    </div>
</div>

<div class="row">
    <div class="col-md-3">
        <div class="card mb-4">
            <div class="card-body text-center">
                <h5>Курсы</h5>
                <h2>{{ course_count }}</h2>
                <a href="{{ url_for('courses') }}" class="btn btn-primary">Управление</a>
            </div>
        </div>
    </div>
</div>

<div class="row">
    <div class="col-md-6">
        <div class="card mb-4">
            <div class="card-header">
                <h5>Ближайшие стримы</h5>
            </div>
            <div class="card-body">
                {% if streams %}
                <div class="table-responsive">
                    <table class="table table-striped">
                        <thead>
                            <tr>
                                <th>Название</th>
                                <th>Дата</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for stream in streams %}
                            <tr>
                                <td>{{ stream.title }}</td>
                                <td>{{ stream.stream_date }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                {% else %}
                <p>Нет предстоящих стримов.</p>
                {% endif %}
            </div>
        </div>
    </div>
    
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h5>Быстрые действия</h5>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-6 mb-3">
                        <a href="{{ url_for('add_stream') }}" class="btn btn-primary d-block">
                            <i class="fas fa-plus-circle"></i> Добавить стрим
                        </a>
                    </div>
                    <div class="col-md-6 mb-3">
                        <a href="{{ url_for('add_content') }}" class="btn btn-info d-block">
                            <i class="fas fa-plus-circle"></i> Добавить контент
                        </a>
                    </div>
                    <div class="col-md-6 mb-3">
                        <a href="{{ url_for('add_sequence') }}" class="btn btn-success d-block">
                            <i class="fas fa-plus-circle"></i> Создать цепочку
                        </a>
                    </div>
                    <div class="col-md-6 mb-3">
                        <a href="{{ url_for('add_course') }}" class="btn btn-warning d-block">
                            <i class="fas fa-plus-circle"></i> Добавить курс
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<div class="mt-4">
    <a href="{{ url_for('logout') }}" class="btn btn-danger">Выйти</a>
</div>
{% endblock %}
''')
    
    print("Шаблон dashboard.html успешно исправлен!")
    return True

if __name__ == "__main__":
    fix_dashboard_html()
