# импортируем библиотеки
from flask import Flask, request
import logging

# библиотека, которая нам понадобится для работы с JSON 
import json


app = Flask(__name__)

UsersInfo = {}

MAX_ATTEMPTS = 3
@app.route('/post', methods=['POST'])
def main():
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }


    handle_dialog(request.json, response)

    return json.dumps(response)

#ID НАВЫКА: ca3cf6a4-23c3-4c5e-ab22-399667851cc2
#TOKEN: AQAAAAAgHVfTAAT7o74wRDdoBEMIsn0Vuvrw_7E

cities = ['москва', 'нью-йорк', 'париж']

cities_images = {
    'москва': ['1656841/d31fa6c666f418af17f9', '1652229/236601277ea4d922b995'],
    'нью-йорк': ['1540737/0370fbd8934a1826b4cf', '1540737/cb8a1ed928b0a9787c7e'],
    'париж': ['1540737/0acfa03fdc091f045310', '1030494/371e70af6f2abef80d4c', '1030494/ea43e5ab50f612f2cd54']
}

countries = {'москва':'россия', 'нью-йорк':'соединённые штаты америки', 'париж':'франция'}


def get_name(req):
    for entity in req['request']['nlu']['entities']:
        if entity['type'] == 'YANDEX.FIO':
            if('first_name' in entity['value']):
                return entity['value']['first_name']
            return None



def handle_dialog(req, res):
    user_id = req['session']['user_id']

    if req['session']['new']: # Приветствуем
        UsersInfo[user_id] = {
            'cities': cities,
            'name': None,
            'progress': 0,
            'get_started': 0,
            'attempt': 0
        }

        res['response']['text'] = 'Привет! Назови своё имя!'
        return


    if UsersInfo[user_id]['name'] is None: # Проверяем представился ли человек
        name = get_name(req)
        if name is None:
            res['response']['text'] = 'Не расслышала имя. Повтори, пожалуйста!'
        else:
            UsersInfo[user_id]['name'] = name
            res['response']['text'] = 'Приятно познакомиться, {}. Я Алиса. Отгадаешь город по фото?'.format(name)

            res['response']['buttons'] = [
                    {
                        'title': 'Да',
                        'hide': True
                    },
                    {
                        'title': 'Нет',
                        'hide': True
                    },
                    {
                    'title': 'Расскажи правила',
                    'hide': True
                    }
                ]
        return

    # Человек представился, начинаем играть

    if 'расскажи правила' in req['request']['original_utterance'].lower():
        res['response'][
            'text'] = 'Правила очень просты, я показываю вам город, вы угадываете его название, простите не расслышала имя. Начнём играть?'
        res['response']['buttons'] = [
            {
                'title': 'Да',
                'hide': True
            },
            {
                'title': 'Нет',
                'hide': True
            }
        ]
        return

    if not UsersInfo[user_id]['get_started']: # Ожидаем желания поиграть
        if 'посмотреть город на карте' in req['request']['original_utterance'].lower():
            res['response'][
                'text'] = 'Продолжим играть?'
            res['response']['buttons'] = [
                {
                    'title': 'Да',
                    'hide': True
                },
                {
                    'title': 'Нет',
                    'hide': True
                }
            ]
            return
        elif 'да' in req['request']['nlu']['tokens']:
            if UsersInfo[user_id]['progress'] == len(cities):
                res['response']['text'] = 'Увы, но у нас кончились города!'
                res['end_session'] = True
            else:
                UsersInfo[user_id]['get_started'] = 1
                play_game(res, req)

        elif 'нет' in req['request']['nlu']['tokens']:
            res['response']['text'] = 'Ну и ладно!'
            res['end_session'] = True

        else:
            res['response']['text'] = 'Не поняла ответа! Так да или нет?'
            res['response']['buttons'] = [
                {
                    'title': 'Да',
                    'hide': True
                },
                {
                    'title': 'Нет',
                    'hide': True
                }
            ]
    elif UsersInfo[user_id]['get_started'] == 1:
        play_game(res, req)

    elif UsersInfo[user_id]['get_started'] == 2:
        play_country(res, req)


