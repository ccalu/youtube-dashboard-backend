"""
Assembles mission_control.py from:
- Python section (existing functions and mappings)
- HTML header/CSS (existing)
- Part 1: mc_v2_part1_RECOVERED.js (PNG character sprites + helpers)
- Part 2: mc_v2_part2_ORIGINAL.js (engine, rendering, game loop)
- HTML footer
"""
import os

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RUNTIME = os.path.join(BASE, '_runtime')

MC_PY = os.path.join(BASE, 'mission_control.py')
PART1 = os.path.join(RUNTIME, 'mc_v2_part1_RECOVERED.js')
PART2 = os.path.join(RUNTIME, 'mc_v2_part2_ORIGINAL.js')
OUTPUT = MC_PY  # overwrite in place

def main():
    # Read current mission_control.py
    with open(MC_PY, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')

    # Find <script> and </script> lines
    script_start = None
    script_end = None
    for i, line in enumerate(lines):
        if '<script>' in line and script_start is None:
            script_start = i
        if '</script>' in line:
            script_end = i

    if script_start is None or script_end is None:
        print("ERROR: Could not find <script> or </script> tags")
        return

    print(f"Found <script> at line {script_start + 1}")
    print(f"Found </script> at line {script_end + 1}")

    # Read Part 1 and Part 2
    with open(PART1, 'r', encoding='utf-8') as f:
        part1 = f.read()
    with open(PART2, 'r', encoding='utf-8') as f:
        part2 = f.read()

    print(f"Part 1: {len(part1)} chars")
    print(f"Part 2: {len(part2)} chars")

    # Build new content:
    # lines[0..script_start] includes <script> tag
    # Then Part1 + Part2
    # Then lines[script_end..] includes </script> and rest

    before_script = '\n'.join(lines[:script_start + 1])  # up to and including <script>
    after_script = '\n'.join(lines[script_end:])  # from </script> onwards

    new_content = before_script + '\n' + part1 + '\n\n' + part2 + '\n' + after_script

    # Backup current
    backup = MC_PY + '.bak'
    with open(backup, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Backup saved to {backup}")

    # Write new
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        f.write(new_content)

    new_lines = new_content.split('\n')
    print(f"\nAssembly complete!")
    print(f"  Old: {len(lines)} lines")
    print(f"  New: {len(new_lines)} lines")
    print(f"  Total chars: {len(new_content)}")

    # Verify
    if 'CHAR_PNG_0' in new_content:
        print("  [OK] CHAR_PNG_0 found")
    else:
        print("  [WARN] CHAR_PNG_0 NOT found!")

    if 'loadPNGSprites' in new_content:
        print("  [OK] loadPNGSprites found")
    else:
        print("  [WARN] loadPNGSprites NOT found!")

    if 'renderScene' in new_content:
        print("  [OK] renderScene found")
    else:
        print("  [WARN] renderScene NOT found!")

    if 'initMissionControl' in new_content:
        print("  [OK] initMissionControl found")
    else:
        print("  [WARN] initMissionControl NOT found!")

    if 'get_agent_report' in new_content:
        print("  [OK] get_agent_report found")
    else:
        print("  [WARN] get_agent_report NOT found!")

    if 'get_agent_overview_batch' in new_content:
        print("  [OK] get_agent_overview_batch found")
    else:
        print("  [WARN] get_agent_overview_batch NOT found!")

if __name__ == '__main__':
    main()
