# Backend Documentation

## Структура папок и файлов

### Корневая директория
- **main.py** - основной файл запуска приложения

### app/pipline/
- **data_processing_pipeline.py** - содержит класс DataProcessingPipeline для координации обработки данных

### app/processors/
- **map_processor.py** - содержит класс MapProcessor для обработки картографических данных
- **simurg_hdf5_processor.py** - содержит класс SimurgHDF5Processor для обработки HDF5 файлов от сервиса SIMuRG

### app/services/auroral_oval/
- **boundary_detector.py** - содержит класс BoundaryDetector для обнаружения границ
- **cluster_processor.py** - содержит класс ClusterProcessor для обработки кластеров
- **crossing_detector.py** - содержит класс BoundaryCrossingDetector для обнаружения пересечений границ спутниками
- **sliding_window_processor.py** - содержит класс SlidingWindowProcessor для обработки скользящего окна

### app/services/satellite/
- **flyby_processor.py** - содержит класс SatelliteFlybyProcessor для обработки пролетов спутников
- **satellite_data_processor.py** - содержит класс SatelliteDataProcessor для обработки данных спутников
- **trajectory_calculator.py** - содержит класс SatelliteTrajectory для расчета траекторий спутников

### app/utils/
- **az_el_to_lot_lon.py** - содержит функцию az_el_to_lot_lon для преобразование азимута и угла возвышения в географические координаты
- **time_utils.py** - содержит функцию generate_5min_timestamps для работы с временными метками

### app/visualization/plotters/
- **combined_plotter.py** - содержит класс CombinedPlotter для создания комбинированных визуализаций
- **map_plotter.py** - содержит класс MapPlotter для построения карт
- **polygon_plotter.py** - содержит класс PolygonPlotter для работы с полигонами
- **satellite_plotter.py** - содержит класс SatellitePlotter для визуализации спутников
- **timeseries_plotter.py** - содержит класс TimeSeriesPlotter для обработки временных рядов

### app/visualization/
- **png_to_video_converter.py** - содержит класс PngToVideoConverter для преобразования PNG в видео

## Детальная документация файлов

### main.py

#### Основной блок выполнения

**Назначение:** Основной скрипт запуска пайплайна обработки данных с SIMuRG

**Конфигурация:**
Используемые константы из config.py:
- `RAW_DATA_PATH` - путь к директории с исходными данными
- `logger` - объект для логирования

**Используемые библиотеки:**
- `os` - для работы с файловой системой
- `matplotlib` - для установки бэкенда 'Agg' (неинтерактивного режима)

**Процесс обработки:**
1. Инициализация DataProcessingPipeline
2. Поиск HDF5 файлов в директории RAW_DATA_PATH
3. Последовательная обработка каждого файла через pipeline.process_date()
4. Логирование результатов обработки

#### Используемые классы

##### DataProcessingPipeline
**Методы:**
- `process_date(date_str)` - основной метод обработки данных для конкретной даты

---

### app/pipline/data_processing_pipeline.py

#### Класс `DataProcessingPipeline`

**Назначение:** Основной класс пайплайна для координации обработки данных GNSS

**Конструктор:**
```python
__init__()
```

**Инициализирует компоненты:**
- `map_processor` - обработчик карт ROTI
- `crossing_detector` - детектор пересечений границ
- `flyby_processor` - обработчик пролетов спутников
- `combined_plotter` - создатель комбинированных визуализаций
- `video_converter` - конвертер PNG в видео

**Конфигурация:**
Используемые константы из config.py:
- `RAW_DATA_PATH` - путь к директории с исходными данными
- `MAP_PATH` - путь для сохранения файлов карт
- `BOUNDARY_PATH` - путь для сохранения файлов границ
- `FLYBYS_PATH` - путь для сохранения файлов пролетов
- `PROCESSED_FLYBYS_PATH` - путь для сохранения обработанных файлов пролетов
- `FRAME_GRAPHS_PATH` - путь для сохранения графиков
- `SAVE_VIDEO_PATH` - путь для сохранения видео
- `LON_CONDITION`, `LAT_CONDITION` - географические условия
- `SEGMENT_LON_STEP`, `SEGMENT_LAT_STEP` - шаги скользящего окна
- `BOUNDARY_CONDITION` - пороговое значение для определения границы
- `logger` - объект для логирования

**Используемые библиотеки:**
- `os` - для работы с файловой системой
- `numpy` - для численных операций
- `h5py` - для работы с HDF5 файлами
- `datetime` - для работы с датами и временем
- `traceback` - для обработки и логирования ошибок

---

#### Методы класса DataProcessingPipeline

##### `process_date(date_str: str) -> bool`
**Назначение:** Основной метод обработки данных для конкретной даты

**Входные данные:**
- `date_str` (str): строка с датой в формате YYYYMMDD

**Результат:**
- `bool`: успешно ли выполнена обработка

**Процесс обработки:**
1. Определение путей к файлам данных
2. Обработка RINEX файла
3. Обработка карт и границ
4. Обработка пролетов спутников
5. Генерация визуализаций

---

##### Вспомогательные методы

###### `_get_rinex_file_path(date_str: str) -> str`
**Назначение:** Получение пути к RINEX файлу

###### `_get_map_file_path(date_str: str) -> str`
**Назначение:** Получение пути к файлу карт

###### `_get_boundary_file_path(date_str: str) -> str`
**Назначение:** Получение пути к файлу границ

###### `_get_flyby_file_path(date_str: str) -> str`
**Назначение:** Получение пути к файлу пролетов

###### `_get_processed_flyby_path(date_str: str) -> str`
**Назначение:** Получение пути к обработанному файлу пролетов

---

##### Методы обработки данных

###### `_process_rinex_file(rinex_file_path: str, date_str: str) -> Tuple[Optional[Dict], Optional[Dict]]`
**Назначение:** Обработка RINEX файла

**Входные данные:**
- `rinex_file_path` (str): путь к RINEX файлу
- `date_str` (str): дата для обработки

**Результат:**
- `Tuple`: данные спутников и пролетов

---

###### `_process_map_and_boundaries(map_file_path: str, boundary_file_path: str, date_str: str) -> Optional[Dict]`
**Назначение:** Обработка карт и извлечение границ

**Входные данные:**
- `map_file_path` (str): путь к файлу карт
- `boundary_file_path` (str): путь для сохранения границ
- `date_str` (str): дата для обработки

**Результат:**
- `Optional[Dict]`: данные кластеров границ

---

###### `_load_boundary_clusters(boundary_file_path: str) -> Optional[Dict]`
**Назначение:** Загрузка кластеров границ из файла

**Входные данные:**
- `boundary_file_path` (str): путь к файлу с границами

**Результат:**
- `Optional[Dict]`: данные кластеров границ

---

###### `_process_flybys(boundary_clusters: Dict, satellite_data: Dict, flybys_data: Dict, date_str: str, processed_flyby_path: str) -> None`
**Назначение:** Обработка пролетов спутников

**Входные данные:**
- `boundary_clusters` (Dict): кластеры границ
- `satellite_data` (Dict): данные спутников
- `flybys_data` (Dict): данные пролетов
- `date_str` (str): дата для обработки
- `processed_flyby_path` (str): путь для сохранения обработанных пролетов

---

##### Методы визуализации

###### `_generate_visualizations(boundary_file_path: str, processed_flyby_path: str, rinex_file_path: str, date_str: str) -> None`
**Назначение:** Генерация визуализаций для данных

**Входные данные:**
- `boundary_file_path` (str): путь к файлу границ
- `processed_flyby_path` (str): путь к обработанным пролетам
- `rinex_file_path` (str): путь к RINEX файлу
- `date_str` (str): дата для обработки

---

###### `_generate_flyby_visualizations(boundary_file_path: str, flyby_file: h5.File, rinex_file_path: str, station: str, satellite: str, flyby_key: str) -> None`
**Назначение:** Генерация визуализаций для конкретного пролета

**Входные данные:**
- `boundary_file_path` (str): путь к файлу границ
- `flyby_file` (h5.File): открытый HDF5 файл с пролетами
- `rinex_file_path` (str): путь к RINEX файлу
- `station` (str): станция
- `satellite` (str): спутник
- `flyby_key` (str): ключ пролета

---

###### `_generate_single_visualization(boundary_file_path: str, rinex_file_path: str, station: str, satellite: str, flyby_key: str, flyby_roti: np.ndarray, timestamp_datetimes: List[dt], cleaned_times: List[str], cleaned_types: List[str], time_point: str) -> None`
**Назначение:** Генерация одиночной визуализации для конкретного времени

**Входные данные:**
- `boundary_file_path` (str): путь к файлу границ
- `rinex_file_path` (str): путь к RINEX файлу
- `station` (str): станция
- `satellite` (str): спутник
- `flyby_key` (str): ключ пролета
- `flyby_roti` (np.ndarray): данные ROTI пролета
- `timestamp_datetimes` (List[dt]): временные метки
- `cleaned_times` (List[str]): очищенные времена событий
- `cleaned_types` (List[str]): типы событий
- `time_point` (str): временная точка

---

###### `_load_boundary_clusters_for_timepoint(boundary_file: h5.File, time_point: str) -> Optional[Dict]`
**Назначение:** Загрузка кластеров границ для конкретной временной точки

