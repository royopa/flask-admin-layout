DIM objShell
set objShell=wscript.createObject("wscript.shell")
iReturn=objShell.Run("start_server.bat", 0, TRUE)