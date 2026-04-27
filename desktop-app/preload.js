const { contextBridge, ipcRenderer, webUtils } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  getPathForFile: (file) => webUtils.getPathForFile(file),
  showSaveDialog: (defaultPath) => ipcRenderer.invoke('show-save-dialog', defaultPath),
  convertPDF: (inputPath, outputPath) => ipcRenderer.invoke('convert-pdf', inputPath, outputPath),
  onConvertLog: (callback) => ipcRenderer.on('convert-log', (event, msg) => callback(msg)),
  removeConvertLogListener: () => ipcRenderer.removeAllListeners('convert-log')
});
