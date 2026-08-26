import logging
from typing import Callable, Any, Optional, Set
from PySide6.QtCore import QRunnable, QObject, Signal, Slot, QThreadPool

logger = logging.getLogger(__name__)

# Conjunto global para mantener referencias vivas a los workers activos
# Esto previene que el Garbage Collector de Python destruya los objetos QRunnable/QObject
# mientras se ejecutan en los hilos del QThreadPool, evitando Segmentation Faults.
_trabajadores_activos: Set['AsyncWorker'] = set()

class WorkerSignals(QObject):
    started = Signal()
    finished = Signal()
    error = Signal(str)
    result = Signal(object)

class AsyncWorker(QRunnable):
    """
    Ejecutor QRunnable seguro para tareas en segundo plano.
    Mantiene referencias vivas a sus señales durante todo su ciclo de vida.
    """
    def __init__(self, fn: Callable, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self.setAutoDelete(True)

    @Slot()
    def run(self) -> None:
        try:
            self.signals.started.emit()
        except Exception:
            pass

        try:
            res = self.fn(*self.args, **self.kwargs)
            try:
                self.signals.result.emit(res)
            except Exception:
                pass
        except Exception as e:
            logger.exception("Error en tarea en segundo plano (%s)", getattr(self.fn, "__qualname__", self.fn))
            try:
                self.signals.error.emit(str(e))
            except Exception:
                pass
        finally:
            try:
                self.signals.finished.emit()
            except Exception:
                pass

def ejecutar_en_segundo_plano(
    fn: Callable,
    on_result: Optional[Callable[[Any], None]] = None,
    on_error: Optional[Callable[[str], None]] = None,
    on_finished: Optional[Callable[[], None]] = None,
    *args,
    **kwargs
) -> AsyncWorker:
    """
    Lanza una tarea asíncrona en el QThreadPool de forma 100% segura contra GC.
    """
    worker = AsyncWorker(fn, *args, **kwargs)
    _trabajadores_activos.add(worker)

    def _cleanup():
        _trabajadores_activos.discard(worker)
        if on_finished:
            try:
                on_finished()
            except Exception:
                pass

    if on_result:
        worker.signals.result.connect(on_result)
    if on_error:
        worker.signals.error.connect(on_error)
    
    worker.signals.finished.connect(_cleanup)
    QThreadPool.globalInstance().start(worker)
    return worker
