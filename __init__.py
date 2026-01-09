"""
fldigi-py: Modern Python client for FLDIGI XML-RPC control
============================================================

A lightweight, type-documented wrapper for FLDIGI's XML-RPC interface.
Supports Python 3.7+. Covers all non-deprecated methods from the official
XML-RPC control page.

Quickstart:
from fldigi_py import Fldigi

radio = Fldigi(host="127.0.0.1", port=7362)
radio.add_tx("CQ CQ DE KM4YRI")
print(radio.frequency) # 14.074 MHz
radio.mode = "BPSK31"


FLDIGI XML-RPC Types:
6=bytes  A=list  b=bool  d=float  i=int  n=None  s=str  S=dict
"""

__version__ = "0.1.0.dev0"
__author__ = "LibertyFarmer & Perplexity AI"

from typing import Any, Dict, List, Optional, Union
import xmlrpc.client
from urllib.parse import urlparse


class FldigiError(Exception):
    """Base exception for fldigi-py errors."""
    pass


class FldigiXmlrpcError(FldigiError):
    """XML-RPC communication or protocol errors."""
    pass


class FldigiRigError(FldigiError):
    """Rig control errors."""
    pass


class FldigiModemError(FldigiError):
    """Modem configuration errors."""
    pass


class FldigiMainError(FldigiError):
    """Main application state errors."""
    pass


class NamespaceProxy:
    """Dynamic proxy for FLDIGI XML-RPC namespaces (main, rig, text, etc.)."""
    
    def __init__(self, client: 'Fldigi', namespace: str):
        self._client = client
        self._namespace = namespace
    
    def __getattr__(self, name: str) -> callable:
        def method(*args, **kwargs):
            return self._client._call(f"{self._namespace}.{name}", *args, **kwargs)
        return method


