from subprocess import Popen    
from psutil import process_iter
from pywinauto import Application
from time import sleep


def isRunning(PROCNAME: str):
    """
    Viene preso il pid di un processo per poter attendere 
    che l'applicazione venga chiusa prima di poter proseguire
    con il programma. Viene impostato un timeout di 86400 secondi (24 ore).

    Args:
        PROCNAME (str): il nome del processo.
    """

    sleep(1)
    pid = 0
    for proc in process_iter():
        if proc.name() == PROCNAME:
            pid = proc.pid
    app = Application().connect(process=pid)
    app.wait_for_process_exit(timeout=86400)


def winOpen(processo, comando):
    """
    Viene eseguito il comando per aprire un'applicazione
    su Windows.
    """
    Popen(['powershell.exe', comando])
    isRunning(processo)