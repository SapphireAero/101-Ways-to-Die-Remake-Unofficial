"""Exercise the actual reader functions without starting a window or audio."""
from pathlib import Path
from types import SimpleNamespace
import copy
import io
import json
import sys
import tempfile
import textwrap
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from generate_dialogue import generate
from check_public import check

def load_runtime():
    preferences = SimpleNamespace(language=None)
    renpy = SimpleNamespace(file=lambda name: io.BytesIO((ROOT / 'game' / name).read_bytes()),
                            game=SimpleNamespace(preferences=preferences))
    env = {'renpy': renpy, 'config': SimpleNamespace(history_callbacks=[])}
    renpy.store = SimpleNamespace()
    for name in ['original_data', 'original_story_support', 'original_supplemental_routes']:
        source = (ROOT / 'game' / (name + '.rpy')).read_text(encoding='utf-8')
        body = source.split('init python:\n', 1)[1].split('\nlabel ', 1)[0]
        exec(compile(textwrap.dedent(body), name + '.rpy:init', 'exec'), env)
    env['original_audio_events'] = lambda name, events: env['original_story_merge_events'](name, events, {})
    return env, preferences

class RuntimeTests(unittest.TestCase):
    def test_root_branches_rejoin_once_and_serialize(self):
        env, _ = load_runtime()
        for choice, expected in [(0, 'DEMO_A.FOB'), (1, 'DEMO_B.FOB')]:
            state = env['original_route_begin']()
            visited = []
            for _ in range(20):
                call = env['original_route_next'](state)
                if call is None:
                    break
                visited.append(call['scenario'])
                env['original_route_apply_choice'](state, choice if len(visited) == 1 else None)
                state = json.loads(json.dumps(state))
                # JSON stringifies integer keys; Ren'Py serialization preserves
                # them. Restore the keys to model a native saved Python state.
                state['conditions'] = {int(key): value for key, value in state['conditions'].items()}
            self.assertEqual(visited, ['DEMO_CHOICE.FOB', expected, 'DEMO_END.FOB'])
            self.assertTrue(state['done'])

    def test_grouped_paragraph_dynamic_language_and_labels(self):
        env, preferences = load_runtime()
        events = env['original_load_scenario_events']('DEMO_A.FOB')
        texts = [item for item in events if item['type'] == 'text']
        self.assertEqual(texts[0]['dialogue_key'], texts[1]['dialogue_key'])
        self.assertNotEqual(texts[0]['dialogue_key'], texts[2]['id'])
        chinese = env['original_localize_event'](texts[0])
        preferences.language = 'japanese'
        japanese = env['original_localize_event'](texts[0])
        self.assertNotEqual(chinese, japanese)
        self.assertEqual(japanese, texts[0]['text'])
        env['original_dialogue_context'] = ('event', texts[0])
        self.assertIn('label ' + env['original_dialogue_label']() + ':', generate())
        self.assertEqual((ROOT / 'game/demo_dialogue_lines.rpy').read_text(encoding='utf-8'), generate())

    def test_scenario_internal_branch_and_nested_frame_restore(self):
        env, _ = load_runtime()
        events = [{'offset': hex(offset), 'id': str(offset)} for offset in (10, 20, 30, 40)]
        route = {'conditions': {10: {'option_count': 2, 'group_end': 40,
                 'branches': [{'start': 20, 'end': 30}, {'start': 30, 'end': 40}]}}}
        for choice in (0, 1):
            state = env['original_scenario_route_begin'](events, route)
            visited = []
            for _ in range(10):
                group = env['original_scenario_route_next'](state)
                if group is None:
                    break
                visited.append(group['offset'])
                env['original_scenario_route_apply_choice'](state, choice)
            self.assertEqual(visited, [10, 20 if choice == 0 else 30, 40])
        store = env['renpy'].store
        store.original_scenario_name = 'DEMO_A.FOB'
        store.original_scenario_event_index = 3
        store.original_auxiliary_progress = {}
        env['original_scenario_call_stack'] = []
        env['original_scenario_push_call']()
        store.original_scenario_name = 'DEMO_NOTE.FOB'
        store.original_scenario_event_index = 99
        env['original_scenario_pop_call'](None)
        self.assertEqual(store.original_scenario_name, 'DEMO_A.FOB')
        self.assertEqual(store.original_scenario_event_index, 3)

    def test_public_boundary_rejects_unlisted_media(self):
        check()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'public-manifest.json').write_text('["public-manifest.json"]', encoding='utf-8')
            (root / 'accidental-original.mp4').write_bytes(b'private media')
            with self.assertRaisesRegex(ValueError, 'Outside public manifest'):
                check(root)

    def test_gallery_progress_ignores_replay_and_separates_branches(self):
        env, _ = load_runtime()
        seen = set()
        env['persistent'] = SimpleNamespace(original_completed_scenarios=set())
        env['ORIGINAL_GALLERY_CG'] = env['ORIGINAL_CG']
        env['original_gallery_replay_mode'] = False
        env['_in_replay'] = False
        renpy = env['renpy']
        renpy.register_persistent = lambda *args: None
        renpy.seen_image = lambda path: path in seen
        renpy.mark_image_seen = seen.add
        renpy.save_persistent = lambda: None
        env['config'].after_load_callbacks = []
        source = (ROOT / 'game/original_gallery_progress.rpy').read_text(encoding='utf-8')
        body = source.split('init 1 python:\n', 1)[1].split('\nscreen ', 1)[0]
        exec(compile(textwrap.dedent(body), 'original_gallery_progress.rpy:init', 'exec'), env)
        path = env['ORIGINAL_CG'][0][1]
        env['original_gallery_record_image'](path)
        env['original_gallery_complete_scenario']('DEMO_A.FOB')
        self.assertTrue(env['original_gallery_unlocked']('cg', 0))
        self.assertTrue(env['original_gallery_unlocked']('scene', 0))
        self.assertFalse(env['original_gallery_unlocked']('cg', 1))
        self.assertFalse(env['original_gallery_unlocked']('scene', 1))
        before = copy.deepcopy(env['persistent'].original_completed_scenarios)
        for field in ('original_gallery_replay_mode', '_in_replay'):
            env[field] = True
            setattr(renpy.store, field, True)
            env['original_gallery_record_image'](env['ORIGINAL_CG'][1][1])
            env['original_gallery_complete_scenario']('DEMO_B.FOB')
            self.assertEqual(before, env['persistent'].original_completed_scenarios)
            self.assertFalse(env['original_gallery_unlocked']('cg', 1))
            env[field] = False
            setattr(renpy.store, field, False)

if __name__ == '__main__':
    unittest.main()
