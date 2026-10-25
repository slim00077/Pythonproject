"""Automated accessibility checks (WCAG 2.1 AA basics) on the pages of the goals and gamification modules.

They complement, and do not replace, a Lighthouse/axe audit in the browser (see README, section Accessibilité).
"""
from datetime import timedelta
from html.parser import HTMLParser

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.testing import make_superuser, make_user
from gamification.models import Badge
from gamification.services import award_points

from .models import Goal


class PageAudit(HTMLParser):
    """Collects the facts needed to check landmarks, headings, images, forms, tables and ARIA."""

    def __init__(self):
        super().__init__()
        self.headings, self.problems = [], []
        self.landmarks, self.ids, self.labels_for = set(), set(), set()
        self.controls, self.describedby = [], []
        self._table = None
        self._in_button = self._in_link = None
        self.tables = []
        self.lang = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a:
            self.ids.add(a['id'])
        if tag == 'html':
            self.lang = a.get('lang')
        if tag in ('main', 'nav', 'header', 'footer', 'aside'):
            self.landmarks.add(tag)
        if tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            self.headings.append(int(tag[1]))
        if tag == 'img' and 'alt' not in a:
            self.problems.append('<img> sans attribut alt')
        if tag == 'svg' and a.get('aria-hidden') != 'true' and a.get('role') not in ('img', 'presentation'):
            self.problems.append('<svg> ni masqué (aria-hidden) ni nommé (role=img)')
        if tag == 'label' and 'for' in a:
            self.labels_for.add(a['for'])
        if tag in ('input', 'select', 'textarea') and a.get('type') not in ('hidden', 'submit', 'button'):
            self.controls.append(a)
        if 'aria-describedby' in a:
            self.describedby.extend(a['aria-describedby'].split())
        if a.get('role') == 'progressbar':
            for attr in ('aria-valuenow', 'aria-valuemin', 'aria-valuemax'):
                if attr not in a:
                    self.problems.append(f'progressbar sans {attr}')
            if 'aria-label' not in a and 'aria-labelledby' not in a:
                self.problems.append('progressbar sans nom accessible')
        if tag == 'table':
            self._table = {'caption': False, 'th_without_scope': 0}
            self.tables.append(self._table)
        if tag == 'caption' and self._table is not None:
            self._table['caption'] = True
        if tag == 'th' and self._table is not None and 'scope' not in a:
            self._table['th_without_scope'] += 1
        if tag == 'a' and 'href' in a and a['href'] == '':
            self.problems.append('lien vide')

    def handle_endtag(self, tag):
        if tag == 'table':
            self._table = None


def audit(test, response):
    parser = PageAudit()
    parser.feed(response.content.decode())
    test.assertEqual(parser.lang, 'fr', 'attribut lang manquant')
    test.assertIn('main', parser.landmarks)
    test.assertIn('nav', parser.landmarks)
    test.assertEqual(parser.headings.count(1), 1, f'un seul h1 attendu : {parser.headings}')
    previous = 0
    for level in parser.headings:
        test.assertLessEqual(level, previous + 1, f'saut de niveau de titre {previous} -> {level} : {parser.headings}')
        previous = level
    test.assertEqual(parser.problems, [])
    for table in parser.tables:
        test.assertTrue(table['caption'], 'tableau sans <caption>')
        test.assertEqual(table['th_without_scope'], 0, '<th> sans scope')
    for control in parser.controls:
        named = control.get('id') in parser.labels_for or 'aria-label' in control or 'aria-labelledby' in control
        test.assertTrue(named, f'champ sans libellé : {control}')
    for ref in parser.describedby:
        test.assertIn(ref, parser.ids, f'aria-describedby vers un id absent : {ref}')
    return parser


class AccessibilityTests(TestCase):
    def setUp(self):
        self.user = make_user('a11y-user')
        self.admin = make_superuser()
        self.today = timezone.localdate()
        self.goal = Goal.objects.create(user=self.user, title='Vélo', target_value=10, current_progress=3,
                                        deadline=self.today + timedelta(days=9))
        self.badge = Badge.objects.create(name='Premier pas', description='x', rule='points_total', threshold=100)
        award_points(user=self.user, amount=10, reason='manual_adjustment', reference='a:1', description='x')

    def test_participant_pages(self):
        self.client.force_login(self.user)
        urls = [reverse('goals:list'), reverse('goals:create'), self.goal.get_absolute_url(),
                reverse('goals:update', args=[self.goal.pk]), reverse('gamification:achievements')]
        for url in urls:
            with self.subTest(url=url):
                audit(self, self.client.get(url))

    def test_back_office_pages(self):
        self.client.force_login(self.admin)
        urls = [reverse('gamification:badge_list'), reverse('gamification:badge_create'),
                reverse('gamification:badge_update', args=[self.badge.pk]), reverse('gamification:ledger'),
                reverse('gamification:adjust')]
        for url in urls:
            with self.subTest(url=url):
                audit(self, self.client.get(url))

    def test_locked_badge_progress_is_exposed_to_screen_readers(self):
        self.client.force_login(self.user)
        html = self.client.get(reverse('gamification:achievements')).content.decode()
        self.assertIn('role="progressbar"', html)
        self.assertIn('(verrouillé)', html)

    def test_invalid_form_marks_fields_and_links_errors(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('goals:create'), {'title': '', 'target_value': 0})
        html = response.content.decode()
        self.assertIn('aria-invalid="true"', html)
        self.assertIn('id="id_title_errors"', html)
        self.assertIn('aria-describedby="id_title_errors"', html)
        audit(self, response)

    def test_required_fields_are_announced_and_help_text_is_linked(self):
        self.client.force_login(self.user)
        html = self.client.get(reverse('goals:create')).content.decode()
        self.assertIn('aria-required="true"', html)
        self.assertIn('aria-describedby="id_current_progress_helptext"', html)

    def test_skip_link_and_focusable_main(self):
        self.client.force_login(self.user)
        html = self.client.get(reverse('goals:list')).content.decode()
        self.assertIn('class="skip-link" href="#main"', html)
        self.assertIn('id="main" tabindex="-1"', html)

    def test_coach_widget_is_a_live_region_with_labelled_controls(self):
        self.client.force_login(self.user)
        html = self.client.get(self.goal.get_absolute_url()).content.decode()
        self.assertIn('role="status" aria-live="polite"', html)
        self.assertIn('aria-describedby="coach-note"', html)
        self.assertIn('aria-pressed=', html)
