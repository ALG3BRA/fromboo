import requests


# def _get_translated_text(text):
#     url = "https://microsoft-translator-text.p.rapidapi.com/translate"
#     api_key = "980166210cmsh67259c90ff4afe7p114dd7jsnc8259e9857d4"
#     #api_key = "0086541c90msh512ac39bbeb60eep1f23bejsn1fddf1acc235"
#     querystring = {"from": "en", "to[0]": "ru", "api-version": "3.0", "profanityAction": "NoAction",
#                    "textType": "plain"}
#     payload = [{"Text": f"{text}"}]
#     headers = {
#         "content-type": "application/json",
#         "X-RapidAPI-Key": api_key,
#         "X-RapidAPI-Host": "microsoft-translator-text.p.rapidapi.com"
#     }
#     try:
#         response = requests.post(url, json=payload, headers=headers, params=querystring)
#         if response.status_code == 200:
#             return response.json()[0]["translations"][0]["text"]
#         else:
#             print("Ошибка при получении данных. Статус код: [rapid api]", response.status_code)
#     except requests.exceptions.RequestException as error:
#         print("Ошибка при выполненении запроса. Статус код: ", error)
#

def _get_translated_text(text):
    return "красный"


