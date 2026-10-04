import { existsSync, readFileSync, readdirSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const isText = (value) => typeof value === 'string' && value.trim().length > 0;

export function validateCases(skill, data) {
  const errors = [];
  if (Array.isArray(data)) {
    if (data.length === 0) return ['trigger cases must not be empty'];
    for (const [index, item] of data.entries()) {
      const prefix = `trigger case ${index}`;
      if (!item || typeof item !== 'object' || Array.isArray(item)) {
        errors.push(`${prefix}: expected object`);
        continue;
      }
      if (!isText(item.name)) errors.push(`${prefix}: name is required`);
      if (!isText(item.input) && !isText(item.user_input)) {
        errors.push(`${prefix}: input or user_input is required`);
      }
      if (item.expected_skill !== skill) errors.push(`${prefix}: expected_skill must be ${skill}`);
      if (item.must_contain !== undefined &&
          (!Array.isArray(item.must_contain) || item.must_contain.length === 0 ||
           !item.must_contain.every(isText))) {
        errors.push(`${prefix}: must_contain must have non-empty strings`);
      }
    }
    return errors;
  }

  if (!data || typeof data !== 'object' || data.skill !== skill ||
      !Array.isArray(data.cases) || data.cases.length === 0) {
    return ['unknown or invalid behavior schema: expected matching skill and non-empty cases'];
  }
  for (const [index, item] of data.cases.entries()) {
    const prefix = `behavior case ${index}`;
    if (!item || typeof item !== 'object' || !isText(item.id) || !isText(item.prompt)) {
      errors.push(`${prefix}: id and prompt are required`);
      continue;
    }
    if (!Array.isArray(item.assertions) || item.assertions.length === 0 ||
        !item.assertions.every((assertion) => assertion &&
          isText(assertion.id) && isText(assertion.text))) {
      errors.push(`${prefix}: assertions need non-empty id and text`);
    }
  }
  return errors;
}

export function validateRepository(root) {
  const skillsRoot = join(root, 'skills');
  const skillNames = readdirSync(skillsRoot, { withFileTypes: true })
    .filter((entry) => entry.isDirectory() && existsSync(join(skillsRoot, entry.name, 'SKILL.md')))
    .map((entry) => entry.name);
  if (skillNames.length === 0) return { skills: 0, covered: 0, trigger: 0, behavior: 0, missing: [], errors: ['no skills found'] };

  const result = { skills: skillNames.length, covered: 0, trigger: 0, behavior: 0, missing: [], errors: [] };
  for (const skill of skillNames) {
    const path = join(skillsRoot, skill, 'evals', 'cases.json');
    if (!existsSync(path)) {
      result.missing.push(skill);
      continue;
    }
    try {
      const data = JSON.parse(readFileSync(path, 'utf8'));
      result.covered += 1;
      if (Array.isArray(data)) result.trigger += 1;
      else result.behavior += 1;
      for (const error of validateCases(skill, data)) result.errors.push(`${skill}: ${error}`);
    } catch (error) {
      result.errors.push(`${skill}: ${error.message}`);
    }
  }
  return result;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
  const result = validateRepository(root);
  console.log(`eval schemas: ${result.covered}/${result.skills} covered (${result.trigger} trigger, ${result.behavior} behavior), ${result.missing.length} missing`);
  for (const error of result.errors) console.error(error);
  process.exitCode = result.errors.length ? 1 : 0;
}
