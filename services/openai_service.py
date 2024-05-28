from openai import AsyncOpenAI
import os

client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Сценарий собеседования
questions = [
    "Почему вы хотите получить Карту Поляка?",
    "Расскажите о вашей семье и их польских корнях.",
    "Как вы поддерживаете польские традиции?",
    "Какие польские праздники вы знаете и как их отмечаете?",
    "Почему для вас важна польская культура?",
    "Что вы знаете о польской истории?",
    "Какие известные польские деятели вам известны и почему?",
    "Какие польские блюда вы готовите или пробовали?",
    "Вы говорите по-польски? Как вы изучали язык?",
    "Какие польские книги или фильмы вам известны?",
    "Как вы планируете использовать Карту Поляка в будущем?",
    "Есть ли у вас родственники или друзья в Польше? Как вы с ними поддерживаете связь?",
    "Какие места в Польше вы хотели бы посетить и почему?",
    "Как вы участвуете в польской общине в вашей стране?",
    "Какие польские народные обычаи и традиции вы знаете и практикуете?"
]

async def ask_question(question: str) -> str:
    context = """
    You are an expert in the process of obtaining the "Karta Polaka" (Card of the Pole). 
    Answer questions only related to the "Karta Polaka" and provide clear, structured, and concise information. 
    If the question is unrelated, respond with "This question is not related to the Karta Polaka process."
    Keep your answers within 1024 characters, ensuring the answers are clear and nothing important is left out.
    """
    messages = [
        {"role": "system", "content": context},
        {"role": "user", "content": question}
    ]
    
    completion = await client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=400,  # Примерное количество токенов, чтобы уложиться в 1024 символа
        temperature=0.7,
    )
    answer = completion.choices[0].message.content.strip()
    
    # Ограничение длины ответа по символам
    max_characters = 1024
    if len(answer) > max_characters:
        answer = answer[:max_characters].rsplit(' ', 1)[0] + "..."
    
    return answer

async def evaluate_answers(questions_and_answers: list) -> str:
    context = """
    You are a Polish consul evaluating answers for the Karta Polaka interview.
    The user's answers are provided below.
    Provide feedback and a score out of 10 for each answer.
    Translate the feedback into Russian.
    Format your response as follows:
    Вопрос: <question>
    Ответ: <answer>
    Оценка: <feedback>. Баллы: <score>/10.
    """
    combined_qa = "\n".join([f"Вопрос: {qa['question']}\nОтвет: {qa['answer']}" for qa in questions_and_answers])
    prompt = context + "\n\n" + combined_qa

    messages = [
        {"role": "system", "content": context},
        {"role": "user", "content": combined_qa}
    ]
    
    completion = await client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=1500,
        temperature=0.7,
    )
    evaluation = completion.choices[0].message.content.strip()
    return evaluation
