import os
import yaml
from pkg.plugin.context import register, handler, llm_func, BasePlugin, APIHost, EventContext
from pkg.plugin.events import *  # 导入事件类


# 注册插件
@register(name="ChatWeather", description="Use function calls to get weather information", version="0.1", author="renil")
class MyPlugin(BasePlugin):

    # 插件加载时触发
    def __init__(self, host: APIHost):
        dirpath = f"data/plugins/ChatWeather/"
        filepath = os.path.join(dirpath,"config.yaml")

        if not os.path.isdir(dirpath):
            os.makedirs(dirpath)
        self.cfg = {
                "hfapi" : "https://devapi.qweather.com/v7/weather/",  # 和风天气免费api接口
                "hfkey" : ""  # 和风天气api key
        }
        if not os.path.exists(filepath):
            with open(filepath, 'w', encoding="utf-8") as f:
                yaml.dump(self.cfg, stream=f, allow_unicode=False)
        with open(filepath, "r", encoding="utf-8") as f:
            self.cfg = yaml.load(f, Loader=yaml.FullLoader)
        
        self.hfapi = self.cfg["hfapi"]
        self.hfkey = self.cfg["hfkey"]
        pass

    # 异步初始化
    async def initialize(self):
        pass

    @llm_func(name="access_the_weather")  # 设置函数名称
    async def access_web(self, query, location: str, adm: str, time: int):
        """Call this function to get location-based weather.
        - You can pass in the obtained weather time in the parameter "time", the optional values are: 3,7,10,15, if the user asks for weather that is not in here, select a longer phase and intercept the weather for the required time.
        - The fxLink in result is Weather detail link, Only provide this link if the user needs more information.
        - China's administrative divisions are organized into three levels. The first level includes "省", "自治区", and "直辖市". The second level comprises "自治州", "县", "自治县", and "市". The third level includes "乡", "民族乡", and "镇", which are subdivisions of "县" and "自治县".
        - You need to identify the level of location zoning and use the higher level as 'adm' parameter.
        - An example of partitioning parameters: INPUT is "山东省济南市历城区", "location" is "历城", "adm" is "山东",
        - Summary the json content result by yourself, DO NOT directly output anything in the result you got.
        - If return error, please tell the error reason.

        Args:
            location(str): location to get weather
            adm(str): The superior division of location, could be None
            time(int): time to get
    
        Returns:
            json: json result for the weather.
            json: .fxLink is "详情链接"
            json: .updateTime is "更新时间"
            json: the INT in .daily[INT] refers to the date from today, so .daily[0] is "今日天气".
            json: .daily[INT].tempMax is "最高温度", .daily[INT].tempMin is "最低温度".
            json: .daily[INT].textDay is "白天天气", .daily[0].textNight is "晚上天气".
        """
        import httpx
        import json
        import urllib.parse

        if not self.hfkey or not self.hfapi or self.hfkey == '':
            return '{"没有输入和风天气api密钥，请让用户知道这一点，并且告诉api在https://console.qweather.com/#/apps获取"}'
        params = {'location': urllib.parse.quote(location), 'key': self.hfkey}
        if adm:
            params['adm'] = urllib.parse.quote(adm)
        rlocation = httpx.get('https://geoapi.qweather.com/v2/city/lookup', params=params)
        locationid ='101010100'
        if rlocation.status_code == 200:
            locationdata = rlocation.json()
            if 'location' in locationdata and len(locationdata['location']) > 0:
                locationid = locationdata['location'][0]['id']
            else:
                print(locationdata)
        else:
            return False

        params = {'location': locationid, 'key': self.hfkey}
        rweather = httpx.get(self.hfapi + str(time) + 'd', params=params)
        weatherdata = '{}'
        if rweather.status_code == 200:
            weatherdict = rweather.json()
            weatherdata = json.dumps(weatherdict)

        return weatherdata


    # 插件卸载时触发
    def __del__(self):
        pass
