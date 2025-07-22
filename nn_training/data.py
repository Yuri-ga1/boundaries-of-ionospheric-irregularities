import h5py
import os

def print_h5_contents(file_path):
    """Выводит содержимое HDF5 файла."""
    try:
        with h5py.File(file_path, 'r') as h5file:
            def print_group_contents(group, indent=0):
                """Рекурсивно выводит содержимое группы."""
                # Выводим имя группы
                print("  " * indent + f"Группа-: {group.name}")

                # Выводим атрибуты группы
                # if group.attrs:
                #     print("  " * (indent + 1) + "Атрибуты:")
                #     for key, value in group.attrs.items():
                #         print(f"  " * (indent + 2) + f"{key}: {value}")

                # Выводим датасеты в группе
                for name, item in group.items():
                    if isinstance(item, h5py.Group):
                        # Если элемент — это группа, рекурсивно вызываем функцию для этой группы
                        print_group_contents(item, indent + 1)
                    # elif isinstance(item, h5py.Dataset):
                        # print("  " * (indent + 1) + f"Датасет: {name}")
                        # print("  " * (indent + 2) + f"Тип данных: {item.dtype}")
                        # print("  " * (indent + 2) + f"Размер: {item.shape}")
                        # print("  " * (indent + 2) + "Содержимое:")
                        # print(item[:])

            # Рекурсивно выводим все группы и их содержимое
            print_group_contents(h5file)

    except Exception as e:
        print(f"Ошибка при чтении HDF5 файла: {e}")

def delete_groups_from_h5(file_path, filenames):
    """Удаляет указанные группы из HDF5-файла."""
    groups_to_delete_final = [f'2019-05-14_{group}' for group in filenames]
    try:
        with h5py.File(file_path, 'a') as h5file:
            for group_path, filename in zip(groups_to_delete_final, filenames):
                try:
                    if group_path in h5file:
                        del h5file[group_path]
                        print(f"[DEL] Удалена группа: {group_path}")
                        delete_file_by_name(directory='accepted', filename=f'{filename}.mp4')
                    else:
                        print(f"[WARN] Группа не найдена: {group_path}")
                except Exception as e:
                    print(f"[ERR] Не удалось удалить группу {group_path}: {e}")
    except Exception as e:
        print(f"[ERR] Не удалось открыть файл: {e}")

def delete_file_by_name(directory, filename):
    """Удаляет файл с указанным именем из заданной папки."""
    file_path = os.path.join(directory, filename)
    try:
        if os.path.isfile(file_path):
            os.remove(file_path)
            print(f"[DEL] Удалён файл: {file_path}")
        else:
            print(f"[WARN] Файл не найден: {file_path}")
    except Exception as e:
        print(f"[ERR] Не удалось удалить файл {file_path}: {e}")

# Пример использования
# file_path = 'video/2019-05-14/2019-05-14.h5'  # Укажите путь к вашему HDF5 файлу
file_path = 'dataset1.h5'  # Укажите путь к вашему HDF5 файлу
groups_to_delete = ['aben_R17_flyby_0', 'abfm_R03_flyby_1', 'arcc_G11_flyby_0']
delete_groups_from_h5(file_path, groups_to_delete)
# print_h5_contents(file_path)
