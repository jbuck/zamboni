import mock
from nose.tools import eq_

from addons.utils import FeaturedManager, CreaturedManager

import amo.tests


class TestFeaturedManager(amo.tests.TestCase):

    def setUp(self):
        patcher = mock.patch('addons.utils.FeaturedManager._get_objects')
        self.objects_mock = patcher.start()
        self.addCleanup(patcher.stop)

        # Fake the objects.values() call.
        self.fields = ['addon', 'type', 'locale', 'application']
        self.values = [
            (1, 1, None, 1),
            (2, 1, None, 1),
            (3, 9, None, 1),     # A different type.
            (4, 1, 'ja', 1),     # Restricted locale.
            (5, 1, 'ja', 1),
            (5, 1, 'en-Us', 1),  # Same add-on, different locale.
            (6, 1, None, 18),    # Different app.
        ]
        self.objects_mock.return_value = [dict(zip(self.fields, v))
                                          for v in self.values]
        self.fm = FeaturedManager
        self.fm.build()

    def test_build(self):
        eq_(self.fm.redis().smembers(self.fm.by_id), set([1, 2, 3, 4, 5, 6]))

    def test_by_app(self):
        eq_(set(self.fm.featured_ids(amo.FIREFOX)), set([1, 2, 3, 4, 5]))
        eq_(set(self.fm.featured_ids(amo.FIREFOX, 'xx')), set([1, 2, 3]))

    def test_by_type(self):
        eq_(set(self.fm.featured_ids(amo.FIREFOX, 'xx', 1)), set([1, 2]))

    def test_by_locale(self):
        eq_(sorted(self.fm.featured_ids(amo.FIREFOX, 'ja')), [1, 2, 3, 4, 5])
        eq_(sorted(self.fm.featured_ids(amo.FIREFOX, 'en-US')), [1, 2, 3, 5])

    def test_locale_shuffle(self):
        # Make sure the locale-specific add-ons are at the front.
        ids = self.fm.featured_ids(amo.FIREFOX, 'ja')
        eq_(set(ids[:2]), set([4, 5]))

    def test_reset(self):
        # Drop the first one to make sure we reset the list properly.
        self.values = self.values[1:]
        self.objects_mock.return_value = [dict(zip(self.fields, v))
                                          for v in self.values]
        self.fm.build()
        eq_(set(self.fm.featured_ids(amo.FIREFOX, 'xx')), set([2, 3]))


class TestCreaturedManager(amo.tests.TestCase):

    def setUp(self):
        patcher = mock.patch('addons.utils.CreaturedManager._get_objects')
        self.objects_mock = patcher.start()
        self.addCleanup(patcher.stop)

        self.category = mock.Mock()
        self.category.id = 1
        self.category.application_id = 1

        self.fields = ['category', 'addon', 'locales', 'app']
        self.values = [
            (1, 1, None, 1),     # No locales.
            (1, 2, '', 1),       # Make sure empty string is ok.
            (2, 3, None, 1),     # Something from a different category.
            (1, 4, 'JA', 1),     # Check locales with no comma.
            (1, 5, 'ja,en', 1),  # Locales with a comma.
            (1, 6, '', 9),       # Make sure empty string is ok.
        ]
        self.objects_mock.return_value = [dict(zip(self.fields, v))
                                          for v in self.values]
        self.cm = CreaturedManager
        self.cm.build()

    def test_by_category(self):
        eq_(set(self.cm.creatured_ids(self.category, 'xx')), set([1, 2]))

    def test_by_locale(self):
        eq_(set(self.cm.creatured_ids(self.category, 'ja')), set([1, 2, 4, 5]))

    def test_shuffle(self):
        ids = self.cm.creatured_ids(self.category, 'ja')
        eq_(set(ids[:2]), set([4, 5]))

    def test_reset(self):
        self.values = self.values[1:]
        self.objects_mock.return_value = [dict(zip(self.fields, v))
                                          for v in self.values]
        self.cm.build()
        eq_(set(self.cm.creatured_ids(self.category, 'xx')), set([2]))
