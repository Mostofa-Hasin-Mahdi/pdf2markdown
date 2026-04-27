const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

let mainWindow;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1000,
    height: 700,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    autoHideMenuBar: true,
    titleBarStyle: 'hiddenInset'
  });

  // In development, load the Next.js localhost server.
  // In production, load the statically exported Next.js HTML files.
  const isDev = process.env.NODE_ENV !== 'production' && !app.isPackaged;
  
  if (isDev) {
    mainWindow.loadURL('http://localhost:3000');
    // mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, 'out/index.html'));
  }
}

app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// IPC handler to show save dialog
ipcMain.handle('show-save-dialog', async (event, defaultPath) => {
  const result = await dialog.showSaveDialog(mainWindow, {
    defaultPath: defaultPath,
    filters: [
      { name: 'Markdown', extensions: ['md'] }
    ]
  });
  return result.filePath;
});

// IPC handler to spawn the pdf2md.exe backend engine
ipcMain.handle('convert-pdf', async (event, inputPath, outputPath) => {
  return new Promise((resolve, reject) => {
    // Determine the path to the executable based on dev or prod environment
    const isDev = process.env.NODE_ENV !== 'production' && !app.isPackaged;
    
    // In dev, the exe is in the dist/ folder at the root
    // In prod, it will be bundled inside the app resources
    const exePath = isDev 
      ? path.join(__dirname, '..', 'dist', 'pdf2md.exe')
      : path.join(process.resourcesPath, 'pdf2md.exe');

    console.log(`Executing: ${exePath} "${inputPath}" "${outputPath}"`);
    
    // Check if exe exists
    if (!fs.existsSync(exePath)) {
      reject(`Executable not found at ${exePath}`);
      return;
    }

    const pythonProcess = spawn(exePath, [inputPath, outputPath]);
    
    let outputData = '';
    let errorData = '';

    // Stream logs back to the React UI in real-time
    pythonProcess.stdout.on('data', (data) => {
      const msg = data.toString();
      outputData += msg;
      console.log(msg);
      mainWindow.webContents.send('convert-log', msg);
    });

    pythonProcess.stderr.on('data', (data) => {
      errorData += data.toString();
      console.error(data.toString());
    });

    pythonProcess.on('close', (code) => {
      if (code === 0) {
        resolve({ success: true, output: outputData });
      } else {
        reject({ success: false, error: errorData });
      }
    });
  });
});
