# OpenRouter API Setup Guide

## Что такое OpenRouter?

OpenRouter - это платформа, которая предоставляет унифицированный доступ к различным языковым моделям (Claude, GPT-4, Llama и др.) через единый API.

## Преимущества OpenRouter по сравнению с Grok:

✅ **Большой выбор моделей**: Claude 3.5 Sonnet, GPT-4, Llama, Gemini и другие  
✅ **Лучшая надежность**: Стабильная работа и высокая доступность  
✅ **Конкурентные цены**: Часто дешевле прямого обращения к провайдерам  
✅ **Единый API**: Легко переключаться между моделями  
✅ **Детальная аналитика**: Отслеживание использования и затрат  

## Настройка OpenRouter API

### 1. Регистрация и получение API ключа

1. Перейдите на [openrouter.ai](https://openrouter.ai)
2. Зарегистрируйтесь и подтвердите email
3. Перейдите в [Settings > API Keys](https://openrouter.ai/settings/keys)
4. Создайте новый API ключ
5. Скопируйте ключ (он показывается только один раз!)

### 2. Пополнение баланса

1. Перейдите в [Settings > Credits](https://openrouter.ai/settings/credits)
2. Пополните баланс (минимум $5)
3. **Важно**: Без кредитов API будет возвращать ошибку 402

### 3. Настройка бота

1. Откройте файл `.env` 
2. Замените значение `OPENROUTER_API_KEY`:

```env
OPENROUTER_API_KEY=sk-or-v1-your-actual-api-key-here
```

### 4. Выбор модели (по желанию)

По умолчанию используется **Claude 3.5 Sonnet** - одна из лучших моделей для понимания и генерации текста.

Чтобы изменить модель, отредактируйте файл `ai/openrouter.py`, строку:

```python
"model": "anthropic/claude-3.5-sonnet",  # <- изменить здесь
```

### Доступные модели:

- `anthropic/claude-3.5-sonnet` - Отлично для сложных задач (рекомендуется)
- `openai/gpt-4` - Классический GPT-4
- `openai/gpt-3.5-turbo` - Быстрый и дешевый
- `meta-llama/llama-3-70b-instruct` - Бесплатная альтернатива
- `google/gemini-pro` - Google Gemini

Полный список: https://openrouter.ai/models

## Мониторинг использования

- **Расходы**: [openrouter.ai/activity](https://openrouter.ai/activity)
- **Лимиты**: [openrouter.ai/settings/limits](https://openrouter.ai/settings/limits)

## Troubleshooting

### Ошибка 402 "Insufficient credits"
❌ **Причина**: Закончились кредиты  
✅ **Решение**: Пополните баланс в Settings > Credits

### Ошибка 401 "Invalid API key"
❌ **Причина**: Неверный API ключ  
✅ **Решение**: Проверьте правильность ключа в `.env`

### Ошибка 429 "Rate limit"  
❌ **Причина**: Превышен лимит запросов  
✅ **Решение**: Подождите или увеличьте лимиты

## Примерная стоимость

- **Claude 3.5 Sonnet**: ~$3 за 1M токенов
- **GPT-4**: ~$30 за 1M токенов  
- **GPT-3.5 Turbo**: ~$2 за 1M токенов

Для обычного использования бота $10-20 хватит надолго.
