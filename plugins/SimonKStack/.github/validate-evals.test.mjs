import test from 'node:test';
import assert from 'node:assert/strict';
import { validateCases } from './validate-evals.mjs';

test('accepts behavior assertions without running a model', () => {
  const data = {
    skill: 'example',
    cases: [{
      id: 'case-1',
      prompt: 'Explain the workflow',
      assertions: [{ id: 'a-1', text: 'Names the prerequisite' }],
    }],
  };
  assert.deepEqual(validateCases('example', data), []);
});

test('accepts legacy trigger cases and preserves their intent', () => {
  const data = [{
    name: 'trigger-example',
    input: 'Build an app',
    expected_skill: 'example',
    must_contain: ['plan'],
  }, {
    name: 'slash-example',
    user_input: '/example',
    expected_skill: 'example',
  }];
  assert.deepEqual(validateCases('example', data), []);
});

test('rejects mismatched trigger targets and empty expectations', () => {
  const data = [{ name: 'bad', input: 'do it', expected_skill: 'other', must_contain: [] }];
  assert.match(validateCases('example', data).join('\n'), /expected_skill/);
  assert.match(validateCases('example', data).join('\n'), /must_contain/);
});

test('rejects malformed behavior assertions and unknown schemas', () => {
  const invalidBehavior = { skill: 'example', cases: [{ id: 'a', prompt: 'x', assertions: [{}] }] };
  assert.match(validateCases('example', invalidBehavior).join('\n'), /assertions/);
  assert.match(validateCases('example', { unknown: true }).join('\n'), /schema/);
});
