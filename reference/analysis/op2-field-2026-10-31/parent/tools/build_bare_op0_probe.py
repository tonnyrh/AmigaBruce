"""Remove per-loop/step timers from the existing OP0 route for overhead control."""
from pathlib import Path
from build_light_op0_probe import ROOT,BASE,replace

def main():
    s=(BASE/'main.c').read_text()
    s=replace(s,'                ULONG stamp=line_clock();light_bin((stamp-light_step_line)&0xffffffUL);\n                light_step_line=stamp;light_steps_begin=step;',
      '                light_steps_begin=step;')
    s=replace(s,'                light_steps=step-light_start_step;',
      '                light_last_line=line_clock();light_steps=step-light_start_step;')
    s=replace(s,'        render_clock=line_clock();\n        PERF_BEGIN(BL_PERF_LOOP);', '        PERF_BEGIN(BL_PERF_LOOP);')
    s=replace(s,'        {ULONG work=elapsed_work(render_clock);if(light_started){light_work+=work;if(work>light_max_work)light_max_work=work;}}\n        light_last_line=line_clock();','')
    s=replace(s,'''        if(light_started){ULONG stamp=line_clock(),cost=(stamp-render_clock)&0xffffffUL;
            light_wait+=(stamp-light_last_line)&0xffffffUL;light_last_line=stamp;
            if(cost>light_max_loop)light_max_loop=cost;''','''        if(light_started){''')
    (BASE/'bare-main.c').write_text(s)
    b=(BASE/'light-build.ps1').read_text().replace('light/out','bare/out').replace("/main.c';$sourceFlags", "/bare-main.c';$sourceFlags")
    assert 'bare-main.c' in b
    (BASE/'bare-build.ps1').write_text(b)
    runner=(ROOT/'tools/test-light-op0.ps1').read_text()
    runner=runner.replace("[ValidateSet('light','profile')][string]$Variant='light'", "[ValidateSet('bare')][string]$Variant='bare'")
    runner=runner.replace('tools/test-light-op0.ps1','tools/test-bare-op0.ps1')
    runner=runner.replace("$paths+=@('amiga/out/bruce_amiga.exe')", "$paths+=@('amiga/out/bruce_amiga.exe','tools/build_bare_op0_probe.py','reference/analysis/op0-light-2026-10-31/bare-main.c')")
    (ROOT/'tools/test-bare-op0.ps1').write_text(runner)
    print('Generated minimal timestamp control; existing OP0 inputs unchanged')

if __name__=='__main__':main()