**Входные данные:**
- `boundary_file` (h5.File): открытый HDF5 файл с границами
- `time_point` (str): временная точка

**Результат:**
- `Optional[Dict]`: данные кластеров для временной точки

---

### app/processors/map_processor.py

#### Класс `MapProcessor`

**Назначение:** Основной класс для обработки карт ROTI и обнаружения границ аврорального овала

**Конструктор:**
```python
__init__(lon_condition, lat_condition, segment_lon_step, segment_lat_step, boundary_condition)
```

**Входные данные:**
- `lon_condition` (float): условие по долготе для близости к полюсу
- `lat_condition` (float): условие по широте для близости к полюсу
- `segment_lon_step` (float): шаг скользящего окна по долготе
- `segment_lat_step` (float): шаг скользящего окна по широте
- `boundary_condition` (float): пороговое значение для определения границы

**Инициализирует компоненты:**
- `boundary_detector` - детектор границ с параметрами конфигурации
- `sliding_window_processor` - процессор скользящего окна
- `cluster_processor` - процессор кластеров

**Конфигурация:**
Используемые константы из config.py:
- `WINDOW_AREA` - площадь окна для сегментации
- `WINDOW_WIDTH` - ширина окна для сегментации
- `logger` - объект для логирования

**Используемые библиотеки:**
- `numpy` - для численных операций с массивами
- `h5py` - для работы с HDF5 файлами
- `os` - для работы с файловой системой

---

#### Методы класса MapProcessor

##### `process_map_file(map_path: str, output_path: str, time_points: Optional[List[str]] = None) -> None`
**Назначение:** Основной метод обработки файла карты

**Входные данные:**
- `map_path` (str): путь к входному HDF5 файлу с картами
- `output_path` (str): путь для сохранения обработанных данных
- `time_points` (Optional[List[str]]): список временных точек для обработки (None = все точки)

**Процесс обработки:**
1. Сохранение исходных точек
2. Фильтрация точек по координатам
3. Применение скользящего окна
4. Обнаружение границ
5. Кластеризация границ

---

##### `_filter_coordinate_points(points_group: h5.Group) -> Dict[str, np.ndarray]`
**Назначение:** Фильтрация точек по координатным условиям

**Входные данные:**
- `points_group` (h5.Group): HDF5 группа с данными точек

**Результат:**
- `Dict[str, np.ndarray]`: отфильтрованные точки {'lon', 'lat', 'vals'}

**Фильтрация:**
- Долгота между -120 и lon_condition
- Широта ≥ lat_condition

---

##### `_process_single_time_point(data_group: h5.Group, time_point: str, output_file: h5.File) -> None`
**Назначение:** Обработка одной временной точки

**Входные данные:**
- `data_group` (h5.Group): группа с данными из входного файла
- `time_point` (str): идентификатор временной точки
- `output_file` (h5.File): выходной HDF5 файл

**Структура выходных данных:**
- `points` - исходные данные
- `filtered_points` - отфильтрованные данные
- `sliding_windows` - данные сегментированные скользящим окном
- `boundary` - данные границ
- `boundary_clusters` - кластеризованные границы

---

#### Методы сохранения данных

##### `_save_raw_points(points_group: h5.Group, time_group: h5.Group) -> None`
**Назначение:** Сохранение исходных точек данных

**Входные данные:**
- `points_group` (h5.Group): группа с исходными точками
- `time_group` (h5.Group): группа для сохранения в выходном файле

---

##### `_save_filtered_points(filtered_points: Dict[str, np.ndarray], time_group: h5.Group) -> None`
**Назначение:** Сохранение отфильтрованных точек

**Входные данные:**
- `filtered_points` (Dict[str, np.ndarray]): отфильтрованные данные точек
- `time_group` (h5.Group): группа для сохранения в выходном файле

---

##### `_save_sliding_windows(sliding_windows: List[Dict[str, float]], time_group: h5.Group) -> None`
**Назначение:** Сохранение данных скользящего окна

**Входные данные:**
- `sliding_windows` (List[Dict[str, float]]): данные сегментов скользящего окна
- `time_group` (h5.Group): группа для сохранения в выходном файле

---

##### `_save_boundary_data(boundary_data: Dict[str, List[float]], time_group: h5.Group) -> None`
**Назначение:** Сохранение данных границ

**Входные данные:**
- `boundary_data` (Dict[str, List[float]]): данные обнаруженных границ
- `time_group` (h5.Group): группа для сохранения в выходном файле

---

##### `_save_boundary_clusters(boundary_clusters: Optional[Dict[str, Any]], time_group: h5.Group) -> None`
**Назначение:** Сохранение кластеризованных границ

**Входные данные:**
- `boundary_clusters` (Optional[Dict[str, Any]]): данные кластеров границ
- `time_group` (h5.Group): группа для сохранения в выходном файле

---

### app/processors/simurg_hdf5_processor.py

#### Класс `SimurgHDF5Processor`

**Назначение:** Обработчик для HDF5-файлов от сервиса SIMuRG, содержащих данные из RINEX-файлов за сутки

**Конструктор:**
```python
__init__(file_path: str)
```

**Входные данные:**
- `file_path` (str): путь к HDF5 файлу

**Атрибуты:**
- `file_path` - путь к файлу
- `filename` - имя файла
- `lon_condition`, `lat_condition` - географические условия
- `stations_coords` - координаты станций
- `map_data` - данные карт
- `flybys` - данные пролетов

**Конфигурация:**
Используемые константы из config.py:
- `LON_CONDITION`, `LAT_CONDITION` - географические условия
- `COORDINATE_BOUNDS` - границы координат для фильтрации станций
- `TIME_DIFF_THRESHOLD_SECONDS` - порог времени для разделения пролетов
- `MAP_PATH`, `FLYBYS_PATH` - пути для сохранения файлов карт и пролетов
- `logger` - объект для логирования

**Используемые библиотеки:**
- `numpy` - для численных операций с массивами
- `h5py` - для работы с HDF5 файлами
- `os` - для работы с файловой системой
- `datetime` - для работы с датами и временем
- `collections.OrderedDict` - для создания упорядоченных словарей

---

#### Методы класса SimurgHDF5Processor

##### Контекстный менеджер
```python
__enter__() -> self
__exit__(exc_type, exc_value, traceback) -> None
```
**Назначение:** Обеспечение корректного открытия и закрытия HDF5 файла

---

##### `process(output_map_name: str) -> None`
**Назначение:** Основной метод обработки HDF5 файла от SIMuRG

**Входные данные:**
- `output_map_name` (str): имя выходного файла карт

**Результат:** Создает два HDF5 файла:
- Файл карт в `MAP_PATH`
- Файл пролетов в `FLYBYS_PATH`

**Процесс обработки:**
1. Извлечение координат станций
2. Обработка данных каждого спутника
3. Разделение на пролеты
4. Фильтрация данных
5. Сохранение в HDF5 формате

---

##### `restore_processed_data(flyby_file_path: str) -> None`
**Назначение:** Восстановление обработанных данных из HDF5 файла

**Входные данные:**
- `flyby_file_path` (str): путь к файлу с пролетами

**Результат:** Заполняет атрибуты `map_data` и `flybys` восстановленными данными

---

#### Приватные методы

##### `_extract_station_coordinates(station_name: str) -> None`
**Назначение:** Извлечение и сохранение координат станции

**Входные данные:**
- `station_name` (str): название станции

**Критерий фильтрации:** Координаты должны находиться в пределах COORDINATE_BOUNDS

---

##### `_split_satellite_data_into_flybys(station_name: str, satellite_name: str, roti: np.ndarray, timestamps: np.ndarray, latitudes: np.ndarray, longitudes: np.ndarray) -> None`
**Назначение:** Разделение данных спутника на отдельные пролеты

**Входные данные:**
- `station_name` (str): название станции
- `satellite_name` (str): название спутника
- `roti` (np.ndarray): массив значений ROTI
- `timestamps` (np.ndarray): массив временных меток
- `latitudes` (np.ndarray): массив широт
- `longitudes` (np.ndarray): массив долгот

**Критерий разделения:** Разрыв во времени ≥ TIME_DIFF_THRESHOLD_SECONDS

---

##### `_process_single_satellite(station_name: str, satellite_name: str) -> Optional[Dict[str, np.ndarray]]`
**Назначение:** Обработка данных одного спутника

**Входные данные:**
- `station_name` (str): название станции
- `satellite_name` (str): название спутника

**Результат:**
- `Optional[Dict]`: отфильтрованные данные спутника или None если данные невалидны

---

##### `_sort_dictionary_recursively(dictionary: Dict) -> OrderedDict`
**Назначение:** Рекурсивная сортировка словаря по ключам

**Входные данные:**
- `dictionary` (Dict): словарь для сортировки

**Результат:**
- `OrderedDict`: отсортированный словарь

---

##### `_create_output_files(map_file_path: str, flyby_file_path: str) -> None`
**Назначение:** Создание выходных HDF5 файлов с картами и пролетами

**Входные данные:**
- `map_file_path` (str): путь для файла карт
- `flyby_file_path` (str): путь для файла пролетов

---

##### `_write_map_data(map_file: h5.File) -> None`
**Назначение:** Запись данных карт в HDF5 файл

