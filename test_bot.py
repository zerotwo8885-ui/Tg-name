import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import bot

@pytest.mark.asyncio
async def test_handle_message_no_mention():
    # Mock update and context
    update = MagicMock()
    update.message.text = "Hello everyone"
    update.message.chat.type = "group"

    context = MagicMock()
    context.bot.get_me = AsyncMock()
    context.bot.get_me.return_value.username = "ChotuBhaiBot"

    # We want to verify that client.chat.completions.create is NOT called
    with patch('bot.client') as mock_client:
        # For AsyncOpenAI, completions.create is an async method
        mock_client.chat.completions.create = AsyncMock()
        await bot.handle_message(update, context)
        mock_client.chat.completions.create.assert_not_called()

@pytest.mark.asyncio
async def test_handle_message_with_mention():
    update = MagicMock()
    update.message.text = "@ChotuBhaiBot kaise ho?"
    update.message.chat.type = "group"
    update.message.from_user.first_name = "Rahul"
    update.message.reply_text = AsyncMock()

    context = MagicMock()
    context.bot.get_me = AsyncMock()
    context.bot.get_me.return_value.username = "ChotuBhaiBot"

    mock_response = MagicMock()
    mock_response.choices[0].message.content = "Arre Rahul bhai! Main ekdum mast hoon. Aap batao?"

    with patch('bot.client') as mock_client:
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        await bot.handle_message(update, context)
        mock_client.chat.completions.create.assert_called_once()
        update.message.reply_text.assert_called_with("Arre Rahul bhai! Main ekdum mast hoon. Aap batao?")

@pytest.mark.asyncio
async def test_handle_message_with_name_address():
    update = MagicMock()
    update.message.text = "Chotu Bhai, ek joke sunao"
    update.message.chat.type = "group"
    update.message.from_user.first_name = "Amit"
    update.message.reply_text = AsyncMock()

    context = MagicMock()
    context.bot.get_me = AsyncMock()
    context.bot.get_me.return_value.username = "ChotuBhaiBot"

    mock_response = MagicMock()
    mock_response.choices[0].message.content = "Haha Amit bhai, suno fir..."

    with patch('bot.client') as mock_client:
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        await bot.handle_message(update, context)
        mock_client.chat.completions.create.assert_called_once()
        update.message.reply_text.assert_called_with("Haha Amit bhai, suno fir...")
