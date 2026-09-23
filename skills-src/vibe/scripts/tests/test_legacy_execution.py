"""Legacy provider entrypoints cannot bypass the central budget/dispatch store."""
import contextlib
import importlib
import io
import json
import pathlib
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

SCRIPTS = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
with patch('subprocess.Popen', side_effect=AssertionError('native import side effect forbidden')):
    routing = importlib.import_module('routing')
    evaluation = importlib.import_module('adversarial_eval')
BLOCKED = 'LEGACY_EXECUTION_DISABLED'


class LegacyExecutionTests(unittest.TestCase):
    def setUp(self):
        # Fail closed at process creation, including paths a test forgot to mock.
        # CLI integration explicitly uses the original Popen for a local Python child;
        # that child installs its own denial sentinel before importing the old CLI.
        self.local_popen = subprocess.Popen
        guard = patch('subprocess.Popen', side_effect=AssertionError('native process forbidden'))
        guard.start()
        self.addCleanup(guard.stop)

    def test_worker_dispatch_is_disabled_before_native_call(self):
        with patch('subprocess.run', return_value=subprocess.CompletedProcess([], 0, '', '')) as native:
            result = routing.run_dispatch('gpt-5.6-sol', 'high', 'task', 'node', 'current')
        native.assert_not_called()
        self.assertEqual(result[0], 2)
        self.assertEqual(result[1], '')
        self.assertIn(BLOCKED, result[2])

    def test_direct_codex_is_disabled_even_with_explicit_low_effort(self):
        with patch('subprocess.run', return_value=subprocess.CompletedProcess([], 0, '', '')) as native:
            result = routing.run_codex_exec('private prompt', effort='low')
        native.assert_not_called()
        self.assertEqual(result[0], 2)
        self.assertIn(BLOCKED, result[2])
        self.assertNotIn('private prompt', str(result))

    def test_validated_legacy_plan_cannot_send_or_invoke_task_callback(self):
        with patch.object(routing, 'validate_plan', return_value=(True, [], [])), \
                patch.object(routing, 'run_dispatch') as sender:
            result = routing.validate_and_dispatch([], lambda _: self.fail('callback'), 'current')
        sender.assert_not_called()
        self.assertFalse(result[0])
        self.assertIn(BLOCKED, result[2])

    def test_raw_orca_generation_and_unknown_commands_are_disabled(self):
        for args in [('orchestration', 'worker-start'), ('orchestration', 'task-create'),
                     ('orchestration', 'worker-retry'), ('orchestration', 'worker-stop'),
                     ('terminal', 'send'), ('status', 'orchestration', 'worker-start'),
                     ('unknown',), ('--instance', 'other', 'status'), ()]:
            with self.subTest(args=args), patch('subprocess.run', return_value=
                    subprocess.CompletedProcess([], 0, '', '')) as native:
                rc, out, error = routing.run_orca(*args)
                native.assert_not_called()
                self.assertEqual((rc, out), (2, ''))
                self.assertIn(BLOCKED, error)

    def test_raw_orca_retains_exact_read_only_inspection(self):
        for args in [('status',), ('account', 'list'), ('orchestration', 'worker-list'),
                     ('orchestration', 'worker-show', '--dispatch', 'd'),
                     ('orchestration', 'worker-read', '--dispatch', 'd')]:
            with self.subTest(args=args), patch('subprocess.run', return_value=
                    subprocess.CompletedProcess([], 0, 'ok', '')) as native:
                self.assertEqual(routing.run_orca(*args), (0, 'ok', ''))
                self.assertEqual(native.call_args.args[0], ['orca', *args])

    def test_invalid_worktree_probe_does_not_attempt_worker_start(self):
        with patch.object(routing, 'run_orca', return_value=(0, '{"ok":true}', '')) as native:
            with self.assertRaisesRegex(RuntimeError, BLOCKED):
                routing.probe_orca_efforts('task', 'codex', 'model', bad_worktree='current')
        native.assert_not_called()

    def test_evaluation_all_vendors_disabled(self):
        for lane, effort in [('claude-opus-5', 'standard'), ('gpt-6-astra', 'high'),
                             ('gemini-3.8-flash', 'medium'), ('grok-4.6', 'high')]:
            with self.subTest(lane=lane), patch('subprocess.run') as native:
                rc, out, error, elapsed = evaluation.run_lane(lane, effort, 'secret prompt', '.')
                native.assert_not_called()
                self.assertEqual((rc, out, elapsed), (2, '', 0.0))
                self.assertIn(BLOCKED, error)
                self.assertNotIn('secret prompt', error)

    def test_preflight_ignores_old_success_cache_and_never_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            cache = pathlib.Path(directory) / 'vendors.json'
            original = json.dumps({'at_epoch': 9999999999, 'vendors': {
                vendor: {'ok': True} for vendor in evaluation.ALL_VENDORS}}).encode()
            cache.write_bytes(original)
            with patch.object(evaluation, 'VENDOR_CACHE', str(cache)), \
                    patch.object(evaluation, 'STATE_DIR', directory), \
                    patch.object(evaluation, 'run_lane') as sender:
                for force in (False, True):
                    result = evaluation.preflight('.', force=force)
                    self.assertTrue(all(not item['ok'] for item in result.values()))
                    self.assertTrue(all(BLOCKED in item['note'] for item in result.values()))
                sender.assert_not_called()
            self.assertEqual(cache.read_bytes(), original)
            self.assertEqual(list(pathlib.Path(directory).iterdir()), [cache])

    def test_live_run_blocks_before_truth_commands_or_ledger(self):
        args = types.SimpleNamespace(repo='.', force=True, dry=False, only=None, seed=1, timeout=1)
        with patch.object(evaluation, 'load_probes') as probes, \
                patch.object(evaluation, 'preflight', return_value={}) as preflight, \
                patch.object(evaluation, 'ground_truth') as truth, \
                patch.object(evaluation, 'append_ledger') as ledger, \
                contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(evaluation.cmd_run(args), 2)
        probes.assert_not_called()
        preflight.assert_not_called()
        truth.assert_not_called()
        ledger.assert_not_called()
        self.assertIn(BLOCKED, output.getvalue())

    def test_cli_preflight_and_run_fail_without_provider_process(self):
        # Instrument the child before importing the CLI: safe even against old code.
        program = """import sys, subprocess
sys.path.insert(0, sys.argv.pop(1))
def no_native(*a, **k):
    print('UNGUARDED_NATIVE_CALL')
    raise RuntimeError('test provider sentinel')
subprocess.run = no_native
subprocess.Popen = no_native
import adversarial_eval
sys.exit(adversarial_eval.main())
"""
        for flags in [('--preflight',), ('--preflight', '--force'), ('--run', '--force')]:
            with self.subTest(flags=flags), tempfile.TemporaryDirectory() as directory:
                child = program.replace('import adversarial_eval\n',
                    'import adversarial_eval\nadversarial_eval.STATE_DIR = ' + repr(directory) +
                    '\nadversarial_eval.VENDOR_CACHE = ' + repr(directory + '/cache.json') + '\n')
                with patch('subprocess.Popen', self.local_popen):
                    result = subprocess.run([sys.executable, '-B', '-X', 'utf8', '-c', child,
                                             str(SCRIPTS), *flags, '--repo', directory],
                                            capture_output=True, text=True, encoding='utf-8', timeout=30)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertIn(BLOCKED, result.stdout)
                self.assertNotIn('UNGUARDED_NATIVE_CALL', result.stdout)
                self.assertEqual(list(pathlib.Path(directory).iterdir()), [])

    def test_dry_builders_still_work_without_native_execution(self):
        with patch('subprocess.run') as native:
            self.assertEqual(routing.run_codex_exec('prompt', dry=True)[0], 0)
            self.assertEqual(routing.run_dispatch('gpt-5.6-sol', 'high', 't', 'n', 'current', dry=True)[0], 0)
            result = evaluation.run_lane('grok-4.6', 'high', 'prompt', '.', dry=True)
            self.assertEqual(result[0], 0)
            self.assertIn('DRY-', result[1])
            self.assertTrue(all(item['note'] == 'dry' for item in evaluation.preflight('.', dry=True).values()))
        native.assert_not_called()

    def test_intake_does_not_reuse_legacy_success_cache(self):
        intake = importlib.import_module('make_intake')
        with patch('builtins.open') as reader:
            result = intake.read_live(now=123)
        reader.assert_not_called()
        self.assertTrue(result['stale'])
        self.assertEqual(result['vendors'], {})

    def test_raw_orca_options_do_not_expand_read_grammar(self):
        for args in [('status', '--json', '--json'), ('status', '--exec', 'x'),
                     ('orchestration', 'worker-list', '--watch'),
                     ('orchestration', 'worker-show', '--dispatch', '--run'),
                     ('orchestration', 'worker-read', '--dispatch', 'a;echo x'),
                     ('orchestration', 'worker-read', '--dispatch', 'd', '--exec', 'x')]:
            with self.subTest(args=args), patch('subprocess.run') as native:
                self.assertEqual(routing.run_orca(*args)[0], 2)
                native.assert_not_called()

    def test_probe_cli_blocks_even_without_task_and_invalid_lane(self):
        with contextlib.redirect_stdout(io.StringIO()) as output, patch('subprocess.run') as native:
            for args in [[], ['--task', 't'], ['--task', 't', '--lane', 'not-a-model']]:
                self.assertEqual(routing._cli_probe(args), 2)
        native.assert_not_called()
        self.assertIn(BLOCKED, output.getvalue())

    def test_generated_intake_routes_to_central_contract_not_live_wrappers(self):
        intake = importlib.import_module('make_intake')
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(intake, 'orca', return_value=None), \
                patch.object(intake.ledger, 'collect_decisions', return_value=([], [])), \
                patch.object(intake.ledger, 'unmerged_runs', return_value=[]), \
                patch.object(intake.ledger, 'read_ledger', return_value=([], [])), \
                contextlib.redirect_stdout(io.StringIO()):
            target = pathlib.Path(directory) / 'intake.html'
            intake.main(out_path=str(target), argv=['make_intake.py'])
            html = target.read_text(encoding='utf-8')
        self.assertIn('run_state.py', html)
        self.assertIn('execute_orca.py', html)
        self.assertIn('Grok HOLD', html)
        self.assertNotIn('routing.validate_and_dispatch()', html)
        self.assertNotIn('run_codex_exec', html)
        self.assertFalse('adversarial_eval.py --preflight 먼저' in html,
                         'Generated intake still recommends the disabled live preflight')
        self.assertFalse('안 건드리면 이대로 간다' in html)
        self.assertFalse('실호출 통과한 공정만' in html)
        self.assertTrue('탐색 보류 — 검증된 실행·비용 증거 없음' in html)
        self.assertTrue('추천 후보 0개' in html)

    def test_intake_orca_helper_cannot_bypass_quarantine(self):
        intake = importlib.import_module('make_intake')
        for args in [['orchestration', 'worker-start', '--task', 't', '--worktree', 'current',
                      '--agent', 'codex', '--model', 'gpt-6-astra', '--effort', 'high'],
                     ['repo', 'list', '--exec', 'x'], ['account', 'list', '--refresh'], []]:
            with self.subTest(args=args), patch('subprocess.run') as native:
                self.assertIsNone(intake.orca(args))
                native.assert_not_called()

    def test_intake_orca_preserves_only_its_two_read_calls(self):
        intake = importlib.import_module('make_intake')
        for args in [['repo', 'list'], ['account', 'list']]:
            with self.subTest(args=args), patch('subprocess.run', return_value=
                    subprocess.CompletedProcess([], 0, '{"ok":true,"result":{}}', '')) as native:
                self.assertEqual(intake.orca(args), {})
                self.assertEqual(native.call_args.args[0], ['orca', *args, '--json'])

    def test_orca_json_block_and_read_compatibility(self):
        with patch('subprocess.run') as native:
            ok, error = routing.run_orca_json('orchestration', 'worker-stop', '--dispatch', 'd')
            self.assertFalse(ok)
            self.assertEqual(error['rc'], 2)
            native.assert_not_called()
        with patch('subprocess.run', return_value=subprocess.CompletedProcess(
                [], 0, '{"ok":true,"result":{"workers":[]}}', '')) as native:
            self.assertEqual(routing.run_orca_json('orchestration', 'worker-list', '--json'),
                             (True, {'workers': []}))
            self.assertEqual(native.call_args.args[0].count('--json'), 1)


if __name__ == '__main__':
    unittest.main()
