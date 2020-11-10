from flask import flash, current_app
import urllib
import base64
import io
from matplotlib import pyplot as plt
import matplotlib.image as mpimg
import random
from skimage.transform import resize
# from tensorflow.keras.models import Sequential
# from tensorflow.keras.layers import Dense, Activation, Flatten, Conv2D, MaxPooling2D
import numpy as np

from flaskr.database.image_models.collection import Collection


BINARY_CLASS = {
    'yellow': 0,
    'red': 1,
    'invalid': 3
}


class Analyzer():
    def __init__(
            self,
    ):
        self.results = []
        self.epochs = 0
        self.img_size = 20
        self.model = None

    def execute(self):
        image_collection = Collection()

        # self.build_model((self.img_size, self.img_size, 3))
        training_data = []
        testing_data = []

        for idx, item in enumerate(image_collection):
            image = item.get_image()
            class_num = BINARY_CLASS[item.get_class()]

            if type(item.get_image()) == str:
                image = urllib.parse.unquote(item.get_image())

            # To save images locally uncomment this:
            # if not item.is_training():
            #     self.save_locally(item=image, title=item.get_class() + str(idx), resize_image=True)

            try:
                new_array = self.convert_image(image, resize_image=True)
                if item.is_training():
                    training_data.append([new_array, class_num])
                else:
                    testing_data.append([new_array, class_num])
            except Exception as e:
                flash(str(e), 'error')
                pass

            # this is for when we have a giant image set, to reduce the memory load
            if training_data is not None and len(training_data) > 1000:
                X, y = self.build_data(training_data)
                self.model.fit(X, y, batch_size=32, epochs=20, validation_split=0.05)
                training_data = []

        flash('Training size: %s, testing size: %s' % (len(training_data), len(testing_data)))

        if len(training_data) > 0:
            X, y = self.build_data(training_data)
            # history = self.model.fit(X, y, batch_size=32, epochs=20, validation_split=0.05)
            # flash('Completed model accuracy: %s ' % history.history['val_accuracy'][-1])

            # self.model.save(current_app.config['UPLOAD_FOLDER']) # TODO: need a file path to save

        if len(testing_data) > 0:
            x_test, y_test = self.build_data(testing_data)
            # results = self.model.evaluate(x_test, y_test, batch_size=32)
            # flash('Testing loss: %s, accuracy: %s' % (str(round(results[0], 2)), str(round(results[1], 2))))
            # predictions = self.model.predict(x_test)
            # flash('Predictions: %s ' % ', '.join([str(round(p[0], 2)) for p in predictions]))
            # flash('Actual: %s ' % ', '.join([str(t[1]) for t in testing_data]))

    def build_data(self, data):
        random.shuffle(data)

        X = []
        y = []

        for features, label in data:
            X.append(features)
            y.append(label)

        X = np.array(X).reshape(-1, self.img_size, self.img_size, 3)  # 1 b/c img is grayscale, come back and try to convert to rgb (1->3)
        y = np.array(y)

        X = X / 255.

        return X, y

    def build_model(self, columns):
        self.model = Sequential()

        self.model.add(Conv2D(64, (3, 3), input_shape=columns))  # First Layer
        self.model.add(Activation("relu"))
        self.model.add(MaxPooling2D(pool_size=(2, 2)))

        self.model.add(Conv2D(64, (3, 3)))  # Second Layer
        self.model.add(Activation("relu"))
        self.model.add(MaxPooling2D(pool_size=(2, 2)))

        self.model.add(Flatten())  # Third Layer
        self.model.add(Dense(64))
        self.model.add(Activation('relu'))

        self.model.add(Dense(1))  # Output Layer
        self.model.add(Activation('sigmoid'))

        self.model.compile(loss="binary_crossentropy", optimizer="adam", metrics=['accuracy'])

    def save_locally(self, item, title, resize_image=False):
        i = self.convert_image(item, resize_image=resize_image)
        plt.imshow(i)
        plt.show()
        plt.savefig(title + '.png')

    def convert_image(self, item, resize_image=False):
        item = base64.b64decode(item)
        i = io.BytesIO(item)
        i = mpimg.imread(i)

        if resize_image:
            i = resize(i, (self.img_size, self.img_size))

        return i