**Входные данные:**
- `map_file` (h5.File): открытый HDF5 файл для записи карт

**Структура файла:** `data/{timestamp}/lon,lat,vals`

---

##### `_write_flyby_data(flyby_file: h5.File) -> None`
**Назначение:** Запись данных пролетов в HDF5 файл

**Входные данные:**
- `flyby_file` (h5.File): открытый HDF5 файл для записи пролетов

**Структура файла:**
- `processed_data/{timestamp}/{station}/lon,lat,vals`
- `flybys/{station}/{satellite}/{flyby}/roti,timestamps,lat,lon`

---

### app/services/auroral_oval/boundary_detector.py

#### Класс `BoundaryDetector`

**Назначение:** Класс для обнаружения границ аврорального овала на основе интерполяции данных ROTI и извлечения контуров методом построения изолиний

**Конструктор:**
```python
__init__(lon_condition: float, lat_condition: float, boundary_condition: float)
```

**Входные данные:**
- `lon_condition` (float): максимальное значение долготы для анализа
- `lat_condition` (float): минимальное значение широты для анализа
- `boundary_condition` (float): пороговое значение ROTI для определения границы

**Атрибуты:**
- `lon_condition` - условие по долготе
- `lat_condition` - условие по широте
- `boundary_condition` - пороговое значение для границы

**Конфигурация:**
Используемые константы из config.py:
- `GRID_POINTS` - количество точек для создания сетки интерполяции

**Используемые библиотеки:**
- `numpy` - для численных операций и работы с массивами
- `matplotlib.pyplot` - для построения контуров (изолиний)
- `scipy.interpolate.griddata` - для интерполяции данных на регулярную сетку

---

#### Методы класса BoundaryDetector

##### `extract_boundary_contours(sliding_windows: List[Dict[str, float]]) -> Dict[str, List[float]]`
**Назначение:** Извлечение граничных контуров методом интерполяции данных и построения изолиний

**Входные данные:**
- `sliding_windows` (List[Dict[str, float]]): данные сегментов скользящего окна, содержащие:
  - `lon` - долгота центра сегмента
  - `lat` - широта центра сегмента
  - `vals` - значение ROTI в сегменте

**Результат:**
- `Dict[str, List[float]]`: словарь с координатами граничных точек:
  - `'lat'` - список широт граничных точек
  - `'lon'` - список долгот граничных точек

**Процесс обработки:**
1. **Извлечение данных**: преобразование данных скользящего окна в массивы numpy
2. **Создание сетки**: генерация равномерной сетки для интерполяции
3. **Интерполяция**: применение линейной интерполяции методом `griddata`
4. **Построение контуров**: создание изолиний для порогового значения `boundary_condition`
5. **Извлечение сегментов**: сбор всех сегментов контура в единый набор точек

**Особенности:**
- Возвращает пустой словарь при отсутствии валидных данных интерполяции
- Обрабатывает множественные сегменты контуров
- Автоматически закрывает фигуру matplotlib для избежания утечек памяти

---

### app/services/auroral_oval/cluster_processor.py

#### Класс `ClusterProcessor`

**Назначение:** Класс для обработки кластеров граничных точек аврорального овала с использованием алгоритма DBSCAN и определения пространственных отношений между кластерами

**Конструктор:**
```python
__init__(lat_condition: float)
```

**Входные данные:**
- `lat_condition` (float): условие по широте для фильтрации данных

**Атрибуты:**
- `lat_condition` - условие по широте

**Конфигурация:**
Используемые константы из config.py:
- `MIN_CLUSTER_SIZE` - минимальный размер кластера
- `DBSCAN_EPS` - параметр eps для алгоритма DBSCAN
- `DBSCAN_MIN_SAMPLES` - минимальное количество samples для DBSCAN
- `MAX_LATITUDE` - максимальное значение широты

**Используемые библиотеки:**
- `numpy` - для численных операций с массивами
- `sklearn.cluster.DBSCAN` - для кластеризации граничных точек
- `collections.Counter` - для подсчета точек в кластерах
- `copy.deepcopy` - для глубокого копирования объектов

---

#### Методы класса ClusterProcessor

##### `create_boundary_clusters(lat_list: List[float], lon_list: List[float], min_cluster_size: int = MIN_CLUSTER_SIZE) -> Optional[Dict[str, Any]]`
**Назначение:** Создание кластеров из граничных точек с использованием алгоритма DBSCAN

**Входные данные:**
- `lat_list` (List[float]): список широт граничных точек
- `lon_list` (List[float]): список долгот граничных точек
- `min_cluster_size` (int): минимальный размер кластера для валидации

**Результат:**
- `Optional[Dict[str, Any]]`: словарь с кластерами и их отношениями или None если кластеры не найдены

**Процесс обработки:**
1. **Подготовка данных**: объединение координат в массив для кластеризации
2. **DBSCAN кластеризация**: применение алгоритма с параметрами из конфигурации
3. **Фильтрация кластеров**: удаление шумовых точек и малых кластеров
4. **Сортировка кластеров**: упорядочивание по размеру (количеству точек)
5. **Определение отношений**: анализ пространственного расположения кластеров

---

##### `_extract_cluster_points(coordinates: np.ndarray, labels: np.ndarray, valid_labels: List[int]) -> Dict[str, List[List[float]]]`
**Назначение:** Извлечение точек для каждого валидного кластера

**Входные данные:**
- `coordinates` (np.ndarray): массив координат всех точек
- `labels` (np.ndarray): метки кластеров от DBSCAN
- `valid_labels` (List[int]): список валидных меток кластеров

**Результат:**
- `Dict[str, List[List[float]]]`: словарь с точками кластеров (ключи: border1, border2, ...)

---

##### `_process_single_cluster(cluster_dict: Dict[str, List[List[float]]], min_cluster_size: int) -> Optional[Dict[str, Any]]`
**Назначение:** Обработка случая с одним кластером

**Входные данные:**
- `cluster_dict` (Dict): словарь с одним кластером
- `min_cluster_size` (int): минимальный размер кластера

**Результат:**
- `Optional[Dict]`: обработанный кластер с добавленными граничными точками или None если невалидный

**Особенности обработки:**
- Добавление левой и правой граничных точек с координатой MAX_LATITUDE
- Удаление циклических точек для предотвращения замыкания контура
- Проверка минимального размера кластера

---

##### `_process_multiple_clusters(cluster_dict: Dict[str, List[List[float]]], sorted_clusters: List[int], min_cluster_size: int) -> Optional[Dict[str, Any]]`
**Назначение:** Обработка случая с несколькими кластерами

**Входные данные:**
- `cluster_dict` (Dict): словарь с кластерами
- `sorted_clusters` (List[int]): отсортированный список меток кластеров
- `min_cluster_size` (int): минимальный размер кластера

**Результат:**
- `Optional[Dict]`: обработанные кластеры с отношениями или None если невалидные

**Логика обработки:**
- Выбор двух крупнейших кластеров для анализа
- Определение пространственного отношения между кластерами
- Специальная обработка для отношения "top-bottom"

---

##### `_determine_cluster_relation(cluster1: np.ndarray, cluster2: np.ndarray) -> str`
**Назначение:** Определение пространственного отношения между двумя кластерами

**Входные данные:**
- `cluster1` (np.ndarray): точки первого кластера
- `cluster2` (np.ndarray): точки второго кластера

**Результат:**
- `str`: тип отношения - "left-right" или "top-bottom"

**Критерии определения:**
- Сравнение разницы по долготе и широте между центрами кластеров
- Большая разница по долготе → "left-right"
- Большая разница по широте → "top-bottom"

---

##### `_process_top_bottom_clusters(cluster1: np.ndarray, cluster2: np.ndarray, cluster_dict: Dict[str, List[List[float]]], sorted_clusters: List[int], top_clusters: List[int], min_cluster_size: int) -> Optional[Dict[str, Any]]`
**Назначение:** Специальная обработка кластеров с отношением "top-bottom"

**Входные данные:**
- `cluster1`, `cluster2` (np.ndarray): кластеры для обработки
- `cluster_dict` (Dict): исходный словарь кластеров
- `sorted_clusters` (List[int]): отсортированные метки
- `top_clusters` (List[int]): метки верхних кластеров
- `min_cluster_size` (int): минимальный размер кластера

**Процесс обработки:**
1. Определение верхнего и нижнего кластера по средним широтам
2. Добавление граничных точек через `_add_boundary_points`
3. Удаление циклических точек через `_remove_circular_points`
4. Проверка минимального размера

---

##### `_add_boundary_points(top_cluster: np.ndarray, bottom_cluster: np.ndarray, top_edge: float, bottom_edge: float) -> Tuple[np.ndarray, np.ndarray]`
**Назначение:** Добавление граничных точек к кластерам для формирования замкнутых контуров

**Входные данные:**
- `top_cluster`, `bottom_cluster` (np.ndarray): кластеры для расширения
- `top_edge` (float): верхняя граничная координата
- `bottom_edge` (float): нижняя граничная координата

**Результат:**
- `Tuple[np.ndarray, np.ndarray]`: кластеры с добавленными граничными точками

---

##### `_remove_circular_points(data: np.ndarray, condition: float) -> np.ndarray`
**Назначение:** Удаление циклических точек из данных для предотвращения замыкания контуров

