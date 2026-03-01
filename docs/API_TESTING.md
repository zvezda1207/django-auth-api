# Руководство по тестированию API

## Подготовка

1. Убедитесь, что PostgreSQL запущен и база данных создана
2. Выполните миграции:
   ```bash
   python manage.py migrate
   ```
3. Создайте тестовые данные (роли, бизнес-элементы, правила доступа):
   ```bash
   python manage.py init_test_data
   ```
4. Запустите сервер разработки:
   ```bash
   python manage.py runserver
   ```

## Тестирование в Postman

### 1. Регистрация пользователя

**Запрос:**
- Метод: `POST`
- URL: `http://127.0.0.1:8000/api/auth/register/`
- Headers:
  ```
  Content-Type: application/json
  ```
- Body (raw JSON):
  ```json
  {
    "first_name": "Ivan",
    "last_name": "Petrov",
    "middle_name": "",
    "email": "ivan@example.com",
    "password": "secret123",
    "password_repeat": "secret123"
  }
  ```

**Ожидаемый ответ (201 Created):**
```json
{
  "id": 1,
  "first_name": "Ivan",
  "last_name": "Petrov",
  "middle_name": "",
  "email": "ivan@example.com",
  "is_active": true,
  "role": 3,
  "role_name": "user"
}
```

### 2. Вход в систему (Login)

**Запрос:**
- Метод: `POST`
- URL: `http://127.0.0.1:8000/api/auth/login/`
- Headers:
  ```
  Content-Type: application/json
  ```
- Body (raw JSON):
  ```json
  {
    "email": "ivan@example.com",
    "password": "secret123"
  }
  ```

**Ожидаемый ответ (200 OK):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Важно:** Сохраните `access_token` из ответа - он понадобится для авторизованных запросов!

### 3. Получение информации о текущем пользователе

**Запрос:**
- Метод: `GET`
- URL: `http://127.0.0.1:8000/api/auth/me/`
- Headers:
  ```
  Authorization: Bearer <ваш_access_token>
  ```

**Ожидаемый ответ (200 OK):**
```json
{
  "id": 1,
  "first_name": "Ivan",
  "last_name": "Petrov",
  "middle_name": "",
  "email": "ivan@example.com",
  "is_active": true,
  "role": 3,
  "role_name": "user"
}
```

**Если токен не передан или невалидный (401 Unauthorized):**
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 4. Обновление профиля

**Запрос:**
- Метод: `PUT` или `PATCH`
- URL: `http://127.0.0.1:8000/api/auth/me/`
- Headers:
  ```
  Authorization: Bearer <ваш_access_token>
  Content-Type: application/json
  ```
- Body (raw JSON):
  ```json
  {
    "first_name": "Ivan",
    "last_name": "Petrov",
    "middle_name": "Sergeevich",
    "email": "ivan@example.com"
  }
  ```

### 5. Мягкое удаление аккаунта

**Запрос:**
- Метод: `DELETE`
- URL: `http://127.0.0.1:8000/api/auth/me/delete/`
- Headers:
  ```
  Authorization: Bearer <ваш_access_token>
  ```

**Ожидаемый ответ (200 OK):**
```json
{
  "message": "Account deleted successfully"
}
```

После удаления пользователь не сможет войти в систему (is_active=False).

### 6. Выход из системы (Logout)

**Запрос:**
- Метод: `POST`
- URL: `http://127.0.0.1:8000/api/auth/logout/`
- Headers:
  ```
  Authorization: Bearer <ваш_access_token>
  ```

**Примечание:** В текущей реализации logout инвалидирует JWT-токен на сервере (blacklist). После logout запросы с этим токеном будут получать 401.

### 7. Работа с продуктами (требует авторизации)

**Получение списка продуктов:**
- Метод: `GET`
- URL: `http://127.0.0.1:8000/api/products/`
- Headers:
  ```
  Authorization: Bearer <ваш_access_token>
  ```

**Создание продукта:**
- Метод: `POST`
- URL: `http://127.0.0.1:8000/api/products/`
- Headers:
  ```
  Authorization: Bearer <ваш_access_token>
  Content-Type: application/json
  ```
- Body (raw JSON):
  ```json
  {
    "name": "Test Product",
    "description": "This is a test product"
  }
  ```

**Если нет прав доступа (403 Forbidden):**
```json
{
  "detail": "You do not have permission to perform this action."
}
```

## Тестирование Admin API (требует роль admin)

