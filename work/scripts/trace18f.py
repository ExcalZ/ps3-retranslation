import sys, os, socket, re; sys.path.insert(0, 'tools')
from ps3emu import *
src = open('PSIII_Disasm/ps3.asm', encoding='utf-8', errors='replace').read().split('\n')
labels = [m.group(1) for l in src[13372:13640] for m in [re.match(r'^([A-Za-z_][A-Za-z0-9_]*):', l)] if m]
labels += ['MainGameLoop', 'ProcessFadeOut', 'VDPDisableDisplay', 'ProcessMapData', 'loc_6EA0', 'ClearSprites', 'LoadDataInVRAM', 'LoadVSRAMData',
           'loc_D878', 'VBlank', 'VBlank_End', 'ProcessPrimaryObjs', 'ProcessSecondaryObjs', 'ProcessTertiaryObjs', 'BuildSprites', 'loc_FBDE', 'loc_75C0', 'loc_820C', 'loc_7184']
addr = {}
for l in labels:
    try: addr[listing_address(l)] = l
    except KeyError: pass
print(len(addr), 'breakpoints', flush=True)
with PS3('ps3en.bin', state='work/states/observe-18.state') as em:
    for a in addr: em.breakpoint(a)
    lines = []
    def hook(pc):
        r = em.regs()
        lines.append('f%d %-22s pc %06X a0 %06X a1 %06X a5 %06X d0 %08X d1 %08X sp %06X' % (em.frame, addr.get(pc, '?'), pc, r['a'][0], r['a'][1], r['a'][5], r['d'][0], r['d'][1], r['a'][7]))
        if len(lines) > 300: del lines[0]
    try:
        for i in range(120):
            em.step_frame(hook)
            lines.append('--- frame %d routine %04X screen %04X' % (em.frame, em.word(0xFFFFD284), em.word(0xFFFFD012)))
    except (socket.timeout, ConnectionResetError) as e:
        lines.append('connection lost: %s' % e)
    open('work/analysis/trace18f.log', 'w').write('\n'.join(lines))
    print('\n'.join(lines[-40:]))
