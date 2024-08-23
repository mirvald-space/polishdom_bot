# PolishDom Bot

PolishDom Bot is a multifunctional Telegram bot designed to help users learn the Polish language and prepare for obtaining the Karta Polaka (Polish Card).

## Functionality

1. **Polish Language Level Test**:

   - 36-question test
   - Determines Polish language proficiency from A1 to B2 level

2. **Karta Polaka Interview Preparation**:

   - Simulates an interview with 10 random questions
   - Evaluates answers and provides a detailed report

3. **Polish Language Quiz**:

   - Interactive quiz with questions in Polish
   - Tracks user scores

4. **Polish Facts Sender**:

   - Periodically sends interesting facts about Poland to a linked channel

5. **Polish Phrases Sender**:

   - Regularly sends useful Polish phrases with translations

6. **Movie Recommendations**:

   - Sends curated lists of Polish movies for viewing

7. **Channel Integration**:

   - Requires subscription to a specific Telegram channel for access to bot features

8. **Progress Tracking**:
   - Saves user results in a MongoDB database

## Requirements

- Python 3.12+
- MongoDB
- Telegram Bot Token
- OpenAI API key
- TMDB API key

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
- `services/`: Directory with services (DB, API, etc.)
- `words/`: Directory with JSON files for facts, phrases, and quiz questions

## Development

To add new features or modify existing ones, follow the project structure and use the appropriate modules.

## Contributing

If you'd like to contribute to the project, please create a pull request with a description of your changes.

## License

[MIT License](https://opensource.org/licenses/MIT)