class Fldigi:
    """
    Modern Python client for FLDIGI XML-RPC control.
    
    Initialize with FLDIGI's XML-RPC server address (default: localhost:7362).
    
    Usage:
        radio = Fldigi(host="127.0.0.1", port=7362)
        radio.add_tx("CQ TEST")
        print(radio.rx_state)  # True/False
    """
    
    def __init__(self, host: str = "127.0.0.1", port: int = 7362, timeout: float = 5.0):
        self._host = host
        self._port = port
        self._timeout = timeout
        self._server = None
        self._connect()
    
    def _connect(self):
        """Connect to FLDIGI XML-RPC server."""
        url = f"http://{self._host}:{self._port}"
        try:
            self._server = xmlrpc.client.ServerProxy(url, timeout=self._timeout)
        except Exception as e:
            raise FldigiXmlrpcError(f"Failed to connect to FLDIGI at {url}: {e}")
    
    def _call(self, method: str, *args) -> Any:
        """Make XML-RPC call with error mapping."""
        try:
            result = getattr(self._server, method)(*args)
            return result
        except xmlrpc.client.Fault as e:
            # Map common FLDIGI errors to specific exceptions
            if "rig" in method.lower():
                raise FldigiRigError(f"Rig error in {method}: {e.faultString}") from e
            elif "modem" in method.lower():
                raise FldigiModemError(f"Modem error in {method}: {e.faultString}") from e
            elif method.startswith("main."):
                raise FldigiMainError(f"Main error in {method}: {e.faultString}") from e
            else:
                raise FldigiXmlrpcError(f"XML-RPC fault in {method}: {e.faultString}") from e
        except Exception as e:
            raise FldigiXmlrpcError(f"XML-RPC call failed for {method}: {e}") from e
    
    # === HIGH-LEVEL CONVENIENCE API ===
    
    def rx(self) -> bool:
        """
        Switch to RX mode.
        
        Returns: True if successful.
        Underlying FLDIGI call: main.rx (b)
        """
        return self._call("main.rx")
    
    def tx(self) -> None:
        """
        Switch to TX mode.
        
        Underlying FLDIGI call: main.tx (n)
        """
        self._call("main.tx")
    
    def tune(self) -> None:
        """
        Switch to TUNE mode.
        
        Underlying FLDIGI call: main.tune (n)
        """
        self._call("main.tune")
    
    def abort(self) -> None:
        """
        Abort TX or TUNE.
        
        Underlying FLDIGI call: main.abort (n)
        """
        self._call("main.abort")
    
    def add_tx(self, text: str) -> None:
        """
        Add text to transmit buffer.
        
        Args:
            text: Text to transmit.
        Underlying FLDIGI call: text.add_tx (n:s)
        """
        self._call("text.add_tx", text)
    
    def clear_rx(self) -> None:
        """
        Clear receive buffer.
        
        Underlying FLDIGI call: text.clear_rx (n)
        """
        self._call("text.clear_rx")
    
    def clear_tx(self) -> None:
        """
        Clear transmit buffer.
        
        Underlying FLDIGI call: text.clear_tx (n)
        """
        self._call("text.clear_tx")
    
    def get_rx(self, start: int = 0, length: Optional[int] = None) -> str:
        """
        Get received text.
        
        Args:
            start: Starting character position (default: 0).
            length: Max length to return (default: all).
        Returns: Received text string.
        Underlying FLDIGI call: text.get_rx (s:iii)
        """
        return self._call("text.get_rx", start, 0, length or 0)
    
    @property
    def frequency(self) -> float:
        """Get current frequency (Hz)."""
        try:
            return self._call("rig.get_frequency")
        except FldigiRigError:
            return self._call("main.get_frequency")  # Fallback
    
    @frequency.setter
    def frequency(self, freq: float) -> None:
        """Set frequency (Hz)."""
        try:
            self._call("rig.set_frequency", freq)
        except FldigiRigError:
            self._call("main.set_frequency", freq)
    
    @property
    def mode(self) -> str:
        """Get current mode name."""
        try:
            return self._call("rig.get_mode")
        except FldigiRigError:
            return self._call("main.get_mode")
    
    @mode.setter
    def mode(self, mode_name: str) -> None:
        """Set mode by name."""
        try:
            self._call("rig.set_mode", mode_name)
        except FldigiRigError:
            self._call("main.set_mode", mode_name)
    
    @property
    def bandwidth(self) -> int:
        """Get current bandwidth (Hz)."""
        try:
            return self._call("rig.get_bandwidth")
        except FldigiRigError:
            return self._call("main.get_bandwidth")
    
    @bandwidth.setter
    def bandwidth(self, bw: int) -> None:
        """Set bandwidth (Hz)."""
        try:
            self._call("rig.set_bandwidth", bw)
        except FldigiRigError:
            self._call("main.set_bandwidth", bw)
    
    @property
    def squelch(self) -> int:
        """Get squelch level (0-100)."""
        return self._call("main.get_squelch_level")
    
    @squelch.setter
    def squelch(self, level: int) -> None:
        """Set squelch level (0-100)."""
        self._call("main.set_squelch_level", level)
    
    @property
    def signal_strength(self) -> float:
        """
        Get current signal quality (0.0-100.0).
        
        Underlying FLDIGI call: modem.get_quality (d)
        """
        return self._call("modem.get_quality")
    
    @property
    def rx_state(self) -> bool:
        """Current RX state."""
        return self._call("main.rx")
    
    @property
    def tx_state(self) -> bool:
        """Current TX state."""
        return self._call("main.tx")
    
    # === LOW-LEVEL NAMESPACE PROXIES ===
    # These map 1:1 to FLDIGI's non-deprecated XML-RPC methods
    
    @property
    def fldigi(self) -> NamespaceProxy:
        """FLDIGI application info (version, name, etc.)."""
        return NamespaceProxy(self, "fldigi")
    
    @property
    def main(self) -> NamespaceProxy:
        """Main application controls (RX/TX, squelch, macros, etc.)."""
        return NamespaceProxy(self, "main")
    
    @property
    def rig(self) -> NamespaceProxy:
        """Rig control (frequency, mode, bandwidth)."""
        return NamespaceProxy(self, "rig")
    
    @property
    def text(self) -> NamespaceProxy:
        """Text transmit/receive buffer operations."""
        return NamespaceProxy(self, "text")
    
    @property
    def modem(self) -> NamespaceProxy:
        """Modem selection and configuration."""
        return NamespaceProxy(self, "modem")
    
    @property
    def modem_olivia(self) -> NamespaceProxy:
        """Olivia-specific modem settings."""
        return NamespaceProxy(self, "modem.olivia")
    
    @property
    def rx(self) -> NamespaceProxy:
        """RX data operations."""
        return NamespaceProxy(self, "rx")
    
    @property
    def rxtx(self) -> NamespaceProxy:
        """RX/TX data operations."""
        return NamespaceProxy(self, "rxtx")
    
    @property
    def tx(self) -> NamespaceProxy:
        """TX-specific operations."""
        return NamespaceProxy(self, "tx")
    
    @property
    def log(self) -> NamespaceProxy:
        """QSO logging fields."""
        return NamespaceProxy(self, "log")
    
    @property
    def io(self) -> NamespaceProxy:
        """ARQ/KISS I/O controls."""
        return NamespaceProxy(self, "io")
    
    @property
    def spot(self) -> NamespaceProxy:
        """PSK Reporter and auto-spotting."""
        return NamespaceProxy(self, "spot")
    
    @property
    def navtex(self) -> NamespaceProxy:
        """NAVTEX message operations."""
        return NamespaceProxy(self, "navtex")
    
    @property
    def wefax(self) -> NamespaceProxy:
        """WEFAX transmit/receive operations."""
        return NamespaceProxy(self, "wefax")
