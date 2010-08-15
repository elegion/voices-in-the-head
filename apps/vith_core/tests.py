import datetime, time

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase

from vith_core.models import Track, NON_EDIT_TIME


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


class VoteTestCase(TestCase):
    def setUp(self):
        self.old_setting = getattr(settings, 'DELETE_THRESHOLD', None)
        settings.DELETE_THRESHOLD = 2
        # Reload settings
        from vith_core import views, models
        reload(models)
        reload(views)

    def tearDown(self):
        settings.DELETE_THRESHOLD = self.old_setting

    def vote_till_removed(self, track_id):
        for i in xrange(settings.DELETE_THRESHOLD):
            response = self.client.post(reverse('vith_core.views.vote'), {'track_id': track_id}, REMOTE_ADDR=i+1)
            self.assertEquals(200, response.status_code)
        self.assertEquals('delete', response.data['result'])

    def test_playtime_updated(self):
        track1 = Track.objects.create(name='Track 1',
                                      play_time=datetime.datetime.now() + datetime.timedelta(seconds=NON_EDIT_TIME + 5),
                                      length=10)
        track2 = Track.objects.create(name='Track 2',
                                      play_time=track1.play_time + datetime.timedelta(seconds=track1.length),
                                      length=20)
        self.vote_till_removed(track1.pk)

        expected_time = track2.play_time - datetime.timedelta(seconds=track1.length)
        track2 = Track.objects.get(pk=track2.pk)
        self.assertEquals(expected_time, track2.play_time)

    def test_deletes(self):
        track = Track.objects.create(name='Track 1',
                                     play_time=datetime.datetime.now() + datetime.timedelta(seconds=NON_EDIT_TIME + 5),
                                     length=10)

        response = self.client.post(reverse('vith_core.views.vote'), {'track_id': track.pk}, REMOTE_ADDR=1)
        self.assertEquals(200, response.status_code)
        self.assertEquals('ok', response.data['result']) # not yet deleted

        response = self.client.post(reverse('vith_core.views.vote'), {'track_id': track.pk}, REMOTE_ADDR=2)
        self.assertEquals(200, response.status_code)
        self.assertEquals('delete', response.data['result'])