# 瓦力盒子 (WalleCube) UPS Home Assistant 集成

Для получения актуальной информации о состоянии ИБП необходимо подписаться на официальный сервер MQTT.

# Получение учетной записи MQTT

## С помощью перехвата пакетов получаем имя пользователя и пароль для подключения к MQTT.

Установите на свой компьютер программу для захвата пакетов, например Wireshark. Затем включите на своём компьютере точку доступа и запустите программу Wireshark (после включения захвата пакетов вы можете ввести в поисковой строке "MQTT" для фильтрации пакетов). Затем подключите ИБП к точке доступа компьютера. Если все в порядке, вы сможете получить информацию для аутентификации MQTT для соответствующего ИБП. После получения информации вы можете отключить точку доступа и переподключить свой ИБП на сеть маршрутизатора.

<a href="wireshark"><img src="https://github.com/xswxm/home-assistant-wallecube/blob/main/wireshark.png?raw=true" width="512" ></a>



# 安装方式

## 使用 HACS 安装

[![打开 Home Assistant 并打开 HACS商店内的存储库。](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=xswxm&repository=[home-assistant-wallecube](https://github.com/xswxm/home-assistant-wallecube)&category=integration)

## 手动安装

将 `custom_components` 下的 `wallecube` 文件夹到 Home Assistant 中的`custom_components` 目录，并手动重启 Home Assistant。

# 设置

[![打开 Home Assistant 并设置新的集成。](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=wallecube)

> [!CAUTION]
> 
> 如果您无法使用上面的按钮，请按照以下步骤操作：
> 
> 1. 导航到 Home Assistant 集成页面（设置 --> 设备和服务）
> 2. 单击右下角的 `+ 添加集成` 按钮
> 3. 搜索 `wallecube`

> [!NOTE]
> 
> 1. 设备IMEI 填写获取到的MQTT用户名
> 2. 设备密钥 填写获取到的MQTT密码


# 拓展衍生

因为集成依赖互联网连接，如果需要本地化，也有很多办法。比如可以将官方mqtt服务器地址本地解析到自己的mqtt服务器，然后再转发给官方服务器，这样就既可以本地化，又可以保留原有的功能。
