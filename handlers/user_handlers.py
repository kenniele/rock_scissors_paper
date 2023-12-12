from aiogram import F, Router
from aiogram.types import Message, KeyboardButton, ReplyKeyboardRemove, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.filters import Command, CommandStart
from lexicon.lexicon import LEXICON_RU
from random import choice

router = Router()

GAME: list[str] = ["Камень", "Ножницы", "Бумага"]
WIN_CONDITIONS: dict[str, str] = {"Камень": "Ножницы", "Ножницы": "Бумага", "Бумага": "Камень"}
PLAYERS: dict[(int, str), dict[str, int | bool]] = {}

def create_kb_builder_begin() -> ReplyKeyboardMarkup:
    kb_builder = ReplyKeyboardBuilder()
    buttons = [KeyboardButton(text="Давай!"), KeyboardButton(text="Не хочу!"),
                KeyboardButton(text="/help"), KeyboardButton(text="/stats")]
    kb_builder.row(*buttons)
    return kb_builder.as_markup(resize_keyboard=True, one_time_keyboard=True)

def create_game_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    buttons = [KeyboardButton(text="Камень"), KeyboardButton(text="Ножницы"), KeyboardButton(text="Бумага")]
    kb.row(*buttons, width=2)
    return kb.as_markup(resize_keyboard=True)

def create_stats_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    buttons = [KeyboardButton(text="Посмотреть общую статистику"), KeyboardButton(text="Посмотреть личную статистику"),
               KeyboardButton(text="На начальную страницу")]
    kb.row(*buttons, width=1)
    return kb.as_markup(resize_keyboard=True)

def end_game(message: Message, tip: str) -> None:
    global PLAYERS
    PLAYERS[(message.from_user.id, message.from_user.username)]["Games"] += 1
    if tip == "draw":
        PLAYERS[(message.from_user.id, message.from_user.username)]["Draws"] += 1
    else:
        if tip == "win":
            PLAYERS[(message.from_user.id, message.from_user.username)]["Wins"] += 1
        else:
            PLAYERS[(message.from_user.id, message.from_user.username)]["Loses"] += 1
        PLAYERS[(message.from_user.id, message.from_user.username)]["Win Percent"] = f'{PLAYERS[(message.from_user.id, message.from_user.username)]["Wins"] / (PLAYERS[(message.from_user.id, message.from_user.username)]["Games"] - PLAYERS[(message.from_user.id, message.from_user.username)]["Draws"]) * 100:0.2f}%'
    PLAYERS[(message.from_user.id, message.from_user.username)]["in_game"] = False

def check_player(message: Message) -> bool:
    return (message.from_user.id, message.from_user.username) in PLAYERS

def update_player(message: Message) -> None:
    if not check_player(message):
        PLAYERS.update({(message.from_user.id, message.from_user.username): {"Games": 0, "Wins": 0, "Draws": 0, "Loses": 0, "Win Percent": 0, "in_game": False}})

@router.message(CommandStart())
async def process_start_message(message: Message) -> None:
    await message.answer(text=LEXICON_RU["/start"], reply_markup=create_kb_builder_begin())
    
@router.message(Command("help"))
async def process_help_message(message: Message) -> None:
    await message.answer(text=LEXICON_RU["/help"], reply_markup=create_kb_builder_begin())

@router.message(Command("stats"))
async def process_stats_message(message: Message) -> None:
    try:
        await message.answer(text=LEXICON_RU["/stats"], reply_markup=create_stats_kb())
    except:
        await message.answer(text=LEXICON_RU["Пустое сообщение"], reply_markup=create_kb_builder_begin())

@router.message(F.text == "Давай!")
async def process_agreement_message(message: Message) -> None:
    update_player(message)
    PLAYERS[(message.from_user.id, message.from_user.username)]["in_game"] = True
    await message.answer(text=LEXICON_RU["Давай!"], reply_markup=create_game_kb())

@router.message(F.text == "Не хочу!")
async def process_disagreement_message(message: Message) -> None:
    update_player(message)
    await message.answer(text=LEXICON_RU["Не хочу!"], reply_markup=create_kb_builder_begin())

@router.message(F.text == "Посмотреть общую статистику")
async def process_get_general_stats(message: Message) -> None:
    general = []
    for info, player in sorted(PLAYERS.items(), key=lambda x: x[1]["Wins"]):
        general.append(f"user - @{info[1]}, Games={player['Games']}, Wins={player['Wins']}, Loses={player['Loses']}, Draws={player['Draws']}, Win Percent={player['Win Percent']}")
    try:
        await message.answer(text="\n".join(general), reply_markup=create_stats_kb())
    except:
        await message.answer(text=LEXICON_RU["Пустое сообщение"], reply_markup=create_kb_builder_begin())

@router.message(F.text == "Посмотреть личную статистику")
async def process_get_own_stats(message: Message) -> None:
    if check_player(message):
        player = PLAYERS[(message.from_user.id, message.from_user.username)]
        await message.answer(text=f"Games={player['Games']}, Wins={player['Wins']}, Loses={player['Loses']}, Draws={player['Draws']}, Win Percent={player['Win Percent']}")
    else:
        await message.answer(text=LEXICON_RU["Вы не играли"], reply_markup=create_kb_builder_begin())

@router.message(F.text == "На начальную страницу")
async def process_back_to_begin(message: Message) -> None:
    await message.answer(text=LEXICON_RU["Возвращаю вас"], reply_markup=create_kb_builder_begin())

@router.message(F.text.in_(GAME))
async def process_get_winner(message: Message) -> None:
    bot_step = choice(GAME)
    player_step = message.text
    bot_choice = f"Бот выбрал {bot_step.lower()}"
    if check_player(message) and PLAYERS[(message.from_user.id, message.from_user.username)]["in_game"]:
        if player_step == bot_step:
            end_game(message, "draw")
            await message.answer(text=LEXICON_RU["Ничья"] + bot_choice)
        elif (player_step, bot_step) in WIN_CONDITIONS.items():
            end_game(message, "win")
            await message.answer(text=LEXICON_RU["Игрок победил"] + bot_choice)
        else:
            end_game(message, "lose")
            await message.answer(text=LEXICON_RU["Бот победил"] + bot_choice)
        await message.answer(text=LEXICON_RU["Предложение сыграть"], reply_markup=create_kb_builder_begin())
    else:
        await message.answer(text=LEXICON_RU["Непредвиденная ошибка"], reply_markup=create_kb_builder_begin())