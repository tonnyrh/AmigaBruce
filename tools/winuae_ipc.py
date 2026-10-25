"""Small text client for WinUAE's documented uaeipc.cpp named-pipe protocol.
Use only the pipe from an owned instance's boot log; does not select a process.
"""
import ctypes,time
from ctypes import wintypes


def command(pipe,text,timeout=5,expected_pid=None):
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.CreateFileW.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,ctypes.c_void_p,wintypes.DWORD,wintypes.DWORD,wintypes.HANDLE]
    k.CreateFileW.restype=wintypes.HANDLE
    k.WriteFile.argtypes=[wintypes.HANDLE,ctypes.c_void_p,wintypes.DWORD,ctypes.POINTER(wintypes.DWORD),ctypes.c_void_p]
    k.ReadFile.argtypes=k.WriteFile.argtypes
    k.PeekNamedPipe.argtypes=[wintypes.HANDLE,ctypes.c_void_p,wintypes.DWORD,ctypes.c_void_p,ctypes.POINTER(wintypes.DWORD),ctypes.c_void_p]
    k.CloseHandle.argtypes=[wintypes.HANDLE]
    end=time.monotonic()+timeout
    while True:
        h=k.CreateFileW(pipe,0xc0000000,0,None,3,0,None)
        if h!=ctypes.c_void_p(-1).value:break
        if ctypes.get_last_error() not in (2,231) or time.monotonic()>=end:raise ctypes.WinError(ctypes.get_last_error())
        time.sleep(.02)
    try:
        if expected_pid is not None:
            owner=wintypes.ULONG()
            k.GetNamedPipeServerProcessId.argtypes=[wintypes.HANDLE,ctypes.POINTER(wintypes.ULONG)]
            if not k.GetNamedPipeServerProcessId(h,ctypes.byref(owner)):raise ctypes.WinError(ctypes.get_last_error())
            assert owner.value==expected_pid, 'Pipe is not owned by the requested test process'
        payload=b'\xef\xbb\xbf'+text.encode('utf-8')+b'\0';written=wintypes.DWORD()
        if not k.WriteFile(h,payload,len(payload),ctypes.byref(written),None):raise ctypes.WinError(ctypes.get_last_error())
        end=time.monotonic()+timeout;available=wintypes.DWORD()
        while time.monotonic()<end:
            if not k.PeekNamedPipe(h,None,0,None,ctypes.byref(available),None):raise ctypes.WinError(ctypes.get_last_error())
            if available.value:
                buf=ctypes.create_string_buffer(32768);got=wintypes.DWORD()
                if not k.ReadFile(h,buf,len(buf),ctypes.byref(got),None):raise ctypes.WinError(ctypes.get_last_error())
                return buf.raw[:got.value].decode('utf-8-sig',errors='replace').rstrip('\0')
            time.sleep(.01)
        raise TimeoutError(text)
    finally:k.CloseHandle(h)

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--pipe',required=True);p.add_argument('command')
    a=p.parse_args();print(command(a.pipe,a.command))