**Входные данные:**
- `data` (np.ndarray): массив данных для фильтрации
- `condition` (float): условие для определения граничных точек

**Алгоритм фильтрации:**
- Анализ монотонности абсолютных значений долгот
- Сохранение точек до экстремума и граничных точек

---

### app/services/auroral_oval/crossing_detector.py

#### Класс `BoundaryCrossingDetector`

**Назначение:** Класс для обнаружения моментов пересечения спутниками границ аврорального овала

**Конструктор:**
```python
__init__(time_threshold_seconds: int = 10800)
```

**Входные данные:**
- `time_threshold_seconds` (int): временной порог для группировки пересечений в секундах (по умолчанию 10800)

**Атрибуты:**
- `time_threshold` - временной порог для группировки событий
- `polygon_plotter` - объект для работы с полигонами

**Конфигурация:**
Используемые константы из config.py:
- Не используются

**Используемые библиотеки:**
- `datetime` - для работы с датами и временем
- `shapely.geometry.Point` - для работы с геометрическими точками

---

#### Методы класса BoundaryCrossingDetector

##### `detect_satellite_crossings(boundaries: Dict[str, Any], satellites: Dict[str, Any]) -> Dict[str, Any]`
**Назначение:** Обнаружение моментов, когда спутники пересекают границы

**Входные данные:**
- `boundaries` (Dict): данные границ для каждой временной метки
- `satellites` (Dict): данные спутников с координатами для каждой временной метки

**Результат:**
- `Dict`: словарь с событиями пересечений для каждого спутника

**Алгоритм работы:**
1. Сортировка временных меток границ
2. Для каждой пары последовательных временных точек:
   - Вычисление полигонов границ
   - Проверка пересечений для каждого спутника
3. Сохранение событий "вошел" (entered) и "вышел" (exited)

---

##### `_check_satellite_crossings_for_time(crossings: Dict[str, Any], satellites: Dict[str, Any], current_time: str, next_time: str, boundary_current: Any, boundary_next: Any) -> None`
**Назначение:** Проверка пересечений для конкретного временного интервала

**Входные данные:**
- `crossings` (Dict): словарь для сохранения результатов
- `satellites` (Dict): данные спутников
- `current_time` (str): текущее время
- `next_time` (str): следующее время
- `boundary_current` (Any): граница текущего времени
- `boundary_next` (Any): граница следующего времени

**Логика определения событий:**
- `was_inside and not is_inside` → "exited" (вышел)
- `not was_inside and is_inside` → "entered" (вошел)

---

##### `_store_crossing_event(crossings: Dict[str, Any], satellite_id: str, event_time: str, event_type: str) -> None`
**Назначение:** Сохранение события пересечения в структуру результатов

**Входные данные:**
- `crossings` (Dict): словарь для сохранения результатов
- `satellite_id` (str): идентификатор спутника (формат: "station_satellite")
- `event_time` (str): время события
- `event_type` (str): тип события ("entered" или "exited")

**Структура хранения:**
```
{
    "station": {
        "satellite": [
            [{"time": "...", "event": "..."}, ...],  # группа событий 1
            [{"time": "...", "event": "..."}, ...]   # группа событий 2
        ]
    }
}
```

**Группировка событий:** События группируются по временному порогу (time_threshold)

---

### app/services/auroral_oval/sliding_window_processor.py

#### Класс `SlidingWindowProcessor`

**Назначение:** Класс для применения метода скользящего окна к пространственным данным ROTI с целью сегментации и агрегации значений

**Конструктор:**
```python
__init__(lon_step: float, lat_step: float)
```

**Входные данные:**
- `lon_step` (float): шаг перемещения окна по долготе в градусах
- `lat_step` (float): шаг перемещения окна по широте в градусах

**Атрибуты:**
- `lon_step` - шаг по долготе
- `lat_step` - шаг по широте

**Конфигурация:**
Используемые константы из config.py:
- Не используются

**Используемые библиотеки:**
- `numpy` - для численных операций с массивами

---

#### Методы класса SlidingWindowProcessor

##### `apply_sliding_window_segmentation(filtered_points: Dict[str, np.ndarray], window_size: Tuple[float, float] = (5, 10)) -> List[Dict[str, float]]`
**Назначение:** Применение метода скользящего окна для сегментации пространственных данных ROTI

**Входные данные:**
- `filtered_points` (Dict[str, np.ndarray]): отфильтрованные данные точек, содержащие:
  - `lon` - массив долгот
  - `lat` - массив широт
  - `vals` - массив значений ROTI
- `window_size` (Tuple[float, float]): размер окна в градусах (широта, долгота), по умолчанию (5, 10)

**Результат:**
- `List[Dict[str, float]]`: список сегментов данных, где каждый сегмент содержит:
  - `lon` - долгота центра окна
  - `lat` - широта центра окна
  - `vals` - медианное значение ROTI в окне

**Алгоритм работы:**
1. Определение географических границ данных
2. Последовательное перемещение окна с заданными шагами
3. Для каждого положения окна:
   - Создание маски точек, попадающих в окно
   - Вычисление медианного значения ROTI для точек в окне
   - Сохранение координат центра окна и медианного значения
4. Возврат всех непустых сегментов

---

##### `_create_window_mask(lon: np.ndarray, lat: np.ndarray, current_lon: float, current_lat: float, window_size: Tuple[float, float]) -> np.ndarray`
**Назначение:** Создание булевой маски для точек, попадающих в текущее окно

**Входные данные:**
- `lon` (np.ndarray): массив долгот всех точек
- `lat` (np.ndarray): массив широт всех точек
- `current_lon` (float): начальная долгота текущего окна
- `current_lat` (float): начальная широта текущего окна
- `window_size` (Tuple[float, float]): размер окна (широта, долгота)

**Результат:**
- `np.ndarray`: булев массив, где True отмечает точки внутри окна

**Критерии попадания:**
- Долгота: `current_lon ≤ lon < current_lon + window_size[1]`
- Широта: `current_lat ≤ lat < current_lat + window_size[0]`

---

##### `_create_window_data(values: np.ndarray, mask: np.ndarray, current_lon: float, current_lat: float, window_size: Tuple[float, float]) -> Dict[str, float]`
**Назначение:** Создание агрегированных данных для текущего окна

**Входные данные:**
- `values` (np.ndarray): массив значений ROTI
- `mask` (np.ndarray): булева маска точек в окне
- `current_lon` (float): начальная долгота окна
- `current_lat` (float): начальная широта окна
- `window_size` (Tuple[float, float]): размер окна

**Результат:**
- `Dict[str, float]`: словарь с агрегированными данными окна

**Агрегация:**
- Координаты центра окна вычисляются как середина диапазона
- Значение ROTI вычисляется как медиана значений точек в окне

---

### app/services/satellite/flyby_processor.py

#### Класс `SatelliteFlybyProcessor`

**Назначение:** Класс для обработки пролетов спутников и сохранения результатов в HDF5

**Конструктор:**
```python
__init__()
```

**Инициализирует компоненты:**
- `crossing_detector` - детектор пересечений границ
- `timeseries_plotter` - обработчик временных рядов для очистки событий

**Конфигурация:**
Используемые константы из config.py:
- `logger` - объект для логирования

**Используемые библиотеки:**
- `h5py` - для работы с HDF5 файлами
- `datetime` - для работы с датами и временем

---

#### Методы класса SatelliteFlybyProcessor

##### `process_flyby_data(boundary_clusters: Dict[str, Any], satellite_data: Dict[str, Any], flybys_data: Dict[str, Any], date_str: str, output_path: str) -> None`
**Назначение:** Обработка данных пролетов и сохранение результатов

**Входные данные:**
- `boundary_clusters` (Dict): кластеры границ
- `satellite_data` (Dict): данные спутников
- `flybys_data` (Dict): данные пролетов
- `date_str` (str): дата для обработки
- `output_path` (str): путь для сохранения результатов

**Процесс обработки:**
1. Обнаружение пересечений границ
2. Обработка пролетов для каждой станции и спутника
3. Сохранение данных в HDF5 файл

---

##### `_process_single_satellite_flybys(h5file: h5.File, station: str, satellite: str, flybys_data: Dict[str, Any], crossings: Dict[str, Any], date_str: str) -> None`
**Назначение:** Обработка пролетов для отдельного спутника

**Входные данные:**
- `h5file` (h5.File): открытый HDF5 файл для записи
- `station` (str): станция
- `satellite` (str): спутник
- `flybys_data` (Dict): данные пролетов
- `crossings` (Dict): данные пересечений
- `date_str` (str): дата для обработки

---

##### `_save_flyby_with_events(h5file: h5.File, station: str, satellite: str, flyby_index: int, flybys_data: Dict[str, Any], crossing_events: List[List[Dict]], flyby_key: str) -> None`
**Назначение:** Сохранение пролета с событиями пересечения

**Входные данные:**
- `h5file` (h5.File): открытый HDF5 файл для записи
- `station` (str): станция
- `satellite` (str): спутник
- `flyby_index` (int): индекс пролета
- `flybys_data` (Dict): данные пролетов
- `crossing_events` (List[List[Dict]]): события пересечений
- `flyby_key` (str): ключ пролета

