import logging
from typing import List, Optional

from PySide6.QtCore import QObject, Signal
from PySide6.QtNetwork import QLocalServer, QLocalSocket

logger = logging.getLogger(__name__)

SOCKET_NAME = "caelum_single_instance_ipc"


class GestorInstanciaUnica(QObject):
    """
    Garantiza que solo exista una instancia en ejecución de Caelum.
    Usa QLocalServer / QLocalSocket para comunicación entre procesos (IPC).
    Si se detecta una instancia previa, le solicita restaurar y enfocar la ventana.
    """
    solicitud_activacion = Signal()

    def __init__(self, nombre_socket: str = SOCKET_NAME, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.nombre_socket = nombre_socket
        self.servidor: Optional[QLocalServer] = None
        self._sockets_clientes: List[QLocalSocket] = []

    def es_otra_instancia_activa(self) -> bool:
        """
        Intenta conectarse a un servidor local existente.
        Si la conexión tiene éxito, significa que ya hay una instancia corriendo.
        """
        socket = QLocalSocket(self)
        socket.connectToServer(self.nombre_socket)
        if socket.waitForConnected(500):
            logger.info("Instancia previa detectada. Enviando señal para restaurar ventana...")
            socket.write(b"SHOW\n")
            socket.flush()
            socket.waitForBytesWritten(500)
            socket.disconnectFromServer()
            if socket.state() != QLocalSocket.LocalSocketState.UnconnectedState:
                socket.waitForDisconnected(500)
            return True
        return False

    def iniciar_servidor(self) -> bool:
        """Inicia el servidor local para escuchar llamadas de nuevas instancias."""
        QLocalServer.removeServer(self.nombre_socket)

        self.servidor = QLocalServer(self)
        self.servidor.newConnection.connect(self._on_nueva_conexion)

        if not self.servidor.listen(self.nombre_socket):
            logger.warning("No se pudo iniciar QLocalServer en %s: %s", self.nombre_socket, self.servidor.errorString())
            return False

        logger.debug("Servidor de instancia única escuchando en %s", self.nombre_socket)
        return True

    def _on_nueva_conexion(self) -> None:
        if not self.servidor:
            return
        socket = self.servidor.nextPendingConnection()
        if not socket:
            return

        socket.setParent(self)
        self._sockets_clientes.append(socket)
        procesado = [False]

        def _procesar():
            if procesado[0]:
                return
            procesado[0] = True
            try:
                if socket in self._sockets_clientes:
                    self._sockets_clientes.remove(socket)
                self.solicitud_activacion.emit()
                socket.deleteLater()
            except Exception:
                pass

        socket.readyRead.connect(_procesar)
        socket.disconnected.connect(_procesar)
        if socket.bytesAvailable() > 0:
            _procesar()
