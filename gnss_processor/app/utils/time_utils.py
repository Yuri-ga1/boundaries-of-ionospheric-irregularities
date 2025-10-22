from datetime import datetime as dt
from datetime import timedelta
from typing import List


def generate_5min_timestamps(flyby_datetimes: List[dt]) -> List[str]:
    """
    Генерация списка временных меток с шагом 5 минут.
    
    Покрывает диапазон flyby_datetimes и заканчивается на :00 или :05.
    
    Args:
        flyby_datetimes: Список меток времени
        
    Returns:
        List[str]: Список строк времени в формате "%Y-%m-%d %H:%M:%S.%f"
    """
    if not flyby_datetimes:
        return []
    
    start_time = min(flyby_datetimes)
    end_time = max(flyby_datetimes)

    # Округление начала до ближайшего >= ближайшего кратного 5 минут
    minute = (start_time.minute // 5) * 5
    start_time_rounded = start_time.replace(minute=minute, second=0, microsecond=0)
    
    if start_time > start_time_rounded:
        start_time_rounded += timedelta(minutes=5)

    # Генерация временных меток с шагом 5 минут
    five_min_steps = []
    current_time = start_time_rounded
    
    while current_time <= end_time:
        five_min_steps.append(current_time.strftime("%Y-%m-%d %H:%M:%S.%f"))
        current_time += timedelta(minutes=5)

    return five_min_steps