**Структура сохранения в HDF5:**
- Группа: `{station}/{satellite}/flyby_{flyby_index}`
- Атрибуты: `times` (времена событий), `types` (типы событий)
- Датсеты: `roti`, `timestamps`, `lat`, `lon`

---

### app/services/satellite/satellite_data_processor.py

#### Класс `SatelliteDataProcessor`

**Назначение:** Класс для обработки данных отдельного спутника, включая вычисление координат и фильтрацию данных

**Конструктор:**
```python
__init__(station_coords: Dict[str, float])
```

**Входные данные:**
- `station_coords` (Dict[str, float]): координаты станции в формате {'lat': float, 'lon': float}

**Атрибуты:**
- `station_coords` - словарь с координатами станции

**Конфигурация:**
Используемые константы из config.py:
- `MIN_ELEVATION_DEGREES` - минимальный угол возвышения для фильтрации данных
- `MAP_TIME_STEP_SECONDS` - шаг времени для фильтрации временных меток
- `LON_CONDITION`, `LAT_CONDITION` - географические условия для фильтрации координат

**Используемые библиотеки:**
- `numpy` - для численных операций с массивами

---

#### Методы класса SatelliteDataProcessor

##### `calculate_satellite_coordinates(azimuths: np.ndarray, elevations: np.ndarray) -> Tuple[np.ndarray, np.ndarray]`
**Назначение:** Вычисление географических координат спутника на основе азимутов и углов возвышения

**Входные данные:**
- `azimuths` (np.ndarray): массив азимутов в радианах
- `elevations` (np.ndarray): массив углов возвышения в радианах

**Результат:**
- `Tuple[np.ndarray, np.ndarray]`: кортеж из массивов широт и долгот в градусах

**Алгоритм работы:**
1. Итерация по парам азимут-возвышение
2. Для каждой пары вызов функции `az_el_to_lat_lon` с координатами станции
3. Преобразование результатов из радиан в градусы
4. Возврат массивов широт и долгот

---

##### `apply_data_filters(roti: np.ndarray, elevations: np.ndarray, timestamps: np.ndarray, latitudes: np.ndarray, longitudes: np.ndarray) -> Dict[str, np.ndarray]`
**Назначение:** Применение фильтров к данным спутника для очистки и подготовки к дальнейшей обработке

**Входные данные:**
- `roti` (np.ndarray): массив значений ROTI
- `elevations` (np.ndarray): массив углов возвышения
- `timestamps` (np.ndarray): массив временных меток
- `latitudes` (np.ndarray): массив широт
- `longitudes` (np.ndarray): массив долгот

**Результат:**
- `Dict[str, np.ndarray]`: словарь с отфильтрованными данными:
  - `roti` - отфильтрованные значения ROTI
  - `timestamps` - отфильтрованные временные метки
  - `latitudes` - отфильтрованные широты
  - `longitudes` - отфильтрованные долготы

**Процесс фильтрации:**
1. **Фильтр по углу возвышения**: удаление точек с углом возвышения ниже `MIN_ELEVATION_DEGREES`
2. **Фильтр по координатам и времени**:
   - Долгота в диапазоне [-120, LON_CONDITION]
   - Широта ≥ LAT_CONDITION
   - Временные метки, кратные `MAP_TIME_STEP_SECONDS`

---

### app/services/satellite/trajectory_calculator.py

#### Класс `SatelliteTrajectory`

**Назначение:** Класс для расчета и обработки траекторий спутников с преобразованием азимута и угла возвышения в географические координаты

**Конструктор:**
```python
__init__(lat_site: float, lon_site: float)
```

**Входные данные:**
- `lat_site` (float): широта станции в градусах
- `lon_site` (float): долгота станции в градусах

**Атрибуты:**
- `station_latitude` - широта станции
- `station_longitude` - долгота станции
- `traj_lat` (np.ndarray) - массив широт траектории
- `traj_lon` (np.ndarray) - массив долгот траектории
- `timestamps` (np.ndarray) - массив временных меток

**Конфигурация:**
Используемые константы из config.py:
- `LON_CONDITION`, `LAT_CONDITION` - географические условия для фильтрации
- `ARTIFICIAL_POINTS_INTERVAL_MINUTES` - минимальный промежуток для вставки искусственных точек
- `ARTIFICIAL_POINTS_OFFSET_SECONDS` - смещение для искусственных точек вокруг середины промежутка

**Используемые библиотеки:**
- `numpy` - для численных операций с массивами
- `datetime` - для работы с датами и временем

---

#### Методы класса SatelliteTrajectory

##### `filter_coordinate_points() -> None`
**Назначение:** Фильтрация точек траектории по географическим условиям

**Критерии фильтрации:**
- Долгота в диапазоне [-120, LON_CONDITION]
- Широта ≥ LAT_CONDITION

**Процесс:**
- Создание маски валидных точек
- Применение маски к массивам координат и временных меток

---

##### `_find_large_time_gaps() -> np.ndarray`
**Назначение:** Поиск больших временных промежутков в данных траектории

**Результат:**
- `np.ndarray`: индексы, после которых находятся промежутки превышающие `ARTIFICIAL_POINTS_INTERVAL_MINUTES`

**Алгоритм:**
1. Преобразование временных меток в объекты datetime
2. Вычисление разниц между последовательными временными точками
3. Поиск промежутков, превышающих заданный порог

---

##### `_calculate_midpoint_timestamps(gap_indices: np.ndarray) -> List[float]`
**Назначение:** Вычисление временных меток для искусственных точек в середине больших промежутков

**Входные данные:**
- `gap_indices` (np.ndarray): индексы больших временных промежутков

**Результат:**
- `List[float]`: список временных меток для вставки искусственных точек

**Логика вставки:**
- Для каждого промежутка создается 3 точки:
  - В середине промежутка
  - За `ARTIFICIAL_POINTS_OFFSET_SECONDS` до середины
  - Через `ARTIFICIAL_POINTS_OFFSET_SECONDS` после середины

---

##### `insert_artificial_points(interval_minutes: int = ARTIFICIAL_POINTS_INTERVAL_MINUTES) -> None`
**Назначение:** Вставка искусственных точек в большие временные промежутки для обеспечения непрерывности траектории

**Входные данные:**
- `interval_minutes` (int): минимальный промежуток для вставки точек (в минутах)

**Процесс:**
1. Поиск больших промежутков через `_find_large_time_gaps()`
2. Расчет временных меток для вставки через `_calculate_midpoint_timestamps()`
3. Вставка точек с координатами NaN в массивы траектории

---

##### `calculate_satellite_coordinates(azimuths: np.ndarray, elevations: np.ndarray) -> Tuple[np.ndarray, np.ndarray]`
**Назначение:** Вычисление географических координат спутника на основе азимутов и углов возвышения

**Входные данные:**
- `azimuths` (np.ndarray): массив азимутов в радианах
- `elevations` (np.ndarray): массив углов возвышения в радианах

**Результат:**
- `Tuple[np.ndarray, np.ndarray]`: кортеж из массивов широт и долгот в градусах

**Алгоритм:**
- Итерация по парам азимут-возвышение
- Для каждой пары вызов функции `az_el_to_lat_lon`
- Преобразование результатов из радиан в градусы

---

##### `process(azimuths: np.ndarray, elevations: np.ndarray, timestamps: np.ndarray) -> None`
**Назначение:** Основной метод обработки траектории спутника

**Входные данные:**
- `azimuths` (np.ndarray): массив азимутов в радианах
- `elevations` (np.ndarray): массив углов возвышения в радианах
- `timestamps` (np.ndarray): массив временных меток

**Процесс обработки:**
1. Расчет координат спутника через `calculate_satellite_coordinates()`
2. Фильтрация точек по координатам через `filter_coordinate_points()`
3. Вставка искусственных точек через `insert_artificial_points()`
4. Проверка целостности данных через `_validate_data_integrity()`

---

##### `_validate_data_integrity() -> None`
**Назначение:** Проверка целостности данных траектории

**Проверки:**
- Совпадение размеров массивов широт, долгот и временных меток

**Исключения:**
- `AssertionError`: если размеры массивов не совпадают

---

##### `get_trajectory_data() -> Tuple[np.ndarray, np.ndarray, np.ndarray]`
**Назначение:** Получение полных данных траектории

**Результат:**
- `Tuple[np.ndarray, np.ndarray, np.ndarray]`: кортеж из массивов широт, долгот и временных меток

---

##### `get_trajectory_length() -> int`
**Назначение:** Получение количества точек в траектории

**Результат:**
- `int`: количество точек в траектории

---

### app/utils/az_el_to_lot_lon.py

#### Функция `az_el_to_lat_lon`

**Назначение:** Преобразование азимута и угла возвышения в географические координаты ионосферной точки

**Конфигурация:**
Используемые константы из config.py:
- `HM` - высота ионосферного максимума (км)
- `RE_KM` - радиус Земли (км)

**Используемые библиотеки**:
- `numpy` - для математических операций и работы с тригонометрическими функциями

**Сигнатура:**
```python
az_el_to_lat_lon(s_lat: float, s_lon: float, az: float, el: float, hm: float = HM, R: float = RE_KM) -> Tuple[float, float]
```

