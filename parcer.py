import requests
import json
import time
import asyncio
import aiohttp


###  Функция для сбора всех цен за период времени от START_TIME до END_TIME
async def get_data(start_time, end_time, pare):
    url = f'https://api.binance.com/api/v3/klines?symbol={pare}&interval=1s&startTime={start_time}&endTime={end_time}&limit=1000'
    session = aiohttp.ClientSession()
    async with session.get(url) as resp:
        response = await resp.json()
    await session.close()
    data = response
    result = []
    for i in data:
        close_time = i[6]
        price = float(i[4])
        result.append((close_time, price))
    return result

### Функция разбивает запрос на 6 частей и формирует сортированный список с ценами с привязкой ко времени
async def get_data_1h(list, timestamp, pare):
    start_time = timestamp - 3600*1000             #millisec
    end_time = start_time + 600*1000
    print('Собираем цены за последний час')
    while start_time < timestamp:
        data = await get_data(start_time, end_time, pare)
        list += data
        start_time += 600*1000
        end_time += 600*1000
        print('Ведется сбор...')
    print('Цены за последний час собраны')
    list.sort(key=lambda x: x[0])

### Функция для сбора цен онлайн каждую секунду
async def get_online_data(list, pare):
    url = f'https://api.binance.com/api/v3/ticker/price?symbol={pare}'
    while True:
        response = requests.get(url)
        if response.status_code != 200:
            return print('CONNECTION ERROR')
        data = response.json()
        price = float(data['price'])
        value = (int(time.time()*1000), price)
        list.append(value)
        if len(list)>3600:
            del list[0:(len(list)-3600)]
        await asyncio.sleep(1)

### Функция для нахождения максимальной цены за последний час с последующим сравнением с текущей ценой, в случае расхождения более 1% выводит сообщение в консоль
async def find_max_price(list, current):
    while True:
        if len(list) >= 3600:
            last_price = list[-1][1]
            last_time = time.ctime(int(list[-1][0])/1000)
            last_3600 = list[-3600::]
            last_3600_sorted = sorted(last_3600, key=lambda x: x[1])
            max_price = last_3600_sorted[-1][1]
            if str(current) == 'y':
                print(f'Текущее время: {last_time}    Текущая цена: {last_price}')
            diff = (max_price - last_price)/max_price*100
            if  diff >= 1:
                print(f'ВНИМАНИЕ! ВНИМАНИЕ! ВНИМАНИЕ! \nТекущая цена: {last_price} ниже максимальной цены: {max_price} на {round(diff, 2)}%')
        await asyncio.sleep(1)

### Асинхронная реализация позволяет с момента запуска скрипта сравнивать текущую цену с ценами за последний час
### Ввод значения позволяет парсить любую валютную пару
def main():
    pare = input('Введите валютную пару без "/": ')
    current = input('Хотите получать текущие значения? (y/n): ')
    timestamp = int(time.time())*1000
    list=[]

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    task0 = loop.create_task(get_data_1h(list, timestamp, pare))
    task1 = loop.create_task(get_online_data(list, pare))
    task2 = loop.create_task(find_max_price(list, current))
    loop.run_until_complete(asyncio.wait([task0, task1, task2]))


if __name__ == '__main__':
    main()