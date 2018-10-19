#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright 2018, University of California, Berkeley
# author: Kevin Laeufer <laeufer@cs.berkeley.edu>

# TODO: connect to treadle via network instead of launching it as a subprocess
#       this would improve startup times!

import os

class Simulator:
	""" Interface to the Treadle Circuit Simulator """

	@staticmethod
	def start_local():
		treadle = TreadleWrapper(debug=False).start()
		return Simulator(treadle)

	@staticmethod
	def start_remote():
		treadle = TreadleClient.start()
		return Simulator(treadle)

	def __init__(self, treadle):
		self.treadle = treadle

	def load(self, ir: str):
		with tempfile.NamedTemporaryFile(suffix='.fir',delete=False) as ff:
			ff.write(ir.encode('UTF-8'))
			fir_file = ff.name
		_compile, _load = self.treadle.execute(f"load {fir_file}", 2)
		os.unlink(fir_file)

	def peek(self, signal: str) -> int:
		res = self.treadle.execute(f"peek {signal}", 1)[0]
		return int(res.split(' ')[-1])

	def poke(self, signal: str, value: int):
		self.treadle.execute(f"poke {signal} {value}")

	def step(self, count=1):
		_ = self.treadle.execute(f"step {count}", 1)[0]

	def stop(self):
		self.treadle.stop()

# server/client infrastructure to help with treadle's long startup times
import socketserver, socket

class TreadleClient:
	@staticmethod
	def start(host='127.0.0.1', port=4321):
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.connect((host, port))
		return TreadleClient(sock)

	def __init__(self, sock):
		self.sock = sock

	def execute(self, cmd: str, count=0):
		msg = f"{cmd}|{count}\n".encode("UTF-8")
		self.sock.sendall(msg)
		resp = self.sock.recv(1024 * 64).decode("UTF-8").split('\n')[:-1]
		if len(resp) == 1 and len(resp[0]) == 0:
			resp = []
		assert len(resp) == count, f"{resp}, {count}"
		return resp

	def stop(self):
		self.sock.close()


class TreadleServer(socketserver.TCPServer):
	@staticmethod
	def run(host='127.0.0.1', port=4321):
		print("Starting treadle...")
		treadle = TreadleWrapper(debug=True).start()
		print("Started treadle...")
		with TreadleServer(host=host, port=port, treadle=treadle) as server:
			server.serve_forever()
	def __init__(self, host, port, treadle):
		self.treadle = treadle
		super().__init__((host, port), TreadleHandler)


class TreadleHandler(socketserver.StreamRequestHandler):
	def handle(self):
		addr = self.client_address[0]
		print(f"Connected to: {addr}")
		try:
			for line in self.rfile:
				cmd, count = line.decode('UTF-8').split('|')
				ret = self.server.treadle.execute(cmd, count=int(count))
				resp = '\n'.join(ret) + '\n'
				self.wfile.write(resp.encode('UTF-8'))
		except ConnectionResetError:
			print(f"Disconnected: {addr}")


# Treadle subprocess wrapper, similar to code used in a previous project in order to run
# a SMT solver as a subprocess

import threading, queue, subprocess, tempfile, time

treadle_path = os.path.join('/home', 'kevin', 'd', 'treadle')
treadle_bin = os.path.join(treadle_path, 'treadle.sh')


class TreadleWrapper:
	def __init__(self, debug=False):
		self.is_running = False
		self._proc = None
		self._output = None
		self.debug_print = print if debug else lambda x: None

	def start(self):
		if self.is_running: return
		cmd = [treadle_bin]
		cwd = treadle_path
		self._proc = subprocess.Popen(cmd, cwd=cwd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
		self._output = SubprocessOutputThread.create(self._proc.stdout)
		if self._proc.poll() is None:
			self.is_running = True
		else:
			raise Exception(f"Failed to start subprocess {self.bin} {self.args}!")
		# wait for repl to load
		line = self._output.read_blocking()
		while not 'Running treadle.TreadleRepl' in line:
			line = self._output.read_blocking()
		return self

	def stop(self):
		if not self.is_running:
			return
		self.send_cmd('quit')
		time.sleep(0.00001)
		self._proc.terminate()
		time.sleep(0.0001)
		if self._proc.poll() is not None:
			self._proc.kill()
		self.is_running = False
		self._proc = None
		self._output = None

	def execute(self, cmd: str, count=0):
		self.send_cmd(cmd=cmd)
		if count > 0:
			return self.read_blocking(count=count)
		return []

	def send_cmd(self, cmd: str):
		assert self.is_running
		self.debug_print("<- " + cmd)
		cmd_str = cmd + '\n'
		self._proc.stdin.write(cmd_str.encode('UTF-8'))
		self._proc.stdin.flush()
		# echo
		assert self._output.read_blocking().startswith('treadle>>')

	def read_blocking(self, count=1, timeout=None):
		resp = []
		for _ in range(count):
			resp.append(self._output.read_blocking(timeout=timeout))
		self.debug_print("-> " + '\n   '.join(resp))
		return resp

class SubprocessOutputThread(threading.Thread):
	""" reads lines from a input stream and puts them into a threadsafe queue """
	@staticmethod
	def create(input_stream):
		t = SubprocessOutputThread(input_stream)
		t.start()
		return t
	def __init__(self, input_stream):
		super().__init__()
		self.daemon = True
		self.inp = input_stream
		self.fifo = queue.Queue()
	def run(self):
		self._read_line_loop()
		self.inp.close()
	def _read_line_loop(self):
		for line in iter(self.inp.readline, b''):
			#print(line[:-1].decode('UTF-8'))
			self.fifo.put(line[:-1].decode('UTF-8'), block=False)
	def read_blocking(self, timeout=None):
		line = self.fifo.get(block=True, timeout=timeout)
		if isinstance(line, Exception):
			raise line
		return line
	def get_lines(self):
		lines = []
		read_done = False
		while not read_done:
			try:
				line = self.fifo.get(block=False)
				if isinstance(line, Exception):
					raise line
				lines.append(line)
			except queue.Empty:
				read_done = True
		return lines
	def clear(self):
		try:
			while True:
				self.fifo.get(block=False)
		except queue.Empty:
			return

if __name__ == '__main__':
	TreadleServer.run()