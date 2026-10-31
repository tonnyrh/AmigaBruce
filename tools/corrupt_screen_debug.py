"""Send a read/debug control command to the explicitly owned test process."""
import argparse,re
from pathlib import Path
from winuae_ipc import command
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--pid',type=int,required=True);p.add_argument('command');a=p.parse_args()
 pipe=re.findall(r"IPC: Named Pipe '([^']+)' open",(ROOT/'.tmp/corrupt-screen-ui/winuaebootlog.txt').read_text(errors='replace'))[-1]
 print(command(pipe,a.command,expected_pid=a.pid))
if __name__=='__main__':main()
