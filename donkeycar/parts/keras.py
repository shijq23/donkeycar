""""

keras.py

functions to run and train autopilots using keras

"""

from tensorflow.python.keras.layers import Input
from tensorflow.python.keras.models import Model, load_model
from tensorflow.python.keras.layers import Convolution2D
from tensorflow.python.keras.layers import Dropout, Flatten, Dense
from tensorflow.python.keras.callbacks import ModelCheckpoint, EarlyStopping, TensorBoard
from PIL import Image
from io import BytesIO
import tensorflow as tf

print("tensorflow version %s" % tf.VERSION)
print("tensorflow.keras version %s" % tf.keras.__version__)


class KerasPilot:

    def load(self, model_path):
        self.model = load_model(model_path)

    def shutdown(self):
        pass

    def train(self, train_gen, val_gen,
              saved_model_path, epochs=100, steps=100, train_split=0.8,
              verbose=1, min_delta=.0005, patience=5, use_early_stop=True):
        """
        train_gen: generator that yields an array of images an array of

        """

        # checkpoint to save model after each epoch
        save_best = ModelCheckpoint(saved_model_path,
                                    monitor='val_loss',
                                    verbose=verbose,
                                    save_best_only=True,
                                    mode='min')

        # stop training if the validation error stops improving.
        early_stop = EarlyStopping(monitor='val_loss',
                                   min_delta=min_delta,
                                   patience=patience,
                                   verbose=verbose,
                                   mode='auto')
        # tensor board
        board = TensorBoard(log_dir='./tb_logs',
                            histogram_freq=1,
                            batch_size=32,
                            write_graph=True,
                            write_grads=True,
                            write_images=False,
                            embeddings_freq=0,
                            embeddings_layer_names=None,
                            embeddings_metadata=None,
                            embeddings_data=None,
                            update_freq='epoch')

        callbacks_list = [save_best, board]

        if use_early_stop:
            callbacks_list.append(early_stop)

        hist = self.model.fit_generator(
            train_gen,
            steps_per_epoch=steps,
            epochs=epochs,
            verbose=1,
            validation_data=val_gen,
            callbacks=callbacks_list,
            validation_steps=int(steps * (1.0 - train_split) / train_split))
        return hist


class KerasLinear(KerasPilot):
    def __init__(self, model=None, num_outputs=None, *args, **kwargs):
        super(KerasLinear, self).__init__(*args, **kwargs)
        if model:
            self.model = model
        elif num_outputs is not None:
            self.model = default_linear()
        else:
            self.model = default_linear()

    def run(self, img_arr):
        img_arr = img_arr.reshape((1,) + img_arr.shape)
        #outputs = self.model.predict(img_arr[None, :, :, :])
        outputs = self.model.predict(img_arr)
        # print(len(outputs), outputs)
        steering = outputs[0]
        throttle = outputs[1]
        return steering[0][0], throttle[0][0]


def default_linear():
    img_in = Input(shape=(120, 160, 3), name='img_in')
    x = img_in

    # Convolution2D class name is an alias for Conv2D
    x = Convolution2D(filters=24, kernel_size=(5, 5), strides=(2, 2), activation='relu')(x)
    x = Convolution2D(filters=32, kernel_size=(5, 5), strides=(2, 2), activation='relu')(x)
    x = Convolution2D(filters=64, kernel_size=(5, 5), strides=(2, 2), activation='relu')(x)
    x = Convolution2D(filters=64, kernel_size=(3, 3), strides=(2, 2), activation='relu')(x)
    x = Convolution2D(filters=64, kernel_size=(3, 3), strides=(1, 1), activation='relu')(x)

    x = Flatten(name='flattened')(x)
    x = Dense(units=100, activation='linear')(x)
    x = Dropout(rate=.1)(x)
    x = Dense(units=50, activation='linear')(x)
    x = Dropout(rate=.1)(x)
    # categorical output of the angle
    angle_out = Dense(units=1, activation='linear', name='angle_out')(x)

    # continous output of throttle
    throttle_out = Dense(units=1, activation='linear', name='throttle_out')(x)

    model = Model(inputs=[img_in], outputs=[angle_out, throttle_out])

    model.compile(optimizer='adam',
                  loss={'angle_out': 'mean_squared_error',
                        'throttle_out': 'mean_squared_error'},
                  loss_weights={'angle_out': 0.5, 'throttle_out': .5})

    return model


class KerasClient():
    def __init__(self, host="127.0.0.1", port=9090, *args, **kwargs):
        import socketio
        self.host = host
        self.port = port
        self.connected = False
        self.sio = socketio.Client()

        self.sio.on('steer', handler=self.on_steer)
        self.sio.on('connect', handler=self.on_connect)
        self.sio.on('disconnect', handler=self.on_disconnect)
        self.steering_angle = 0.0
        self.throttle = 0.0

    def on_connect(self):
        print("connected")

    def on_disconnect(self):
        print("disconneted")

    def on_steer(self, data):
        print("steer " + str(data))
        self.steering_angle = float(data['steering_angle'])
        self.throttle = float(data['throttle'])
        
    def connect(self):
        url = "http://" + self.host + ":" + str(self.port)
        print("connecting to %s" % url)
        self.sio.connect(url)
        self.connected = True

    def run(self, img_arr, angle=0.0, throttle=0.0):
        import base64
        if not self.connected:
            self.connect()
        
        if angle is None:
            angle = 0.0
        if throttle is None:
            throttle = 0.0

        img = Image.fromarray(img_arr)
        stream = BytesIO()
        img.save(stream, format="jpeg")
        img_str = base64.b64encode(stream.getvalue()).decode()
        dat = {
            "steering_angle": angle, #[-1.0, 1.0]
            "throttle": throttle, #[-1.0, 1.0]
            "speed": 1.0, #[]
            "image": img_str
        }
        self.sio.emit(
            "telemetry",
            data=dat)
        
        return self.steering_angle, self.throttle
