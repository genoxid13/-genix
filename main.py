ardButton(text="Наш канал", url="https://t.me/+7Juwn6rwy6owNGYy"),
                InlineKeyboardButton(text="Работы", url="https://t.me/+bUkMsYZDc2o3YzRl")
            ]
        ]
    )
    
    # Твоя картинка
    PHOTO_URL = "https://i.postimg.cc/BnWNfr6N/IMG-3869.jpg"
    
    # Отправляем картинку с подписью "Главное меню" и кнопками
    await message.answer_photo(
        photo=PHOTO_URL,
        caption="Главное меню",
        reply_markup=keyboard
    )

# Обработка нажатия на кнопку "Атака"
@dp.callback_query(F.data == "start_attack")
async def start_attack(callback: CallbackQuery):
    # Отправляем сообщение про подписку
    await callback.message.answer("у вас нету подписки,напишите@yuopoma для покупки")
    # Убирает часики загрузки на кнопке
    await callback.answer()
