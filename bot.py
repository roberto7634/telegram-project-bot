import pandas as pd
import os
from datetime import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext

TOKEN = "8631281500:AAEETEgkMt2CYO06sYhaTUZbjkaQJZE8h5g"
FILE = "database.xlsx"

# =========================
# INIT DATABASE
# =========================
def init_db():

    if not os.path.exists(FILE):

        writer = pd.ExcelWriter(FILE, engine="openpyxl")

        pd.DataFrame(columns=["ID","Nama"]).to_excel(writer, sheet_name="Projects", index=False)
        pd.DataFrame(columns=["Tanggal","ProjectID","Nama"]).to_excel(writer, sheet_name="Absensi", index=False)
        pd.DataFrame(columns=["Tanggal","ProjectID","Jenis","Jumlah","Keterangan"]).to_excel(writer, sheet_name="Keuangan", index=False)

        writer.close()

# =========================
# START MENU
# =========================
def start(update: Update, context: CallbackContext):

    keyboard = [

        [InlineKeyboardButton("📁 Pilih Project", callback_data="project")],
        [InlineKeyboardButton("➕ Tambah Project", callback_data="add_project")],
        [InlineKeyboardButton("📝 Absen", callback_data="absen")],
        [InlineKeyboardButton("💰 Keuangan", callback_data="keuangan")]

    ]

    update.message.reply_text(
        "📊 Sistem Rekap Project",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =========================
# BUTTON
# =========================
def button(update: Update, context: CallbackContext):

    query = update.callback_query
    query.answer()

    data = query.data

    if data == "add_project":

        context.user_data["mode"] = "add_project"
        query.message.reply_text("Ketik nama project")

    elif data == "project":

        df = pd.read_excel(FILE, sheet_name="Projects")

        keyboard = []

        for _, row in df.iterrows():

            keyboard.append([
                InlineKeyboardButton(
                    row["Nama"],
                    callback_data=f"set_{row['ID']}"
                )
            ])

        query.message.reply_text(
            "Pilih Project",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data.startswith("set_"):

        pid = int(data.split("_")[1])

        context.user_data["project"] = pid

        query.message.reply_text("✅ Project dipilih")

    elif data == "absen":

        context.user_data["mode"] = "absen"
        query.message.reply_text("Ketik nama yang absen")

    elif data == "keuangan":

        context.user_data["mode"] = "keuangan"

        query.message.reply_text(
            "Format:\nmasuk 100000 keterangan\natau\nkeluar 50000 beli bahan"
        )

# =========================
# HANDLE TEXT
# =========================
def handle(update: Update, context: CallbackContext):

    mode = context.user_data.get("mode")
    text = update.message.text

    # tambah project
    if mode == "add_project":

        df = pd.read_excel(FILE, sheet_name="Projects")

        new_id = len(df) + 1

        df.loc[len(df)] = [new_id, text]

        with pd.ExcelWriter(FILE, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:

            df.to_excel(writer, sheet_name="Projects", index=False)

        update.message.reply_text("✅ Project ditambahkan")

    # absen
    elif mode == "absen":

        df = pd.read_excel(FILE, sheet_name="Absensi")

        df.loc[len(df)] = [

            datetime.now(),
            context.user_data.get("project"),
            text

        ]

        with pd.ExcelWriter(FILE, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:

            df.to_excel(writer, sheet_name="Absensi", index=False)

        update.message.reply_text("📝 Absen tersimpan")

    # keuangan
    elif mode == "keuangan":

        data = text.split()

        jenis = data[0]
        jumlah = int(data[1])
        ket = " ".join(data[2:])

        df = pd.read_excel(FILE, sheet_name="Keuangan")

        df.loc[len(df)] = [

            datetime.now(),
            context.user_data.get("project"),
            jenis,
            jumlah,
            ket

        ]

        with pd.ExcelWriter(FILE, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:

            df.to_excel(writer, sheet_name="Keuangan", index=False)

        update.message.reply_text("💰 Data keuangan tersimpan")

    context.user_data["mode"] = None

# =========================
# MAIN
# =========================
def main():

    init_db()

    updater = Updater(TOKEN, use_context=True)

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle))

    print("BOT BERJALAN")

    updater.start_polling()

    updater.idle()

if __name__ == "__main__":
    main()
