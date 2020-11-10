from flask import flash, request
import urllib
from bson import ObjectId
from PIL import Image
import numpy as np
import random
import base64
import datetime
from skimage import io
from skimage.feature import blob_doh
from skimage.color import rgb2gray, rgb2hsv
from matplotlib import pyplot as plt
from io import BytesIO
import colorsys

from flaskr.framework.model.request.response import Response
from flaskr.framework.abstract.abstract_processor import AbstractProcessor
from flaskr.database.image_models.manager import Manager
from flaskr.database.image_models.factory import Factory
from flaskr.database.image_models.repository import Repository


def validate_blob(current_index, blobs):
    for idx, other_blob in enumerate(blobs):
        if idx == current_index:
            continue
        if abs(other_blob[0] - blobs[current_index][0]) < 50 and abs(other_blob[1] - blobs[current_index][1]) < 50:
            return False
    return True


def get_color(rgb, textcolor=False):
    # convert to hsl color wheel
    hsv = colorsys.rgb_to_hls(rgb[0]/255, rgb[1]/255, rgb[2]/255)
    if hsv[0] < .5:
        if textcolor:
            return 'black'
        return 'yellow'
    return 'red'


def convert_to_base64(image):
    sio = BytesIO()
    pil = Image.fromarray(image)
    pil.save(sio, format='png')
    sio.seek(0)
    return base64.b64encode(sio.getvalue())


def get_previous_upload(name):
    image_repository = Repository()
    return image_repository.get_by_name(name)


class ImageProcessor(AbstractProcessor):
    def __init__(
            self,
            request: request,
    ):
        self.request = request
        self.graph_urls = dict()
        self.original = None
        self.gray_image = None
        self.dataset_id = ObjectId()
        self.dataset_name = ''
        self.results = dict()

    def execute(self):
        self.image_manager = Manager()
        self.image_factory = Factory()

        imported_file = self.request.files.get('imagefile')
        if imported_file.filename == '':
            return Response(False, 'No image uploaded')

        self.dataset_name = imported_file.filename

        upload = True
        model = get_previous_upload(self.dataset_name)
        if model is not None:
            upload = False
            self.dataset_id = model['dataset_id']

        self.original = io.imread(fname=imported_file)
        # io.imsave(fname='copy_' + imported_file.filename[:-4] + '.png', arr=image)

        blobs_list = self.blob_finder()

        # draw circles around blobs and display image
        f, ax = plt.subplots(figsize=(5, 5))
        ax.imshow(self.original)
        ixs = np.indices(self.gray_image.shape)
        count = 0

        invalid_blobs = []
        for i, blob in enumerate(blobs_list):
            if not validate_blob(i, blobs_list):
                invalid_blobs.append(i)
                continue
            y, x, r = blob

            # Calculate the average intensity of pixels under the mask
            blob_center = np.array([y, x])[:, np.newaxis, np.newaxis]
            mask_gray = ((ixs - blob_center) ** 2).sum(axis=0) < r ** 2
            blob_avg = self.original[mask_gray].mean(0)

            # Add the color to the blob information
            blobs_list[i] = list(blobs_list[i]) + [get_color(blob_avg)]
            c = plt.Circle((x, y), r, color='blue', linewidth=.5, fill=False)
            ax.add_patch(c)
            ax.text(x, y, str(count), color=get_color(blob_avg, textcolor=True))

            count += 1
        self.save_image(plt, str(self.dataset_id), plot=True)
        self.results[-1] = dict(index='dataset',
                                graph=self.graph_urls[str(self.dataset_id)])

        # remove any invalid blobs and save to database
        blobs_log = [blob for idx, blob in enumerate(blobs_list) if idx not in invalid_blobs]
        # TODO: verify that all radiuses are the same

        for idx, blob in enumerate(blobs_log):
            y, x, r, color = blob

            # flash(f'Tube {idx} is {color}')
            self.add_measurement(image=self.original[int(y - r):int(y + r), int(x - r):int(x + r), :],
                                 color=color,
                                 label_number=idx)

            fig = plt.figure(figsize=(4, 2))
            fig.figimage(self.original[int(y - r):int(y + r), int(x - r):int(x + r), :],
                         60, fig.bbox.ymax - 170)
            self.save_image(image=plt, title=idx, plot=True)

            self.results[idx] = dict(index=idx,
                                     color=color,
                                     graph=self.graph_urls[idx])

            # self.histogram(self.original[int(y - r):int(y + r), int(x - r):int(x + r), :], 'hist ' + str(idx))
        if upload:
            self.image_manager.save()

        return Response(True, '', name=imported_file.filename)

    def save_image(self, image, title, plot=False):
        sio = BytesIO()
        if not plot:
            self.graph_urls[title] = convert_to_base64(image)
            return

        plt.savefig(sio, format='png')
        plt.close()
        self.graph_urls[title] = base64.b64encode(sio.getvalue()).decode(
            'utf-8').replace('\n', '')

    def histogram(self, image, title):
        colors = ("r", "g", "b")
        channel_ids = (0, 1, 2)
        fig = plt.figure(figsize=(4, 2))
        plt.xlim([0, 256])
        for channel_id, c in zip(channel_ids, colors):
            histogram, bin_edges = np.histogram(
                image[:, :, channel_id], bins=64, range=(0, 256)
            )
            plt.plot(bin_edges[0:-1], histogram, color=c)

        self.save_image(image=plt, title=id, plot=True)

    def blob_finder(self):
        # high saturated pixels:
        imagecopy = np.copy(self.original)
        hsv_img = rgb2hsv(imagecopy)
        sat_img = hsv_img[:, :, 1]
        imagecopy[sat_img < .3] = 0

        #to show the saturation image:
        # f, ax = plt.subplots(figsize=(5, 5))
        # ax.imshow(self.original)
        # ax.imshow(sat_img)
        # self.save_image(plt, 'title', plot=True)

        # to grayscale
        self.gray_image = rgb2gray(imagecopy)

        # identify blobs with a determinent of the hessian
        blobs_log = blob_doh(self.gray_image, min_sigma=10, max_sigma=70, threshold=.003, overlap=.0001)
        if len(blobs_log) == 0:
            flash('Nothing identified as a colored tube or vial', 'error')
            return blobs_log

        blobs_log[:, 2] = blobs_log[:, 2] * np.sqrt(.8)
        #TODO: make each the same size

        blobs_log = [blob for blob in blobs_log if blob[2] > 6]
        return blobs_log

    def add_measurement(self, image, color, label_number):
        training = True if random.randint(0, 10) < 7 else False

        data = {'dataset_id': ObjectId(self.dataset_id),
                'dataset_name': self.dataset_name,
                'image': convert_to_base64(image),
                'class': color,
                'training': training,
                'date': datetime.datetime.today(),
                'label': str(label_number)}

        data = self.image_factory.create(data)
        self.image_manager.add(data)

