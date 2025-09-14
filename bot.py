import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, ContextTypes, CallbackQueryHandler,
    MessageHandler, filters, ConversationHandler
)
from dotenv import load_dotenv
import json
import asyncio
import html

# Load environment variables
load_dotenv()

# Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))
POWERED_BY_USERNAME = os.getenv('POWERED_BY_USERNAME', '@Adult_Flux')

# Load channels from environment variable
CHANNELS_STR = os.getenv('CHANNELS', '{}').replace("'", '"')  # Replace single quotes with double quotes for JSON
CHANNELS = json.loads(CHANNELS_STR)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
(
    TITLE, TITLE_STYLE, MEDIA_TYPE, STATUS, CHAPTERS, RATING,
    GENRE, SYNOPSIS, PREMIUM_URL, TUTORIAL_URL, DOWNLOAD_URL, IMAGE,
    CHANNEL_SELECTION, CONFIRM
) = range(14)

# Store post data
post_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("You are not authorized to use this bot.")
        return ConversationHandler.END

    await update.message.reply_text(
        "Hi! I'm your channel post bot.\n\n"
        "Use /post to create a new post with thumbnail image."
    )
    return ConversationHandler.END

async def post_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the post creation process."""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("You are not authorized to use this bot.")
        return ConversationHandler.END

    # Clear any existing data for this user
    user_id = update.effective_user.id
    if user_id in post_data:
        del post_data[user_id]
    
    # Initialize post data
    post_data[user_id] = {}

    await update.message.reply_text(
        "Let's create a new post! Please provide the title:"
    )
    return TITLE

async def title_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store title and ask for title style."""
    user_id = update.effective_user.id
    post_data[user_id]['title'] = update.message.text

    # Create inline keyboard for title style selection
    keyboard = [
        [
            InlineKeyboardButton("Normal Title", callback_data="normal_title"),
            InlineKeyboardButton("Quote Title", callback_data="quote_title")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "How would you like to format the title?",
        reply_markup=reply_markup
    )
    return TITLE_STYLE

async def title_style_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle title style selection."""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    if query.data == "normal_title":
        post_data[user_id]['title_style'] = 'normal'
        style_text = "normal"
    else:
        post_data[user_id]['title_style'] = 'quote'
        style_text = "quote"

    await query.edit_message_text(f"Title style set to {style_text}. Now provide the type (e.g., Manhwa):")
    return MEDIA_TYPE

async def type_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store type and ask for status."""
    user_id = update.effective_user.id
    post_data[user_id]['type'] = update.message.text

    await update.message.reply_text("Now provide the status (e.g., Releasing):")
    return STATUS

async def status_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store status and ask for chapters."""
    user_id = update.effective_user.id
    post_data[user_id]['status'] = update.message.text

    await update.message.reply_text("Now provide the number of chapters (e.g., 20):")
    return CHAPTERS

async def chapters_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store chapters and ask for rating."""
    user_id = update.effective_user.id
    post_data[user_id]['chapters'] = update.message.text

    await update.message.reply_text("Now provide the rating (e.g., 69%):")
    return RATING

async def rating_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store rating and ask for genre."""
    user_id = update.effective_user.id
    post_data[user_id]['rating'] = update.message.text

    await update.message.reply_text("Now provide the genre (e.g., DRAMA, HENTAI):")
    return GENRE

async def genre_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store genre and ask for synopsis."""
    user_id = update.effective_user.id
    post_data[user_id]['genre'] = update.message.text

    await update.message.reply_text("Now provide the synopsis:")
    return SYNOPSIS

async def synopsis_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store synopsis and ask for premium URL."""
    user_id = update.effective_user.id
    post_data[user_id]['synopsis'] = update.message.text

    await update.message.reply_text(
        "Now provide the URL for the PREMIUM button (e.g., https://t.me/your_channel):"
    )
    return PREMIUM_URL

async def premium_url_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store premium URL and ask for tutorial URL."""
    user_id = update.effective_user.id
    post_data[user_id]['premium_url'] = update.message.text

    await update.message.reply_text(
        "Now provide the URL for the TUTORIAL VID button (e.g., https://t.me/your_channel):"
    )
    return TUTORIAL_URL

async def tutorial_url_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store tutorial URL and ask for download URL."""
    user_id = update.effective_user.id
    post_data[user_id]['tutorial_url'] = update.message.text

    await update.message.reply_text(
        "Now provide the URL for the DOWNLOAD LINK button (e.g., https://t.me/your_channel):"
    )
    return DOWNLOAD_URL

async def download_url_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store download URL and ask for image."""
    user_id = update.effective_user.id
    post_data[user_id]['download_url'] = update.message.text

    await update.message.reply_text(
        "Now send me an image to use as thumbnail for the post (or send /skip to continue without an image):"
    )
    return IMAGE

async def image_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store image and ask for channel selection."""
    user_id = update.effective_user.id

    try:
        if update.message.photo:
            # Get the highest resolution photo
            photo = update.message.photo[-1]
            file_id = photo.file_id

            # Store only the file_id, not the image data
            post_data[user_id]['file_id'] = file_id
            await update.message.reply_text("Image received successfully!")
        elif update.message.document and update.message.document.mime_type.startswith('image/'):
            # Handle image sent as document
            file_id = update.message.document.file_id
            post_data[user_id]['file_id'] = file_id
            await update.message.reply_text("Image received successfully!")
        else:
            await update.message.reply_text("Please send a valid image or /skip to continue.")
            return IMAGE
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        await update.message.reply_text("Error processing the image. Please try again or use /skip to continue without an image.")
        return IMAGE

    # Ask for channel selection
    return await ask_channel_selection(update, context)

async def skip_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Skip image input and ask for channel selection."""
    user_id = update.effective_user.id
    if 'file_id' in post_data[user_id]:
        del post_data[user_id]['file_id']
        
    await update.message.reply_text("Skipping image. Continuing without an image.")
    return await ask_channel_selection(update, context)

async def ask_channel_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask user to select a channel."""
    user_id = update.effective_user.id

    # Check if channels are configured
    if not CHANNELS:
        await update.message.reply_text("No channels configured. Please contact the administrator.")
        return ConversationHandler.END

    # Create inline keyboard for channel selection
    keyboard = []
    for channel_name in CHANNELS.keys():
        keyboard.append([InlineKeyboardButton(channel_name, callback_data=f"channel_{channel_name}")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Please select a channel to post to:",
        reply_markup=reply_markup
    )

    return CHANNEL_SELECTION

async def channel_selection_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle channel selection."""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    channel_key = query.data.replace("channel_", "")

    if channel_key not in CHANNELS:
        await query.edit_message_text("Invalid channel selection. Please try again.")
        return CHANNEL_SELECTION

    post_data[user_id]['channel_id'] = CHANNELS[channel_key]
    post_data[user_id]['channel_name'] = channel_key

    # Format the post
    formatted_post = format_post(post_data[user_id])

    # Create inline keyboard with URL buttons
    keyboard = [
        [
            InlineKeyboardButton("PREMIUM", url=post_data[user_id]['premium_url']),
            InlineKeyboardButton("TUTORIAL VID", url=post_data[user_id]['tutorial_url'])
        ],
        [
            InlineKeyboardButton("DOWNLOAD LINK", url=post_data[user_id]['download_url'])
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Show preview
    try:
        # First, edit the query message to show we're processing
        await query.edit_message_text("Creating preview...")
        
        # Send the preview as a new message
        if 'file_id' in post_data[user_id]:
            # Send the photo with caption
            await context.bot.send_photo(
                chat_id=user_id,
                photo=post_data[user_id]['file_id'],
                caption=formatted_post,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        else:
            # Send text only
            await context.bot.send_message(
                chat_id=user_id,
                text=formatted_post,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )

        # Edit the original message to show it's done
        await query.edit_message_text("Post preview sent!")
        
        # Send confirmation message
        await context.bot.send_message(
            chat_id=user_id,
            text=f"Post will be sent to: {post_data[user_id]['channel_name']}\n\nSend /confirm to post or /cancel to discard."
        )
    except Exception as e:
        logger.error(f"Error showing preview: {e}")
        # Try to show text-only preview if image fails
        try:
            await query.edit_message_text("Error with image, showing text-only preview...")
            
            # Send text-only preview
            await context.bot.send_message(
                chat_id=user_id,
                text=formatted_post,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            
            # Send confirmation message
            await context.bot.send_message(
                chat_id=user_id,
                text=f"Post will be sent to: {post_data[user_id]['channel_name']}\n\nSend /confirm to post or /cancel to discard."
            )
        except Exception as e2:
            logger.error(f"Error showing text preview: {e2}")
            await query.edit_message_text("Error creating preview. Please try again.")
            return ConversationHandler.END

    return CONFIRM

async def confirm_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm and send the post to the selected channel."""
    user_id = update.effective_user.id

    if user_id not in post_data:
        await update.message.reply_text("No post data found. Please use /post to create a new post.")
        return ConversationHandler.END

    # Format the post
    formatted_post = format_post(post_data[user_id])

    # Create inline keyboard with URL buttons
    keyboard = [
        [
            InlineKeyboardButton("PREMIUM", url=post_data[user_id]['premium_url']),
            InlineKeyboardButton("TUTORIAL VID", url=post_data[user_id]['tutorial_url'])
        ],
        [
            InlineKeyboardButton("DOWNLOAD LINK", url=post_data[user_id]['download_url'])
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send to selected channel
    channel_id = post_data[user_id]['channel_id']

    try:
        if 'file_id' in post_data[user_id]:
            # Send image with caption
            await context.bot.send_photo(
                chat_id=channel_id,
                photo=post_data[user_id]['file_id'],
                caption=formatted_post,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        else:
            # Send text only
            await context.bot.send_message(
                chat_id=channel_id,
                text=formatted_post,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )

        await update.message.reply_text(f"Post has been sent to {post_data[user_id]['channel_name']}!")
    except Exception as e:
        logger.error(f"Error sending post: {e}")
        await update.message.reply_text(f"Error sending post: {str(e)}")

    # Clear user data
    if user_id in post_data:
        del post_data[user_id]

    return ConversationHandler.END

async def cancel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the post creation process."""
    user_id = update.effective_user.id

    if user_id in post_data:
        del post_data[user_id]

    await update.message.reply_text("Post creation cancelled.")
    return ConversationHandler.END

def format_post(data):
    """Format the post data into the desired structure with HTML formatting."""
    # Escape HTML special characters to prevent parsing issues
    def escape_text(text):
        return html.escape(str(text))
    
    # Format title based on style selection
    if data.get('title_style') == 'quote':
        title_formatted = f"<blockquote>{escape_text(data['title'])}</blockquote>"
    else:
        title_formatted = f"<b>{escape_text(data['title'])}</b>"

    return (
        f"{title_formatted}\n"
        f"╭━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"‣ Type : {escape_text(data['type'])}\n"
        f"‣ Status : {escape_text(data['status'])}\n"
        f"‣ Chapters : {escape_text(data['chapters'])}\n"
        f"‣ Rating : {escape_text(data['rating'])}\n"
        f"‣ Genre : {escape_text(data['genre'])}\n"
        f"╰━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<blockquote>Synopsis: {escape_text(data['synopsis'])}</blockquote>\n\n"
        f"<blockquote>Powered By: {escape_text(POWERED_BY_USERNAME)}</blockquote>"
    )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors caused by Updates."""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    
    # Notify user about the error
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "An error occurred while processing your request. Please try again."
            )
        except Exception as e:
            logger.error(f"Error sending error message: {e}")

def main():
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add error handler
    application.add_error_handler(error_handler)

    # Add handlers
    application.add_handler(CommandHandler("start", start))

    # Conversation handler for post creation
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('post', post_command)],
        states={
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, title_input)],
            TITLE_STYLE: [CallbackQueryHandler(title_style_handler)],
            MEDIA_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, type_input)],
            STATUS: [MessageHandler(filters.TEXT & ~filters.COMMAND, status_input)],
            CHAPTERS: [MessageHandler(filters.TEXT & ~filters.COMMAND, chapters_input)],
            RATING: [MessageHandler(filters.TEXT & ~filters.COMMAND, rating_input)],
            GENRE: [MessageHandler(filters.TEXT & ~filters.COMMAND, genre_input)],
            SYNOPSIS: [MessageHandler(filters.TEXT & ~filters.COMMAND, synopsis_input)],
            PREMIUM_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, premium_url_input)],
            TUTORIAL_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, tutorial_url_input)],
            DOWNLOAD_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, download_url_input)],
            IMAGE: [
                MessageHandler(filters.PHOTO | filters.Document.IMAGE, image_input),
                CommandHandler('skip', skip_image)
            ],
            CHANNEL_SELECTION: [CallbackQueryHandler(channel_selection_handler)],
            CONFIRM: [
                CommandHandler('confirm', confirm_post),
                CommandHandler('cancel', cancel_post)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel_post)],
        conversation_timeout=300,  # 5 minutes timeout
    )

    application.add_handler(conv_handler)

    # Start the Bot
    application.run_polling(
        poll_interval=1.0,
        timeout=10,
        drop_pending_updates=True
    )

if __name__ == '__main__':
    main()
