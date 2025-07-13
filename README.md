# Complaints API

## Описание
Сервис для приёма и обработки жалоб клиентов:
- Принимает POST `/complaints` с текстом жалобы  
- Классифицирует sentiment (TextBlob)  
- Классифицирует category (GPT-4o-mini)  
- Позволяет получать новые жалобы GET `/complaints/new?last_id=<id>`  
- Закрывает жалобу PATCH `/complaints/{id}/close`

---

## Переменные окружения
| Переменная               | Описание                                   |
|--------------------------|---------------------------------------------|
| `OPENAI_API_KEY`         | API-ключ OpenAI                             |

### Пример файла `.env`
```dotenv
OPENAI_API_KEY=sk-...
```

---

## Установка зависимостей
```bash
git clone https://github.com/haremor/complaints-processing.git
cd complaints-processing
python3 -m venv venv
source .venv/bin/activate        # macOS/Linux
# .venv\Scripts\activate         # Windows PowerShell
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Запуск приложения
```bash
uvicorn app.main:app --reload
```