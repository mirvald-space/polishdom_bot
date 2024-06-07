from openai import AsyncOpenAI
import config

client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)

questions = config.INTERVIEW_QUESTIONS

async def ask_question(question: str) -> str:
    context = config.INTERVIEW_CONTEXT
    messages = [
        {"role": "system", "content": context},
        {"role": "user", "content": question}
    ]
    
    completion = await client.chat.completions.create(
        model=config.GPT_MODEL,
        messages=messages,
        max_tokens=400,  # Approximate token count to fit within 1024 characters
        temperature=config.TEMPERATURE,
    )
    answer = completion.choices[0].message.content.strip()
    
    # Limit answer length to 1024 characters
    if len(answer) > config.MAX_CHARACTERS:
        answer = answer[:config.MAX_CHARACTERS].rsplit(' ', 1)[0] + "..."
    
    return answer

async def evaluate_answers(questions_and_answers: list) -> str:
    combined_qa = "\n".join([f"Вопрос: {qa['question']}\nОтвет: {qa['answer']}" for qa in questions_and_answers])
    
    messages = [
        {"role": "system", "content": config.EVALUATION_CONTEXT},
        {"role": "user", "content": combined_qa}
    ]
    
    completion = await client.chat.completions.create(
        model=config.GPT_MODEL,
        messages=messages,
        max_tokens=config.MAX_TOKENS,
        temperature=config.TEMPERATURE,
    )
    evaluation = completion.choices[0].message.content.strip()
    return evaluation
