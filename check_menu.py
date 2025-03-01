import os

def check_base_html():
    base_path = os.path.join('templates', 'base.html')
    
    if not os.path.exists(base_path):
        print(f"ОШИБКА: Файл {base_path} не найден!")
        return False
    
    with open(base_path, 'r') as f:
        content = f.read()
    
    # Проверяем, есть ли пункт меню для курсов
    if 'url_for(\'courses\')' in content:
        print("Пункт меню 'Курсы' найден в base.html")
        return True
    else:
        print("Пункт меню 'Курсы' НЕ найден в base.html")
        print("Добавляем пункт меню...")
        
        # Находим, где добавить пункт меню
        try:
            # Ищем место после пункта "Цепочки"
            sequences_item = '<a class="nav-link {% if request.endpoint == \'sequences\' %}active{% endif %}" href="{{ url_for(\'sequences\') }}">'
            courses_item = '''<li class="nav-item">
                    <a class="nav-link {% if request.endpoint == 'courses' %}active{% endif %}" href="{{ url_for('courses') }}">
                        <i class="fas fa-graduation-cap me-2"></i>Курсы
                    </a>
                </li>'''
            
            if sequences_item in content:
                # Находим конец элемента меню "Цепочки"
                sequences_end = content.find('</li>', content.find(sequences_item))
                if sequences_end != -1:
                    # Вставляем пункт "Курсы" после "Цепочки"
                    new_content = content[:sequences_end+5] + '\n                ' + courses_item + content[sequences_end+5:]
                    
                    with open(base_path, 'w') as f:
                        f.write(new_content)
                    
                    print("Пункт меню 'Курсы' успешно добавлен")
                    return True
                else:
                    print("Не удалось найти конец элемента меню 'Цепочки'")
            else:
                print("Не удалось найти пункт меню 'Цепочки'")
            
            return False
        except Exception as e:
            print(f"Ошибка при обновлении base.html: {e}")
            return False

if __name__ == "__main__":
    check_base_html()
