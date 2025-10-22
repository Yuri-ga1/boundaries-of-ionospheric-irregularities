import numpy as np

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
from matplotlib.patches import Patch

from datetime import datetime as dt
from datetime import timedelta
import datetime

from typing import List, Tuple, Optional, Dict, Any
from config import TIME_GAP_LIMIT, logger


class TimeSeriesPlotter:
    """Класс для визуализации временных рядов и пролетов спутников."""
    
    def __init__(self):
        self.color_mappings = {
            "entered": "green",
            "exited": "red", 
            "noise": "yellow"
        }
    
    def create_roti_dynamics_plot(
        self,
        station_data: Dict[str, Any],
        satellite: str,
        time_point: Optional[str] = None,
        ax: Optional[plt.Axes] = None
    ) -> Tuple[plt.Figure, plt.Axes]:
        """
        Визуализация динамики ROTI для пары станция-спутник.
        
        Args:
            station_data: Данные станции
            satellite: Идентификатор спутника
            time_point: Временная точка для выделения
            ax: Ось для отрисовки (опционально)
            
        Returns:
            Tuple: Объекты figure и axes
        """
        created_fig = False
        if ax is None:
            fig, ax = plt.subplots()
            created_fig = True
        else:
            fig = ax.figure

        roti = station_data[satellite]['roti'][:]
        timestamps = station_data[satellite]['timestamp'][:]
        times = [dt.fromtimestamp(float(t), datetime.UTC) for t in timestamps]

        ax.scatter(times, roti)

        day_start = dt.combine(times[0].date(), dt.min.time())
        day_end = dt.combine(times[0].date(), dt.max.time())
        ax.set_xlim(day_start, day_end)

        self._configure_time_axis(ax)
        self._configure_value_axis(ax, roti)

        ax.set_xlabel("Time")
        ax.set_ylabel("ROTI")

        if time_point is not None:
            self._highlight_time_point(ax, time_point)

        if created_fig:
            ax.set_title(f"ROTI Dynamics for {satellite}")
            plt.show()
        else:
            ax.set_title(f"ROTI Dynamics")
            return fig, ax
    
    def create_flyby_plot(
        self,
        roti: np.ndarray,
        times: List[dt],
        station: str,
        satellite: str,
        cleaned_times: List[dt],
        cleaned_types: List[str],
        time_point: Optional[str] = None,
        ax: Optional[plt.Axes] = None
    ) -> Tuple[plt.Figure, plt.Axes]:
        """
        Визуализация пролета спутника с событиями.
        
        Args:
            roti: Значения ROTI
            times: Временные метки
            station: Идентификатор станции
            satellite: Идентификатор спутника
            cleaned_times: Очищенные времена событий
            cleaned_types: Типы событий
            time_point: Временная точка для выделения
            ax: Ось для отрисовки (опционально)
            
        Returns:
            Tuple: Объекты figure и axes
        """
        created_fig = False
        if ax is None:
            fig, ax = plt.subplots()
            created_fig = True
        else:
            fig = ax.figure

        ax.scatter(times, roti)

        ax.set_xlim(min(times), max(times))
        self._configure_time_axis(ax)
        self._configure_value_axis(ax, roti)

        ax.set_xlabel("Time")
        ax.set_ylabel("ROTI")

        self._add_event_highlights(ax, times, cleaned_times, cleaned_types)
        
        if time_point is not None:
            self._highlight_time_point(ax, time_point)

        self._add_flyby_legend(ax)
        ax.set_title(f"Flyby for {station}_{satellite}")
        
        if created_fig:
            plt.show()
        return fig, ax
    
    def _configure_time_axis(self, ax: plt.Axes) -> None:
        """
        Настройка временной оси.
        
        Args:
            ax: Ось для настройки
        """
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        ax.tick_params(axis='x', rotation=45)
    
    def _configure_value_axis(self, ax: plt.Axes, values: np.ndarray) -> None:
        """
        Настройка оси значений.
        
        Args:
            ax: Ось для настройки
            values: Значения для определения диапазона
        """
        ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.3f'))
        y_max = max(values)
        y_lim = ((y_max // 0.5) + 1) * 0.5
        ax.set_ylim(0, y_lim)
        
        ax.yaxis.set_major_locator(ticker.MultipleLocator(0.5))
        ax.yaxis.set_minor_locator(ticker.MultipleLocator(0.1))
        ax.grid(True, which='major', linewidth=1, linestyle='-', alpha=0.7)
        ax.grid(True, which='minor', linestyle='--', alpha=0.4)
    
    def _highlight_time_point(self, ax: plt.Axes, time_point: str) -> None:
        """
        Выделение временной точки на графике.
        
        Args:
            ax: Ось для отрисовки
            time_point: Временная точка
        """
        try:
            time_dt = dt.strptime(time_point, "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=datetime.UTC)
        except ValueError:
            time_dt = dt.strptime(time_point, "%Y-%m-%d %H:%M:%S").replace(tzinfo=datetime.UTC)
            
        ax.axvspan(time_dt, time_dt + timedelta(minutes=5), color='red', alpha=0.3, label="Time Point")
    
    def _add_event_highlights(
        self, 
        ax: plt.Axes, 
        times: List[dt], 
        cleaned_times: List[dt], 
        cleaned_types: List[str]
    ) -> None:
        """
        Добавление подсветки событий на график.
        
        Args:
            ax: Ось для отрисовки
            times: Все временные метки
            cleaned_times: Времена событий
            cleaned_types: Типы событий
        """
        last_time = times[0].strftime("%Y-%m-%d %H:%M:%S.%f")
        for i in range(len(cleaned_times)):
            current_time = cleaned_times[i]
            current_event = cleaned_types[i]

            color = self.color_mappings.get(current_event, "gray")
            ax.axvspan(last_time, current_time, color=color, alpha=0.3)
            last_time = current_time

        final_color = self.color_mappings.get(cleaned_types[-1], "gray")
        ax.axvspan(last_time, times[-1], color=final_color, alpha=0.3)
    
    def _add_flyby_legend(self, ax: plt.Axes) -> None:
        """
        Добавление легенды для пролета.
        
        Args:
            ax: Ось для отрисовки
        """
        legend_elements = [
            Patch(facecolor='red', alpha=0.3, label='Inside'),
            Patch(facecolor='green', alpha=0.3, label='Outside')
        ]
        ax.legend(handles=legend_elements, loc='upper right')
    
    def clean_events(self, event_times: List[dt], event_types: List[str]) -> Tuple[List[dt], List[str]]:
        """
        Очистка и фильтрация событий пролета.
        
        Args:
            event_times: Времена событий
            event_types: Типы событий
            
        Returns:
            Tuple: Очищенные времена и типы событий
        """
        # Удаление дубликатов
        dedup_times = []
        dedup_types = []
        for idx, (t, e) in enumerate(zip(event_times, event_types)):
            if idx == 0 or e != event_types[idx - 1]:
                dedup_times.append(t)
                dedup_types.append(e)
                
        i = 0
        cleaned_times = []
        cleaned_types = []

        while i < len(dedup_times):
            current_time = dedup_times[i]
            current_type = dedup_types[i]

            j = i + 1
            future = []
            while j < len(dedup_times) and dedup_times[j] <= current_time + timedelta(minutes=TIME_GAP_LIMIT):
                future.append((dedup_times[j], dedup_types[j]))
                j += 1

            if len(future) == 1:
                cleaned_times.append(future[0][0])
                cleaned_types.append(current_type)
                i = j
            elif len(future) >= 2:
                k = j-1
                look_time = dedup_times[k]

                while k < len(dedup_times):
                    m = k + 1
                    count = 0

                    while m < len(dedup_times) and dedup_times[m] <= look_time + timedelta(minutes=TIME_GAP_LIMIT):
                        count += 1
                        m += 1

                    if count >= 2:
                        look_time = dedup_times[m - 1]
                        k = m
                        i = m
                        if m >= len(dedup_times):
                            cleaned_times.append(dedup_times[m - 1])
                            cleaned_types.append(dedup_types[m - 1])
                    else:
                        cleaned_times.append(dedup_times[m - 1])
                        cleaned_types.append(dedup_types[m - 1])
                        i = m
                        break
                
            else:
                cleaned_times.append(current_time)
                cleaned_types.append(current_type)
                i += 1
            
        final_times = []
        final_types = []
        for idx, (t, e) in enumerate(zip(cleaned_times, cleaned_types)):
            if idx == len(cleaned_times) - 1 or e != cleaned_types[idx + 1]:
                final_times.append(t)
                final_types.append(e)

        return final_times, final_types