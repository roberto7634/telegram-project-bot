import pandas as pd
import os
from datetime import datetime
import matplotlib.pyplot as plt

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4

TOKEN = "8631281500:AAEETEgkMt2CYO06sYhaTUZbjkaQJZE8h5g"
ADMIN_ID = 8650707421
FILE = "database.xlsx"

# =====================
# INIT DATABASE
# =====================

def init_db():

    if not os.path.exists(FILE):

        writer = pd.ExcelWriter(FILE, engine="openpyxl")

        pd.DataFrame(columns=["UserID","Role"]).to_excel(writer,"Users",index=False)
        pd.DataFrame(columns=["ID","Nama","Nilai"]).to_excel(writer,"Projects",index=False)
        pd.DataFrame(columns=["Tanggal","ProjectID","Nama"]).to_excel(writer,"Absensi",index=False)
        pd.DataFrame(columns=["Tanggal","ProjectID","Jenis","Jumlah","Keterangan"]).to_excel(writer,"Keuangan",index=False)

        writer.close()

# =====================
# ROLE
# =====================

def get_role(user_id):

    if user_id == ADMIN_ID:
        return "admin"

    return "staff"

# =====================
# MENU
# =====================

def start(update: Update, context: CallbackContext):

    role = get_role(update.message.from_user.id)

    keyboard = [
        [InlineKeyboardButton("📁 Pilih Project",callback_data="project")],
        [InlineKeyboardButton("📝 Absen",callback_data="absen")],
        [InlineKeyboardButton("💰 Keuangan",callback_data="keuangan")],
        [InlineKeyboardButton("📊 Statistik",callback_data="stats")]
    ]

    if role == "admin":

        keyboard.append([InlineKeyboardButton("➕ Tambah Project",callback_data="add_project")])
        keyboard.append([InlineKeyboardButton("📄 Export PDF",callback_data="export_pdf")])
        keyboard.append([InlineKeyboardButton("📂 Export Excel",callback_data="export_excel")])

    update.message.reply_text(
        "📊 Sistem Manajemen Project",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =====================
# BUTTON
# =====================

def button(update: Update, context: CallbackContext):

    query = update.callback_query
    query.answer()

    data = query.data

    if data == "add_project":

        context.user_data["mode"] = "add_project"
        query.message.reply_text("Ketik nama project")

    elif data == "project":

        df = pd.read_excel(FILE,"Projects")

        keyboard=[]

        for _,row in df.iterrows():

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

        query.message.reply_text("Project dipilih")

    elif data == "absen":

        context.user_data["mode"] = "absen"
        query.message.reply_text("Ketik nama anggota")

    elif data == "keuangan":

        context.user_data["mode"] = "keuangan"

        query.message.reply_text(
            "Format:\nmasuk 100000 keterangan\natau\nkeluar 50000 beli bahan"
        )

    elif data == "stats":

        show_stats(query,context)

    elif data == "export_pdf":

        export_pdf(query,context)

    elif data == "export_excel":

        query.message.reply_document(open(FILE,"rb"))

# =====================
# HANDLE TEXT
# =====================

def handle(update: Update, context: CallbackContext):

    mode = context.user_data.get("mode")
    text = update.message.text

    if mode == "add_project":

        df = pd.read_excel(FILE,"Projects")

        new_id = len(df)+1
        df.loc[len(df)] = [new_id,text,0]

        with pd.ExcelWriter(FILE,engine="openpyxl",mode="a",if_sheet_exists="replace") as writer:

            df.to_excel(writer,"Projects",index=False)

        update.message.reply_text("Project ditambahkan")

    elif mode == "absen":

        df = pd.read_excel(FILE,"Absensi")

        df.loc[len(df)] = [
            datetime.now(),
            context.user_data["project"],
            text
        ]

        with pd.ExcelWriter(FILE,engine="openpyxl",mode="a",if_sheet_exists="replace") as writer:

            df.to_excel(writer,"Absensi",index=False)

        update.message.reply_text("Absen tersimpan")

    elif mode == "keuangan":

        data = text.split()

        jenis = data[0]
        jumlah = int(data[1])
        ket = " ".join(data[2:])

        df = pd.read_excel(FILE,"Keuangan")

        df.loc[len(df)] = [
            datetime.now(),
            context.user_data["project"],
            jenis,
            jumlah,
            ket
        ]

        with pd.ExcelWriter(FILE,engine="openpyxl",mode="a",if_sheet_exists="replace") as writer:

            df.to_excel(writer,"Keuangan",index=False)

        update.message.reply_text("Data keuangan tersimpan")

    context.user_data["mode"] = None

# =====================
# STATISTIK
# =====================

def show_stats(query,context):

    pid = context.user_data.get("project")

    absensi = pd.read_excel(FILE,"Absensi")
    keuangan = pd.read_excel(FILE,"Keuangan")

    total_absen = len(absensi[absensi["ProjectID"]==pid])

    pemasukan = keuangan[(keuangan["ProjectID"]==pid)&(keuangan["Jenis"]=="masuk")]["Jumlah"].sum()
    pengeluaran = keuangan[(keuangan["ProjectID"]==pid)&(keuangan["Jenis"]=="keluar")]["Jumlah"].sum()

    query.message.reply_text(
        f"""
📊 Statistik Project

Total Absen : {total_absen}

Pemasukan : {pemasukan}

Pengeluaran : {pengeluaran}

Saldo : {pemasukan-pengeluaran}
"""
    )

# =====================
# EXPORT PDF
# =====================

def export_pdf(query,context):

    pid = context.user_data.get("project")

    absensi = pd.read_excel(FILE,"Absensi")
    keuangan = pd.read_excel(FILE,"Keuangan")

    total_absen = len(absensi[absensi["ProjectID"]==pid])

    pemasukan = keuangan[(keuangan["ProjectID"]==pid)&(keuangan["Jenis"]=="masuk")]["Jumlah"].sum()
    pengeluaran = keuangan[(keuangan["ProjectID"]==pid)&(keuangan["Jenis"]=="keluar")]["Jumlah"].sum()

    file = f"laporan_{pid}.pdf"

    doc = SimpleDocTemplate(file,pagesize=A4)

    style = ParagraphStyle(name="Normal",fontSize=12)

    elements=[]

    elements.append(Paragraph("Laporan Project",style))
    elements.append(Spacer(1,20))
    elements.append(Paragraph(f"Total Absen: {total_absen}",style))
    elements.append(Paragraph(f"Pemasukan: {pemasukan}",style))
    elements.append(Paragraph(f"Pengeluaran: {pengeluaran}",style))
    elements.append(Paragraph(f"Saldo: {pemasukan-pengeluaran}",style))

    doc.build(elements)

    query.message.reply_document(open(file,"rb"))

# =====================
# MAIN
# =====================

def main():

    init_db()

    updater = Updater(TOKEN,use_context=True)

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start",start))
    dp.add_handler(CallbackQueryHandler(button))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command,handle))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
