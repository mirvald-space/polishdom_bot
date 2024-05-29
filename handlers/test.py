from aiogram import Dispatcher, types
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from services.test_service import check_test_answer
from services.db import mongo


class TestStates(StatesGroup):
    Q1 = State()
    Q2 = State()
    Q3 = State()
    Q4 = State()
    Q5 = State()
    Q6 = State()
    Q7 = State()
    Q8 = State()
    Q9 = State()
    Q10 = State()
    Q11 = State()
    Q12 = State()
    Q13 = State()
    Q14 = State()
    Q15 = State()
    Q16 = State()
    Q17 = State()
    Q18 = State()
    Q19 = State()
    Q20 = State()
    Q21 = State()
    Q22 = State()
    Q23 = State()
    Q24 = State()
    Q25 = State()
    Q26 = State()
    Q27 = State()
    Q28 = State()
    Q29 = State()
    Q30 = State()
    Q31 = State()
    Q32 = State()
    Q33 = State()
    Q34 = State()
    Q35 = State()
    Q36 = State()
    RESULT = State()


async def test_welcome(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Старт", callback_data="start_test")],
        [InlineKeyboardButton(text="Отмена", callback_data="cancel_test")]
    ])
    await callback.message.answer(
        "Для определения вашего уровня владения польским языком необходимо ответить на 36 вопросов. Уровень будет определен от A1 до B2.",
        reply_markup=keyboard
    )
    await callback.answer()


async def start_test(callback: CallbackQuery, state: FSMContext):
    questions = await mongo.language_level.find().to_list(length=None)
    await state.update_data(questions=questions, correct_answers=0, current_question=0)
    await ask_next_question(callback.message, state)


async def ask_next_question(message: Message, state: FSMContext):
    data = await state.get_data()
    questions = data.get('questions')
    current_question = data.get('current_question')
    
    if current_question < len(questions):
        question = questions[current_question]
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=option, callback_data=f"answer_{question['_id']}_{option}")]
            for option in question.get('options', [])
        ] + [
            [InlineKeyboardButton(text="Отмена", callback_data="cancel_test")]
        ])
        
        if 'options' in question:
            sent_message = await message.answer(question['question'], reply_markup=keyboard)
        else:
            sent_message = await message.answer(f"{question['question']} (пожалуйста, напишите ваш ответ)", reply_markup=keyboard)

        await state.update_data(last_message_id=sent_message.message_id)
        await state.set_state(TestStates.__dict__[f'Q{current_question + 1}'])
    else:
        await show_result(message, state)


async def handle_test_answer(callback: CallbackQuery, state: FSMContext):
    _, question_id, user_answer = callback.data.split('_')
    data = await state.get_data()
    correct_answers = data.get('correct_answers')
    if await check_test_answer(question_id, user_answer):
        correct_answers += 1
        await state.update_data(correct_answers=correct_answers)
    current_question = data.get('current_question') + 1
    await state.update_data(current_question=current_question)
    await ask_next_question(callback.message, state)
    await callback.answer()


async def handle_written_answer(message: Message, state: FSMContext):
    data = await state.get_data()
    current_question = data.get('current_question')
    questions = data.get('questions')
    question = questions[current_question]
    
    user_answer = message.text
    if await check_test_answer(question['_id'], user_answer):
        correct_answers = data.get('correct_answers') + 1
    else:
        correct_answers = data.get('correct_answers')
    
    await state.update_data(
        correct_answers=correct_answers,
        current_question=current_question + 1
    )
    await ask_next_question(message, state)


async def show_result(message: Message, state: FSMContext):
    data = await state.get_data()
    correct_answers = data.get('correct_answers')
    last_message_id = data.get('last_message_id')
    if last_message_id:
        await message.bot.delete_message(chat_id=message.chat.id, message_id=last_message_id)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Вернуться в главное меню", callback_data="main_menu")]
    ])
    
    await message.answer(f"Вы ответили правильно на {correct_answers} из 36 вопросов.", reply_markup=keyboard)
    if correct_answers >= 28:
        await message.answer("Ваш уровень языка: B2 (Выше среднего уровня).")
    elif correct_answers >= 19:
        await message.answer("Ваш уровень языка: B1 (Средний уровень).")
    elif correct_answers >= 10:
        await message.answer("Ваш уровень языка: A2 (Элементарный уровень).")
    else:
        await message.answer("Ваш уровень языка: A1 (Начальный уровень).")
    await state.clear()


async def cancel_test(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await return_to_main_menu(callback)


async def return_to_main_menu(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Проверка уровня языка", callback_data="test")],
        [InlineKeyboardButton(text="Подготовка к собеседованию", callback_data="interview")]
    ])
    await callback.message.answer("Вы вернулись в главное меню. Выберите нужный раздел:", reply_markup=keyboard)
    await callback.answer()


async def register_test_handlers(dp: Dispatcher):
    dp.callback_query.register(test_welcome, lambda c: c.data == "test")
    dp.callback_query.register(start_test, lambda c: c.data == "start_test")
    dp.callback_query.register(cancel_test, lambda c: c.data == "cancel_test")
    dp.callback_query.register(handle_test_answer, lambda c: c.data.startswith("answer_"))
    questions = await mongo.language_level.find().to_list(length=None)
    for i in range(1, 37):
        question = questions[i-1]
        if 'options' in question:
            dp.callback_query.register(handle_test_answer, TestStates.__dict__[f'Q{i}'])
        else:
            dp.message.register(handle_written_answer, TestStates.__dict__[f'Q{i}'])
    dp.callback_query.register(return_to_main_menu, lambda c: c.data == "main_menu")


__all__ = ["register_test_handlers"]
