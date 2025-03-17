# Polish Language Learning Bot 🇵🇱

A Telegram bot for learning Polish language with interactive features, language level testing, and a daily notification system for learning new words.

## 🌟 Key Features

- **Language Level Testing**: Determine your current Polish language proficiency
- **Interview Trainer**: Practice conversational Polish through interview simulation
- **Topic-based Word Learning**: Subscribe to daily notifications with new words by chosen topics
- **AI Integration**: Using AI for generating contextual examples and explanations
- **Smart Notifications**: Notification system considering user-convenient time (9:00-21:00)

## 🛠 Tech Stack

- Python 3.x
- aiogram 3.0+ (Telegram Bot API)
- MongoDB (via motor)
- Pydantic for data validation
- AI integration for content generation

## 📋 Prerequisites

- Python 3.x
- MongoDB
- Telegram Bot Token
- AI API key (for content generation)

## 🚀 Installation and Launch

1. Clone the repository:
```bash
git clone <repository-url>
cd <project-directory>
```

2. Create and activate virtual environment:
```bash
python -m venv .myenv
source .myenv/bin/activate  # for Linux/Mac
# or
.myenv\Scripts\activate  # for Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create .env file based on .env.example and fill in the required variables:
```
TOKEN=your_telegram_bot_token
MONGODB_URL=your_mongodb_url
AI_API_KEY=your_ai_api_key
```

5. Launch the bot:
```bash
python main.py
```

## 💬 Bot Commands

- `/start` - Start working with the bot
- `/info` - Get information about the bot
- `/test` - Take a language level test
- `/interview` - Start a practice interview
- `/word` - Subscribe to words by chosen topic
- `/stopword` - Unsubscribe from topic words

## 🔄 Notification System

The bot sends daily notifications with new words at a convenient time for the user:
- Time range: 9:00 - 21:00
- Random time within the selected range
- Considers user's language level
- Tracks learned words
- Contextual usage examples

## 🗄 Project Structure

```
├── ai/                 # AI integration
├── db/                 # Database operations
├── handlers/           # Command handlers
├── states/             # Dialog states
├── utils/             # Helper functions
├── main.py            # Entry point
├── scheduler.py       # Notification scheduler
├── config.py          # Configuration
└── requirements.txt   # Dependencies
```

## 📝 License

MIT

## 👥 Authors

- Project Developer
- Contributors

## 🤝 Contributing

We welcome contributions to the project! Please create issues and pull requests.

## Available Commands

- `/start` - Start the bot and get welcome message
- `/info` - Get detailed information about bot features
- `/interview` - Start Polish Card interview preparation
- `/test` - Take a language level test

## Database Structure

### Users Collection
```json
{
    "user_id": int,
    "username": str,
    "language_level": str,
    "tests_completed": int
}
```

### Sessions Collection
```json
{
    "user_id": int,
    "session_type": str,
    "questions": list,
    "answers": list,
    "timestamp": datetime
}
``` 