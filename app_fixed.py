#!/usr/bin/env python3
"""
Fixed version of app.py - patches the scenario detection issue
"""

# This is a patch for the create_video_onestep function
# Add this right before the scenario detection (around line 327):

def patch_create_video_onestep():
    """
    The issue: has_effects and has_subtitles variables are defined early in the function
    but used much later for scenario detection, causing them to be undefined or incorrect.
    
    Solution: Recalculate these values right before scenario detection.
    """
    
    # Original code around line 328-336 has:
    # scenario = "unknown"
    # if not has_effects and not has_subtitles:
    #     scenario = "baseline"
    # ...
    
    # FIXED CODE - Add before line 328:
    fixed_code = '''
            # Recalculate for scenario detection based on original request
            scenario_has_effects = bool(data.get('effects', []))
            scenario_has_subtitles = bool(data.get('subtitle'))
            
            # Log processing summary
            scenario = "unknown"
            if not scenario_has_effects and not scenario_has_subtitles:
                scenario = "baseline"
            elif not scenario_has_effects and scenario_has_subtitles:
                scenario = "subtitles_only"
            elif scenario_has_effects and not scenario_has_subtitles:
                scenario = "effects_only"
            elif scenario_has_effects and scenario_has_subtitles:
                scenario = "full_featured"
    '''
    
    return fixed_code

# Alternative minimal fix - just add these two lines before scenario detection:
minimal_fix = '''
# Add at line 327, before scenario detection:
has_effects = bool(data.get('effects', []))
has_subtitles = bool(data.get('subtitle'))
'''

print("""
ISSUE IDENTIFIED: The scenario is showing as "unknown" because the Docker container's app.py
is losing track of the has_effects and has_subtitles variables by the time it reaches the
scenario detection code at the end of the function.

ROOT CAUSE: Variable scope issue - the variables are defined early but used much later.

SOLUTION: Add these two lines before the scenario detection (line 327):

has_effects = bool(data.get('effects', []))
has_subtitles = bool(data.get('subtitle'))

This ensures the scenario is correctly detected based on the original request parameters.
""")