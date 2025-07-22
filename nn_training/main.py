import os
import h5py
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models, backend as K
from tensorflow.keras.metrics import Metric
from tensorflow.keras.saving import register_keras_serializable
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
import matplotlib.pyplot as plt

from config import *


@register_keras_serializable()
class F1Score(Metric):
    def __init__(self, name='f1_score', **kwargs):
        super().__init__(name=name, **kwargs)
        self.true_positives = self.add_weight(name='tp', initializer='zeros')
        self.false_positives = self.add_weight(name='fp', initializer='zeros')
        self.false_negatives = self.add_weight(name='fn', initializer='zeros')

    def update_state(self, y_true, y_pred, sample_weight=None):
        y_pred = K.round(y_pred)
        tp = K.sum(K.cast(y_true * y_pred, 'float32'))
        fp = K.sum(K.cast((1 - y_true) * y_pred, 'float32'))
        fn = K.sum(K.cast(y_true * (1 - y_pred), 'float32'))

        self.true_positives.assign_add(tp)
        self.false_positives.assign_add(fp)
        self.false_negatives.assign_add(fn)

    def result(self):
        precision = self.true_positives / (self.true_positives + self.false_positives + K.epsilon())
        recall = self.true_positives / (self.true_positives + self.false_negatives + K.epsilon())
        return 2 * ((precision * recall) / (precision + recall + K.epsilon()))

    def reset_states(self):
        self.true_positives.assign(0)
        self.false_positives.assign(0)
        self.false_negatives.assign(0)
        self.fn.assign(0)

def correct_labels(timestamps, event_times, event_types):
    labels = np.zeros_like(timestamps, dtype=float)

    current_state = None  # может быть 'entered' или 'exited'
    current_index = None

    for t, t_type in zip(event_times, event_types):
        idx_arr = np.where(timestamps == t)[0]
        if len(idx_arr) == 0:
            continue
        idx = idx_arr[0]

        if t_type == 'entered':
            if current_state == 'exited':
                labels[idx:] = 1.0
                current_state = None
                current_index = None
            else:
                current_state = 'entered'
                current_index = idx

        elif t_type == 'exited':
            if current_state == 'entered':
                labels[current_index:idx + 1] = 1.0
                current_state = None
                current_index = None
            else:
                labels[:idx + 1] = 1.0
                current_state = 'exited'
                current_index = idx

    # если остался незакрытый entered
    if current_state == 'entered' and current_index is not None:
        labels[current_index:] = 1.0
    return labels

def load_data(h5_file, index=None):
    """
    Универсальная функция загрузки данных:
    - Если index=None: возвращает все выборки как списки X, y (список примеров)
    - Если index задан: возвращает один пример (X, y)
    """
    def extract_features_and_labels(group):
        roti = group['roti'][()]
        delta_roti = group['roti_gradient'][()]
        amplitude = group['roti_amplitude'][()]
        spectrum = group['roti_spectrum'][()]
        sin_time = group['sin_time'][()]
        cos_time = group['cos_time'][()]
        symh = group['symh'][()]
        mlat = group['mlat'][()]
        mlon = group['mlon'][()]
        timestamps = group['timestamps'][()]
        event_times = group.attrs['times']
        event_types = group.attrs['types']

        labels = correct_labels(timestamps, event_times, event_types)
        features = np.column_stack([
            roti,
            delta_roti,
            amplitude,
            spectrum,
            sin_time, 
            cos_time,
            symh,
            mlat, 
            mlon
        ])
        return features, labels, timestamps

    X, y, ts = [], [], []

    with h5py.File(h5_file, 'r') as f:
        groups = list(f.values())

        if index is not None:
            features, labels, timestamps = extract_features_and_labels(groups[index])
            return features, labels

        for group in groups:
            features, labels, timestamps = extract_features_and_labels(group)
            X.append(features)
            y.append(labels)
            ts.append(timestamps)

    return X, y

def create_model(n_features):
    """Создание модели с последовательным выводом на каждый временной шаг"""
    model = models.Sequential([
        layers.Input(shape=(None, n_features)),

        layers.Conv1D(32, 5, activation='relu', padding='same'),
        layers.BatchNormalization(),

        layers.Conv1D(64, 3, activation='relu', padding='same'),
        layers.BatchNormalization(),

        layers.TimeDistributed(layers.Dense(1, activation='sigmoid'))
    ])

    model.compile(
        optimizer='adam',
        loss=tf.keras.losses.BinaryCrossentropy(),
        metrics=[tf.keras.metrics.BinaryAccuracy(), F1Score()]
    )
    return model

