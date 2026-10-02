"""Actual snapshotted sender-loop AST with a real socket and explicit halt/close interleaving."""
import ast
from pathlib import Path
from queue import Queue,Empty
import socket
from threading import Event,Lock
from types import SimpleNamespace
import unittest

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'artifacts/roboboat-live-endpoint-source-audit-v30-001/tcp_sender.py'
CANDIDATE=ROOT/'artifacts/roboboat-endpoint-close-race-candidate-v31-001/tcp_sender_candidate_v31.py'


def run_loop(path,halt_before_close,other_errno=None):
    tree=ast.parse(Path(path).read_text())
    method=next(n for c in tree.body if isinstance(c,ast.ClassDef) for n in c.body if isinstance(n,ast.FunctionDef) and n.name=='sender_loop')
    namespace={'Queue':Queue,'Empty':Empty,'SysCommand_Handshake_Metadata':lambda:None,
        'SysCommand_Handshake':lambda metadata:None,'ClientThread':SimpleNamespace(serialize_command=lambda name,meta:b'handshake'),
        'errno':__import__('errno')}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[method],type_ignores=[])),str(path),'exec'),namespace)
    errors=[];infos=[];halt=Event();real_socket=socket.socket()
    class InterleavedClose:
        def sendall(self,item):
            # This happens after the sender's while-condition and queue get.
            # Match the reader's actual halt-before-close order.
            if halt_before_close:halt.set()
            real_socket.close()
            if other_errno is not None:raise OSError(other_errno,'deliberate unrelated I/O fault')
            real_socket.sendall(item)
    obj=SimpleNamespace(queue_lock=Lock(),queue=None,time_between_halt_checks=.01,
        tcp_server=SimpleNamespace(logerr=errors.append,loginfo=infos.append))
    namespace['sender_loop'](obj,InterleavedClose(),0,halt)
    return errors,infos,halt.is_set(),obj.queue


class EndpointCloseRaceTests(unittest.TestCase):
    def test_original_actual_sender_logs_ebadf_after_reader_halt(self):
        errors,_,halt,queue=run_loop(BASE,True)
        self.assertEqual(len(errors),1);self.assertIn('Bad file descriptor',errors[0])
        self.assertTrue(halt);self.assertIsNone(queue)

    def test_candidate_does_not_log_false_transport_error_after_explicit_reader_halt(self):
        path=CANDIDATE if CANDIDATE.exists() else BASE
        errors,infos,halt,queue=run_loop(path,True)
        self.assertFalse(errors,'Known halted socket close still counted as an active transport error')
        self.assertTrue(infos);self.assertTrue(halt);self.assertIsNone(queue)

    def test_unrelated_os_error_stays_error_even_after_halt(self):
        path=CANDIDATE if CANDIDATE.exists() else BASE
        errors,_,_,_=run_loop(path,True,__import__('errno').EIO)
        self.assertEqual(len(errors),1);self.assertIn('I/O fault',errors[0])

    def test_unexpected_closed_socket_without_prior_halt_stays_error(self):
        path=CANDIDATE if CANDIDATE.exists() else BASE
        errors,_,_,_=run_loop(path,False)
        self.assertEqual(len(errors),1);self.assertIn('Bad file descriptor',errors[0])

if __name__=='__main__':unittest.main()
