const { contextBridge } = require('electron')

contextBridge.exposeInMainWorld('zimonDesktop', {
  isDesktop: true,
})
