import pandas as pd
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
from datetime import datetime
import os
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4

TOKEN = "8631281500:AAEETEgkMt2CYO06sYhaTUZbjkaQJZE8h5g"
FILE = "database_project.xlsx"

# =============================
# INIT DATABASE
# =============================
def init_db():

    if not os.path.exists(FILE):

        writer = pd.ExcelWriter(FILE, engine="openpyxl")

        pd.DataFrame(columns=["UserID","Role"]).to_excel(writer, sheet_name="Users", index=False)
        pd.DataFrame(columns=["ID","Nama","Nilai"]).to_excel(writer, sheet_name="Projects", index=False)
        pd.DataFrame(columns=["Tanggal","ProjectID","Nama"]).to_excel(writer, sheet_name="Absensi", index=False)
        pd.DataFrame(columns=["Tanggal","ProjectID","Jenis","Jumlah","Keterangan"]).to_excel(writer, sheet_name="Keuangan", index=False)

        writer.close()

# =============================
# MENU START
# =============================
def start(update: Update, context: CallbackContext):

    keyboard = [

        [InlineKeyboardButton("📁 Pilih Project", callback_data="pilih_project")],
        [InlineKeyboardButton("📝 Absen", callback_data="absen")],
        [InlineKeyboardButton("💰 Keuangan", callback_data="keuangan")],
        [InlineKeyboardButton("➕ Tambah Project", callback_data="tambah_project")],
        [InlineKeyboardButton("📄 Export", callback_data="export")]

    ]

    update.message.reply_text(
        "📊 Sistem Rekap Project\nSilakan pilih menu:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =============================
# BUTTON
# =============================
def button(update: Update, context: CallbackContext):

    query = update.callback_query
    query.answer()

    data = query.data

    # TAMBAH PROJECT
    if data == "tambah_project":

        context.user_data["mode"] = "add_project"
        query.message.reply_text("Ketik nama project:")

    # PILIH PROJECT
    elif data == "pilih_project":

        df = pd.read_excel(FILE, sheet_name="Projects")

        if df.empty:
            query.message.reply_text("Belum ada project")
            return

        keyboard = []

        for _,row in df.iterrows():

            keyboard.append([
                InlineKeyboardButton(row["Nama"],callback_data=f"setproj_{row['ID']}")
            ])

        query.message.reply_text(
            "Pilih project:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # SET PROJECT
    elif data.startswith("setproj_"):

        pid = int(data.split("_")[1])
        context.user_data["project_id"] = pid

        query.message.reply_text("✅ Project dipilih")

    # ABSEN
    elif data == "absen":

        if "project_id" not in context.user_data:

            query.message.reply_text("⚠️ Pilih project dulu")
            return

        context.user_data["mode"] = "absen"
        query.message.reply_text("Ketik nama yang absen:")

    # KEUANGAN
    elif data == "keuangan":

        if "project_id" not in context.user_data:

            query.message.reply_text("⚠️ Pilih project dulu")
            return

        context.user_data["mode"] = "keuangan"

        query.message.reply_text(
            "Format:\nmasuk 100000 keterangan\natau\nkeluar 50000 beli bahan"
        )

    # EXPORT
    elif data == "export":

        export_pdf(query,context)

# =============================
# HANDLE TEXT
# =============================
def handle_text(update: Update, context: CallbackContext):

    mode = context.user_data.get("mode")
    text = update.message.text

    # TAMBAH PROJECT
    if mode == "add_project":

        df = pd.read_excel(FILE, sheet_name="Projects")

        new_id = len(df) + 1

        df.loc[len(df)] = [new_id,text,0]

        with pd.ExcelWriter(FILE,engine="openpyxl",mode="a",if_sheet_exists="replace") as writer:

            df.to_excel(writer,sheet_name="Projects",index=False)

        update.message.reply_text("✅ Project ditambahkan")

    # ABSEN
    elif mode == "absen":

        df = pd.read_excel(FILE,sheet_name="Absensi")

        df.loc[len(df)] = [

            datetime.now(),
            context.user_data["project_id"],
            text

        ]

        with pd.ExcelWriter(FILE,engine="openpyxl",mode="a",if_sheet_exists="replace") as writer:

            df.to_excel(writer,sheet_name="Absensi",index=False)

        update.message.reply_text("📝 Absen tersimpan")

    # KEUANGAN
    elif mode == "keuangan":

        data = text.split()

        jenis = data[0]
        jumlah = int(data[1])
        ket = " ".join(data[2:])

        df = pd.read_excel(FILE,sheet_name="Keuangan")

        df.loc[len(df)] = [

            datetime.now(),
            context.user_data["project_id"],
            jenis,
            jumlah,
            ket

        ]

        with pd.ExcelWriter(FILE,engine="openpyxl",mode="a",if_sheet_exists="replace") as writer:

            df.to_excel(writer,sheet_name="Keuangan",index=False)

        update.message.reply_text("💰 Data keuangan tersimpan")

    context.user_data["mode"] = None

# =============================
# EXPORT PDF
# =============================
def export_pdf(query,context):

    pid = context.user_data.get("project_id")

    if not pid:

        query.message.reply_text("Pilih project dulu")
        return

    absensi = pd.read_excel(FILE,"Absensi")
    keuangan = pd.read_excel(FILE,"Keuangan")

    total_absen = len(absensi[absensi["ProjectID"]==pid])

    pemasukan = keuangan[(keuangan["ProjectID"]==pid)&(keuangan["Jenis"]=="masuk")]["Jumlah"].sum()

    pengeluaran = keuangan[(keuangan["ProjectID"]==pid)&(keuangan["Jenis"]=="keluar")]["Jumlah"].sum()

    filename = f"laporan_project_{pid}.pdf"

    doc = SimpleDocTemplate(filename,pagesize=A4)

    style = ParagraphStyle(name="Normal",fontSize=12)

    elements = []

    elements.append(Paragraph(f"Laporan Project {pid}",style))
    elements.append(Spacer(1,20))
    elements.append(Paragraph(f"Total Absen: {total_absen}",style))
    elements.append(Paragraph(f"Pemasukan: {pemasukan}",style))
    elements.append(Paragraph(f"Pengeluaran: {pengeluaran}",style))
    elements.append(Paragraph(f"Laba/Rugi: {pemasukan-pengeluaran}",style))

    doc.build(elements)

    query.message.reply_document(open(filename,"rb"))

# =============================
# MAIN
# =============================
def main():

    init_db()

    updater = Updater(TOKEN,use_context=True)

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start",start))
    dp.add_handler(CallbackQueryHandler(button))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command,handle_text))

    updater.start_polling()

    print("BOT BERJALAN")

    updater.idle()

if __name__ == "__main__":
    main()
