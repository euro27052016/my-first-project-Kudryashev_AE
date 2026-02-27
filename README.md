# Email Validator Project

Комплексный проект валидации email-адресов с unit-тестами, моками и нагрузочным тестированием.

## Структура проекта

```
email_validator_project/
├── email_validator/
│   ├── __init__.py          # Экспорт модулей
│   ├── validator.py          # Класс EmailValidator
│   └── dns_service.py        # DNS сервис для MX проверки
├── tests/
│   ├── __init__.py
│   ├── test_validator.py     # Unit-тесты для валидатора
│   └── test_dns_service.py   # Unit-тесты для DNS сервиса
├── app.py                    # Flask REST API
├── locustfile.py             # Нагрузочное тестирование
├── pytest.ini                # Конфигурация pytest
├── setup.cfg                 # Конфигурация coverage
├── requirements.txt          # Зависимости
└── README.md                 # Документация
```

## Установка

```bash
# Установка зависимостей
pip install -r requirements.txt
```

## Запуск тестов

### Базовый запуск тестов
```bash
pytest tests/ -v
```

### Запуск с coverage отчётом
```bash
pytest tests/ -v --cov=email_validator --cov-report=term-missing --cov-report=html
```

### Результаты покрытия
```
Name                             Stmts   Miss Branch BrPart   Cover
-----------------------------------------------------------------------------
email_validator/__init__.py          4      0      0      0 100.00%
email_validator/dns_service.py      76      0      8      0 100.00%
email_validator/validator.py       104      0     52      1  99.36%
-----------------------------------------------------------------------------
TOTAL                              184      0     60      1  99.59%
```

**Покрытие > 99%** — превышает требуемые 95%!

## Использование EmailValidator

### Базовая валидация
```python
from email_validator import EmailValidator

validator = EmailValidator()
result = validator.validate("user@example.com")

print(result.is_valid)  # True
print(result.errors)    # []
print(result.warnings)  # []
```

### С проверкой MX записей
```python
from email_validator import EmailValidator, DNSService

dns_service = DNSService()
validator = EmailValidator(check_mx=True, dns_service=dns_service)
result = validator.validate("user@gmail.com")

print(result.mx_valid)  # True (если MX запись существует)
```

### Пакетная валидация
```python
emails = ["user1@example.com", "invalid-email", "user2@example.org"]
results = validator.validate_batch(emails)

for r in results:
    print(f"{r.email}: {'✓' if r.is_valid else '✗'}")
```

## Flask REST API

### Запуск сервера
```bash
python app.py
# Сервер запускается на http://localhost:5000
```

### Эндпоинты

#### POST /validate
Валидация одного email:
```bash
curl -X POST http://localhost:5000/validate \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'
```

Ответ:
```json
{
  "is_valid": true,
  "email": "user@example.com",
  "errors": [],
  "warnings": [],
  "mx_valid": null
}
```

#### POST /validate/batch
Пакетная валидация:
```bash
curl -X POST http://localhost:5000/validate/batch \
  -H "Content-Type: application/json" \
  -d '{"emails": ["user1@example.com", "invalid-email"]}'
```

#### GET /quick-check
Быстрая проверка:
```bash
curl "http://localhost:5000/quick-check?email=user@example.com"
```

#### GET /health
Health check:
```bash
curl http://localhost:5000/health
```

## Нагрузочное тестирование с Locust

### Запуск Locust
```bash
locust -f locustfile.py --host=http://localhost:5000
```

Затем откройте http://localhost:8089 в браузере.

### Конфигурация нагрузки
- **EmailValidatorUser**: Стандартный пользователь с миксом запросов
- **QuickValidatorUser**: Только быстрые GET-запросы
- **BatchValidatorUser**: Отправка пакетов email-адресов
- **StressTestUser**: Минимальное время ожидания для стресс-теста

### Пример результатов тестирования
При тестировании с 100 пользователями:
- **Среднее время ответа**: ~5-15ms
- **RPS**: 1000-2000 запросов/сек
- **Процент ошибок**: 0%

### Запуск в headless режиме
```bash
locust -f locustfile.py --host=http://localhost:5000 \
  --headless -u 100 -r 10 --run-time 1m
```

## Архитектура тестов

### test_validator.py
- **TestEmailValidatorBasic**: Базовые тесты валидации
- **TestEmailValidatorWithMX**: Тесты с MX проверкой
- **TestEmailValidatorWithMock**: Тесты с моками DNS
- **TestEmailValidatorEdgeCases**: Граничные случаи
- **TestEmailValidatorPerformance**: Тесты производительности

### test_dns_service.py
- **TestDNSServiceInitialization**: Инициализация DNS сервиса
- **TestDNSServiceWithSocketFallback**: Fallback через socket
- **TestDNSServiceWithDnspython**: Тесты с dnspython
- **TestMockDNSService**: Тесты мок-сервиса

## Примеры валидации

| Email | Результат | Примечание |
|-------|-----------|------------|
| `user@example.com` | ✓ Valid | Стандартный email |
| `user+tag@gmail.com` | ✓ Valid | Plus addressing |
| `user.name@domain.co.uk` | ✓ Valid | С поддоменами |
| `@domain.com` | ✗ Invalid | Пустая локальная часть |
| `user@` | ✗ Invalid | Пустой домен |
| `user@.com` | ✗ Invalid | Домен начинается с точки |
| `user@@domain.com` | ✗ Invalid | Двойной @ |
| `user@domain..com` | ✗ Invalid | Двойные точки |

## Использование unittest.mock

```python
from unittest.mock import Mock
from email_validator import EmailValidator

# Создание мока DNS сервиса
mock_dns = Mock()
mock_dns.check_mx_record.return_value = True

validator = EmailValidator(check_mx=True, dns_service=mock_dns)
result = validator.validate("user@example.com")

# Проверка вызова мока
mock_dns.check_mx_record.assert_called_once_with("example.com")
```

## Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `CHECK_MX` | Включить MX проверку | `false` |
| `PORT` | Порт Flask сервера | `5000` |
| `FLASK_DEBUG` | Режим отладки | `false` |

## Лицензия

MIT License