def get_city(req):
    # перебираем именованные сущности
    for entity in req['request']['nlu']['entities']:
        # если тип YANDEX.GEO, то пытаемся получить город(city), если нет, то возвращаем None
        if entity['type'] == 'YANDEX.GEO':
            # возвращаем None, если не нашли сущности с типом YANDEX.GEO
            return entity['value'].get('city', None)


def play_game(res, req):
    user_id = req['session']['user_id']
    attempt = UsersInfo[user_id]['attempt']
    if attempt == 0:
        city = cities[UsersInfo[user_id]['progress']]
        res['response']['card'] = {}
        res['response']['card']['type'] = 'BigImage'
        res['response']['card']['title'] = 'Что это за город?'
        res['response']['card']['image_id'] = cities_images[city][attempt]
        res['response']['text'] = 'Тогда сыграем!'
        UsersInfo[user_id]['attempt'] += 1
    else:
        UsersInfo[user_id]['attempt'] += 1
        city = cities[UsersInfo[user_id]['progress']]

        if get_city(req) == city:
            UsersInfo[user_id]['progress'] += 1
            UsersInfo[user_id]['attempt'] = 0


            res['response']['text'] = 'Правильно! А в какой стране находится этот город?'
            res['response']['buttons'] = [
                {
                    "title": "Посмотреть город на карте",
                    "url": "https://yandex.ru/maps/?mode=search&text={}".format(city),
                    "hide": True
                }
            ]
            UsersInfo[user_id]['get_started'] = 2
            return
        else:
            if attempt == len(cities_images[city]):
                # если попытка третья, то значит, что все картинки мы показали.
                # В этом случае говорим ответ пользователю,
                # добавляем город к sessionStorage[user_id]['guessed_cities'] и отправляем его на второй круг.
                # Обратите внимание на этот шаг на схеме.
                res['response']['text'] = 'Вы пытались. Это {}. Попробуйте угадать в какой стране он находится'.format(city)
                res['response']['buttons'] = [
                    {
                        "title": "Посмотреть город на карте",
                        "url": "https://yandex.ru/maps/?mode=search&text={}".format(city),
                        "hide": True
                    }
                ]
                UsersInfo[user_id]['get_started'] = 2
                UsersInfo[user_id]['progress'] += 1
                UsersInfo[user_id]['attempt'] = 0
            else:
                # иначе показываем следующую картинку
                res['response']['card'] = {}
                res['response']['card']['type'] = 'BigImage'
                res['response']['card']['title'] = 'Неправильно. Вот тебе дополнительное фото'
                res['response']['card']['image_id'] = cities_images[city][attempt]
                res['response']['text'] = 'А вот и не угадал!'


def play_country(res, req):
    user_id = req['session']['user_id']
    country = get_country(req)
    need_country = countries[cities[UsersInfo[user_id]['progress'] - 1]]


    if(country is None):
        res['response'][
            'text'] = 'Я не расслышала название страны? Повторите пожалуйста!'
        return
    if (country == need_country):
        res['response'][
            'text'] = 'Правильно! Продолжим угадывать города?'
        res['response']['buttons'] = [
            {
                'title': 'Да',
                'hide': True
            },
            {
                'title': 'Нет',
                'hide': True
            }
        ]
    else:
        res['response'][
            'text'] = 'Увы, но это {} ! Продолжим угадывать города?'.format(need_country)
        res['response']['buttons'] = [
            {
                'title': 'Да',
                'hide': True
            },
            {
                'title': 'Нет',
                'hide': True
            }
        ]

    UsersInfo[user_id]['get_started'] = 0


def get_country(req):
    # перебираем именованные сущности
    for entity in req['request']['nlu']['entities']:
        # если тип YANDEX.GEO, то пытаемся получить город(city), если нет, то возвращаем None
        if entity['type'] == 'YANDEX.GEO':
            # возвращаем None, если не нашли сущности с типом YANDEX.GEO
            return entity['value'].get('country', None)


if __name__ == '__main__':
    app.run()