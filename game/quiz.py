import asyncio

from aiogram import Dispatcher, types
from aiogram.filters import Command
from loguru import logger

from services.db import mongo


class QuizGame:
    def __init__(self, db):
        self.current_question = None
        self.current_answer = None
        self.current_question_id = None
        self.current_question_message_id = None
        self.game_active = False
        self.db = db
        self.quiz_timeout = 4 * 3600  # 4 часа в секундах
        self.quiz_task = None

    async def start_quiz_game(self, message: types.Message):
        if self.game_active:
            if self.current_question_message_id:
                await message.answer(f"Викторина уже запущена. Текущий вопрос: <b>{self.current_question}</b>", parse_mode='HTML', reply_to_message_id=self.current_question_message_id)
            else:
                next_question_data = await self.get_next_question()
                if next_question_data is None:
                    await message.answer("Все вопросы были использованы. Викторина окончена.")
                    self.game_active = False
                    return
                next_question = next_question_data['question']
                sent_message = await message.answer(f"<b>{next_question}</b>", parse_mode='HTML', reply_to_message_id=message.message_id)
                self.current_question_message_id = sent_message.message_id
                self.current_question_id = next_question_data['_id']
                logger.info(f"Следующий вопрос: {next_question}, ID сообщения: {self.current_question_message_id}")
            return
        
        self.game_active = True
        question_data = await self.get_next_question()
        if question_data is None:
            await message.answer("Все вопросы были использованы. Викторина окончена.")
            self.game_active = False
            return
        question = question_data['question']
        sent_message = await message.answer(f"<b>{question}</b>", parse_mode='HTML', reply_to_message_id=message.message_id)
        self.current_question_message_id = sent_message.message_id
        self.current_question_id = question_data['_id']
        logger.info(f"Викторина началась. Вопрос: {question}, ID сообщения: {self.current_question_message_id}")

        if self.quiz_task:
            self.quiz_task.cancel()
        self.quiz_task = asyncio.create_task(self.quiz_timeout_task())

    async def quiz_timeout_task(self):
        try:
            await asyncio.sleep(self.quiz_timeout)
            if self.game_active:
                self.game_active = False
                logger.info("Викторина отключена из-за неактивности.")
                # Отправляем сообщение в группу об окончании викторины
                await self.db.bot.send_message(chat_id=self.db.channel_id, text="Викторина отключена из-за неактивности.")
        except asyncio.CancelledError:
            pass

    async def show_scores(self, message: types.Message):
        scores_message = await self.get_scores()
        await message.answer(scores_message, reply_to_message_id=message.message_id)

    async def handle_message(self, message: types.Message):
        logger.info(f"Получено сообщение: {message.text} из чата {message.chat.type}")

        if not self.game_active:
            logger.info("Игра не активна.")
            return

        if message.chat.type != 'supergroup' and message.chat.type != 'group':
            logger.info("Получено сообщение не из группы или супергруппы.")
            return  # Игнорируем сообщения не из групп или супергрупп

        # Проверяем, что сообщение является ответом на сообщение с вопросом
        if not message.reply_to_message or message.reply_to_message.message_id != self.current_question_message_id:
            logger.info("Сообщение не является ответом на текущий вопрос.")
            return

        user_name = message.from_user.first_name
        user_id = message.from_user.id
        answer = message.text.strip()

        response = await self.check_answer(user_id, user_name, answer)
        await message.answer(response, reply_to_message_id=message.message_id)
        
        if "Правильно!" in response:
            next_question_data = await self.get_next_question()
            if next_question_data is None:
                await message.answer("Все вопросы были использованы. Викторина окончена.")
                self.game_active = False
                return
            next_question = next_question_data['question']
            sent_message = await message.answer(f"<b>{next_question}</b>", parse_mode='HTML', reply_to_message_id=message.message_id)
            self.current_question_message_id = sent_message.message_id
            self.current_question_id = next_question_data['_id']
            logger.info(f"Следующий вопрос: {next_question}, ID сообщения: {self.current_question_message_id}")

            if self.quiz_task:
                self.quiz_task.cancel()
            self.quiz_task = asyncio.create_task(self.quiz_timeout_task())

    async def get_next_question(self):
        question_data = await self.db.get_unused_quiz_question()
        if question_data:
            await self.db.mark_question_used(question_data['_id'])
            self.current_question = question_data['question']
            self.current_answer = question_data['answer']
            logger.info(f"Выбран вопрос: {self.current_question}, Ответ: {self.current_answer}")
            return question_data
        return None

    async def check_answer(self, user_id, user_name, answer):
        logger.info(f"Проверка ответа: {answer} (Правильный ответ: {self.current_answer})")
        if self.current_answer.lower() == answer.lower():
            await self.db.update_quiz_score(user_id, user_name)
            return "Правильно! Следующий вопрос:"
        else:
            return "Неправильно. Попробуйте снова."

    async def get_scores(self):
        scores_list = await self.db.get_quiz_scores()
        if not scores_list:
            return "Нет игроков и очков пока что."
        
        scores = "Текущие очки:\n"
        for user in scores_list:
            scores += f"{user['username']}: {user['score']} очков\n"
        return scores

async def register_quiz_game_handlers(dp: Dispatcher):
    game = QuizGame(mongo)
    dp.message.register(game.start_quiz_game, Command(commands=["start_quiz"]))
    dp.message.register(game.show_scores, Command(commands=["scores"]))
    dp.message.register(game.handle_message)
