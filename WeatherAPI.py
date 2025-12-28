import requests


    
def get_weather (city):
    r = requests.get(f'https://api.openweathermap.org/data/2.5/forecast?q={city}&appid=67175b1397b0a6a4a5bae494a69730bc&units=metric')
    content = r.json()
    weathers = content["list"]
    results = []    
    for i in weathers:
        results.append(f"{city}, {i['dt_txt']}, {i['main']['temp']}, {i['weather'][0]['description']}")
        
    return results

city = input("What City would like to check the weather on? ")
test = get_weather(city)

for item in test:
    print(item)
