from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from PIL import Image, ExifTags
import pytesseract
from geopy.geocoders import Nominatim
import cv2
import os

# Функция для извлечения координат из EXIF
def get_exif_coordinates(image_path):
    try:
        image = Image.open(image_path)
        exif_data = image._getexif()
        if not exif_data:
            return None

        gps_info = {}
        for tag, value in exif_data.items():
            decoded = ExifTags.TAGS.get(tag, tag)
            if decoded == "GPSInfo":
                for key in value.keys():
                    gps_tag = ExifTags.GPSTAGS.get(key, key)
                    gps_info[gps_tag] = value[key]

        if "GPSLatitude" in gps_info and "GPSLongitude" in gps_info:
            lat = convert_to_degrees(gps_info["GPSLatitude"])
            lon = convert_to_degrees(gps_info["GPSLongitude"])
            if gps_info.get("GPSLatitudeRef") == "S":
                lat = -lat
            if gps_info.get("GPSLongitudeRef") == "W":
                lon = -lon
            return lat, lon
    except Exception as e:
        print(f"Ошибка при извлечении EXIF: {e}")
    return None

# Преобразование координат
def convert_to_degrees(value):
    d, m, s = value
    return d + (m / 60.0) + (s / 3600.0)

# Распознавание текста
def extract_text(image_path):
    try:
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image, lang="eng")
        return text.strip()
    except Exception as e:
        print(f"Ошибка при распознавании текста: {e}")
    return None

# Поиск местоположения
def search_osm(query):
    try:
        geolocator = Nominatim(user_agent="geoapi")
        location = geolocator.geocode(query)
        if location:
            return location.address
    except Exception as e:
        print(f"Ошибка при поиске в OSM: {e}")
    return "Место не найдено."

# Обнаружение объектов
def detect_objects(image_path):
    try:
        image = cv2.imread(image_path)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        objects = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        detections = objects.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        return detections
    except Exception as e:
        print(f"Ошибка при обнаружении объектов: {e}")
    return None

# Обработчик изображений
def handle_image(update: Update, context: CallbackContext):
    file = update.message.photo[-1].get_file()
    image_path = f"{file.file_id}.jpg"
    file.download(image_path)

    # 1. Координаты
    coordinates = get_exif_coordinates(image_path)
    if coordinates:
        update.message.reply_text(f"Координаты из EXIF: {coordinates}")
    else:
        update.message.reply_text("Геоданные отсутствуют в EXIF.")

    # 2. Текст
    text = extract_text(image_path)
    if text:
        update.message.reply_text(f"Распознанный текст: {text}")
        location = search_osm(text)
        update.message.reply_text(f"Местоположение по тексту: {location}")
    else:
        update.message.reply_text("Текст не обнаружен.")

    # 3. Объекты
    objects = detect_objects(image_path)
    if objects is not None and len(objects) > 0:
        update.message.reply_text(f"Найдено объектов: {len(objects)}")
    else:
        update.message.reply_text("Объекты не обнаружены.")

    # Удаляем локальный файл
    os.remove(image_path)

# Команда /start
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Привет! Отправьте мне изображение, и я обработаю его.")

# Основная функция
def main():
    updater = Updater("7519051898:AAGpbEnrD44Lu2xQhc_nLdYflS8XAKEHheA", use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.photo, handle_image))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
