/**
 * Free Tour Ceylon frontend dev ports before starting concurrently.
 * Safe to run when nothing is listening — exits 0 either way.
 */
import { execSync } from 'node:child_process';

const PORTS = [5175, 5176, 5177, 5180, 5181, 5182];

function pidsOnPort(port) {
  try {
    const out = execSync(`netstat -ano | findstr :${port}`, {
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'ignore'],
    });
    const pids = new Set();
    for (const line of out.split(/\r?\n/)) {
      if (!/LISTENING/.test(line)) continue;
      const pid = line.trim().split(/\s+/).at(-1);
      if (pid && pid !== '0') pids.add(pid);
    }
    return [...pids];
  } catch {
    return [];
  }
}

for (const port of PORTS) {
  for (const pid of pidsOnPort(port)) {
    try {
      execSync(`taskkill /PID ${pid} /F`, { stdio: 'ignore' });
      console.log(`[free-dev-ports] freed ${port} (PID ${pid})`);
    } catch {
      // Process may have already exited.
    }
  }
}
