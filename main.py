from pyrogram import Client, filters
from pymongo import MongoClient
from datetime import datetime, timedelta

# Thiết lập bot Telegram
API_ID = "29849735"
API_HASH = "01cd8192498b6b6dca10995b0504e7fc"
BOT_TOKEN = "7078453005:AAGr4lmiINmNLZsY6EjWWPbj38CT8p07ev8"

app = Client("stats_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
# Kết nối với MongoDB
mongo_client = MongoClient("mongodb+srv://music:2407@muoi.bqveh.mongodb.net/?retryWrites=true&w=majority&appName=music")
db = mongo_client["telegram_stats"]
collection = db["message_counts"]

def update_message_count(user_id, chat_id):
    """ Cập nhật số lượng tin nhắn theo tuần/tháng trong MongoDB cho từng nhóm """
    now = datetime.now()
    
    user_data = collection.find_one({"user_id": user_id, "chat_id": chat_id})

    if user_data:
        collection.update_one(
            {"user_id": user_id, "chat_id": chat_id},
            {"$inc": {"weekly_count": 1, "monthly_count": 1}, "$set": {"last_updated": now}}
        )
    else:
        collection.insert_one(
            {"user_id": user_id, "chat_id": chat_id, "weekly_count": 1, "monthly_count": 1, "last_updated": now}
        )

@app.on_message(filters.group & ~filters.bot)
def track_messages(client, message):
    """ Theo dõi tin nhắn mới trong bất kỳ nhóm nào và cập nhật thống kê vào MongoDB """
    update_message_count(message.from_user.id, message.chat.id)

@app.on_message(filters.command("top10", prefixes=["/", "!"]) & filters.group)
async def send_top10(client, message):
    """ Gửi danh sách top 10 người nhắn nhiều nhất khi có lệnh /top10 trong nhóm hiện tại """
    chat_id = message.chat.id

    top_weekly = collection.find({"chat_id": chat_id}).sort("weekly_count", -1).limit(10)
    top_monthly = collection.find({"chat_id": chat_id}).sort("monthly_count", -1).limit(10)

    message_text = "🏆 **Top 10 người nhắn nhiều nhất:**\n\n"
    message_text += "**📅 Trong tuần:**\n" + "\n".join([f"- [{user['user_id']}](tg://user?id={user['user_id']}): {user['weekly_count']} tin nhắn" for user in top_weekly])
    message_text += "\n\n**🗓 Trong tháng:**\n" + "\n".join([f"- [{user['user_id']}](tg://user?id={user['user_id']}): {user['monthly_count']} tin nhắn" for user in top_monthly])

    await app.send_message(message_text, disable_web_page_preview=True)

print("✅ Bot đang chạy với MongoDB...")
app.run()
