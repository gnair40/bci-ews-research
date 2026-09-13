# -*- coding: utf-8 -*-
import re, subprocess, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import build
import part1, part2, part3, part4

REPO = '/home/user/bci-ews-research'

def verifier_rows():
    out = subprocess.run([sys.executable, 'scripts/31_verify_claims.py'],
                         cwd=REPO, capture_output=True, text=True).stdout
    # The verifier states its own total. Check the parse against that rather
    # than against a number written here, which goes stale every time a study
    # is added -- as it did on 13 Sep 2026 at 93 vs 97.
    m = re.search(r'All (\d+) headline claims match', out)
    if not m:
        raise SystemExit('verifier did not report a passing total; '
                         'appendix A cannot be built from a failing run')
    expected = int(m.group(1))
    rows = []
    for ln in out.split('\n'):
        m = re.match(r'^(.*?)\s{2,}(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(ok|MISMATCH)\s*$', ln)
        if m and m.group(1).strip() not in ('claim',):
            name = m.group(1).strip()
            name = (name.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                        .replace('—', '&#8212;'))
            rows.append((name, m.group(2), m.group(3)))
    if len(rows) != expected:
        raise SystemExit(f'parsed {len(rows)} claim rows but the verifier '
                         f'reports {expected}; the parser has drifted')
    return rows

def main():
    claims = verifier_rows()
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
