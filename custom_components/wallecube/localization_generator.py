"""
Автоматическая генерация локализаций для интеграции WalleCube.

Этот модуль создаёт словари локализаций на основе SENSOR_TYPES и BINARY_SENSOR_TYPES
из const.py и может использоваться для генерации ru/en/zh-Hans.json.
"""

import json
from .const import SENSOR_TYPES, BINARY_SENSOR_TYPES


# -----------------------------
#  Переводы для всех языков
# -----------------------------

TRANSLATIONS = {
    "en": {
        "sensor": {
            "totalConsumption": "Total Consumption",
            "leftSecs": "Remaining Runtime",
            "batteryCapacity": "Battery Level",
            "currentOut": "Output Current",
            "voltageOut": "Output Voltage",
            "pwrOut": "Output Power",
            "chargingCurrent": "Charging Current",
            "batteryVoltage": "Battery Voltage",
            "currentInput": "Input Current",
            "voltageInput": "Input Voltage",
            "batteryTemperature": "Battery Temperature",
            "ipAddress": "IP Address"
        },
        "binary_sensor": {
            "acOK": "AC Adapter Status",
            "charging": "Charging Status"
        }
    },
    "ru": {
        "sensor": {
            "totalConsumption": "Общее потребление",
            "leftSecs": "Оставшееся время работы",
            "batteryCapacity": "Уровень заряда батареи",
            "currentOut": "Выходной ток",
            "voltageOut": "Выходное напряжение",
            "pwrOut": "Выходная мощность",
            "chargingCurrent": "Ток зарядки",
            "batteryVoltage": "Напряжение батареи",
            "currentInput": "Входной ток",
            "voltageInput": "Входное напряжение",
            "batteryTemperature": "Температура батареи",
            "ipAddress": "IP‑адрес"
        },
        "binary_sensor": {
            "acOK": "Состояние адаптера питания",
            "charging": "Состояние зарядки"
        }
    },
    "zh-Hans": {
        "sensor": {
            "totalConsumption": "总耗电量",
            "leftSecs": "剩余运行时间",
            "batteryCapacity": "电池电量",
            "currentOut": "输出电流",
            "voltageOut": "输出电压",
            "pwrOut": "输出功率",
            "chargingCurrent": "充电电流",
            "batteryVoltage": "电池电压",
            "currentInput": "输入电流",
            "voltageInput": "输入电压",
            "batteryTemperature": "电池温度",
            "ipAddress": "IP 地址"
        },
        "binary_sensor": {
            "acOK": "电源适配器状态",
            "charging": "充电状态"
        }
    }
}


# -----------------------------
#  Генератор локализаций
# -----------------------------

def generate_language(lang: str) -> dict:
    """Создаёт структуру локализации Home Assistant для указанного языка."""

    if lang not in TRANSLATIONS:
        raise ValueError(f"Language '{lang}' is not supported")

    lang_map = TRANSLATIONS[lang]

    result = {
        "entity": {
            "sensor": {},
            "binary_sensor": {}
        }
    }

    # Сенсоры
    for sensor_id in SENSOR_TYPES.keys():
        result["entity"]["sensor"][sensor_id] = {
            "name": lang_map["sensor"][sensor_id]
        }

    # Бинарные сенсоры
    for sensor_id in BINARY_SENSOR_TYPES.keys():
        result["entity"]["binary_sensor"][sensor_id] = {
            "name": lang_map["binary_sensor"][sensor_id]
        }

    return result


def save_language_file(lang: str, path: str):
    """Сохраняет JSON-файл локализации."""
    data = generate_language(lang)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# -----------------------------
#  Пример использования
# -----------------------------
if __name__ == "__main__":
    save_language_file("en", "translations/en.json")
    save_language_file("ru", "translations/ru.json")
    save_language_file("zh-Hans", "translations/zh-Hans.json")
    print("Localization files generated successfully.")