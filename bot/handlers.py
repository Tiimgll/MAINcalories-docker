from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select
from db import async_session
from models import User, Product, FoodEntry
from datetime import datetime

router = Router()

# 📌 FSM состояния
class Registration(StatesGroup):
    gender = State()
    age = State()
    weight = State()
    height = State()

class ProductStates(StatesGroup):
    cal_per_100g = State()
    weight_g = State()

class AddFoodStates(StatesGroup):
    calories = State()
    description = State()

# 📌 Регистрация
@router.message(Command("start"))
async def start_registration(message: types.Message, state: FSMContext):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id_telegram == message.from_user.id))
        user = result.scalar_one_or_none()

        if user:
            await message.answer("👋 Вы уже зарегистрированы. Используйте /info")
        else:
            await message.answer("Добро пожаловать! Укажите ваш пол (М/Ж):")
            await state.set_state(Registration.gender)

@router.message(Registration.gender)
async def process_gender_reg(message: types.Message, state: FSMContext):
    if message.text.upper() not in ["М", "Ж"]:
        await message.answer("Введите М или Ж.")
        return

    gender = "M" if message.text.upper() == "М" else "F"
    await state.update_data(gender=gender)
    await message.answer("Введите ваш возраст:")
    await state.set_state(Registration.age)

@router.message(Registration.age)
async def process_age_reg(message: types.Message, state: FSMContext):
    await state.update_data(age=int(message.text))
    await message.answer("Введите ваш вес (кг):")
    await state.set_state(Registration.weight)

@router.message(Registration.weight)
async def process_weight_reg(message: types.Message, state: FSMContext):
    await state.update_data(weight=float(message.text))
    await message.answer("Введите ваш рост (см):")
    await state.set_state(Registration.height)

@router.message(Registration.height)
async def process_height_reg(message: types.Message, state: FSMContext):
    await state.update_data(height=float(message.text))
    data = await state.get_data()

    async with async_session() as session:
        new_user = User(
            id_telegram=message.from_user.id,
            gender=data["gender"],
            age=data["age"],
            weight=data["weight"],
            height=data["height"]
        )
        session.add(new_user)
        await session.commit()

    await message.answer("✅ Регистрация завершена! Используйте /info.")
    await state.clear()

# 📌 Команды и функционал
@router.message(Command("info"))
async def info_command(message: types.Message):
    text = (
        "📋 *Описание команд бота:*\n\n"
        "/info — Показать это описание всех доступных команд.\n\n"
        "/add — Добавить запись о съеденной еде с калориями и описанием.\n\n"
        "/today — Показать список съеденного сегодня.\n\n"
        "/mycalories — Показать твою дневную норму калорий.\n\n"
        "/calcproduct — Калькулятор калорийности продукта по весу.\n\n"
        "/product — Показать список продуктов с калорийностью.\n\n"
        "/me — Показать информацию о тебе (пол, возраст, вес, рост)."
    )
    await message.answer(text, parse_mode="Markdown")

@router.message(Command("mycalories"))
async def get_calories(message: types.Message):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id_telegram == message.from_user.id))
        user = result.scalar_one_or_none()

        if user is None:
            await message.answer("Вы ещё не зарегистрированы. Введите /start для начала.")
            return

        if user.gender == "M":
            bmr = 10 * user.weight + 6.25 * user.height - 5 * user.age + 5
        elif user.gender == "F":
            bmr = 10 * user.weight + 6.25 * user.height - 5 * user.age - 161
        else:
            await message.answer("Ошибка в параметрах пола. Пройдите регистрацию заново: /start")
            return

        await message.answer(f"🔥 Ваша дневная норма калорий: {round(bmr)} ккал")

@router.message(Command("calcproduct"))
async def start_product_calc(message: types.Message, state: FSMContext):
    await message.answer("Введите калорийность на 100 г продукта:")
    await state.set_state(ProductStates.cal_per_100g)

@router.message(ProductStates.cal_per_100g)
async def process_cal_per_100g(message: types.Message, state: FSMContext):
    await state.update_data(cal_per_100g=float(message.text))
    await message.answer("Введите вес продукта в граммах:")
    await state.set_state(ProductStates.weight_g)

@router.message(ProductStates.weight_g)
async def process_weight_g(message: types.Message, state: FSMContext):
    data = await state.get_data()
    cal_per_100g = data["cal_per_100g"]
    weight_g = float(message.text)
    calories = (cal_per_100g / 100) * weight_g
    await message.answer(f"🥗 Энергетическая ценность порции: {round(calories, 2)} ккал")
    await state.clear()

@router.message(Command("product"))
async def list_products(message: types.Message):
    async with async_session() as session:
        result = await session.execute(select(Product))
        products = result.scalars().all()

        if not products:
            await message.answer("Пока продуктов нет.")
            return

        text = "📋 Продукты на 100 г:\n"
        for p in products:
            text += f"- {p.name} — {p.cal_per_100g} ккал\n"

        await message.answer(text)

@router.message(Command("add"))
async def add_food_entry(message: types.Message, state: FSMContext):
    await message.answer("Сколько калорий?")
    await state.set_state(AddFoodStates.calories)

@router.message(AddFoodStates.calories)
async def add_food_calories(message: types.Message, state: FSMContext):
    await state.update_data(calories=float(message.text))
    await message.answer("Что именно ели?")
    await state.set_state(AddFoodStates.description)

@router.message(AddFoodStates.description)
async def add_food_description(message: types.Message, state: FSMContext):
    data = await state.get_data()

    async with async_session() as session:
        entry = FoodEntry(
            user_id=message.from_user.id,
            calories=data["calories"],
            description=message.text,
            created_at=datetime.utcnow()
        )
        session.add(entry)
        await session.commit()

    await message.answer("✅ Записано!")
    await state.clear()

@router.message(Command("today"))
async def show_today_entries(message: types.Message):
    now = datetime.utcnow()
    start_of_day = datetime(now.year, now.month, now.day)

    async with async_session() as session:
        result = await session.execute(
            select(FoodEntry).where(
                FoodEntry.user_id == message.from_user.id,
                FoodEntry.created_at >= start_of_day
            )
        )
        entries = result.scalars().all()

        if not entries:
            await message.answer("Сегодня пока ничего не ели.")
            return

        text = "🍽️ Сегодня ты ел:\n"
        for i, e in enumerate(entries, 1):
            text += f"{i}) {e.calories} ккал — {e.description}\n"

        await message.answer(text)

@router.message(Command("me"))
async def get_me(message: types.Message):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id_telegram == message.from_user.id))
        user = result.scalar_one_or_none()

        if user is None:
            await message.answer("Вы ещё не зарегистрированы. Введите /start для начала.")
            return

        gender_display = "М" if user.gender == "M" else "Ж"

        await message.answer(
            f"👤 Ваши параметры:\n"
            f"Пол: {gender_display}\n"
            f"Возраст: {user.age}\n"
            f"Вес: {user.weight} кг\n"
            f"Рост: {user.height} см"
        )