**Входные параметры:**
- `s_lat` (float): широта станции в радианах
- `s_lon` (float): долгота станции в радианах
- `az` (float): азимут в радианах
- `el` (float): угол возвышения в радианах
- `hm` (float): высота ионосферного максимума в километрах (по умолчанию HM)
- `R` (float): радиус Земли в километрах (по умолчанию RE_KM)

**Результат:**
- `Tuple[float, float]`: кортеж из широты и долготы ионосферной точки в радианах

**Математическая модель:**
1. **Расчет угла ψ (psi)**:
   ```
   ψ = π/2 - el - arcsin(cos(el) * R / (R + hm))
   ```
   Где ψ - центральный угол между станцией и ионосферной точкой

2. **Расчет широты ионосферной точки**:
   ```
   lat = arcsin(sin(s_lat) * cos(ψ) + cos(s_lat) * sin(ψ) * cos(az))
   ```

3. **Расчет долготы ионосферной точки**:
   ```
   lon = s_lon + arcsin(sin(ψ) * sin(az) / cos(lat))
   ```

4. **Нормализация долготы** в диапазон [-π, π]

**Особенности:**
- Использует сферическую модель Земли
- Предназначена для расчета координат точки пересечения луча "станция-спутник" с ионосферой
- Все углы работают в радианах
- Автоматически нормализует долготу в допустимый диапазон

---

### app/utils/time_utils.py

#### Функции

##### `generate_5min_timestamps(flyby_datetimes: List[dt]) -> List[str]`
**Назначение:** Генерация списка временных меток с шагом 5 минут

**Конфигурация:**
Используемые константы из config.py:
- Не используются

**Используемые библиотеки:**
- `datetime` - для работы с датами и временем
- `typing` - для аннотации типов (List)

**Входные данные:**
- `flyby_datetimes` (List[dt]): список меток времени

**Результат:**
- `List[str]`: список строк времени в формате "%Y-%m-%d %H:%M:%S.%f"

**Алгоритм работы:**
1. Определение диапазона времени от минимальной до максимальной метки
2. Округление начального времени до ближайшего кратного 5 минут (в большую сторону)
3. Генерация временных меток с шагом 5 минут до конца диапазона

**Особенности:**
- Все временные метки заканчиваются на :00 или :05
- Покрывает весь диапазон пролета спутников
- Используется для синхронизации данных с границами

---

### app/visualization/plotters/combined_plotter.py

#### Класс `CombinedPlotter`

**Назначение:** Класс для создания комбинированных визуализаций, объединяющих несколько графиков

**Конструктор:**
```python
__init__()
```

**Инициализирует компоненты:**
- `polygon_plotter` - построитель полигонов границ
- `map_plotter` - построитель карт ROTI
- `timeseries_plotter` - построитель временных рядов пролетов
- `satellite_plotter` - построитель траекторий спутников

**Конфигурация:**
Используемые константы из config.py:
- `FRAME_GRAPHS_PATH` - путь для сохранения графиков
- `COMMON_X_LIMITS` - общие пределы по оси X для карт
- `COMMON_Y_LIMITS` - общие пределы по оси Y для карт
- `logger` - объект для логирования

**Используемые библиотеки:**
- `os` - для работы с файловой системой и создания директорий
- `numpy` - для работы с массивами данных
- `h5py` - для чтения HDF5 файлов с данными ROTI
- `matplotlib.pyplot` - для создания графиков и визуализаций
- `matplotlib.gridspec` - для создания сложных компоновок графиков
- `typing` - для аннотации типов (Dict, List, Any, Optional)

---

#### Методы класса CombinedPlotter

##### `create_combined_visualization(map_points: Dict[str, Any], sliding_windows: Dict[str, Any], boundary_data: Dict[str, Any], boundary_condition: float, time_point: str, boundary_clusters: Dict[str, Any], roti_file: str, flyby_idx: str, flyby_roti: np.ndarray, flyby_times: List, flyby_events_times: List, flyby_events_types: List, station: str, satellite: str, save_to_file: bool = False) -> Optional[plt.Figure]`
**Назначение:** Создание комбинированной визуализации, объединяющей несколько графиков

**Входные данные:**
- `map_points` (Dict): данные карты ROTI
- `sliding_windows` (Dict): данные скользящего окна
- `boundary_data` (Dict): граничные данные
- `boundary_condition` (float): условие границы
- `time_point` (str): временная метка
- `boundary_clusters` (Dict): кластеры границ
- `roti_file` (str): путь к файлу ROTI
- `flyby_idx` (str): идентификатор пролета
- `flyby_roti` (np.ndarray): ROTI пролета
- `flyby_times` (List): времена пролета
- `flyby_events_times` (List): времена событий пролета
- `flyby_events_types` (List): типы событий пролета
- `station` (str): станция
- `satellite` (str): спутник
- `save_to_file` (bool): сохранять ли в файл

**Результат:**
- `Optional[plt.Figure]`: объект figure или None при ошибке

**Структура комбинированного графика:**
1. **Верхний левый** - карта ROTI
2. **Верхний правый** - скользящее окно с границами
3. **Нижний левый** - полигоны границ
4. **Нижний правый** - динамика пролета с событиями

---

##### `_adjust_subplot_sizes(fig: plt.Figure, map_ax: plt.Axes, polygon_ax: plt.Axes, dynamics_ax: plt.Axes) -> None`
**Назначение:** Корректировка размеров подграфиков для лучшего отображения

**Входные данные:**
- `fig` (plt.Figure): объект figure
- `map_ax` (plt.Axes): ось карты
- `polygon_ax` (plt.Axes): ось полигонов
- `dynamics_ax` (plt.Axes): ось динамики

---

##### `_save_plot_to_file(fig: plt.Figure, station: str, satellite: str, flyby_idx: str, time_point: str) -> None`
**Назначение:** Сохранение графика в файл

**Входные данные:**
- `fig` (plt.Figure): объект figure для сохранения
- `station` (str): станция
- `satellite` (str): спутник
- `flyby_idx` (str): идентификатор пролета
- `time_point` (str): временная метка

**Структура сохранения:**
- Путь: `FRAME_GRAPHS_PATH/{station}/{satellite}/{flyby_idx}/`
- Имя файла: `{time_point.replace(':', '_')}.png`

---

### app/visualization/plotters/map_plotter.py

#### Класс `MapPlotter`

**Назначение:** Класс для визуализации карт ROTI и данных скользящего окна

**Конструктор:**
```python
__init__()
```

**Атрибуты:**
- Нет атрибутов

**Конфигурация:**
Используемые константы из config.py:
- Не используются

#### Используемые библиотеки:
- `numpy` - для работы с массивами данных
- `matplotlib.pyplot` - для создания графиков и визуализаций
- `typing` - для аннотации типов (Dict, Tuple, Optional)

---

#### Методы класса MapPlotter

##### `create_roti_map_plot(roti_points: Dict[str, np.ndarray], time_point: str, ax: Optional[plt.Axes] = None, cmap: str = 'coolwarm') -> Tuple[plt.Figure, plt.Axes]`
**Назначение:** Создание карты ROTI на основе предоставленных точек

**Входные данные:**
- `roti_points` (Dict[str, np.ndarray]): словарь с данными точек, содержащий ключи:
  - `lon` - массив долгот
  - `lat` - массив широт  
  - `vals` - массив значений ROTI
- `time_point` (str): временная метка для заголовка
- `ax` (Optional[plt.Axes]): ось для отрисовки (опционально)
- `cmap` (str): цветовая карта (по умолчанию 'coolwarm')

**Результат:**
- `Tuple[plt.Figure, plt.Axes]`: объекты figure и axes

**Процесс визуализации:**
1. Создание scatter plot с цветами, соответствующими значениям ROTI
2. Нормализация значений ROTI в диапазоне [0, 0.1]
3. Извлечение данных из HDF5 массивов с помощью `[()]`
4. Добавление цветовой шкалы (colorbar)
5. Установка заголовка и меток осей
6. Отображение сетки

**Особенности:**
- Поддерживает как создание новой фигуры, так и использование существующей оси
- Автоматически показывает график при создании новой фигуры

---

##### `create_sliding_window_plot(sliding_windows: Dict[str, np.ndarray], boundary_data: Dict[str, np.ndarray], boundary_condition: float, ax: Optional[plt.Axes] = None, time_point: Optional[str] = None, cmap: str = 'coolwarm') -> Tuple[plt.Figure, plt.Axes]`
**Назначение:** Визуализация данных скользящего окна с граничными данными

**Входные данные:**
- `sliding_windows` (Dict[str, np.ndarray]): данные скользящего окна, содержащие:
  - `lon` - долготы сегментов
  - `lat` - широты сегментов
  - `vals` - значения ROTI в сегментах
- `boundary_data` (Dict[str, np.ndarray]): граничные точки, содержащие:
  - `lon` - долготы граничных точек
  - `lat` - широты граничных точек
- `boundary_condition` (float): пороговое значение для определения границы
- `ax` (Optional[plt.Axes]): ось для отрисовки (опционально)
- `time_point` (Optional[str]): временная метка для заголовка
- `cmap` (str): цветовая карта (по умолчанию 'coolwarm')

**Результат:**
- `Tuple[plt.Figure, plt.Axes]`: объекты figure и axes

