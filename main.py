import logging
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

logging.basicConfig(level=logging.INFO)

TelegramToken = "8809208766:AAGNL7qWsCpAes81t4b8BlFbITkLWlqY-c0"
AdministratorUsernames = ["rodomits", "weqosik"]

BotInstance = Bot(token=TelegramToken)
BotDispatcher = Dispatcher(storage=MemoryStorage())
ActiveAdminSessions = {}

class BotStates(StatesGroup):
    WaitingForAdminResponse = State()

@BotDispatcher.message(CommandStart())
async def HandleStartCommand(UserMessage: Message):
    CurrentUser = UserMessage.from_user
    CurrentUsername = CurrentUser.username.lower() if CurrentUser.username else ""

    if CurrentUsername in [AdminName.lower() for AdminName in AdministratorUsernames]:
        if CurrentUser.id not in ActiveAdminSessions:
            ActiveAdminSessions[CurrentUser.username.lower()] = CurrentUser.id
        await UserMessage.answer("Привет, admin! Ты успешно авторизован. Сюда будут приходить предложения.")
        return

    await UserMessage.answer("Привет Это предложка УРМ! Пришли свои идеи или предложения (ты можешь приложить любые файлы).")

@BotDispatcher.message(F.chat.type == "private")
async def HandleUserSuggestion(UserMessage: Message):
    CurrentUser = UserMessage.from_user
    CurrentUsername = CurrentUser.username.lower() if CurrentUser.username else ""

    if CurrentUsername in [AdminName.lower() for AdminName in AdministratorUsernames]:
        if CurrentUser.id not in ActiveAdminSessions:
            ActiveAdminSessions[CurrentUser.username.lower()] = CurrentUser.id
        return

    AdminReplyMarkup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Ответить",
                    callback_data=f"ReplyToUser:{CurrentUser.id}"
                )
            ]
        ]
    )

    for AdminName in AdministratorUsernames:
        AdminId = ActiveAdminSessions.get(AdminName.lower())
        if AdminId:
            try:
                await BotInstance.forward_message(
                    chat_id=AdminId,
                    from_chat_id=UserMessage.chat.id,
                    message_id=UserMessage.message_id
                )
                await BotInstance.send_message(
                    chat_id=AdminId,
                    text=f"Получено предложение от @{CurrentUser.username or 'Без_Ника'} (ID: {CurrentUser.id})",
                    reply_markup=AdminReplyMarkup
                )
            except Exception:
                pass

    await UserMessage.answer("Ваше предложение успешно отправлено администрации. Спасибо!")

@BotDispatcher.callback_query(F.data.startswith("ReplyToUser:"))
async def InitiateAdminResponse(AdminCallback: CallbackQuery, CurrentState: FSMContext):
    TargetUserId = AdminCallback.data.split(":")[1]
    await CurrentState.update_data(TargetUserId=TargetUserId)
    await AdminCallback.message.answer("Введите ответ для пользователя:")
    await CurrentState.set_state(BotStates.WaitingForAdminResponse)
    await AdminCallback.answer()

@BotDispatcher.message(BotStates.WaitingForAdminResponse)
async def SendAdminResponse(AdminMessage: Message, CurrentState: FSMContext):
    ContextData = await CurrentState.get_data()
    TargetUserId = ContextData.get("TargetUserId")
    
    try:
        await BotInstance.send_message(
            chat_id=TargetUserId,
            text=f"Ответ от администрации:\n\n{AdminMessage.text}"
        )
        await AdminMessage.answer("Ответ успешно доставлен пользователю.")
    except Exception:
        await AdminMessage.answer("Не удалось отправить сообщение. Возможно, пользователь заблокировал бота.")
    
    await CurrentState.clear()

async def MainApplicationLoop():
    await BotDispatcher.start_polling(BotInstance)

if __name__ == "__main__":
    asyncio.run(MainApplicationLoop())
