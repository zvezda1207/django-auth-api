# Auth & Access Control API

Backend-приложение с собственной системой аутентификации и авторизации — без использования стандартного Django-auth «из коробки».

## Стек технологий

- **Python** · Django 6 · Django REST Framework
- **PostgreSQL**
- **JWT** (PyJWT) для аутентификации
- **bcrypt** для хеширования паролей

## Основные возможности

- Регистрация, логин, логаут (с blacklist токенов)
- Обновление профиля и мягкое удаление аккаунта
- Система ролей (admin, manager, user, guest) и правил доступа
- CRUD API для управления ролями, элементами и правилами (только для admin)
- Демонстрационные бизнес-объекты (Product) с проверкой прав

## Быстрый старт

1. Установите зависимости: `pip install -r requirements.txt`
2. Скопируйте `.env.example` в `.env` и настройте `JWT_SECRET_KEY` и параметры PostgreSQL
3. Создайте БД и выполните миграции: `python manage.py migrate`
4. Заполните тестовые данные: `python manage.py init_test_data`
5. Запустите сервер: `python manage.py runserver`

Подробные инструкции и описание API — в `API_TESTING.md`.

---

## Техническая документация

### Схема БД (упрощённо)

- `accounts_user`
  - `id` — PK
  - `first_name`, `last_name`, `middle_name`
  - `email` (уникальный)
  - `password_hash` (bcrypt)
  - `is_active` — soft delete / блокировка
  - `role_id` — FK -> `access_control_role`
  - `created_at`, `updated_at`

- `accounts_blacklistedtoken`
  - `id` — PK
  - `token` — текст токена (уникальный)
  - `expires_at` — время истечения токена
  - `created_at` — время добавления в blacklist

- `access_control_role`
  - `id`
  - `name` (admin, manager, user, guest)
  - `description`

- `access_control_businesselement`
  - `id`
  - `code` (users, products, orders, access_rules и т.п.)
  - `description`

- `access_control_accessrolerule`
  - `id`
  - `role_id` (FK -> role)
  - `element_id` (FK -> business_elements)
  - `read_permission`, `read_all_permission`
  - `create_permission`
  - `update_permission`, `update_all_permission`
  - `delete_permission`, `delete_all_permission`

Идея: все `*_permission` — действия только над **своими** объектами; `*_all_permission` — над **любыми** объектами.

## Аутентификация

- Регистрация: `POST /api/auth/register/`
  - ввод: имя/фамилия/отчество, email, пароль, повтор пароля
  - пароль хэшируется с помощью `bcrypt` и сохраняется как `password_hash`
  - пользователю задаётся роль по умолчанию (например, `user`)

- Логин: `POST /api/auth/login/`
  - вход: `email`, `password`
  - при успешной проверке создаётся JWT-токен:
    - payload содержит `user_id` и `exp`
  - ответ: `{ "access_token": "<JWT>" }`

- Идентификация пользователя:
  - Клиент отправляет заголовок `Authorization: Bearer <token>`
  - Кастомный middleware (`JWTAuthenticationMiddleware`) и DRF authentication класс (`JWTAuthentication`) декодируют токен,
    проверяют, что токен не в blacklist, находят пользователя в БД, проверяют `is_active` и добавляют `request.user`.

- Logout: `POST /api/auth/logout/`
  - Требует заголовок `Authorization: Bearer <token>`
  - Токен добавляется в таблицу `BlacklistedToken` (blacklist)
  - После logout запросы с этим токеном будут получать `401 Unauthorized`
  - Это позволяет инвалидировать токены на сервере, а не только удалять их на клиенте

- Получение/обновление профиля: `GET/PUT/PATCH /api/auth/me/`
  - Требует заголовок `Authorization: Bearer <token>`
  - Возвращает/обновляет данные текущего пользователя

- Удаление пользователя: `DELETE /api/auth/me/delete/`
  - Требует заголовок `Authorization: Bearer <token>`
  - Аккаунт помечается как `is_active = False` (soft delete), но запись остаётся в БД
  - После удаления пользователь не сможет войти в систему

## Авторизация

- Роли описаны в таблице `roles` (`access_control_role`).
- Бизнес-элементы (объекты приложения) описаны в таблице `business_elements`.
- Правила доступа (связка роль–элемент–набор прав) хранятся в `access_role_rules`.

Пример:
- роль `admin` может читать/создавать/обновлять/удалять все объекты `products`;
- роль `user` может создавать свои `products` и читать все, но не удалять чужие.

Права проверяются в кастомном DRF Permission-классе `HasAccessPermission`:
- у вьюхи задаётся `element_code` (например, `'products'`);
- по `request.user.role` и `element_code` находится запись в `AccessRoleRule`;
- в зависимости от HTTP-метода выбирается нужный флаг:
  - GET → `read_permission` / `read_all_permission`
  - POST → `create_permission`
  - PUT/PATCH → `update_permission` / `update_all_permission`
  - DELETE → `delete_permission` / `delete_all_permission`
- если пользователь не определён (нет токена / невалидный), возвращается `401 Unauthorized`;
- если пользователь определён, но прав нет — `403 Forbidden`.

## Admin API для управления правилами

Пользователь с ролью `admin` (по полю `role.name`) может управлять доступом через API:

- `GET/POST /api/admin/roles/`
- `GET/PUT/PATCH/DELETE /api/admin/roles/{id}/`
- `GET/POST /api/admin/elements/`
- `GET/PUT/PATCH/DELETE /api/admin/elements/{id}/`
- `GET/POST /api/admin/access-rules/`
- `GET/PUT/PATCH/DELETE /api/admin/access-rules/{id}/`

Пермишен `IsAdminRole` проверяет, что у текущего пользователя роль `admin`.
Таким образом, администратор может динамически изменять правила доступа без изменения кода.

## Минимальные бизнес-объекты

Для демонстрации создана тестовая сущность `Product`:

- `Product`: `id`, `name`, `description`, `owner_id`
- API:
  - `GET /api/products/` — список продуктов (права зависят от роли и `access_role_rules`)
  - `POST /api/products/` — создание продукта с автоматическим владельцем = текущий пользователь

Если запрос выполняется без токена или с невалидным токеном — возвращается `401`.
Если токен валиден, но по правилам доступ запрещён — `403 Forbidden`.


### Переменные окружения

Приложение читает настройки из `.env`.  
Скопируйте `.env.example` в `.env` и задайте:
- `JWT_SECRET_KEY` — секретный ключ для подписи JWT токенов
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` — параметры подключения к PostgreSQL

