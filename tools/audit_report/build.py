# -*- coding: utf-8 -*-
import re, subprocess, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import build
import part1, part2, part3, part4

REPO = '/home/user/bci-ews-research'

def verifier_rows():
    out = subprocess.run([sys.executable, 'scripts/31_verify_claims.py'],
                         cwd=REPO, capture_output=True, text=True).stdout
    rows = []
    for ln in out.split('\n'):
        m = re.match(r'^(.*?)\s{2,}(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(ok|MISMATCH)\s*$', ln)
        if m and m.group(1).strip() not in ('claim',):
            name = m.group(1).strip()
            name = (name.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                        .replace('—', '&#8212;'))
            rows.append((name, m.group(2), m.group(3)))
    return rows

def main():
    claims = verifier_rows()
    assert len(claims) == 93, 'expected 93 claims, parsed %d' % len(claims)
    story = []
    story += part1.front_matter()
    story += part1.section_0()
    story += part1.section_1()
    story += part1.section_2()
    story += part1.section_3()
    story += part1.section_4()
    story += part2.section_5()
    story += part2.section_6()
    story += part2.section_7()
    story += part2.section_8()
    story += part3.section_9()
    story += part3.section_10()
    story += part3.section_11()
    story += part3.section_12()
    story += part4.section_13()
    story += part4.section_14()
    story += part4.section_15()
    story += part4.appendix_a(claims)
    story += part4.appendix_b()
    out = sys.argv[1] if len(sys.argv) > 1 else 'audit.pdf'
    build(out, story)
    print('wrote', out)

main()
