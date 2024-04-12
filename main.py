import requests
import json
import re
import locale
import pytz
from bs4 import BeautifulSoup
from os.path import exists
from datetime import datetime, timedelta
from timeit import default_timer as timer

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

# NOTE: Setiap tahap eksekusi dilacak waktu eksekusinya
waktu_scraping = 0
waktu_cleansing = 0
waktu_menyimpan = 0

FORMAT_WAKTU_REPUBLIKA = "%A , %d %b %Y, %H:%M %Z"
FORMAT_WAKTU_BARU = "%A, %d %b %Y, %H:%M:%S"

def clean_text(text: str) -> str:
    '''
        Fungsi untuk membersihkan teks
        
        Author: Yobel El'Roy Doloksaribu - 231524029
    '''

    kumpulanKata = text.strip().split()

    return ' '.join(kumpulanKata)

def convert_history_to_time(text: str) -> str:
    '''
        Melakukan konversi dari teks seperti
        "8 menit yang lalu"
        Menjadi waktu terbit berita

        Author: Yobel El'Roy Doloksaribu - 231524029
    '''

    pattern = r"(\d+)\s+(\w+)"
    match = re.search(pattern, text)

    if match:
        angka = int(match.group(1))
        satuanWaktu = match.group(2)
        
        waktuSekarang = datetime.now()
        if satuanWaktu == 'jam':
            date = timedelta(hours=angka)
        elif satuanWaktu == 'menit':
            date = timedelta(minutes=angka)
        elif satuanWaktu == 'detik':
            date = timedelta(seconds=angka) 
        else:
            date = timedelta(seconds=0)

        waktuTerbit = waktuSekarang - date
        return waktuTerbit.strftime(FORMAT_WAKTU_BARU)
    else:
        return ''

def format_waktuberita(text: str):
    '''
        Melakukan konversi dari teks yang berpola
        "Rabu , 10 Apr 2024, 06:16 WIB"
        Menjadi format waktu sesuai standard yang diberikan

        Author: Yobel El'Roy Doloksaribu - 231524029
    '''

    date_string = clean_text(text)

    # Split the string by comma and remove any leading/trailing spaces
    date_parts = [part.strip() for part in date_string.split(",")]

    # Extract day, date, month, year, time, and timezone
    day = date_parts[0]  # Day name
    date_info = date_parts[1].split()  # Date, month, year
    time = date_parts[2].split()[0]  # Time
    timezone_abbreviation = date_parts[2].split()[1]  # Timezone abbreviation

    # Map the Indonesian day name to English
    day_mapping = {
        "Senin": "Monday",
        "Selasa": "Tuesday",
        "Rabu": "Wednesday",
        "Kamis": "Thursday",
        "Jumat": "Friday",
        "Sabtu": "Saturday",
        "Minggu": "Sunday"
    }
    english_day = day_mapping.get(day)

    # Construct datetime string in a format recognizable by strptime
    datetime_string = f"{english_day}, {date_info[0]} {date_info[1]} {date_info[2]}, {time}"

    # Parse the datetime string
    datetime_object = datetime.strptime(datetime_string, "%A, %d %b %Y, %H:%M")

    # Set the timezone
    local_timezone = pytz.timezone('Asia/Jakarta')
    datetime_object = local_timezone.localize(datetime_object)

    return datetime_object.strftime(FORMAT_WAKTU_BARU)


# ---------------------------------------------------------------------------- #
#                     TAHAP 1: Mengambil html dari website                     #
# ---------------------------------------------------------------------------- #

start = timer()

URL = 'https://www.republika.co.id/'
SAVED_WEBSITE_PATH = 'website.html'

request = requests.get(URL)
page = BeautifulSoup(request.text, features='html.parser')

end = timer()

waktu_scraping = end - start
print(f'Waktu untuk scrapping data: {waktu_scraping} detik')

# ---------------------------------------------------------------------------- #
#                            TAHAP 2: Cleansing data                           #
# ---------------------------------------------------------------------------- #
        
# ------------------- BAGIAN 1 -- Mengambil berita headline ------------------ #

start = timer()
rawHeadline = page.find_all('a', { 'class': 'link-headline' })
listBeritaHeadline = []

for item in rawHeadline:
    judul = clean_text(item.find('div', { 'class': 'title-headline' }).text)
    link_berita = item['href']
    
    listBeritaHeadline.append({
        'judul': judul,
        'link_berita': link_berita
    })


# ------------------- BAGIAN 2 -- Mengambil berita unggulan ------------------ #

rawBeritaUnggulan = page.find('div', { 'id': 'wrap-unggulan-carousel' })
listBeritaUnggulan = []

for item in rawBeritaUnggulan.find_all('a'):
    judul = clean_text(item.find('div', { 'class': 'title' }).text)
    link_berita = item['href']

    listBeritaUnggulan.append({
        'judul': judul,
        'link_berita': link_berita
    })

# ------------------- BAGIAN 3 -- Mengambil berita lainnya ------------------- #
    
rawBeritaLainnya = page.select('li.list-group-item.list-border.conten1:not(.eksternal)')
listBeritaLainnya = []

for item in rawBeritaLainnya:
    judul = clean_text(item.find('h3').text)
    link_berita = item.find('a').get('href')
    kategori = item.find('span', { 'class': 'kanal-info' }).get_text(strip=True)
    waktuTerbit = convert_history_to_time(item.find('div', { 'class': 'date' }).get_text(strip=True).split('-')[1].strip())

    listBeritaLainnya.append({
        'judul': judul,
        'link_berita': link_berita,
        'kategori': kategori,
        'tanggal_terbit': waktuTerbit
    })


# Mengambil berita yang memiliki tanggal lengkap
beritaGrid = page.select('div.medium-box')
for item in beritaGrid:
    judul = clean_text(item.select_one('div.title').text)
    link_berita = item.find('a').get('href')
    kategori = kategori = item.find('span', { 'class': 'kanal-info' }).get_text(strip=True)
    waktuTerbit = format_waktuberita(item.find('div', { 'class': 'date' }).get_text(strip=True).split('-')[1].strip())

    listBeritaLainnya.append({
        'judul': judul,
        'link_berita': link_berita,
        'kategori': kategori,
        'tanggal_terbit': waktuTerbit
    })

end = timer()
waktu_cleansing = end - start
print(f'Waktu untuk cleansing data: {waktu_cleansing} detik')

# ---------------------------------------------------------------------------- #
#              TAHAP 3: Menyatukan semua data dalam satu file json             #
# ---------------------------------------------------------------------------- #

start = timer()
local_timezone = pytz.timezone('Asia/Jakarta')

hasilCleansing = {
    'berita_headline': listBeritaHeadline,
    'berita_unggulan': listBeritaUnggulan,
    'berita_lainnya': listBeritaLainnya,
    'waktu_scraping': local_timezone.localize(datetime.now()).strftime(FORMAT_WAKTU_BARU)
}

with open('serve/result.json', 'w') as jsonfile:
    json.dump(hasilCleansing, jsonfile, indent=2)
    jsonfile.close()

end = timer()
waktu_menyimpan = end - start

print(f'Waktu untuk menyimpan data: {waktu_menyimpan} detik')
print(f'Total waktu: {waktu_scraping + waktu_cleansing + waktu_menyimpan} detik')
