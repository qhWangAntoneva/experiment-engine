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

// ─── YAML Parser (reverse of conditionSetToYaml) ────────────────────────────

/**
 * Parse a YAML scalar value from a string.
 *
 * Handles:
 *   - quoted strings (single and double)
 *   - numeric literals (int and float)
 *   - boolean literals (true / false)
 *   - null / ~ literals
 *   - bare (unquoted) strings
 */
function parseYamlValue(value: string): unknown {
  const v = value.trim();
  if (v === '' || v === 'null' || v === '~') return null;
  if (v === 'true') return true;
  if (v === 'false') return false;
  // Numeric: optional minus, digits, optional dot + digits
  if (/^-?\d+(\.\d+)?$/.test(v)) {
    return v.includes('.') ? parseFloat(v) : parseInt(v, 10);
  }
  // Remove surrounding quotes
  if (v.length >= 2) {
    if ((v.startsWith('"') && v.endsWith('"')) || (v.startsWith("'") && v.endsWith("'"))) {
      return v.slice(1, -1);
    }
  }
  return v;
}

/**
 * Parse the `prototypes:` sub-block lines into a ConceptPrototype array.
 *
 * Expected structure (2-space indent):
 *   prototypes:
 *   - prototype_text: "..."     (indent = baseLevel)
 *     is_member: 1              (indent = baseLevel + 2)
 *     weight: 1.0               (indent = baseLevel + 2)
 */
function parsePrototypes(
  lines: string[],
  baseLevel: number,
): { prototypes: import('../types/qca').ConceptPrototype[]; consumed: number } {
  const prototypes: import('../types/qca').ConceptPrototype[] = [];
  let i = 0; // relative index within the sub-block
  const protoFieldIndent = baseLevel + 2;

  while (i < lines.length) {
    const raw = lines[i];
    const trimmed = raw.trimEnd();
    const stripped = trimmed.trimStart();
    const indent = trimmed.length - stripped.length;

    // Stop when we drop back to or above baseLevel
    if (indent <= baseLevel) break;

    // Array item start: "- prototype_text: ..."
    if (stripped.startsWith('- ')) {
      const content = stripped.slice(2); // remove "- "
      const colonIdx = content.indexOf(':');
      const proto: import('../types/qca').ConceptPrototype = {
        prototype_text:
          colonIdx >= 0 ? (parseYamlValue(content.slice(colonIdx + 1).trim()) as string) : '',
        is_member: 0,
        weight: 1.0,
      };

      // Consume sub-field lines at protoFieldIndent after the "- " line
      i++;
      while (i < lines.length) {
        const subRaw = lines[i];
        const subTrimmed = subRaw.trimEnd();
        const subStripped = subTrimmed.trimStart();
        const subIndent = subTrimmed.length - subStripped.length;

        if (subIndent < protoFieldIndent) break;
        if (subStripped === '' || subStripped.startsWith('#')) {
          i++;
          continue;
        }

        const subColon = subStripped.indexOf(':');
        if (subColon > 0) {
          const subKey = subStripped.slice(0, subColon).trim();
          const subVal = subStripped.slice(subColon + 1).trim();
          if (subVal !== '') {
            if (subKey === 'is_member') proto.is_member = parseYamlValue(subVal) as 0 | 1;
            else if (subKey === 'weight') proto.weight = parseYamlValue(subVal) as number;
          }
        }
        i++;
      }
      prototypes.push(proto);
      continue;
    }

    // Unknown line at prototype level — jump over silently
    i++;
  }

  return { prototypes, consumed: i };
}

/**
 * Parse `calibration_params:` sub-block lines into a CalibrationParams object.
 *
 * Expected structure (2-space indent relative to the header):
 *   calibration_params:
 *     threshold_full_in: 0.85   (indent = baseLevel + 2)
 *     threshold_full_out: 0.25
 *     crossover_point: 0.50
 *     direction: ascending
 *     steepness: 10.0           (optional)
 */
