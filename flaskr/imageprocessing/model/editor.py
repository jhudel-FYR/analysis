from flask import flash, request
from bson import ObjectId

from flaskr.framework.model.request.response import Response
from flaskr.database.image_models.manager import Manager
from flaskr.database.image_models.repository import Repository
from flaskr.database.image_models.collection import Collection


def validate_color(entry):
    if str(entry).lower() == 'red':
        return True
    elif str(entry).lower() == 'yellow':
        return True
    else:
        flash('%s was not recognized. Please only enter red or yellow' % entry, 'error')
        return False


class Editor:
    def __init__(
            self,
            dataset_id
    ):
        self.dataset_id = dataset_id
        self.results = dict()

    def execute(self, request):
        image_manager = Manager()
        image_repository = Repository()
        image_collection = Collection()

        if type(self.dataset_id) == str:
            self.dataset_id = ObjectId(self.dataset_id)
        image_collection.add_filter('dataset_id', ObjectId(self.dataset_id))
        if image_collection.get_size() == 0:
            return Response(False, 'No images found')

        invalid_images = []
        for image in image_collection:
            valid_placeholder = 'valid ' + str(image.get_label())
            label_placeholder = 'label ' + str(image.get_label())

            if request.form.get(valid_placeholder) is not None\
                    or request.form.get('valid dataset') is not None:
                invalid_images.append(ObjectId(image.get_id()))
                continue

            elif request.form.get(label_placeholder) is not None and \
                    request.form.get(label_placeholder) != '':

                if not validate_color(request.form[label_placeholder]):
                    continue
                image['class'] = str(request.form[label_placeholder]).lower()
                image_manager.add(image)

            self.results[image.get_label()] = dict(index=image.get_label(),
                                                   color=image['class'],
                                                   graph=image['image'])

        image_manager.save()

        for delete_id in invalid_images:
            image_repository.delete_by_filter({'_id': delete_id})
        return Response(True, '')
