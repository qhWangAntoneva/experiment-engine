/**
 * React hook wrapping the Pyodide bridge singleton.
 *
 * Provides:
 *   - initState: current worker/loading status
 *   - bridge: the bridge instance (for calling calibrate/analyze/etc.)
 *   - logs: worker log stream
 *   - init(): trigger or await initialization
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import {
  getPyodideBridge,
  type PyodideInitState,
  type PyodideBridge,
  type WorkerLogEntry,
} from '../services/pyodide';

interface UsePyodideReturn {
  initState: PyodideInitState;
  bridge: PyodideBridge;
  logs: WorkerLogEntry[];
  init: (packages?: string[]) => Promise<void>;
  clearLogs: () => void;
}

export function usePyodide(maxLogEntries = 200): UsePyodideReturn {
  const bridge = getPyodideBridge();
  const [initState, setInitState] = useState<PyodideInitState>(
    bridge.getInitState
  );
  const [logs, setLogs] = useState<WorkerLogEntry[]>([]);
  const logsRef = useRef<WorkerLogEntry[]>([]);

  useEffect(() => {
    const unsubInit = bridge.onInitChange(setInitState);
    const unsubLog = bridge.onLog((entry) => {
      logsRef.current = [...logsRef.current, entry].slice(-maxLogEntries);
      setLogs(logsRef.current);
    });

    return () => {
      unsubInit();
      unsubLog();
    };
  }, [bridge, maxLogEntries]);

  const init = useCallback(
    async (packages: string[] = []) => {
      await bridge.init(packages);
    },
    [bridge]
  );

  const clearLogs = useCallback(() => {
    logsRef.current = [];
    setLogs([]);
  }, []);

  return { initState, bridge, logs, init, clearLogs };
}