**Процесс визуализации:**
1. Создание scatter plot для данных скользящего окна
2. Преобразование данных в numpy массивы
3. Добавление граничных точек серым цветом с легендой, если они присутствуют
4. Добавление цветовой шкалы (colorbar)
5. Установка заголовка и меток осей

**Особенности:**
- Проверяет наличие граничных данных перед их отображением
- Поддерживает гибкое использование как самостоятельного графика, так и части композитной визуализации

---

### app/visualization/plotters/polygon_plotter.py

#### Класс `PolygonPlotter`

**Назначение:** Класс для визуализации полигонов и кластеров границ аврорального овала, использует библиотеки matplotlib и shapely для работы с геометрией

**Конструктор:**
```python
__init__()
```

**Атрибуты:**
- Нет атрибутов

**Конфигурация:**
Используемые константы из config.py:
- `logger` - объект для логирования

**Используемые библиотеки:**
- `numpy` - для работы с массивами данных кластеров
- `matplotlib.pyplot` - для визуализации полигонов и графиков
- `shapely.geometry` - для работы с геометрическими объектами (Polygon, MultiPolygon)
- `typing` - для аннотации типов (Dict, List, Tuple, Optional, Any)

---

#### Методы класса PolygonPlotter

##### `plot_clusters(cluster_dict: Dict[str, np.ndarray], time_point: str) -> None`
**Назначение:** Визуализация кластеров границ в виде точечной диаграммы

**Входные данные:**
- `cluster_dict` (Dict[str, np.ndarray]): словарь с данными кластеров, где ключи - метки кластеров, значения - массивы координат
- `time_point` (str): временная метка для заголовка графика

**Процесс визуализации:**
1. Создание scatter plot для каждого кластера с уникальным цветом
2. Установка пределов осей: долгота (-120, -70), широта (40, 90)
3. Добавление легенды и заголовка
4. Отображение графика

---

##### `compute_polygons(boundary_clusters: Dict[str, Any], time_point: str) -> Tuple[Optional[List], Optional[Any], Optional[Any]]`
**Назначение:** Вычисление полигонов и их пересечений на основе кластеров границ

**Входные данные:**
- `boundary_clusters` (Dict[str, Any]): данные кластеров границ для разных временных точек
- `time_point` (str): временная метка для извлечения конкретных данных

**Результат:**
- `Tuple[Optional[List], Optional[Any], Optional[Any]]`: 
  - Список полигонов с цветами и метками
  - Объект пересечения полигонов
  - Одиночный полигон кластера (если применимо)

**Логика обработки:**
- **single-cluster**: создает один полигон из border1
- **left-right**: возвращает None (не обрабатывается)
- **top-bottom**: создает два полигона и вычисляет их пересечение

---

##### `plot_polygon(boundary_clusters: Dict[str, Any], time_point: str, ax: Optional[plt.Axes] = None) -> Tuple[plt.Figure, plt.Axes]`
**Назначение:** Визуализация полигонов границ на основе кластеров

**Входные данные:**
- `boundary_clusters` (Dict[str, Any]): данные кластеров границ
- `time_point` (str): временная метка
- `ax` (Optional[plt.Axes]): ось для отрисовки (опционально)

**Результат:**
- `Tuple[plt.Figure, plt.Axes]`: объекты figure и axes

**Процесс визуализации:**
1. Создание новой фигуры или использование существующей оси
2. Вычисление полигонов через `compute_polygons`
3. Отрисовка полигонов и их пересечений
4. Отображение "No Data" при отсутствии данных

---

#### Приватные методы

##### `_draw_polygons(ax: plt.Axes, polygons: List[Tuple], single_cluster_polygon: Any, intersection: Any) -> None`
**Назначение:** Отрисовка полигонов на графике

**Входные данные:**
- `ax` (plt.Axes): ось для отрисовки
- `polygons` (List[Tuple]): список кортежей (полигон, цвет, метка)
- `single_cluster_polygon` (Any): одиночный полигон кластера
- `intersection` (Any): область пересечения полигонов

**Процесс отрисовки:**
- Рисует контуры полигонов пунктирными линиями
- Заливает одиночные кластеры и пересечения фиолетовым цветом

---

##### `_fill_single_cluster(ax: plt.Axes, polygon: Any) -> None`
**Назначение:** Заливка одиночного полигона кластера

**Входные данные:**
- `ax` (plt.Axes): ось для отрисовки
- `polygon` (Any): полигон для заливки (может быть Polygon или MultiPolygon)

**Особенности:**
- Обрабатывает как простые полигоны, так и мультиполигоны
- Использует полупрозрачную фиолетовую заливку

---

##### `_fill_intersection(ax: plt.Axes, intersection: Any) -> None`
**Назначение:** Заливка области пересечения полигонов

**Входные данные:**
- `ax` (plt.Axes): ось для отрисовки
- `intersection` (Any): область пересечения (может быть Polygon или MultiPolygon)

**Особенности:**
- Обрабатывает как простые пересечения, так и множественные
- Использует полупрозрачную фиолетовую заливку

---

### app/visualization/plotters/satellite_plotter.py

#### Класс `SatellitePlotter`

**Назначение:** Класс для визуализации траекторий спутников на картах и графиках

**Конструктор:**
```python
__init__()
```

**Атрибуты:**
- `trajectory_elements` (List[Tuple]): список элементов траектории (линии и точки) для последующего удаления

**Конфигурация:**
Используемые константы из config.py:
- Не используются

**Используемые библиотеки:**
- `numpy` - для численных операций и работы с массивами
- `matplotlib.pyplot` - для визуализации траекторий и графиков
- `datetime` - для работы с временными метками и преобразования дат
- `typing` - для аннотации типов (List)

---

#### Методы класса SatellitePlotter

##### `remove_trajectory_lines() -> None`
**Назначение:** Удаление всех ранее нарисованных линий траекторий с графиков

**Процесс работы:**
1. Итерация по всем элементам в `trajectory_elements`
2. Удаление линий и точек с графиков
3. Очистка списка `trajectory_elements`

**Использование:**
- Вызывается перед отрисовкой новых траекторий для очистки предыдущих
- Обеспечивает чистоту визуализации при обновлении данных

---

##### `add_satellite_trajectory(station_lat: float, station_lon: float, satellite_azimuths: np.ndarray, satellite_elevations: np.ndarray, satellite_times: np.ndarray, time_point: str, ax_list: List[plt.Axes]) -> None`
**Назначение:** Добавление траектории спутника на несколько графиков

**Входные данные:**
- `station_lat` (float): географическая широта наземной станции
- `station_lon` (float): географическая долгота наземной станции
- `satellite_azimuths` (np.ndarray): массив азимутальных углов спутника
- `satellite_elevations` (np.ndarray): массив углов возвышения спутника
- `satellite_times` (np.ndarray): массив временных меток спутника
- `time_point` (str): временная точка для выделения позиции спутника
- `ax_list` (List[plt.Axes]): список осей для отрисовки траектории

**Процесс работы:**
1. Создание объекта `SatelliteTrajectory` с координатами станции
2. Расчет траектории спутника на основе азимутов и углов возвышения
3. Отрисовка траектории и позиции спутника на всех осях из списка
4. Сохранение элементов для последующего удаления

---

#### Приватные методы

##### `_add_trajectory_to_axis(ax: plt.Axes, trajectory: SatelliteTrajectory, time_point: str, color: str) -> None`
**Назначение:** Добавление траектории на конкретную ось графика

**Входные данные:**
- `ax` (plt.Axes): ось для отрисовки
- `trajectory` (SatelliteTrajectory): объект с рассчитанной траекторией
- `time_point` (str): временная точка для выделения позиции
- `color` (str): цвет траектории

**Процесс работы:**
1. **Фильтрация легенды**: удаление дублирующихся элементов легенды
2. **Поиск позиции спутника**: определение ближайшей к `time_point` позиции спутника
3. **Отрисовка точки**: создание зеленой точки в позиции спутника в заданное время
4. **Отрисовка траектории**: создание линии траектории черного цвета
5. **Обновление легенды**: добавление элементов "Time Point" и "Trajectory" в легенду

**Особенности:**
- Поддерживает два формата временных меток
- Автоматически обрабатывает ошибки при отрисовке точек
- Сохраняет элементы для управления видимостью

---

### app/visualization/plotters/timeseries_plotter.py

#### Класс `TimeSeriesPlotter`

**Назначение:** Класс для визуализации временных рядов и пролетов спутников с обработкой событий пересечения границ

**Конструктор:**
```python
__init__()
```

**Атрибуты:**
- `color_mappings` (Dict[str, str]): словарь сопоставления типов событий с цветами:
  - `"entered"` - зеленый (вход в авроральный овал)
  - `"exited"` - красный (выход из аврорального овала)
  - `"noise"` - желтый (шумовые события)

**Конфигурация:**
Используемые константы из config.py:
- `TIME_GAP_LIMIT` - временной лимит для фильтрации событий пролета
- `logger` - объект для логирования

