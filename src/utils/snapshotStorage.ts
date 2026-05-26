/**
 * Snapshot Storage (P1-7)
 *
 * Manages ParameterSnapshots in localStorage under key 'qca-comparison-snapshots'.
 * Two slots: 'a' and 'b', enabling A/B comparison of analysis runs.
 */

import type { ParameterSnapshot } from '../types/qca';

const STORAGE_KEY = 'qca-comparison-snapshots';

interface SnapshotSlots {
  a: ParameterSnapshot | null;
  b: ParameterSnapshot | null;
}

function readSlots(): SnapshotSlots {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { a: null, b: null };
    const parsed = JSON.parse(raw);
    return {
      a: parsed.a ?? null,
      b: parsed.b ?? null,
    };
  } catch {
    return { a: null, b: null };
  }
}

function writeSlots(slots: SnapshotSlots): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(slots));
  } catch {
    // localStorage full or unavailable — silently skip
  }
}

/** Save a snapshot into slot 'a' or 'b'. */
export function saveSnapshot(
  label: 'a' | 'b',
  snapshot: ParameterSnapshot
): void {
  const slots = readSlots();
  slots[label] = snapshot;
  writeSlots(slots);
}

/** Load a snapshot from slot 'a' or 'b'. */
export function loadSnapshot(label: 'a' | 'b'): ParameterSnapshot | null {
  const slots = readSlots();
  return slots[label] ?? null;
}

/** Return metadata for all populated snapshots. */
export function listSnapshots(): Array<{
  label: 'a' | 'b';
  id: string;
  name: string;
  timestamp: string;
  conditionCount: number;
  caseCount: number;
}> {
  const slots = readSlots();
  const results: Array<{
    label: 'a' | 'b';
    id: string;
    name: string;
    timestamp: string;
    conditionCount: number;
    caseCount: number;
  }> = [];
  for (const label of ['a', 'b'] as const) {
    const snap = slots[label];
    if (snap) {
      results.push({
        label,
        id: snap.id,
        name: snap.name,
        timestamp: snap.timestamp,
        conditionCount: snap.conditionSet?.conditions?.length ?? 0,
        caseCount: snap.result?.fuzzy_data?.membership?.length ?? 0,
      });
    }
  }
  return results;
}

/** Remove a snapshot from the given slot. */
export function clearSnapshot(label: 'a' | 'b'): void {
  const slots = readSlots();
  slots[label] = null;
  writeSlots(slots);
}

/** Swap the two slots (A becomes B, B becomes A). */
export function swapSnapshots(): void {
  const slots = readSlots();
  const temp = slots.a;
  slots.a = slots.b;
  slots.b = temp;
  writeSlots(slots);
}
