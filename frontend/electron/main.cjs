const { app, BrowserWindow, dialog } = require('electron')
const path = require('path')
const http = require('http')
const fs = require('fs')
const { spawn, execFile } = require('child_process')

const STATIC_PORT = 5180
const VITE_DEV_URL = 'http://127.0.0.1:5173'

/** @type {import('http').Server | null} */
let staticServer = null
/** @type {import('child_process').ChildProcess | null} */
let apiProcess = null

function isDev() {
  return !app.isPackaged
}

function getRepoRoot() {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, 'zimon-repo')
  }
  return path.resolve(__dirname, '..', '..')
}

function getDistDir() {
  return path.join(app.isPackaged ? app.getAppPath() : path.join(__dirname, '..'), 'dist')
}

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
  '.woff2': 'font/woff2',
  '.woff': 'font/woff',
  '.ttf': 'font/ttf',
  '.map': 'application/json',
  '.webmanifest': 'application/manifest+json',
}

/**
 * @param {string} root
 * @param {number} port
 * @returns {Promise<import('http').Server>}
 */
function startStaticServer(root, port) {
  return new Promise((resolve, reject) => {
    const server = http.createServer((req, res) => {
      if (req.method !== 'GET' && req.method !== 'HEAD') {
        res.statusCode = 405
        res.end()
        return
      }
      const raw = decodeURIComponent((req.url || '/').split('?')[0])
      const rel = raw === '/' ? 'index.html' : raw.replace(/^\//, '')
      const candidate = path.resolve(path.join(root, rel))
      const rootResolved = path.resolve(root)
      if (candidate !== rootResolved && !candidate.startsWith(rootResolved + path.sep)) {
        res.statusCode = 403
        res.end()
        return
      }

      const send = (filePath) => {
        const ext = path.extname(filePath).toLowerCase()
        fs.readFile(filePath, (err, data) => {
          if (err) {
            const indexPath = path.join(root, 'index.html')
            if (filePath !== indexPath) {
              fs.readFile(indexPath, (e2, html) => {
                if (e2) {
                  res.statusCode = 404
                  res.end('Not found')
                  return
                }
                res.setHeader('Content-Type', MIME['.html'])
                res.end(req.method === 'HEAD' ? undefined : html)
              })
              return
            }
            res.statusCode = 404
            res.end('Not found')
            return
          }
          res.setHeader('Content-Type', MIME[ext] || 'application/octet-stream')
          res.end(req.method === 'HEAD' ? undefined : data)
        })
      }

      fs.stat(candidate, (err, st) => {
        if (!err && st.isFile()) {
          send(candidate)
          return
        }
        send(path.join(root, 'index.html'))
      })
    })

    server.on('error', reject)
    server.listen(port, '127.0.0.1', () => {
      staticServer = server
      resolve(server)
    })
  })
}

function stopStaticServer() {
  return new Promise((resolve) => {
    if (!staticServer) {
      resolve()
      return
    }
    staticServer.close(() => {
      staticServer = null
      resolve()
    })
  })
}

function startApiProcess() {
  if (process.env.ZIMON_SKIP_API_SPAWN === '1') return
  const repoRoot = getRepoRoot()
  const marker = path.join(repoRoot, 'backend', 'api', 'main.py')
  if (!fs.existsSync(marker)) {
    console.warn('[ZIMON] Backend not found at', repoRoot, '- start the API manually.')
    return
  }
  const py = process.env.ZIMON_PYTHON || 'python'
  const hide =
    process.platform === 'win32' && process.env.ZIMON_API_SHOW_CONSOLE !== '1'
  apiProcess = spawn(py, ['-m', 'backend.api'], {
    cwd: repoRoot,
    env: { ...process.env, PYTHONUNBUFFERED: '1' },
    stdio: 'ignore',
    windowsHide: hide,
    shell: false,
  })
  apiProcess.on('error', (err) => {
    console.error('[ZIMON] Failed to start API:', err.message)
    void dialog.showMessageBox({
      type: 'warning',
      title: 'ZIMON',
      message: 'Could not start the API automatically.',
      detail:
        'Install Python and dependencies, then run from the repo root:\n' +
        '  python -m backend.api\n\n' +
        'Or set ZIMON_SKIP_API_SPAWN=1 and start the API yourself.',
    })
  })
  apiProcess.on('exit', (code, signal) => {
    if (signal === 'SIGTERM' || signal === 'SIGKILL') return
    if (code !== 0 && code !== null) {
      console.warn('[ZIMON] API process exited with code', code)
    }
  })
}

function stopApiProcess() {
  return new Promise((resolve) => {
    if (!apiProcess) {
      resolve()
      return
    }
    const p = apiProcess
    apiProcess = null
    if (process.platform === 'win32' && p.pid) {
      execFile('taskkill', ['/pid', String(p.pid), '/f', '/t'], () => resolve())
      return
    }
    try {
      p.kill('SIGTERM')
    } catch {
      /* ignore */
    }
    setTimeout(resolve, 400)
  })
}

async function createWindow() {
  const win = new BrowserWindow({
    width: 1280,
    height: 800,
    show: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
    },
  })

  if (isDev()) {
    await win.loadURL(VITE_DEV_URL)
    win.webContents.openDevTools({ mode: 'detach' })
  } else {
    const dist = getDistDir()
    if (!fs.existsSync(path.join(dist, 'index.html'))) {
      void dialog.showErrorBox(
        'ZIMON',
        'UI build missing (dist/index.html). Rebuild the app.',
      )
      app.quit()
      return
    }
    await startStaticServer(dist, STATIC_PORT)
    await win.loadURL(`http://127.0.0.1:${STATIC_PORT}`)
  }

  win.once('ready-to-show', () => win.show())
}

app.whenReady().then(async () => {
  startApiProcess()
  await createWindow()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) void createWindow()
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})

let exitCleanupStarted = false
let exitCleanupDone = false

app.on('before-quit', (e) => {
  if (exitCleanupDone) return
  e.preventDefault()
  if (exitCleanupStarted) return
  exitCleanupStarted = true
  void (async () => {
    await stopApiProcess()
    await stopStaticServer()
    exitCleanupDone = true
    app.exit(0)
  })()
})