**Используемые библиотеки:**
- `numpy` - для работы с массивами данных ROTI
- `matplotlib.pyplot` - для построения графиков временных рядов
- `matplotlib.dates` - для форматирования временных осей
- `matplotlib.ticker` - для настройки форматирования осей значений
- `matplotlib.patches` - для создания элементов легенды (Patch)
- `datetime` - для работы с временными метками и преобразования дат
- `typing` - для аннотации типов (List, Tuple, Optional, Dict, Any)

---

#### Методы класса TimeSeriesPlotter

##### `create_roti_dynamics_plot(station_data: Dict[str, Any], satellite: str, time_point: Optional[str] = None, ax: Optional[plt.Axes] = None) -> Tuple[plt.Figure, plt.Axes]`
**Назначение:** Визуализация динамики ROTI для пары станция-спутник

**Входные данные:**
- `station_data` (Dict[str, Any]): данные станции, содержащие информацию о спутниках
- `satellite` (str): идентификатор спутника
- `time_point` (Optional[str]): временная точка для выделения на графике
- `ax` (Optional[plt.Axes]): ось для отрисовки (опционально)

**Результат:**
- `Tuple[plt.Figure, plt.Axes]`: объекты figure и axes

**Процесс визуализации:**
1. Извлечение данных ROTI и временных меток из HDF5 структур
2. Преобразование временных меток в объекты datetime
3. Создание scatter plot динамики ROTI
4. Установка временных пределов на текущий день
5. Настройка осей времени и значений
6. Выделение временной точки при наличии

---

##### `create_flyby_plot(roti: np.ndarray, times: List[dt], station: str, satellite: str, cleaned_times: List[dt], cleaned_types: List[str], time_point: Optional[str] = None, ax: Optional[plt.Axes] = None) -> Tuple[plt.Figure, plt.Axes]`
**Назначение:** Визуализация пролета спутника с событиями пересечения границ

**Входные данные:**
- `roti` (np.ndarray): значения ROTI во время пролета
- `times` (List[dt]): временные метки пролета
- `station` (str): идентификатор станции
- `satellite` (str): идентификатор спутника
- `cleaned_times` (List[dt]): очищенные времена событий пересечения
- `cleaned_types` (List[str]): типы событий пересечения
- `time_point` (Optional[str]): временная точка для выделения
- `ax` (Optional[plt.Axes]): ось для отрисовки (опционально)

**Результат:**
- `Tuple[plt.Figure, plt.Axes]`: объекты figure и axes

**Процесс визуализации:**
1. Создание scatter plot значений ROTI
2. Установка временных пределов на диапазон пролета
3. Настройка осей времени и значений
4. Добавление подсветки событий пересечения
5. Выделение временной точки при наличии
6. Добавление легенды для событий

---

##### `clean_events(event_times: List[dt], event_types: List[str]) -> Tuple[List[dt], List[str]]`
**Назначение:** Очистка и фильтрация событий пролета от шума и дубликатов

**Входные данные:**
- `event_times` (List[dt]): исходные времена событий
- `event_types` (List[str]): исходные типы событий

**Результат:**
- `Tuple[List[dt], List[str]]`: очищенные времена и типы событий

**Алгоритм очистки:**
1. **Удаление дубликатов**: удаление последовательных событий одного типа
2. **Фильтрация по времени**: группировка событий в пределах `TIME_GAP_LIMIT`
3. **Стабилизация последовательностей**: поиск устойчивых паттернов событий
4. **Финальная фильтрация**: удаление изолированных событий

---

#### Приватные методы

##### `_configure_time_axis(ax: plt.Axes) -> None`
**Назначение:** Настройка временной оси для оптимального отображения

**Входные данные:**
- `ax` (plt.Axes): ось для настройки

**Конфигурация:**
- Основные деления каждый час
- Формат времени ЧЧ:ММ
- Поворот меток на 45 градусов

---

##### `_configure_value_axis(ax: plt.Axes, values: np.ndarray) -> None`
**Назначение:** Настройка оси значений ROTI

**Входные данные:**
- `ax` (plt.Axes): ось для настройки
- `values` (np.ndarray): значения ROTI для определения диапазона

**Конфигурация:**
- Форматирование значений с тремя знаками после запятой
- Установка пределов оси Y с округлением до ближайших 0.5
- Основная сетка с шагом 0.5, дополнительная с шагом 0.1

---

##### `_highlight_time_point(ax: plt.Axes, time_point: str) -> None`
**Назначение:** Выделение временной точки на графике

**Входные данные:**
- `ax` (plt.Axes): ось для отрисовки
- `time_point` (str): временная точка в формате "%Y-%m-%d %H:%M:%S.%f" или "%Y-%m-%d %H:%M:%S"

**Особенности:**
- Поддерживает два формата временных меток
- Создает полупрозрачную серую область шириной 5 минут

---

##### `_add_event_highlights(ax: plt.Axes, times: List[dt], cleaned_times: List[dt], cleaned_types: List[str]) -> None`
**Назначение:** Добавление подсветки событий пересечения на график

**Входные данные:**
- `ax` (plt.Axes): ось для отрисовки
- `times` (List[dt]): все временные метки пролета
- `cleaned_times` (List[dt]): очищенные времена событий
- `cleaned_types` (List[str]): типы событий

**Логика подсветки:**
- Создает цветные области между событиями
- Использует цвета из `color_mappings`
- Растягивает последнюю область до конца пролета

---

##### `_add_flyby_legend(ax: plt.Axes) -> None`
**Назначение:** Добавление легенды для событий пролета

**Входные данные:**
- `ax` (plt.Axes): ось для отрисовки

**Элементы легенды:**
- Красный: внутри аврорального овала
- Зеленый: вне аврорального овала

---

### app/visualization/png_to_video_converter.py

#### Класс `PngToVideoConverter`

**Назначение:** Класс для преобразования последовательностей PNG изображений в видеофайлы с возможностью очистки исходных файлов

**Конструктор:**
```python
__init__(input_dir: str, output_dir: str, fps: int = 16, remove_png_after_convert: bool = True)
```

**Входные данные:**
- `input_dir` (str): путь к корневой директории, содержащей PNG файлы
- `output_dir` (str): путь к директории для сохранения видеофайлов
- `fps` (int): количество кадров в секунду для генерируемого видео (по умолчанию 16)
- `remove_png_after_convert` (bool): флаг удаления PNG файлов после успешной конвертации (по умолчанию True)

**Конфигурация:**
Используемые константы из config.py:
- `logger` - объект для логирования

#### Используемые библиотеки:
- `os` - для работы с файловой системой и обхода директорий
- `imageio` - для создания видео из последовательности изображений
- `traceback` - для форматирования и логирования исключений
- `shutil` - для рекурсивного удаления директорий с PNG файлами

---

#### Методы класса PngToVideoConverter

##### `find_all_png_folders() -> List[str]`
**Назначение:** Рекурсивный поиск всех директорий, содержащих PNG файлы

**Результат:**
- `List[str]`: список путей к директориям, содержащим PNG изображения

**Алгоритм поиска:**
- Рекурсивный обход директории `input_dir`
- Проверка наличия файлов с расширением `.png` в каждой поддиректории

---

##### `create_video_from_images(image_files: List[str], output_path: str) -> bool`
**Назначение:** Создание видеофайла из списка изображений

**Входные данные:**
- `image_files` (List[str]): список путей к PNG изображениям для компиляции в видео
- `output_path` (str): путь для сохранения сгенерированного видеофайла

**Результат:**
- `bool`: True если видео успешно создано, False в случае ошибки

**Процесс создания видео:**
1. Создание целевой директории (если не существует)
2. Инициализация видео-писателя с кодеком libx264
3. Последовательное чтение и добавление изображений в видео
4. Обработка ошибок чтения отдельных файлов
5. Логирование результата операции

---

##### `remove_png_folder(folder_path: str) -> bool`
**Назначение:** Удаление директории с PNG файлами после успешной конвертации

**Входные данные:**
- `folder_path` (str): путь к директории для удаления

**Результат:**
- `bool`: True если директория успешно удалена, False в случае ошибки

**Особенности:**
- Рекурсивное удаление всей директории с содержимым
- Проверка существования директории перед удалением
- Логирование предупреждений и ошибок

---

##### `remove_empty_parent_folders(folder_path: str) -> None`
**Назначение:** Рекурсивное удаление пустых родительских директорий до корневой директории ввода

**Входные данные:**
- `folder_path` (str): путь к директории, с которой начинать проверку

**Алгоритм:**
1. Начало с переданной директории
2. Рекурсивная проверка родительских директорий до `input_dir`
3. Удаление только пустых директорий
4. Прекращение при обнаружении непустой директории

---

##### `process_images_to_video() -> None`
**Назначение:** Основной метод обработки - поиск PNG директорий и создание видео для каждой

**Процесс обработки:**
1. Поиск всех директорий с PNG файлами через `find_all_png_folders()`
2. Для каждой директории:
   - Сбор всех PNG файлов
   - Пропуск директорий без структуры поддиректорий
   - Формирование пути для выходного видео на основе структуры исходных директорий
   - Создание видео через `create_video_from_images()`
   - Удаление исходных PNG файлов при успешной конвертации (если `remove_png_after_convert=True`)
   - Очистка пустых родительских директорий

**Структура именования видео:**
- Видео сохраняется в поддиректории, соответствующей первой части пути
- Имя видео формируется из оставшихся частей пути, объединенных через "_"

---