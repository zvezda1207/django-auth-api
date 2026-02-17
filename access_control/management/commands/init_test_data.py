"""
Команда для создания тестовых данных: роли, бизнес-элементы и правила доступа.
Запуск: python manage.py init_test_data
"""
from django.core.management.base import BaseCommand
from access_control.models import Role, BusinessElement, AccessRoleRule


class Command(BaseCommand):
    help = 'Создает тестовые данные: роли, бизнес-элементы и правила доступа'

    def handle(self, *args, **options):
        self.stdout.write('Создание тестовых данных...')

        # Создаем роли
        roles_data = [
            {'name': 'admin', 'description': 'Администратор - полный доступ ко всем ресурсам'},
            {'name': 'manager', 'description': 'Менеджер - расширенные права доступа'},
            {'name': 'user', 'description': 'Обычный пользователь - базовые права'},
            {'name': 'guest', 'description': 'Гость - минимальные права доступа'},
        ]

        created_roles = {}
        for role_data in roles_data:
            role, created = Role.objects.get_or_create(
                name=role_data['name'],
                defaults={'description': role_data['description']}
            )
            created_roles[role_data['name']] = role
            if created:
                self.stdout.write(self.style.SUCCESS(f'[OK] Создана роль: {role.name}'))
            else:
                self.stdout.write(f'  Роль уже существует: {role.name}')

        # Создаем бизнес-элементы
        elements_data = [
            {'code': 'users', 'description': 'Управление пользователями'},
            {'code': 'products', 'description': 'Управление продуктами'},
            {'code': 'orders', 'description': 'Управление заказами'},
            {'code': 'access_rules', 'description': 'Управление правилами доступа'},
        ]

        created_elements = {}
        for element_data in elements_data:
            element, created = BusinessElement.objects.get_or_create(
                code=element_data['code'],
                defaults={'description': element_data['description']}
            )
            created_elements[element_data['code']] = element
            if created:
                self.stdout.write(self.style.SUCCESS(f'[OK] Создан бизнес-элемент: {element.code}'))
            else:
                self.stdout.write(f'  Бизнес-элемент уже существует: {element.code}')

        # Создаем правила доступа
        # Администратор - полный доступ ко всему
        admin_role = created_roles['admin']
        for element in created_elements.values():
            rule, created = AccessRoleRule.objects.get_or_create(
                role=admin_role,
                element=element,
                defaults={
                    'read_permission': True,
                    'read_all_permission': True,
                    'create_permission': True,
                    'update_permission': True,
                    'update_all_permission': True,
                    'delete_permission': True,
                    'delete_all_permission': True,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(
                    f'[OK] Создано правило: {admin_role.name} -> {element.code} (все права)'
                ))

        # Менеджер - может читать и создавать все, обновлять и удалять только свои
        manager_role = created_roles['manager']
        for element in created_elements.values():
            rule, created = AccessRoleRule.objects.get_or_create(
                role=manager_role,
                element=element,
                defaults={
                    'read_permission': True,
                    'read_all_permission': True,
                    'create_permission': True,
                    'update_permission': True,
                    'update_all_permission': False,
                    'delete_permission': True,
                    'delete_all_permission': False,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(
                    f'[OK] Создано правило: {manager_role.name} -> {element.code}'
                ))

        # Обычный пользователь - может читать и создавать свои, обновлять и удалять только свои
        user_role = created_roles['user']
        for element_code, element in created_elements.items():
            # Для продуктов пользователь может создавать свои
            if element_code == 'products':
                rule, created = AccessRoleRule.objects.get_or_create(
                    role=user_role,
                    element=element,
                    defaults={
                        'read_permission': True,
                        'read_all_permission': False,
                        'create_permission': True,
                        'update_permission': True,
                        'update_all_permission': False,
                        'delete_permission': True,
                        'delete_all_permission': False,
                    }
                )
            else:
                # Для остальных элементов - только чтение своих
                rule, created = AccessRoleRule.objects.get_or_create(
                    role=user_role,
                    element=element,
                    defaults={
                        'read_permission': True,
                        'read_all_permission': False,
                        'create_permission': False,
                        'update_permission': False,
                        'update_all_permission': False,
                        'delete_permission': False,
                        'delete_all_permission': False,
                    }
                )
            if created:
                self.stdout.write(self.style.SUCCESS(
                    f'[OK] Создано правило: {user_role.name} -> {element.code}'
                ))

        # Гость - только чтение (без создания, обновления, удаления)
        guest_role = created_roles['guest']
        for element in created_elements.values():
            rule, created = AccessRoleRule.objects.get_or_create(
                role=guest_role,
                element=element,
                defaults={
                    'read_permission': True,
                    'read_all_permission': False,
                    'create_permission': False,
                    'update_permission': False,
                    'update_all_permission': False,
                    'delete_permission': False,
                    'delete_all_permission': False,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(
                    f'[OK] Создано правило: {guest_role.name} -> {element.code} (только чтение)'
                ))

        self.stdout.write(self.style.SUCCESS('\n[OK] Тестовые данные успешно созданы!'))
        self.stdout.write('\nРоли:')
        for role_name, role in created_roles.items():
            self.stdout.write(f'  - {role.name}: {role.description}')
