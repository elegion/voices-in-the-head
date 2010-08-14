from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase

from vith_core.models import Track


class UploadTestCase(TestCase):
    def test_enqueues(self):
        track_name = 'Test track name'
        with open(settings.MEDIA_ROOT + '/sample/test.mp3') as f:
            response = self.client.post(
                reverse('vith_core.views.upload'),
                {'name': track_name, 'track_file': f})
        self.assertEquals(200, response.status_code)
        self.assertEquals('ok', response.data['status'])
        self.assertEquals(1, Track.objects.all().count())
        self.assertEquals(track_name, Track.objects.all()[0].name)
        self.assertEquals(track_name, response.data['name'])


    def test_wrong_post(self):
        response = self.client.post(reverse('vith_core.views.upload'))
        self.assertEquals(200, response.status_code)
        self.assertEquals(response.data['status'], 'error')
        self.assertTrue(response.data['errors'].has_key('track_file'))
        self.assertTrue(response.data['errors'].has_key('name'))