### 1. Создание администратора

Сначала нужно создать пользователя с ролью admin через Django shell:

```bash
python manage.py shell
```

```python
from accounts.models import User
from access_control.models import Role
import bcrypt

admin_role = Role.objects.get(name='admin')
password_hash = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

admin_user = User.objects.create(
    first_name='Admin',
    last_name='User',
    email='admin@example.com',
    password_hash=password_hash,
    role=admin_role
)
```

**ВАЖНО:** После создания админа нужно **залогиниться как админ**, чтобы получить токен для Admin API!

### 1.1. Получение токена администратора

**Запрос:**
- Метод: `POST`
- URL: `http://127.0.0.1:8000/api/auth/login/`
- Headers:
  ```
  Content-Type: application/json
  ```
- Body (raw JSON):
  ```json
  {
    "email": "admin@example.com",
    "password": "admin123"
  }
  ```

**Ожидаемый ответ (200 OK):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Сохраните этот `access_token`** — он понадобится для всех запросов к Admin API!

**Проверка роли:**
Чтобы убедиться, что у вас правильная роль, выполните запрос `GET /api/auth/me/` с полученным токеном. В ответе должно быть `"role_name": "admin"`.

**Примечание:** Токен от обычного пользователя (с ролью `user`) **не подойдет** для Admin API — вы получите `403 Forbidden`. Нужен именно токен от пользователя с ролью `admin`.

### 2. Управление ролями

**Получение списка ролей:**
- Метод: `GET`
- URL: `http://127.0.0.1:8000/api/admin/roles/` 
- Headers:
  ```
  Authorization: Bearer <admin_access_token>
  ```

**Ожидаемый ответ (200 OK):**
```json
[
  {
    "id": 1,
    "name": "admin",
    "description": "Администратор - полный доступ ко всем ресурсам"
  },
  {
    "id": 2,
    "name": "manager",
    "description": "Менеджер - расширенные права доступа"
  },
  {
    "id": 3,
    "name": "user",
    "description": "Обычный пользователь - базовые права"
  },
  {
    "id": 4,
    "name": "guest",
    "description": "Гость - минимальные права доступа"
  }
]
```

**Если получаете 404:**
- Проверьте, что URL правильный: `http://127.0.0.1:8000/api/admin/roles/` 
- Убедитесь, что используете токен от пользователя с ролью `admin` (не от обычного пользователя!)
- Проверьте, что сервер запущен и перезапустите его, если нужно

**Если получаете 403 Forbidden:**
- Это означает, что токен валидный, но у пользователя нет роли `admin`
- Нужно залогиниться именно как админ (см. шаг 1.1)

**Создание роли:**
- Метод: `POST`
- URL: `http://127.0.0.1:8000/api/admin/roles/`
- Headers:
  ```
  Authorization: Bearer <admin_access_token>
  Content-Type: application/json
  ```
- Body:
  ```json
  {
    "name": "moderator",
    "description": "Moderator role"
  }
  ```

### 3. Управление бизнес-элементами

**Получение списка элементов:**
- Метод: `GET`
- URL: `http://127.0.0.1:8000/api/admin/elements/`
- Headers:
  ```
  Authorization: Bearer <admin_access_token>
  ```

### 4. Управление правилами доступа

**Получение списка правил:**
- Метод: `GET`
- URL: `http://127.0.0.1:8000/api/admin/access-rules/`
- Headers:
  ```
  Authorization: Bearer <admin_access_token>
  ```

**Ожидаемый ответ (200 OK):**
```json
[
  {
    "id": 1,
    "role": "admin",
    "element": "users",
    "read_permission": true,
    "read_all_permission": true,
    "create_permission": true,
    "update_permission": true,
    "update_all_permission": true,
    "delete_permission": true,
    "delete_all_permission": true
  },
  ...
]
```

**Перед созданием правила полезно получить списки ролей и элементов:**
- Роли: `GET /api/admin/roles/` — вернет список с полями `id`, `name`, `description`
- Элементы: `GET /api/admin/elements/` — вернет список с полями `id`, `code`, `description`

Используйте значения из полей `name` (для роли) и `code` (для элемента) при создании правила!

**ВАЖНО:** После выполнения команды `init_test_data` все правила уже созданы! Если вы попытаетесь создать правило, которое уже существует, получите ошибку `"The fields role, element must make a unique set."` (400 Bad Request). В этом случае используйте обновление правила (см. ниже) вместо создания нового.