def train_model(h5_file, model_save_path='models\\binary_model.keras'):
    X, y = load_data(h5_file)
    n_features = X[0].shape[1]

    # Трехуровневое разделение данных:
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y,
        test_size=0.2,
        random_state=42
    )

    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp,
        test_size=0.5,
        random_state=42
    )

    # Создаем модель
    model = create_model(n_features)

    # Обучение с callback'ами
    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            patience=10,
            monitor='val_f1_score',
            mode='max',  # потому что F1 нужно **максимизировать**
            restore_best_weights=True
        ),
        tf.keras.callbacks.ModelCheckpoint(
            model_save_path,
            save_best_only=True,
            monitor='val_f1_score',
            mode='max'  # обязательно!
        )
    ]

    X_train_padded = tf.keras.preprocessing.sequence.pad_sequences(
        X_train, dtype='float32', padding='post'
    )
    X_val_padded = tf.keras.preprocessing.sequence.pad_sequences(
        X_val, dtype='float32', padding='post'
    )
    X_test_padded = tf.keras.preprocessing.sequence.pad_sequences(
        X_test, dtype='float32', padding='post'
    )

    y_train_padded = tf.keras.preprocessing.sequence.pad_sequences(
        y_train, dtype='float32', padding='post'
    )[..., np.newaxis]
    y_val_padded = tf.keras.preprocessing.sequence.pad_sequences(
        y_val, dtype='float32', padding='post'
    )[..., np.newaxis]
    y_test_padded = tf.keras.preprocessing.sequence.pad_sequences(
        y_test, dtype='float32', padding='post'
    )[..., np.newaxis]


    def get_sample_weights(y_padded, weight_for_1=ONE_WEIGTH, weight_for_0=ZERO_WEIGTH):
        return np.where(y_padded == 1.0, weight_for_1, weight_for_0)

    sample_weights_train = get_sample_weights(y_train_padded)
    sample_weights_test = get_sample_weights(y_test_padded)

    history = model.fit(
        X_train_padded,
        y_train_padded,
        validation_data=(X_val_padded, y_val_padded),
        batch_size=32,
        epochs=50,
        callbacks=callbacks,
        sample_weight=sample_weights_train
    )

    test_loss, test_acc, test_f1 = model.evaluate(
        X_test_padded,
        y_test_padded,
        sample_weight=sample_weights_test,
        verbose=0
    )

    print(f"\nFinal Test Accuracy: {test_acc:.4f}")
    print(f"Final Test Loss: {test_loss:.4f}")
    print(f"Final Test F1: {test_f1:.4f}")

    return model, history

def save_confusion_matrix(y_true, y_pred, save_path="results/confusion_matrix.png"):
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=[0, 1])
    disp.plot(cmap=plt.cm.Blues, values_format='d')

    plt.title("Confusion Matrix")
    plt.tight_layout()
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path)
    plt.close()

def plot_example(model_path, h5_file_path):
    # Загрузка модели
    model = tf.keras.models.load_model(model_path, custom_objects={'F1Score': F1Score})

    # Загрузка одного реального примера
    features, true_labels = load_data(h5_file_path, index=TEST_IDX)
    # print('true_labels', true_labels, '\n')
    # return

    # Подготовка к подаче в модель
    features_input = np.expand_dims(features, axis=0) 

    # Предсказание
    pred = model.predict(features_input)
    probs = pred[0, :, 0]  # (T,)
    # print('probs', probs, '\n')
    binary_preds = (probs > 0.5).astype(int)
    # print('binary_preds', binary_preds)

    plt.figure(figsize=(14, 4))
    plt.plot(features[:, 0], label='ROTI')
    plt.plot(probs, label='Event probability')
    plt.plot(true_labels, label='True event label', linestyle='dotted')

    plt.plot(binary_preds, label='Predicted label', linestyle='--')
    
    # save_confusion_matrix(true_labels.astype(int), binary_preds)

    plt.legend()
    plt.title("Model prediction vs true labels")

    # y_true = true_labels.astype(int)
    # y_pred = binary_preds

    # cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    # disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=[0, 1])
    # disp.plot(cmap=plt.cm.Blues, values_format='d')
    
    # plt.xticks([])  
    # plt.yticks([])  
    # plt.grid(False)

    plt.xlabel("Time step")
    plt.tight_layout()
    plt.show()


model, history = train_model(h5_file=DATASET, model_save_path=MODEL_PATH)

#0 2 10 11
TEST_IDX = 2
plot_example(
    h5_file_path=DATASET,
    model_path=MODEL_PATH,
)