import datetime, time

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase

from vith_core.models import Track


class UploadTestCase(TestCase):
    def tearDown(self):
        Track.objects.all().delete() # To remove uploaded files

    def test_enqueues(self):
        # Track already played and shouldn't affect new track play_time
        Track.objects.create(
            play_time=datetime.datetime.now() - datetime.timedelta(seconds=50),
            length=10,
            name='Another test track')

        track_name = 'Test track name'
        with open(settings.MEDIA_ROOT + '/sample/test.mp3', 'rb') as f:
            response = self.client.post(
                reverse('vith_core.views.upload'),
                {'name': track_name, 'track_file': f})
        self.assertEquals(200, response.status_code)
        self.assertEquals('ok', response.data['status'])
        self.assertEquals(2, Track.objects.all().count())
        self.assertEquals(track_name, Track.objects.all()[1].name)
        self.assertEquals(track_name, response.data['track']['name'])
        self.assertAlmostEquals(time.time(), response.data['track']['play_time'], 0)

    def test_upload_schedules(self):
        # There is track currently playing, schedule (Track.play_time) new track to play after current
        current_track = Track.objects.create(
            play_time=datetime.datetime.now() - datetime.timedelta(seconds=5),
            length=10,
            name='Another test track')
        with open(settings.MEDIA_ROOT + '/sample/test.mp3', 'rb') as f:
            response = self.client.post(
                reverse('vith_core.views.upload'),
                {'name': 'Test track', 'track_file': f})
        self.assertEquals(200, response.status_code)
        self.assertEquals(2, Track.objects.all().count())

        expected_time = current_track.play_time + datetime.timedelta(seconds=current_track.length)
        expected_time = time.mktime(expected_time.timetuple()) + 1e-6*expected_time.microsecond
        self.assertEquals(expected_time, response.data['track']['play_time'], 0)

    def test_wrong_post(self):
        response = self.client.post(reverse('vith_core.views.upload'))
        self.assertEquals(200, response.status_code)
        self.assertEquals(response.data['status'], 'error')
        self.assertTrue(response.data['errors'].has_key('track_file'))
        self.assertTrue(response.data['errors'].has_key('name'))
