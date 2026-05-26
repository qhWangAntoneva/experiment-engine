import type {
  ConditionSet,
  ConditionDefinition,
  ConceptPrototype,
  CalibrationParams,
} from '../types/qca';

/**
 * Check whether a YAML scalar value needs double-quoting.
 *
 * Quotes are required for:
 * - empty strings
 * - strings containing whitespace / spaces
 * - YAML-reserved keywords (true, false, null, yes, no, etc.)
 * - strings starting with YAML-special characters (brackets, braces, etc.)
 * - strings containing colon-space or hash-space sequences (ambiguous)
 * - strings with leading or trailing whitespace
 */
function yamlNeedsQuotes(s: string): boolean {
  if (s.length === 0) return true;
  // Contains any whitespace (spaces, tabs, etc.)
  if (/\s/.test(s)) return true;
  // YAML-reserved bare words
  if (/^(true|false|yes|no|on|off|null|undefined|~)$/i.test(s)) return true;
  // Starts with a YAML-special character
  if (
    /^[\[\]\{\},&\*\?!|>'%@`#\d]/.test(s)
  )
    return true;
  // Contains colon-space (ambiguous key-value) or hash-space (comment)
  if (s.includes(': ') || s.includes(' #')) return true;
  // Leading or trailing whitespace (already checked above, but belt-and-suspenders)
  if (s !== s.trim()) return true;
  return false;
}

/**
 * Format a string for YAML output.
 *
 * Escapes backslashes and double quotes, then wraps in double quotes
 * if the value would otherwise be ambiguous in YAML.
 */
function yamlStr(s: string): string {
  if (yamlNeedsQuotes(s)) {
    const escaped = s.replace(/\\/g, '\\\\').replace(/"/g, '\\"');
    return `"${escaped}"`;
  }
  return s;
}

/**
 * Write a ConditionDefinition's body fields (everything after the leading
 * name line) to the lines array at the given indentation level.
 */
function writeConditionBody(
  lines: string[],
  cond: ConditionDefinition,
  indent: number,
): void {
  // ── Scalar fields ────────────────────────────────────────────────────
  lines.push(
    `${' '.repeat(indent)}display_name: ${yamlStr(cond.display_name)}`,
  );
  lines.push(`${' '.repeat(indent)}domain: ${yamlStr(cond.domain)}`);
  lines.push(
    `${' '.repeat(indent)}calibration_type: ${yamlStr(cond.calibration_type)}`,
  );
  lines.push(
    `${' '.repeat(indent)}description: ${yamlStr(cond.description)}`,
  );
  lines.push(
    `${' '.repeat(indent)}scoring_source: ${yamlStr(cond.scoring_source)}`,
  );

  // ── Prototypes ──────────────────────────────────────────────────────
  if (cond.prototypes.length === 0) {
    lines.push(`${' '.repeat(indent)}prototypes: []`);
  } else {
    lines.push(`${' '.repeat(indent)}prototypes:`);
    for (const p of cond.prototypes) {
      lines.push(
        `${' '.repeat(indent)}- prototype_text: ${yamlStr(p.prototype_text)}`,
      );
      lines.push(`${' '.repeat(indent + 2)}is_member: ${p.is_member}`);
      lines.push(`${' '.repeat(indent + 2)}weight: ${String(p.weight)}`);
    }
  }

  // ── Calibration params ──────────────────────────────────────────────
  if (
    cond.calibration_params === null ||
    cond.calibration_params === undefined
  ) {
    lines.push(`${' '.repeat(indent)}calibration_params: null`);
  } else {
    const cp = cond.calibration_params;
    lines.push(`${' '.repeat(indent)}calibration_params:`);
    lines.push(
      `${' '.repeat(indent + 2)}threshold_full_in: ${String(
        cp.threshold_full_in,
      )}`,
    );
    lines.push(
      `${' '.repeat(indent + 2)}threshold_full_out: ${String(
        cp.threshold_full_out,
      )}`,
    );
    lines.push(
      `${' '.repeat(indent + 2)}crossover_point: ${String(
        cp.crossover_point,
      )}`,
    );
    lines.push(
      `${' '.repeat(indent + 2)}direction: ${cp.direction}`,
    );
    if (cp.steepness !== undefined) {
      lines.push(
        `${' '.repeat(indent + 2)}steepness: ${String(cp.steepness)}`,
      );
    }
  }
}

/**
 * Convert a ConditionSet to a manually formatted YAML string.
 *
 * The output mirrors the structure of the fixture YAML files in
 * tests/fixtures/condset_*.yaml with 2-space indentation and
 * controlled double-quoting of ambiguous values.
 *
 * This function does **not** use js-yaml's `dump()` internally because
 * manual formatting gives precise control over field order, indentation,
 * and quoting conventions.
 *
 * @param cs - The condition set to serialize
 * @returns A YAML-formatted string terminated by a single newline
 */
export function conditionSetToYaml(cs: ConditionSet): string {
  const lines: string[] = [];

  // ── Header ────────────────────────────────────────────────────────────
  lines.push('# QCA Condition Set Definition');
  lines.push('');
  lines.push(`name: ${yamlStr(cs.name)}`);
  lines.push(`description: ${yamlStr(cs.description)}`);
  lines.push(`domain: ${yamlStr(cs.domain)}`);
  lines.push(`scoring_source: ${yamlStr(cs.scoring_source)}`);
  if (cs.qca_variant) {
    lines.push(`qca_variant: ${yamlStr(cs.qca_variant)}`);
  }
  lines.push('');

  // ── Causal conditions ─────────────────────────────────────────────────
  lines.push('conditions:');
  for (const cond of cs.conditions) {
    lines.push(`- name: ${yamlStr(cond.name)}`);
    writeConditionBody(lines, cond, 2);
  }

  // ── Outcome ───────────────────────────────────────────────────────────
  if (cs.outcome) {
    lines.push('');
    lines.push('outcome:');
    lines.push(`  name: ${yamlStr(cs.outcome.name)}`);
    writeConditionBody(lines, cs.outcome, 2);
  }

  return lines.join('\n') + '\n';
}
