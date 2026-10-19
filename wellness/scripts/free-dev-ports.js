/**
 * Free Tour Ceylon dev ports before starting all frontends together.
 * Stale Vite processes otherwise collide and break `npm run dev`.
 */
import { execSync } from 'child_process';

const PORTS = [5174, 5175, 5176, 5180, 5181, 5182];

function freePortWindows(port) {
  let out = '';
  try {
    out = execSync(`netstat -ano | findstr ":${port}"`, { encoding: 'utf8', stdio: ['pipe', 'pipe', 'ignore'] });
  } catch {
    return;
  }

  const pids = new Set();
  for (const line of out.split(/\r?\n/)) {
    if (!line.includes('LISTENING')) continue;
    const match = line.match(new RegExp(`:${port}\\s+\\S+\\s+LISTENING\\s+(\\d+)`));
    if (match) pids.add(match[1]);
  }

  for (const pid of pids) {
    if (pid === '0') continue;
    try {
      execSync(`taskkill /PID ${pid} /F`, { stdio: 'ignore' });
      console.log(`[free-dev-ports] Stopped PID ${pid} on port ${port}`);
    } catch {
      /* process may have already exited */
    }
  }
}

function freePortUnix(port) {
  try {
    execSync(`lsof -ti tcp:${port} | xargs -r kill -9`, { stdio: 'ignore', shell: true });
    console.log(`[free-dev-ports] Freed port ${port}`);
  } catch {
    /* nothing listening */
  }
}

for (const port of PORTS) {
  if (process.platform === 'win32') {
    freePortWindows(port);
  } else {
    freePortUnix(port);
  }
}
