import time
import pandas as pd
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
from datetime import datetime
import os

TOKEN = "8631281500:AAEETEgkMt2CYO06sYhaTUZbjkaQJZE8h5g"
ADMIN_ID = 8650707421
FILE = "database_project.xlsx"

def init_db():
    if not os.path.exists(FILE):
        writer = pd.ExcelWriter(FILE, engine="openpyxl")

        pd.DataFrame(columns=["UserID","Role"]).to_excel(writer, sheet_name="Users", index=False)
        pd.DataFrame(columns=["ID","Nama","Nilai"]).to_excel(writer, sheet_name="Projects", index=False)
        pd.DataFrame(columns=["Tanggal","ProjectID","Nama"]).to_excel(writer, sheet_name="Absensi", index=False)
        pd.DataFrame(columns=["Tanggal","ProjectID","Jenis","Jumlah","Keterangan"]).to_excel(writer, sheet_name="Keuangan", index=False)

        writer.close()

def start(update: Update, context: CallbackContext):

    keyboard = [
        [InlineKeyboardButton("📁 Pilih Project", callback_data='pilih_project')],
        [InlineKeyboardButton("📝 Absen", callback_data='absen')],
        [InlineKeyboardButton("💰 Keuangan", callback_data='keuangan')],
        [InlineKeyboardButton("➕ Tambah Project", callback_data='tambah_project')],
        [InlineKeyboardButton("📄 Export", callback_data='export')]
    ]

    update.message.reply_text(
        "📊 *Sistem Rekap Project*\nSilakan pilih menu:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def button(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    # =====================
    # TAMBAH PROJECT
    # =====================
    if query.data == "tambah_project":
        query.message.reply_text("Ketik nama project:")
        context.user_data["mode"] = "add_project"

    # =====================
    # PILIH PROJECT
    # =====================
    elif query.data == "pilih_project":

        df = pd.read_excel(FILE, sheet_name="Projects")

        if df.empty:
            query.message.reply_text("Belum ada project.")
            return

        keyboard = []

        for _, row in df.iterrows():
            keyboard.append([
                InlineKeyboardButton(
                    row["Nama"],
                    callback_data=f"setproj_{row['ID']}"
                )
            ])

        query.message.reply_text(
            "Pilih project:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # =====================
    # SET PROJECT AKTIF
    # =====================
    elif query.data.startswith("setproj_"):

        pid = int(query.data.split("_")[1])

        context.user_data["project_id"] = pid

        query.message.reply_text("✅ Project dipilih")

    # =====================
    # ABSEN
    # =====================
    elif query.data == "absen":

        if "project_id" not in context.user_data:
            query.message.reply_text("Pilih project dulu.")
            return

        query.message.reply_text("Ketik nama yang absen:")
        context.user_data["mode"] = "absen"

    # =====================
    # KEUANGAN
    # =====================
    elif query.data == "keuangan":

        if "project_id" not in context.user_data:
            query.message.reply_text("Pilih project dulu.")
            return

        query.message.reply_text(
            "Format:\nmasuk 100000 keterangan\natau\nkeluar 50000 beli bahan"
        )

        context.user_data["mode"] = "keuangan"

    # =====================
    # EXPORT
    # =====================
    elif query.data == "export":

        if "project_id" not in context.user_data:
            query.message.reply_text("Pilih project dulu.")
            return

        export_pdf(query, context)
def handle_text(update: Update, context: CallbackContext):
    mode=context.user_data.get("mode")
    text=update.message.text

    if mode=="add_project":
        df=pd.read_excel(FILE,"Projects")
        new_id=len(df)+1
        df.loc[len(df)]=[new_id,text,0]

        with pd.ExcelWriter(FILE, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
           df.to_excel(writer, sheet_name="Users", index=False)

        update.message.reply_text("✅ Project ditambahkan")
        context.user_data["mode"]=None

def main():

    init_db()

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))

    updater.start_polling()

    print("BOT BERJALAN...")

    while True:
        time.sleep(60)

if __name__ == "__main__":
    main()
