"""Offline discovery contract checks; never launches Orca or model workers."""
import unittest
from orca_skills import discover, synchronize


class DiscoveryTests(unittest.TestCase):
    def probe(self, topics, selected=(), guides=None):
        calls = []
        def read(args):
            calls.append(args)
            if args == ['--version']:
                return 'test-version'
            if args == ['skills', 'list', '--json']:
                return {'topics': topics}
            name = args[2]
            return (guides or {}).get(name, {'name': name, 'markdown': '# Guide ' + name})
        return discover(read, selected), calls

    def test_new_topic_needs_no_code_change(self):
        result, calls = self.probe([{'name': 'future-skill', 'description': 'New capability'}], ['future-skill'])
        self.assertEqual(result['selected'][0]['name'], 'future-skill')
        self.assertEqual(len(calls), 3)
        self.assertFalse(result['execution_verified'])

    def test_catalog_does_not_load_every_guide(self):
        result, calls = self.probe([{'name': 'orca-cli', 'description': 'Workspace'}])
        self.assertEqual(result['selected'], [])
        self.assertEqual(len(calls), 2)

    def test_known_alias_is_deduplicated_only_with_target_present(self):
        topics = [{'name': n, 'description': n} for n in ['linear-tickets', 'orca-linear']]
        result, calls = self.probe(topics, ['linear-tickets', 'orca-linear'])
        self.assertEqual(result['aliases'], {'linear-tickets': 'orca-linear'})
        self.assertEqual(len(result['selected']), 1)
        self.assertEqual(calls[-1][2], 'orca-linear')
        result, _ = self.probe(topics[:1], ['linear-tickets'])
        self.assertEqual(result['aliases'], {})
        self.assertEqual(result['selected'][0]['name'], 'linear-tickets')

    def test_missing_selection_does_not_fetch_any_guide(self):
        calls = []
        def read(args):
            calls.append(args)
            return 'v' if args == ['--version'] else {'topics': [{'name': 'ok', 'description': 'ok'}]}
        with self.assertRaisesRegex(ValueError, 'TOPIC_NOT_LISTED'):
            discover(read, ['ok', 'missing'])
        self.assertEqual(len(calls), 2)

    def test_bad_catalog_rejected(self):
        for topics in [None, [], [{'name': '--help', 'description': 'x'}],
                       [{'name': 'ok', 'description': 4}],
                       [{'name': 'ok', 'description': 'x'}] * 2]:
            with self.subTest(topics=topics), self.assertRaises(ValueError):
                self.probe(topics)

    def test_invalid_guide_is_not_loaded(self):
        for guide in [{'name': 'other', 'markdown': 'text'}, {'name': 'ok', 'markdown': ''},
                      {'name': 'ok', 'markdown': '  '}, {'name': 'ok', 'markdown': 5}]:
            with self.subTest(guide=guide), self.assertRaisesRegex(ValueError, 'GUIDE_INVALID'):
                self.probe([{'name': 'ok', 'description': 'x'}], ['ok'], {'ok': guide})

    def test_read_failure_propagates_without_retry(self):
        calls = []
        def read(args):
            calls.append(args)
            raise RuntimeError('unavailable')
        with self.assertRaises(RuntimeError):
            discover(read, [])
        self.assertEqual(len(calls), 1)


class SyncTests(unittest.TestCase):
    @staticmethod
    def plan(kind='keep'):
        return {'executed': False, 'scope': 'global', 'planDigest': 'digest',
                'plan': {'skills': [{'name': 'orca-cli', 'ops': [{'kind': kind}]}]}}

    def test_current_install_never_writes(self):
        calls = []
        def read(args):
            calls.append(args)
            return self.plan()
        self.assertEqual(synchronize(read)['status'], 'current')
        self.assertEqual(calls, [['skills', 'update', '--all', '--dry-run', '--json']])

    def test_update_uses_official_command_then_rechecks(self):
        calls = []
        replies = [self.plan('update'), {'executed': True, 'summary': {'ok': True,
                   'exitCode': 0, 'leftAloneCount': 0}}, self.plan()]
        def read(args):
            calls.append(args)
            return replies.pop(0)
        self.assertEqual(synchronize(read)['status'], 'updated')
        self.assertEqual(calls[1], ['skills', 'update', '--all', '--json'])
        self.assertEqual(calls[0], calls[2])
        self.assertTrue(all('--force' not in c and 'install' not in c for c in calls))

    def test_modified_copy_is_reported_not_forced(self):
        replies = [self.plan('skip'), {'executed': True, 'summary': {'ok': True,
                   'exitCode': 0, 'leftAloneCount': 1}}, self.plan('skip')]
        self.assertEqual(synchronize(lambda args: replies.pop(0))['status'], 'attention_required')

    def test_bad_preview_never_mutates(self):
        calls = []
        def read(args):
            calls.append(args)
            return {'plan': {'skills': []}}
        with self.assertRaisesRegex(ValueError, 'UPDATE_PLAN_INVALID'):
            synchronize(read)
        self.assertEqual(len(calls), 1)

    def test_failed_update_is_not_retried(self):
        calls = []
        def read(args):
            calls.append(args)
            return self.plan('update') if len(calls) == 1 else {'executed': True, 'summary': {'ok': False}}
        with self.assertRaisesRegex(ValueError, 'UPDATE_FAILED'):
            synchronize(read)
        self.assertEqual(len(calls), 2)

    def test_no_installed_skills_does_not_install(self):
        preview = self.plan()
        preview['plan']['skills'] = []
        calls = []
        def read(args):
            calls.append(args)
            return preview
        self.assertEqual(synchronize(read)['status'], 'nothing_installed')
        self.assertEqual(len(calls), 1)

    def test_success_receipt_with_remaining_drift_is_not_current(self):
        replies = [self.plan('update'), {'executed': True, 'summary': {'ok': True,
                   'exitCode': 0, 'leftAloneCount': 0}}, self.plan('update')]
        self.assertEqual(synchronize(lambda args: replies.pop(0))['status'], 'attention_required')


if __name__ == '__main__':
    unittest.main()
