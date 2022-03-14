import time
import vk_api
import requests
from bs4 import BeautifulSoup
from dadata import Dadata
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard


#  функция для парсинга данных со страницы Яндекс
#  используется только для Москвы и Санкт-Петербурга
def get_statistics_yandex(region):
    url = "https://yandex.ru/maps/covid19?ll=41.775580%2C54.894027&z=3"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"}
    full_page = requests.get(url, headers=headers)
    soup = BeautifulSoup(full_page.content, "html.parser")
    soup = soup.find("td", {"class": "covid-table-view__item-name"}, string=region).parent
    new_cases = soup.find("span", {"class": "covid-table-view__item-cases-diff-text"}).getText()
    count_cases = soup.find("td", {"class": "covid-table-view__item-cases"}).getText()
    new_cases = '+' + new_cases
    return {"region": region, "new_cases": new_cases, "count_cases": count_cases}


#  функция для парсинга данных со страницы Google
#  используется для всех регионов, кроме Москвы и Санкт-Петербурга
def get_statistics_google(region):
    url = "https://www.google.com/search?q=%D0%A1%D1%82%D0%B0%D1%82%D0%B8%D1%81%D1%82%D0%B8%D0%BA%D0%B0+%D0%BA%D0%BE%D0%B2%D0%B8%D0%B4+19+%D1%80%D0%BE%D1%81%D1%81%D0%B8%D1%8F&sxsrf=AOaemvJGYry9y48m1adb8n1juYvKjRH9GA%3A1640791540060&ei=9H3MYaKSA42WrwSKmZCgAg&ved=0ahUKEwii3JTnqIn1AhUNy4sKHYoMBCQQ4dUDCA4&uact=5&oq=%D0%A1%D1%82%D0%B0%D1%82%D0%B8%D1%81%D1%82%D0%B8%D0%BA%D0%B0+%D0%BA%D0%BE%D0%B2%D0%B8%D0%B4+19+%D1%80%D0%BE%D1%81%D1%81%D0%B8%D1%8F&gs_lcp=Cgdnd3Mtd2l6EAMyBQgAEMsBMgYIABAWEB4yBggAEBYQHjIGCAAQFhAeMgYIABAWEB4yBggAEBYQHjIGCAAQFhAeMgYIABAWEB4yBggAEBYQHjoECCMQJzoKCC4QxwEQowIQJzoGCCMQJxATOgUIABCABDoKCAAQgAQQhwIQFDoFCC4QgARKBAhBGABKBAhGGABQAFjrKGCGKmgAcAJ4AoAB0ASIAaEYkgEKMTkuNS4xLjUtMZgBAKABAcABAQ&sclient=gws-wiz"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"}
    full_page = requests.get(url, headers=headers)
    soup = BeautifulSoup(full_page.content, "html.parser")
    soup = soup.find_all("td", {"class": "HB6aoe p8lMe QM7g5b mvzKZe Pmvw7b"})
    for reg in soup:
        if region.lower() in reg.getText().lower():
            region = reg.getText()
            try:
                new_cases = reg.parent.find("div", {"class": "JZLOZd"}).find("span").getText()
            except AttributeError:
                new_cases = ''
            count_cases = reg.parent.find("div", {"class": "ruktOc"}).find("span").getText()
            return {"region": region, "new_cases": new_cases, "count_cases": count_cases}


def main():
    vk_session = vk_api.VkApi(
        token="*Your token*")
    vk = vk_session.get_api()
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_location_button()
    token = "*Your token*"
    dadata = Dadata(token)  # объект dadata нужен для преобразования координат в название региона
    while True:
        chats = vk.messages.getConversations(offset=0, filter="unread")
        for chat in chats["items"]:
            msg = chat["last_message"]
            if msg["text"] == "Начать" or msg["text"] == "/start":
                mess = "Это бот, который следит за эпидемологической ситуацией 🦠" \
                       "\nВведите название региона или укажите его на карте 👇🏻"
            else:
                if "geo" in msg:
                    place = dadata.geolocate(name="address", lat=msg["geo"]["coordinates"]["latitude"],
                                             lon=msg["geo"]["coordinates"]["longitude"])
                    try:
                        place = place[0]["data"]["region"]
                    except IndexError:
                        place = "Не удалось найти информацию"
                else:
                    place = msg["text"]
                if place.lower() == "москва":
                    res = get_statistics_yandex("Москва")
                elif place.lower() == "санкт-петербург" or place.lower() == "санкт петербург":
                    res = get_statistics_yandex("Санкт-Петербург")
                else:
                    res = get_statistics_google(place)
                if res == None:
                    mess = "Данные некорректны. Попробуйте еще раз"
                else:
                    if res["new_cases"] != '':
                        mess = "Регион: " + res["region"] + "\nНовые случаи: " + res[
                            "new_cases"] + "\nОбщее число заражений: " + res["count_cases"]
                    else:
                        mess = "Регион: " + res["region"] + "\nОбщее число заражений: " + res["count_cases"]
            vk.messages.send(
                peer_id=msg["from_id"],
                random_id=get_random_id(),
                keyboard=keyboard.get_keyboard(),
                message=mess
            )
        time.sleep(1)


if __name__ == "__main__":
    main()
