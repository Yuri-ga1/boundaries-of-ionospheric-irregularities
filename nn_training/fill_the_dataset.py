from datetime import timedelta, datetime as dt
import datetime
import numpy as np
import h5py
import os


import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

from calc_dataset_data import *

def plot_roti_and_spectrum(roti, spectrum, station='', satellite='', fb=''):
    """
    Строит один график: ROTI и спектр (реальная и мнимая части), сохраняет в папку graphs.

    roti: np.ndarray — сигнал ROTI
    timestamps: np.ndarray — UNIX-время (UTC)
    spectrum: np.ndarray — спектр (np.fft.fft(roti)), используется напрямую
    """
    # Убедимся, что папка существует
    os.makedirs("graphs", exist_ok=True)

    # Индексы спектра
    spectrum_indices = np.arange(len(spectrum))

    fig, ax1 = plt.subplots(figsize=(12, 5))

    # Первая ось — ROTI
    ax1.plot(spectrum_indices, roti, color='blue', label='ROTI')
    ax1.set_xlabel('Время от начала, часы')
    ax1.set_ylabel('ROTI', color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')
    ax1.grid(True)

    # Вторая ось — спектр
    ax2 = ax1.twinx()
    ax2.plot(spectrum_indices, spectrum.real, color='red', label='Real spectrum', alpha=0.6)
    ax2.plot(spectrum_indices, spectrum.imag, color='green', label='Imag spectrum', alpha=0.6)
    ax2.set_ylabel('Спектр', color='red')
    ax2.tick_params(axis='y', labelcolor='red')

    # Заголовок и легенда
    plt.title(f'ROTI и спектр (станция: {station}, спутник: {satellite}, fb: {fb})')
    fig.tight_layout()
    fig.legend(loc='upper right', bbox_to_anchor=(1, 1), bbox_transform=ax1.transAxes)

    # Сохранение
    filename = f"{station}_{satellite}_{fb}.png"
    save_path = os.path.join("specrtum_ROTI", filename)
    plt.savefig(save_path)
    plt.close(fig)

def create_h5_dataset(
        out_dataset_path, group_path,
        roti, amplitude, spectrum, gradient,
        timestamps, times, types,
        sin_time, cos_time,
        symh,
        mlat, mlon
    ):
    logger.info(f'Creating new entry: {group_path}')
    try:
        with h5py.File(out_dataset_path, 'a') as h5file:
            if group_path not in h5file:
                group = h5file.create_group(group_path)
                # Сохраняем атрибуты
                group.create_dataset('timestamps', data=timestamps)
                group.attrs['times'] = times
                group.attrs['types'] = types
                
                group.create_dataset('roti', data=roti)
                group.create_dataset('roti_amplitude', data=amplitude)
                group.create_dataset('roti_spectrum', data=spectrum)
                group.create_dataset('roti_gradient', data=gradient)

                group.create_dataset('sin_time', data=sin_time)
                group.create_dataset('cos_time', data=cos_time)

                group.create_dataset('symh', data=symh)
                group.create_dataset('mlat', data=mlat)
                group.create_dataset('mlon', data=mlon)
            else:
                logger.warning(f"group_path is already exist: {group_path}")
                    
    except Exception as e:
        logger.error(f"Ошибка при записи в HDF5 файл: {group_path}")



h5_file_path = os.path.join("video", '2019-05-14', f"2019-05-14.h5")
dataset_path = os.path.join('dataset_v1.h5')
out_dataset_path = os.path.join('dataset_cor_fb.h5')

with h5py.File(dataset_path, 'r') as metah5file:
    for group in metah5file:
        logger.info(f'Process {group}')
        date, station, satellite, fb, fb_num = group.split('_')
        new_group_name = f'{date}_{station}_{satellite}_{fb}-{fb_num}'
        fb +=f"_{fb_num}"
        
        roti, timestamps, lon, lat, event_times, event_types = get_metadata_from_h5(h5_file_path, station, satellite, fb)
        amplitude, spectrum, gradient = calc_roti_amplitude_spectrum_gradient(roti)
        sin_time, cos_time = calc_sin_and_cos_time(timestamps, lon)

        unix_times = [dt.fromisoformat(s).timestamp() for s in event_times]

        symh = calc_symh(date, timestamps)
        mlat, mlon = calc_mlat_mlon(lat, lon)
        
        create_h5_dataset(
            out_dataset_path=out_dataset_path,
            group_path=new_group_name,
            roti=roti,
            amplitude=amplitude,
            spectrum=spectrum,
            gradient=gradient,
            timestamps=timestamps,
            times=unix_times,
            types=event_types,
            sin_time=sin_time,
            cos_time=cos_time,
            symh=symh,
            mlat=mlat,
            mlon=mlon,
        )