function parseCalibrationParams(
  lines: string[],
  baseLevel: number,
): { params: import('../types/qca').CalibrationParams | null; consumed: number } {
  const paramIndent = baseLevel + 2;
  const raw: Record<string, unknown> = {};
  let i = 0;

  while (i < lines.length) {
    const rawLine = lines[i];
    const trimmed = rawLine.trimEnd();
    const stripped = trimmed.trimStart();
    const indent = trimmed.length - stripped.length;

    if (indent < paramIndent) break;
    if (stripped === '' || stripped.startsWith('#')) {
      i++;
      continue;
    }

    const colonIdx = stripped.indexOf(':');
    if (colonIdx > 0) {
      const key = stripped.slice(0, colonIdx).trim();
      const value = stripped.slice(colonIdx + 1).trim();
      if (value !== '') {
        raw[key] = parseYamlValue(value);
      }
    }
    i++;
  }

  if (Object.keys(raw).length === 0) {
    return { params: null, consumed: i };
  }

  return {
    params: {
      threshold_full_in: raw.threshold_full_in as number,
      threshold_full_out: raw.threshold_full_out as number,
      crossover_point: raw.crossover_point as number,
      direction: raw.direction as 'ascending' | 'descending',
      steepness: raw.steepness as number | undefined,
    },
    consumed: i,
  };
}

/**
 * Parse a YAML string back into a ConditionSet object.
 *
 * This is the reverse of `conditionSetToYaml`. It handles the fixed 2-space
 * indent structure that `conditionSetToYaml` always produces, but is also
 * tolerant of the hand-written DEFAULT_CONDITION_SET_YAML format where
 * `- name:` items may appear at indent 2 instead of indent 0.
 *
 * No external YAML library is used — this is a hand-written parser for the
 * project's specific, constrained YAML schema.
 *
 * @param yaml - A YAML-formatted condition set string
 * @returns A fully populated ConditionSet object
 */
