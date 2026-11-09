import asyncio
import logging
import requests
import datetime
import json
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.client.session.aiohttp import AiohttpSession

TOKEN = "9259216256:AAHR2bm9FEV0odlQRi_-DWM1kqa_cEjTttU"

logging.basicConfig(level=logging.INFO)
session = AiohttpSession()
bot = Bot(token=TOKEN, session=session)
dp = Dispatcher()

def get_weather(city: str):
    return f"В городе {city} сейчас 15°C, облачно."

def get_current_time(timezone: str = "Москва"):
    now = datetime.datetime.now().strftime("%H:%M:%S")
    return f"Текущее время ({timezone}): {now}"

def calculate(expression: str):
    try:
        result = eval(expression)
        return f"Результат: {result}"
    except Exception as e:
        return f"Ошибка вычисления: {e}"


tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Узнать погоду в городе",
            "parameters": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Узнать текущее время",
            "parameters": {"type": "object", "properties": {"timezone": {"type": "string"}}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Вычислить математическое выражение",
            "parameters": {"type": "object", "properties": {"expression": {"type": "string"}}, "required": ["expression"]}
        }
    }
]

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Я бот-агент! Напиши мне, например:\n- Какая погода в Москве?\n- Сколько сейчас времени?\n- Сколько будет 15 * 24?")

@dp.message()
async def agent_handler(message: types.Message):
    query = message.text
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

    messages = [{"role": "user", "content": query}]

    while True:
        try:
            response = requests.post("http://localhost:11434/api/chat", json={
                "model": "llama3.2",
                "messages": messages,
                "tools": tools,
                "stream": False
            }).json()

            msg = response["message"]
            messages.append(msg)

            if "tool_calls" in msg and msg["tool_calls"]:
                for tool_call in msg["tool_calls"]:
                    func_name = tool_call["function"]["name"]
                    args = tool_call["function"]["arguments"]
                    
                    if isinstance(args, str):
                        args = json.loads(args)

                    result = None
                    if func_name == "get_weather":
                        result = get_weather(args.get("city"))
                    elif func_name == "get_current_time":
                        result = get_current_time(args.get("timezone"))
                    elif func_name == "calculate":
                        result = calculate(args.get("expression"))

                    messages.append({"role": "tool", "content": str(result)})
            
            else:
                await message.answer(msg["content"])
                break
                
        except Exception as e:
            await message.answer(f"Ошибка: {e}")
            break

async def main():
    print("Агентный бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())