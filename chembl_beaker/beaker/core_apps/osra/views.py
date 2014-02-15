__author__ = 'mnowotka'

#-----------------------------------------------------------------------------------------------------------------------

from bottle import request
import base64
from chembl_beaker.beaker import app, config
from chembl_beaker.beaker.core_apps.osra.impl import _image2ctab

#-----------------------------------------------------------------------------------------------------------------------

@app.get('/image2ctab/<image>', name="image2ctab")
def image2ctab(image):
    """
Uses OSRA to convert image to CTAB. Image should be urlsafe_base65 encoded data of 300 DPI png graphic.
    """

    if image.startswith('data:'):
        img = base64.urlsafe_b64decode(image[image.find(',')+1:])
    else:
        img = base64.urlsafe_b64decode(image)
    #TODO: check /usr/local/bin/osra when no explicit value given
    return _image2ctab(img, config.get('osra_binaries_location', '/usr/bin/osra'))

#-----------------------------------------------------------------------------------------------------------------------

@app.route('/image2ctab', method=['OPTIONS', 'POST'], name="image2ctab")
def image2ctab():
    """
Uses OSRA to convert image to CTAB. Image should be 300 DPI png graphic.
    """

    img = request.body.read()
    if img.startswith('data:'):
        img = base64.b64decode(img[img.find(',')+1:])
    #TODO: check /usr/local/bin/osra when no explicit value given      
    return _image2ctab(img, config.get('osra_binaries_location', '/usr/bin/osra'))

#-----------------------------------------------------------------------------------------------------------------------
