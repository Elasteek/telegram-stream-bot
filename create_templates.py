import os

# Создаем директории, если их нет
os.makedirs("templates", exist_ok=True)

# Создаем шаблон courses.html
with open("templates/courses.html", "w") as f:
    f.write('''{% extends 'base.html' %}

{% block content %}
<div class="container mt-4">
    <div class="card shadow-sm">
        <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center">
            <h5 class="m-0">Управление курсами</h5>
            <a href="{{ url_for('add_course') }}" class="btn btn-light btn-sm">
                <i class="fas fa-plus"></i> Добавить курс
            </a>
        </div>
        <div class="card-body">
            {% if courses %}
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Название</th>
                            <th>Описание</th>
                            <th>Ссылка</th>
                            <th>Порядок</th>
                            <th>Статус</th>
                            <th>Действия</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for course in courses %}
                        <tr>
                            <td>{{ course.course_id }}</td>
                            <td>{{ course.title }}</td>
                            <td>{{ course.description[:50] ~ '...' if course.description and course.description|length > 50 else course.description }}</td>
                            <td>
                                <a href="{{ course.link }}" target="_blank" class="text-truncate d-inline-block" style="max-width: 200px;">
                                    {{ course.link }}
                                </a>
                            </td>
                            <td>{{ course.order_num }}</td>
                            <td>
                                {% if course.is_active == 1 %}
                                <span class="badge bg-success">Активный</span>
                                {% else %}
                                <span class="badge bg-secondary">Скрыт</span>
                                {% endif %}
                            </td>
                            <td>
                                <div class="btn-group">
                                    <a href="{{ url_for('edit_course', course_id=course.course_id) }}" class="btn btn-sm btn-outline-primary">
                                        <i class="fas fa-edit"></i>
                                    </a>
                                    <button type="button" class="btn btn-sm btn-outline-danger" data-bs-toggle="modal" data-bs-target="#deleteModal{{ course.course_id }}">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </div>
                                
                                <!-- Модальное окно подтверждения удаления -->
                                <div class="modal fade" id="deleteModal{{ course.course_id }}" tabindex="-1" aria-labelledby="deleteModalLabel{{ course.course_id }}" aria-hidden="true">
                                    <div class="modal-dialog">
                                        <div class="modal-content">
                                            <div class="modal-header">
                                                <h5 class="modal-title" id="deleteModalLabel{{ course.course_id }}">Подтверждение удаления</h5>
                                                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                                            </div>
                                            <div class="modal-body">
                                                Вы уверены, что хотите удалить курс <strong>{{ course.title }}</strong>?
                                            </div>
                                            <div class="modal-footer">
                                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Отмена</button>
                                                <form action="{{ url_for('delete_course', course_id=course.course_id) }}" method="post" class="d-inline">
                                                    <button type="submit" class="btn btn-danger">Удалить</button>
                                                </form>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            {% else %}
            <div class="alert alert-info">
                <i class="fas fa-info-circle"></i> Курсы не найдены. <a href="{{ url_for('add_course') }}">Добавить первый курс</a>
            </div>
            {% endif %}
        </div>
    </div>
</div>
{% endblock %}''')

# Создаем шаблон course_form.html
with open("templates/course_form.html", "w") as f:
    f.write('''{% extends 'base.html' %}

{% block content %}
<div class="container mt-4">
    <div class="card shadow-sm">
        <div class="card-header bg-primary text-white">
            <h5 class="m-0">{{ title }}</h5>
        </div>
        <div class="card-body">
            <form method="post" enctype="multipart/form-data">
                <div class="mb-3">
                    <label for="title" class="form-label">Название курса</label>
                    <input type="text" class="form-control" id="title" name="title" 
                           value="{{ course.title if course else '' }}" required>
                </div>
                
                <div class="mb-3">
                    <label for="description" class="form-label">Описание курса</label>
                    <textarea class="form-control" id="description" name="description" rows="3">{{ course.description if course else '' }}</textarea>
                </div>
                
                <div class="mb-3">
                    <label for="link" class="form-label">Ссылка на курс</label>
                    <input type="url" class="form-control" id="link" name="link" 
                           value="{{ course.link if course else '' }}" required>
                </div>
                
                <div class="mb-3">
                    <label for="order_num" class="form-label">Порядковый номер (для сортировки)</label>
                    <input type="number" class="form-control" id="order_num" name="order_num" 
                           value="{{ course.order_num if course else 0 }}" min="0">
                </div>
                
                <div class="mb-3 form-check">
                    <input type="checkbox" class="form-check-input" id="is_active" name="is_active" 
                           {{ 'checked' if not course or course.is_active == 1 else '' }}>
                    <label class="form-check-label" for="is_active">Активный курс</label>
                </div>
                
                <div class="d-flex justify-content-between">
                    <a href="{{ url_for('courses') }}" class="btn btn-secondary">Отмена</a>
                    <button type="submit" class="btn btn-primary">Сохранить</button>
                </div>
            </form>
        </div>
    </div>
</div>
{% endblock %}''')

print("Шаблоны успешно созданы!")