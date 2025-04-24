from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select
from db import async_session
from models import User

router = Router()

# FSM состояния
class Registration(StatesGroup):
    gender = State()
    age = State()
    weight = State()
    height = State()

class ProductStates(StatesGroup):
    cal_per_100g = State()
    weight_g = State()

# 📌 Регистрация пользователя
@router.message(Command("start"))
async def start_registration(message: types.Message, state: FSMContext):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id_telegram == message.from_user.id))
        user = result.scalar_one_or_none()

        if user:
            await message.answer("👋 Вы уже зарегистрированы. Используйте /my_calories или /calc_product.")
        else:
            await message.answer("Добро пожаловать! Укажите ваш пол (M/F):")
            await state.set_state(Registration.gender)

@router.message(Registration.gender)
async def process_gender_reg(message: types.Message, state: FSMContext):
    if message.text.upper() not in ["M", "F"]:
        await message.answer("Введите M или F.")
        return
    await state.update_data(gender=message.text.upper())
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

    await message.answer("✅ Регистрация завершена! Используйте /my_calories и /calc_product.")
    await state.clear()

# 📌 Получение дневной нормы калорий из БД
@router.message(Command("my_calories"))
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

# 📌 Вывод параметров пользователя
@router.message(Command("me"))
async def get_me(message: types.Message):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id_telegram == message.from_user.id))
        user = result.scalar_one_or_none()

        if user is None:
            await message.answer("Вы ещё не зарегистрированы. Введите /start для начала.")
            return

        await message.answer(
            f"👤 Ваши параметры:\n"
            f"Пол: {user.gender}\n"
            f"Возраст: {user.age}\n"
            f"Вес: {user.weight} кг\n"
            f"Рост: {user.height} см"
        )

# 📌 Калькулятор калорийности продукта
@router.message(Command("calc_product"))
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
