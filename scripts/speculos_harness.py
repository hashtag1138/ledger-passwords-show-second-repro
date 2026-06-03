from __future__ import annotations

import http.client
import json
import os
import signal
import socket
import subprocess
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

from utils import ReproError

_KEY_MAPS = (
    "abcdefghijklmnopqrstuvwxyz\b\n\r",
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ\b\n\r",
    "0123456789 '\"`&/?!:;.,~*$=+-[](){}^<>\\_#@|%\b\n\r",
)
_MODE_LOWER = 0
_MODE_UPPER = 1
_MODE_DIGITS = 2


class SpeculosHarness:
    def __init__(
        self,
        *,
        app_path: Path,
        speculos_image: str,
        app_name: str,
        model: str,
        display: str,
        apdu_port: int,
        api_port: int,
        log_path: Path,
        server: str = "127.0.0.1",
    ) -> None:
        self.app_path = app_path
        self.speculos_image = speculos_image
        self.app_name = app_name
        self.model = model
        self.display = display
        self.apdu_port = apdu_port
        self.api_port = api_port
        self.log_path = log_path
        self.server = server
        self.process: subprocess.Popen[str] | None = None
        self._kbd_mode: int | None = None
        self._kbd_index = 0

    def start(self) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("w", encoding="utf-8") as log_file:
            self.process = subprocess.Popen(
                [
                    "docker",
                    "run",
                    "--rm",
                    "-e",
                    f"SPECULOS_APPNAME={self.app_name}",
                    "-v",
                    f"{self.app_path.parent}:/speculos/apps:ro",
                    "-p",
                    f"{self.api_port}:{self.api_port}",
                    "-p",
                    f"{self.apdu_port}:{self.apdu_port}",
                    self.speculos_image,
                    "--model",
                    self.model,
                    "--display",
                    self.display,
                    "--api-port",
                    str(self.api_port),
                    "--apdu-port",
                    str(self.apdu_port),
                    f"/speculos/apps/{self.app_path.name}",
                ],
                stdout=log_file,
                stderr=subprocess.STDOUT,
                text=True,
                start_new_session=True,
            )
        self._wait_for_port(self.apdu_port, timeout_seconds=20.0)
        self._wait_for_port(self.api_port, timeout_seconds=20.0)
        self._wait_for_api_ready(timeout_seconds=20.0)
        self.delete_events()

    def stop(self) -> None:
        if self.process is None:
            return
        if self.process.poll() is None:
            try:
                os.killpg(self.process.pid, signal.SIGTERM)
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(self.process.pid, signal.SIGKILL)
                self.process.wait(timeout=5)
        self.process = None

    def ensure_running(self) -> None:
        if self.process is None:
            raise ReproError("Speculos process not started")
        if self.process.poll() is not None:
            raise ReproError(f"Speculos exited with code {self.process.returncode}")

    def log_tail(self, lines: int = 120) -> str:
        if not self.log_path.exists():
            return ""
        content = self.log_path.read_text(encoding="utf-8", errors="replace").splitlines()
        return "\n".join(content[-lines:])

    def safe_current_screen_text(self) -> str:
        try:
            return self.current_screen_text()
        except Exception:
            return ""

    def current_screen_text(self) -> str:
        body = self._http_get_json(f"http://{self.server}:{self.api_port}/events?currentscreenonly=true")
        texts = [event.get("text", "") for event in body.get("events", []) if event.get("text", "")]
        return " | ".join(texts)

    def delete_events(self) -> None:
        self._http_delete(f"http://{self.server}:{self.api_port}/events")

    def press_button(self, button: str) -> None:
        self._http_post_json(
            f"http://{self.server}:{self.api_port}/button/{button}",
            {"action": "press-and-release"},
        )
        time.sleep(0.2)

    def wait_for_screen_text(
        self,
        *,
        contains: str | None = None,
        excludes: tuple[str, ...] = (),
        timeout_seconds: float = 5.0,
    ) -> str:
        deadline = time.time() + timeout_seconds
        last_text = ""
        while time.time() < deadline:
            self.ensure_running()
            text = self.current_screen_text()
            last_text = text
            if contains is not None and contains not in text:
                time.sleep(0.1)
                continue
            if any(excluded in text for excluded in excludes):
                time.sleep(0.1)
                continue
            if text:
                return text
            time.sleep(0.1)
        raise ReproError(
            f"Timed out waiting for screen contains={contains!r}, excludes={list(excludes)!r}; last={last_text!r}"
        )

    def initialize_first_run(self) -> None:
        deadline = time.time() + 8.0
        while time.time() < deadline:
            text = self.safe_current_screen_text()
            if "Disclaimer" in text:
                self.press_button("right")
                continue
            if "Yes, I understand" in text:
                self.press_button("both")
                continue
            if "Host keyboard" in text:
                self.press_button("both")
                time.sleep(0.2)
                break
            if "Manage passwords" in text or "Tap to manage" in text:
                break
            time.sleep(0.1)
        self._kbd_reset_state()
        self.delete_events()

    def home_to_menu(self) -> None:
        deadline = time.time() + 8.0
        last_text = ""
        while time.time() < deadline:
            text = self.safe_current_screen_text()
            last_text = text
            if "Disclaimer" in text:
                self.press_button("right")
                time.sleep(0.2)
                continue
            if "Yes, I understand" in text:
                self.press_button("both")
                time.sleep(0.3)
                continue
            if "Host keyboard" in text:
                self.press_button("both")
                time.sleep(0.3)
                continue
            if "Which action?" in text:
                return
            if "Tap to manage" in text:
                self.press_button("both")
                time.sleep(0.3)
                continue
            if "Manage passwords" in text:
                self.press_button("right")
                time.sleep(0.2)
                self.press_button("both")
                self.wait_for_screen_text(contains="Which action?", timeout_seconds=3.0)
                return
            if "PASSWORD HAS" in text or "NEW PASSWORD" in text or "CREATED" in text or "BEEN DELETED" in text:
                self.press_button("both")
                time.sleep(0.3)
                continue
            if "Passwords list" in text:
                for _ in range(12):
                    if self.safe_current_screen_text().strip() == "Back":
                        self.press_button("both")
                        time.sleep(0.3)
                        break
                    self.press_button("right")
                    time.sleep(0.2)
                continue
            if text.strip() == "Back":
                self.press_button("both")
                time.sleep(0.3)
                continue
            if text and "Which action?" not in text:
                self.press_button("right")
                time.sleep(0.3)
                continue
            time.sleep(0.2)
        raise ReproError(f"Timed out waiting to reach action menu; last screen={last_text!r}")

    def menu_select(self, index: int) -> None:
        for _ in range(index):
            self.press_button("right")
        self.press_button("both")

    def list_choose(self, position: int) -> None:
        if position < 1:
            raise ReproError(f"Invalid list position: {position}")
        for _ in range(position - 1):
            self.press_button("right")
        self.press_button("both")

    def show_password(self, position: int) -> str:
        self.home_to_menu()
        self.menu_select(2)
        self.wait_for_screen_text(contains="Passwords list", timeout_seconds=3.0)
        before = self.safe_current_screen_text()
        self.list_choose(position)
        after = self.wait_for_screen_text(
            excludes=("Passwords list", "Which action?", "Manage passwords", "Tap to manage", "Host keyboard"),
            timeout_seconds=3.0,
        )
        if after == before:
            raise ReproError(f"Show password did not leave the list screen: {after!r}")
        return after

    def type_password(self, position: int) -> str:
        self.home_to_menu()
        self.menu_select(1)
        self.wait_for_screen_text(contains="Passwords list", timeout_seconds=3.0)
        self.list_choose(position)
        return self.wait_for_screen_text(contains="PASSWORD HAS", timeout_seconds=3.0)

    def create_password(self, nickname: str) -> str:
        if not nickname:
            raise ReproError("Nickname must not be empty")
        self.home_to_menu()
        self.menu_select(0)
        self.wait_for_screen_text(contains="Create password", timeout_seconds=3.0)
        self._write(nickname)
        self._keyboard_confirm()
        return self.wait_for_screen_text(contains="NEW PASSWORD", timeout_seconds=3.0)

    def load_metadatas(self, raw: bytes) -> None:
        if not raw:
            raise ReproError("Raw metadata must not be empty")
        auto_approver = self._start_auto_approver()
        try:
            with socket.create_connection((self.server, self.apdu_port), timeout=5) as sock:
                sock.settimeout(10)
                offset = 0
                while offset < len(raw):
                    end = min(offset + 0xFF, len(raw))
                    chunk = raw[offset:end]
                    p1 = 0xFF if end == len(raw) else 0x00
                    _, status_word = self._exchange_apdu(sock, 0xE0, 0x05, p1, 0x00, chunk)
                    if status_word != 0x9000:
                        raise ReproError(f"LOAD_METADATAS failed at offset {offset}: sw=0x{status_word:04x}")
                    offset = end
        finally:
            self._stop_auto_approver(auto_approver)

    def _kbd_reset_state(self) -> None:
        self._kbd_mode = None
        self._kbd_index = 0

    def _start_auto_approver(self) -> tuple[threading.Thread, threading.Event]:
        stop_event = threading.Event()
        thread = threading.Thread(target=self._auto_approve_loop, args=(stop_event,), daemon=True)
        thread.start()
        return thread, stop_event

    def _stop_auto_approver(self, handle: tuple[threading.Thread, threading.Event] | None) -> None:
        if handle is None:
            return
        thread, stop_event = handle
        stop_event.set()
        thread.join(timeout=1.0)

    def _auto_approve_loop(self, stop_event: threading.Event) -> None:
        last_text = ""
        while not stop_event.is_set():
            try:
                text = self.safe_current_screen_text()
                if not text or text == last_text:
                    stop_event.wait(0.2)
                    continue
                if "Transfer metadatas" in text or "Overwrite metadatas" in text:
                    self.press_button("right")
                elif "Approve" in text:
                    self.press_button("both")
                last_text = text
            except Exception:
                stop_event.wait(0.2)

    def _kbd_navigate_to(self, target_index: int, ring_size: int) -> None:
        right_steps = (target_index - self._kbd_index) % ring_size
        left_steps = (self._kbd_index - target_index) % ring_size
        if right_steps <= left_steps:
            steps, action = right_steps, lambda: self.press_button("right")
        else:
            steps, action = left_steps, lambda: self.press_button("left")
        for _ in range(steps):
            action()
        self._kbd_index = target_index

    def _kbd_enter_mode(self, target_mode: int) -> None:
        self._kbd_navigate_to(target_mode, ring_size=3)
        self.press_button("both")
        self._kbd_mode = target_mode
        self._kbd_index = 0

    def _kbd_leave_mode(self) -> None:
        if self._kbd_mode is None:
            return
        keys = _KEY_MAPS[self._kbd_mode]
        self._kbd_navigate_to(len(keys) - 1, ring_size=len(keys))
        self.press_button("both")
        self._kbd_mode = None
        self._kbd_index = 0

    def _required_mode(self, char: str) -> int:
        if char.isupper():
            return _MODE_UPPER
        if char.islower():
            return _MODE_LOWER
        return _MODE_DIGITS

    def _kbd_ensure_mode(self, target_mode: int) -> None:
        if self._kbd_mode == target_mode:
            return
        if self._kbd_mode is not None:
            self._kbd_leave_mode()
        self._kbd_enter_mode(target_mode)

    def _kbd_type_char(self, char: str) -> None:
        target_mode = self._required_mode(char)
        self._kbd_ensure_mode(target_mode)
        keys = _KEY_MAPS[self._kbd_mode]
        try:
            target_index = keys.index(char)
        except ValueError as error:
            raise ReproError(f"Character {char!r} cannot be typed on Nano keyboard") from error
        self._kbd_navigate_to(target_index, ring_size=len(keys))
        self.press_button("both")

    def _write(self, text: str) -> None:
        for char in text:
            self._kbd_type_char(char)

    def _keyboard_confirm(self) -> None:
        if self._kbd_mode is None:
            self._kbd_enter_mode(_MODE_LOWER)
        keys = _KEY_MAPS[self._kbd_mode]
        self._kbd_navigate_to(keys.index("\n"), ring_size=len(keys))
        self.press_button("both")
        self._kbd_reset_state()

    def _http_get_json(self, url: str) -> dict:
        with urllib.request.urlopen(url, timeout=5) as response:
            payload = response.read()
        return json.loads(payload.decode("utf-8"))

    def _http_post_json(self, url: str, payload: dict) -> None:
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=5):
            return

    def _http_delete(self, url: str) -> None:
        request = urllib.request.Request(url, method="DELETE")
        with urllib.request.urlopen(request, timeout=5):
            return

    def _wait_for_port(self, port: int, timeout_seconds: float) -> None:
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(0.5)
                if sock.connect_ex((self.server, port)) == 0:
                    return
            time.sleep(0.1)
        raise ReproError(f"Timed out waiting for {self.server}:{port}")

    def _wait_for_api_ready(self, timeout_seconds: float) -> None:
        deadline = time.time() + timeout_seconds
        last_error = ""
        while time.time() < deadline:
            try:
                self._http_get_json(f"http://{self.server}:{self.api_port}/events?currentscreenonly=true")
                return
            except Exception as error:
                last_error = str(error)
                time.sleep(0.1)
        raise ReproError(f"Timed out waiting for Speculos API readiness: {last_error}")

    def _exchange_apdu(
        self,
        sock: socket.socket,
        cla: int,
        ins: int,
        p1: int,
        p2: int,
        data: bytes,
    ) -> tuple[bytes, int]:
        if len(data) > 0xFF:
            raise ReproError(f"APDU payload too large: {len(data)}")
        apdu = bytes((cla, ins, p1, p2, len(data))) + data
        sock.sendall(len(apdu).to_bytes(4, byteorder="big"))
        sock.sendall(apdu)
        response_length = int.from_bytes(self._socket_read_exactly(sock, 4), byteorder="big")
        response_data = self._socket_read_exactly(sock, response_length)
        status_word = int.from_bytes(self._socket_read_exactly(sock, 2), byteorder="big")
        return response_data, status_word

    def _socket_read_exactly(self, sock: socket.socket, length: int) -> bytes:
        output = bytearray()
        while len(output) < length:
            chunk = sock.recv(length - len(output))
            if not chunk:
                raise ReproError(f"Unexpected end of APDU stream after {len(output)} bytes, expected {length}")
            output.extend(chunk)
        return bytes(output)