**Создание правила:**
- Метод: `POST`
- URL: `http://127.0.0.1:8000/api/admin/access-rules/` 
- Headers:
  ```
  Authorization: Bearer <admin_access_token>
  Content-Type: application/json
  ```
- Body:
  ```json
  {
    "role": "user",
    "element": "products",
    "read_permission": true,
    "read_all_permission": false,
    "create_permission": true,
    "update_permission": true,
    "update_all_permission": false,
    "delete_permission": true,
    "delete_all_permission": false
  }
  ```

**ВАЖНО:** 
- `role` должен быть строкой с **названием роли** (`"admin"`, `"user"`, `"manager"`, `"guest"`), а не ID!
- `element` должен быть строкой с **кодом элемента** (`"users"`, `"products"`, `"orders"`, `"access_rules"`), а не ID!

**Примеры правильных значений:**
- Роли: `"admin"`, `"manager"`, `"user"`, `"guest"`
- Элементы: `"users"`, `"products"`, `"orders"`, `"access_rules"`

**Ожидаемый ответ (201 Created):**
```json
{
  "id": 1,
  "role": "user",
  "element": "products",
  "read_permission": true,
  "read_all_permission": false,
  "create_permission": true,
  "update_permission": true,
  "update_all_permission": false,
  "delete_permission": true,
  "delete_all_permission": false
}
```

**Если получаете 404:**
- Проверьте, что URL правильный: `http://127.0.0.1:8000/api/admin/access-rules/` 
- Убедитесь, что используете токен от пользователя с ролью `admin`
- Проверьте, что сервер запущен и перезапустите его, если нужно

**Если получаете 400 Bad Request с ошибкой `"The fields role, element must make a unique set."`:**
- Это означает, что правило с такой комбинацией `role` + `element` уже существует
- После выполнения `init_test_data` все правила уже созданы автоматически
- Используйте **обновление правила** (PUT/PATCH) вместо создания нового (см. ниже)

**Если получаете 400 Bad Request по другим причинам:**
- Проверьте, что `role` и `element` переданы как строки (названия), а не числа (ID)
- Убедитесь, что роль и элемент существуют в базе данных
- Проверьте формат всех полей (должны быть boolean для permissions)

**Обновление существующего правила:**
- Метод: `PUT` (полное обновление) или `PATCH` (частичное обновление)
- URL: `http://127.0.0.1:8000/api/admin/access-rules/<id>/` (где `<id>` — ID правила из списка)
- Headers:
  ```
  Authorization: Bearer <admin_access_token>
  Content-Type: application/json
  ```
- Body (пример для PATCH):
  ```json
  {
    "read_permission": true,
    "read_all_permission": true,
    "create_permission": true,
    "update_permission": true,
    "update_all_permission": true,
    "delete_permission": true,
    "delete_all_permission": true
  }
  ```

**Получение конкретного правила:**
- Метод: `GET`
- URL: `http://127.0.0.1:8000/api/admin/access-rules/<id>/`
- Headers:
  ```
  Authorization: Bearer <admin_access_token>
  ```

**Удаление правила:**
- Метод: `DELETE`
- URL: `http://127.0.0.1:8000/api/admin/access-rules/<id>/`
- Headers:
  ```
  Authorization: Bearer <admin_access_token>
  ```

## Коды ошибок

- **200 OK** - Успешный запрос
- **201 Created** - Ресурс успешно создан
- **400 Bad Request** - Неверные данные запроса
- **401 Unauthorized** - Требуется аутентификация или токен невалидный
- **403 Forbidden** - Доступ запрещен (нет прав)
- **404 Not Found** - Ресурс не найден
- **500 Internal Server Error** - Внутренняя ошибка сервера

## Советы по тестированию

1. **Используйте переменные окружения в Postman:**
   - Создайте переменную `base_url` = `http://127.0.0.1:8000`
   - Создайте переменную `token` для хранения access_token
   - Используйте их в запросах: `{{base_url}}/api/auth/me/`

2. **Создайте коллекцию запросов:**
   - Группируйте запросы по функциональности
   - Используйте Pre-request Script для автоматической установки токена

3. **Проверяйте логи сервера:**
   - Ошибки 500 обычно содержат подробную информацию в консоли Django

4. **Тестируйте граничные случаи:**
   - Регистрация с существующим email
   - Вход с неверным паролем
   - Запросы без токена
   - Запросы с истекшим токеном
