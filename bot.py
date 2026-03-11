import pandas as pd
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
from datetime import datetime
import os
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4

TOKEN = "8631281500:AAEBi0xKTj5X3qxBhJWOm9dyZ_E1Tbxa8D0"
ADMIN_ID = 8650707421
FILE = "database_project.xlsx"

# =============================
# INIT DATABASE
# =============================
def init_db():
    if not os.path.exists(FILE):
        writer = pd.ExcelWriter(FILE, engine='openpyxl')
        
        pd.DataFrame(columns=["UserID","Role"]).to_excel(writer,"Users",index=False)
        pd.DataFrame(columns=["ID","Nama","Nilai"]).to_excel(writer,"Projects",index=False)
        pd.DataFrame(columns=["Tanggal","ProjectID","Nama"]).to_excel(writer,"Absensi",index=False)
        pd.DataFrame(columns=["Tanggal","ProjectID","Jenis","Jumlah","Keterangan"]).to_excel(writer,"Keuangan",index=False)
        
        writer.close()

# =============================
# CEK ROLE
# =============================
def get_role(user_id):
    if user_id == ADMIN_ID:
        return "admin"
    return "staff"

# =============================
# MENU
# =============================
def start(update: Update, context: CallbackContext):
    role = get_role(update.message.from_user.id)

    keyboard = [
        [InlineKeyboardButton("📁 Pilih Project", callback_data='pilih_project')],
        [InlineKeyboardButton("📝 Absen", callback_data='absen')],
        [InlineKeyboardButton("💰 Keuangan", callback_data='keuangan')],
    ]

    if role == "admin":
        keyboard.append([InlineKeyboardButton("➕ Tambah Project", callback_data='tambah_project')])
        keyboard.append([InlineKeyboardButton("📊 Set Nilai", callback_data='nilai')])
        keyboard.append([InlineKeyboardButton("📄 Export PDF", callback_data='export')])

    update.message.reply_text("MENU", reply_markup=InlineKeyboardMarkup(keyboard))

# =============================
# BUTTON HANDLER
# =============================
def button(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    if query.data == "tambah_project":
        query.message.reply_text("Ketik nama project:")
        context.user_data["mode"]="add_project"

    elif query.data == "pilih_project":
        df = pd.read_excel(FILE,"Projects")
        keyboard=[]
        for _,row in df.iterrows():
            keyboard.append([InlineKeyboardButton(row["Nama"],callback_data=f"setproj_{row['ID']}")])
        query.message.reply_text("Pilih:",reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("setproj_"):
        context.user_data["project_id"]=int(query.data.split("_")[1])
        query.message.reply_text("Project aktif dipilih")

    elif query.data == "absen":
        query.message.reply_text("Ketik nama absen:")
        context.user_data["mode"]="absen"

    elif query.data == "keuangan":
        query.message.reply_text("Format: masuk 100000 keterangan")
        context.user_data["mode"]="keuangan"

    elif query.data == "nilai":
        query.message.reply_text("Masukkan nilai project:")
        context.user_data["mode"]="nilai"

    elif query.data == "export":
        export_pdf(query,context)

# =============================
# HANDLE TEXT
# =============================
def handle_text(update: Update, context: CallbackContext):
    mode=context.user_data.get("mode")
    text=update.message.text

    if mode=="add_project":
        df=pd.read_excel(FILE,"Projects")
        new_id=len(df)+1
        df.loc[len(df)]=[new_id,text,0]
        df.to_excel(FILE,"Projects",index=False)
        update.message.reply_text("Project ditambahkan")

    elif mode=="absen":
        df=pd.read_excel(FILE,"Absensi")
        df.loc[len(df)]=[datetime.now(),context.user_data["project_id"],text]
        df.to_excel(FILE,"Absensi",index=False)
        update.message.reply_text("Absen tersimpan")

    elif mode=="keuangan":
        data=text.split()
        df=pd.read_excel(FILE,"Keuangan")
        df.loc[len(df)]=[datetime.now(),context.user_data["project_id"],data[0],int(data[1])," ".join(data[2:])]
        df.to_excel(FILE,"Keuangan",index=False)
        update.message.reply_text("Keuangan tersimpan")

    elif mode=="nilai":
        df=pd.read_excel(FILE,"Projects")
        df.loc[df["ID"]==context.user_data["project_id"],"Nilai"]=int(text)
        dwith pd.ExcelWriter(FILE, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
    df.to_excel(writer, sheet_name="Projects", index=False)
        update.message.reply_text("Nilai diperbarui")

    context.user_data["mode"]=None

# =============================
# EXPORT PDF
# =============================
def export_pdf(query,context):
    pid=context.user_data.get("project_id")
    if not pid:
        query.message.reply_text("Pilih project dulu")
        return

    absensi=pd.read_excel(FILE,"Absensi")
    keuangan=pd.read_excel(FILE,"Keuangan")

    total_absen=len(absensi[absensi["ProjectID"]==pid])
    pemasukan=keuangan[(keuangan["ProjectID"]==pid)&(keuangan["Jenis"]=="masuk")]["Jumlah"].sum()
    pengeluaran=keuangan[(keuangan["ProjectID"]==pid)&(keuangan["Jenis"]=="keluar")]["Jumlah"].sum()

    filename=f"laporan_project_{pid}.pdf"
    doc=SimpleDocTemplate(filename,pagesize=A4)
    elements=[]

    style=ParagraphStyle(name='Normal',fontSize=12)

    elements.append(Paragraph(f"Laporan Project ID {pid}",style))
    elements.append(Spacer(1,12))
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
    updater=Updater(TOKEN)
    dp=updater.dispatcher

    dp.add_handler(CommandHandler("start",start))
    dp.add_handler(CallbackQueryHandler(button))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command,handle_text))

    updater.start_polling()
    updater.idle()

if __name__=="__main__":
    main()
