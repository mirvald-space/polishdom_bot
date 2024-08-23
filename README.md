# PolishDom Bot

PolishDom Bot is a multifunctional Telegram bot designed to help users learn the Polish language and prepare for obtaining the Karta Polaka (Polish Card). The bot utilizes AI technology to provide an immersive and interactive learning experience.

## Key Features

1. **AI-Powered Virtual Consul for Karta Polaka Preparation**:

   - Simulates a real interview experience with an AI-driven virtual Polish consul
   - Generates dynamic, context-aware questions based on typical Karta Polaka interview topics
   - Provides instant, detailed feedback on user responses, helping to improve answer quality
   - Offers personalized advice and tips for better interview performance

2. **Polish Language Level Test**:

   - 36-question test to determine Polish language proficiency from A1 to B2 level

3. **Interactive Polish Language Quiz**:

   - Engaging quiz with questions in Polish to reinforce language skills
   - Tracks user scores and progress over time

4. **Polish Culture and Language Content**:

   - Sends interesting facts about Poland to a linked channel
   - Regularly delivers useful Polish phrases with translations

5. **Polish Movie Recommendations**:

   - Curates and sends lists of Polish movies to enhance cultural understanding

6. **Progress Tracking**:
   - Saves user results and progress in a MongoDB database for personalized learning paths

## Technical Requirements

- Python 3.12+
- MongoDB
- Telegram Bot Token
- OpenAI API key (for AI-powered virtual consul)
- TMDB API key (for movie recommendations)

## Installation

1. Clone the repository:

   ```
   git clone https://github.com/yourusername/polishdom_bot.git
   cd polishdom_bot
   ```

2. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root directory and add the following environment variables:

   ```
   BOT_TOKEN=your_telegram_bot_token
   MONGO_URI=your_mongodb_connection_string
   MONGO_DB_NAME=your_database_name
   MONGO_COLLECTION_NAME=your_collection_name
   OPENAI_API_KEY=your_openai_api_key
   TMDB_API_KEY=your_tmdb_api_key
   CHANNEL_ID=your_telegram_channel_id
   WEBHOOK_URL=your_webhook_url
   ```

   Replace `your_*` with the appropriate values.

## Running the Bot

To start the bot, run the following command:

```
python bot.py
```

## Project Structure

- `bot.py`: Main bot file
- `config.py`: Configuration file
- `handlers/`: Directory with command handlers
- `services/`: Directory with services (DB, API, AI integration, etc.)
- `words/`: Directory with JSON files for facts, phrases, and quiz questions

## Development

To add new features or modify existing ones, follow the project structure and use the appropriate modules. The AI-powered virtual consul functionality is primarily handled in the `services/interview_service.py` file.

## Contributing

We welcome contributions to improve the PolishDom Bot! If you'd like to contribute, please create a pull request with a description of your changes.

## License

[MIT License](https://opensource.org/licenses/MIT)