export function yamlToConditionSet(yaml: string): import('../types/qca').ConditionSet {
  const rawLines = yaml.replace(/^﻿/, '').split(/\r?\n/);

  // ── Phase 1: Collect top-level scalars ──────────────────────────────────
  //
  // While scanning, we also record the line index ranges for the `conditions:`
  // and `outcome:` sections so we can parse them independently later.

  const topScalars: Record<string, string> = {};
  let conditionsStart = -1;
  let conditionsEnd = -1;
  let outcomeStart = -1;
  let outcomeEnd = -1;
  let currentSection: 'none' | 'conditions' | 'outcome' = 'none';

  for (let i = 0; i < rawLines.length; i++) {
    const trimmed = rawLines[i].trimEnd();
    const stripped = trimmed.trimStart();
    const indent = trimmed.length - stripped.length;

    if (stripped === '' || stripped.startsWith('#')) continue;

    // ── Detect section boundaries by tracking indent-0 lines ──
    //
    // conditions: / outcome: are always at indent 0. Everything indented
    // below them belongs to the section. The first indent-0 line after
    // entering a section ends it.

    // Check for indent-0 markers that begin or end sections
    if (indent === 0) {
      // End the previous section if any
      if (currentSection === 'conditions') {
        conditionsEnd = i;
        currentSection = 'none';
      } else if (currentSection === 'outcome') {
        outcomeEnd = i;
        currentSection = 'none';
      }

      if (stripped === 'conditions:' || stripped.startsWith('conditions: ')) {
        currentSection = 'conditions';
        conditionsStart = i + 1; // content starts on the next line
        continue;
      }

      if (stripped === 'outcome:' || stripped.startsWith('outcome: ')) {
        currentSection = 'outcome';
        outcomeStart = i + 1;
        continue;
      }

      // Top-level scalar
      const colonIdx = stripped.indexOf(':');
      if (colonIdx > 0) {
        const key = stripped.slice(0, colonIdx).trim();
        const value = stripped.slice(colonIdx + 1).trim();
        if (value !== '') {
          topScalars[key] = value;
        }
      }
      continue;
    }

    // Lines with indent > 0 — they belong to the current section (if any).
    // We don't need to handle them here; they'll be parsed in Phase 2.
  }

  // Close any trailing section
  if (currentSection === 'conditions') conditionsEnd = rawLines.length;
  else if (currentSection === 'outcome') outcomeEnd = rawLines.length;

  // ── Phase 2: Parse scalars into typed values ────────────────────────────

  const parsedTop: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(topScalars)) {
    parsedTop[key] = parseYamlValue(value);
  }

  // ── Phase 3: Parse conditions section ───────────────────────────────────

  const conditions: import('../types/qca').ConditionDefinition[] = [];

  if (conditionsStart >= 0 && conditionsEnd > conditionsStart) {
    const condLines = rawLines.slice(conditionsStart, conditionsEnd);

    // Determine base indent: look for the first "- name:" line
    let baseIndent = -1;
    for (const line of condLines) {
      const trimmed = line.trimEnd();
      const stripped = trimmed.trimStart();
      if (stripped === '' || stripped.startsWith('#')) continue;
      if (stripped.startsWith('- ')) {
        baseIndent = trimmed.length - stripped.length;
        break;
      }
    }

    if (baseIndent >= 0) {
      let ci = 0; // cursor index into condLines

      while (ci < condLines.length) {
        // Skip empty / comment lines between conditions
        const trimmed = condLines[ci].trimEnd();
        const stripped = trimmed.trimStart();
        if (stripped === '' || stripped.startsWith('#')) {
          ci++;
          continue;
        }

        // Expect an array item: "- name: value"
        if (!stripped.startsWith('- ')) {
          ci++;
          continue;
        }

        const itemContent = stripped.slice(2);
        const firstColon = itemContent.indexOf(':');
        const condName =
          firstColon >= 0 ? (parseYamlValue(itemContent.slice(firstColon + 1).trim()) as string) : '';
        ci++;

        // Build the condition definition by consuming indented lines
        const cond: Record<string, unknown> = {
          name: condName,
          prototypes: [] as import('../types/qca').ConceptPrototype[],
          calibration_params: null,
        };

        while (ci < condLines.length) {
          const fieldTrimmed = condLines[ci].trimEnd();
          const fieldStripped = fieldTrimmed.trimStart();
          const lineIndent = fieldTrimmed.length - fieldStripped.length;

          // Stop at next array item or section exit
          if (lineIndent < baseIndent) break;
          if (lineIndent === baseIndent && fieldStripped.startsWith('- ')) break;
          if (lineIndent === 0) break;

          if (fieldStripped === '' || fieldStripped.startsWith('#')) {
            ci++;
            continue;
          }

          const colonIdx = fieldStripped.indexOf(':');
          if (colonIdx < 0) {
            ci++;
            continue;
          }

          const key = fieldStripped.slice(0, colonIdx).trim();
          const value = fieldStripped.slice(colonIdx + 1).trim();

          // ── prototypes sub-block ──
          if (key === 'prototypes') {
            if (value === '[]') {
              cond.prototypes = [];
              ci++;
              continue;
            }
            // Sub-block follows (value is empty, lines below are indented)
            ci++;
            const remaining = condLines.slice(ci);
            const result = parsePrototypes(remaining, lineIndent);
            cond.prototypes = result.prototypes;
            ci += result.consumed;
            continue;
          }

          // ── calibration_params sub-block ──
          if (key === 'calibration_params') {
            if (value === 'null' || value === '') {
              cond.calibration_params = null;
              ci++;
              // Skip any indented lines that were meant to be sub-fields but
              // aren't (edge case: "calibration_params:" with no fields)
              while (ci < condLines.length) {
                const nTrimmed = condLines[ci].trimEnd();
                const nStripped = nTrimmed.trimStart();
                const nIndent = nTrimmed.length - nStripped.length;
                if (nIndent <= lineIndent) break;
                ci++;
              }
              continue;
            }
            // Sub-block follows
            ci++;
            const remaining = condLines.slice(ci);
            const result = parseCalibrationParams(remaining, lineIndent);
            cond.calibration_params = result.params;
            ci += result.consumed;
            continue;
          }

          // ── Regular scalar field (only when value is present on same line) ──
          if (value !== '') {
            cond[key] = parseYamlValue(value);
          }
          ci++;
        }

        // Build a proper ConditionDefinition from the raw record
        const cd: import('../types/qca').ConditionDefinition = {
          name: (cond.name as string) || '',
          display_name: (cond.display_name as string) || (cond.name as string) || '',
          domain: (cond.domain as import('../types/qca').TextDomain) || 'dissatisfaction',
          calibration_type: (cond.calibration_type as import('../types/qca').CalibrationMethod) || 'direct',
          calibration_params: cond.calibration_params as import('../types/qca').CalibrationParams | null,
          description: (cond.description as string) || '',
          scoring_source: (cond.scoring_source as import('../types/qca').ScoringSource) || 'prototype',
          prototypes: (cond.prototypes as import('../types/qca').ConceptPrototype[]) || [],
          prototype_embeddings: null,
          embedding_model: null,
        };
        conditions.push(cd);
      }
    }
  }

  // ── Phase 4: Parse outcome section ──────────────────────────────────────

  let outcome: import('../types/qca').ConditionDefinition | null = null;

  if (outcomeStart >= 0 && outcomeEnd > outcomeStart) {
    const ocLines = rawLines.slice(outcomeStart, outcomeEnd);

    // Determine baseIndent for outcome: it's the indent of the first non-empty line
    let baseIndent = -1;
    for (const line of ocLines) {
      const trimmed = line.trimEnd();
      const stripped = trimmed.trimStart();
      if (stripped === '' || stripped.startsWith('#')) continue;
      // Lines with "key: value" start fields
      baseIndent = trimmed.length - stripped.length;
      break;
    }

    if (baseIndent >= 0) {
      const out: Record<string, unknown> = {
        prototypes: [] as import('../types/qca').ConceptPrototype[],
        calibration_params: null,
      };
      let oi = 0;

      while (oi < ocLines.length) {
        const trimmed = ocLines[oi].trimEnd();
        const stripped = trimmed.trimStart();
        const indent = trimmed.length - stripped.length;

        if (stripped === '' || stripped.startsWith('#')) {
          oi++;
          continue;
        }
        if (indent < baseIndent) break;
        if (indent === 0) break; // back to top level

        const colonIdx = stripped.indexOf(':');
        if (colonIdx < 0) {
          oi++;
          continue;
        }

        const key = stripped.slice(0, colonIdx).trim();
        const value = stripped.slice(colonIdx + 1).trim();

        if (key === 'prototypes') {
          if (value === '[]') {
            out.prototypes = [];
            oi++;
            continue;
          }
          oi++;
          const remaining = ocLines.slice(oi);
          const result = parsePrototypes(remaining, indent);
          out.prototypes = result.prototypes;
          oi += result.consumed;
          continue;
        }

        if (key === 'calibration_params') {
          if (value === 'null' || value === '') {
            out.calibration_params = null;
            oi++;
            while (oi < ocLines.length) {
              const nTrimmed = ocLines[oi].trimEnd();
              const nStripped = nTrimmed.trimStart();
              const nIndent = nTrimmed.length - nStripped.length;
              if (nIndent <= indent) break;
              oi++;
            }
            continue;
          }
          oi++;
          const remaining = ocLines.slice(oi);
          const result = parseCalibrationParams(remaining, indent);
          out.calibration_params = result.params;
          oi += result.consumed;
          continue;
        }

        if (value !== '') {
          out[key] = parseYamlValue(value);
        }
        oi++;
      }

      outcome = {
        name: (out.name as string) || '',
        display_name: (out.display_name as string) || (out.name as string) || '',
        domain: (out.domain as import('../types/qca').TextDomain) || 'dissatisfaction',
        calibration_type: (out.calibration_type as import('../types/qca').CalibrationMethod) || 'direct',
        calibration_params: out.calibration_params as import('../types/qca').CalibrationParams | null,
        description: (out.description as string) || '',
        scoring_source: (out.scoring_source as import('../types/qca').ScoringSource) || 'prototype',
        prototypes: (out.prototypes as import('../types/qca').ConceptPrototype[]) || [],
        prototype_embeddings: null,
        embedding_model: null,
      };
    }
  }

  // ── Phase 5: Assemble final ConditionSet ─────────────────────────────────

  return {
    name: (parsedTop.name as string) || '',
    description: (parsedTop.description as string) || '',
    domain: (parsedTop.domain as import('../types/qca').TextDomain) || 'dissatisfaction',
    scoring_source: (parsedTop.scoring_source as import('../types/qca').ScoringSource) || 'prototype',
    qca_variant: parsedTop.qca_variant as import('../types/qca').QCAVariant | undefined,
    conditions,
    outcome,
  };
}
