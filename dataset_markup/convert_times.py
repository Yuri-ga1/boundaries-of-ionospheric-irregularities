import h5py
import numpy as np
from datetime import datetime
import datetime as dat

def convert_times_to_timestamps_inplace(h5_path):
    """Заменяет атрибут 'times' на массив float timestamp'ов во всех группах."""
    
    def parse_times(times):
        """Преобразует список строк или байт в временные метки."""
        timestamps = []
        for t in times:
            if isinstance(t, bytes):
                t = t.decode('utf-8')
            try:
                dt = datetime.fromisoformat(t)
            except ValueError:
                dt = datetime.fromtimestamp(float(t), dat.UTC)
            timestamps.append(dt.timestamp())
        return np.array(timestamps, dtype='float64')

    with h5py.File(h5_path, 'a') as f:
        def visit_group(name, obj):
            if isinstance(obj, h5py.Group) and 'times' in obj.attrs:
                try:
                    original_times = obj.attrs['times']
                    timestamps = parse_times(original_times)
                    del obj.attrs['times']  # Удаляем старый атрибут перед заменой
                    obj.attrs.create('times', timestamps)  # Создаем с нужным типом
                    print(f"[OK] Обновлён атрибут 'times' в группе {name}")
                except Exception as e:
                    print(f"[ERR] Ошибка при обработке группы {name}: {e}")

        f.visititems(visit_group)

convert_times_to_timestamps_inplace('dataset1.h5')
