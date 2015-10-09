import unittest
import os
import cv2

class TestSceneLobbyVideos(unittest.TestCase):

    scene_name = 'lobby'

    def _load_screenshot(self, filename):
        filepath = os.path.join('test_data', 'movies',
            self.scene_name, filename)

    def noop(self, context):
        pass

    def on_frame_read_failed(self, context):
        self.engine.stop()

    def onUncatchedEvent(self, event_name, context):
        if not (event_name in self.event_tickets):
            self.errors.append('Unexpected event %s triggered' % event_name)

        if self.event_tickets[event_name] is None:
            return

        self.event_tickets[event_name] = self.event_tickets[event_name] - 1

        if not (0 <= self.event_tickets[event_name]):
            self.errors.append('Too many events triggered: %s' % event_name)

    def _test_engine(self, mp4_filename):
        from ikalog.inputs.cvcapture import CVCapture
        from ikalog.engine import IkaEngine
        from ikalog.outputs.preview import Screen
        from ikalog.outputs.debug import DebugLog

        self.errors = []
        source = CVCapture()
        source.start_recorded_file(mp4_filename)
        source.need_resize = True
        outputPlugins = [
            self, 
            Screen(0, size=(640, 360)),
            DebugLog(dir='./debug/', screenshot=True),
        ]

        self.engine = IkaEngine()

        self.engine.set_capture(source)
        self.engine.set_plugins(outputPlugins)
        self.engine.pause(False)

        print('Engine started')
        self.engine.run()
        print('Engine stopped')

        # 期待されたイベントが全て発生しているか確認
        for event_name in list(self.event_tickets.keys()):
            if self.event_tickets[event_name] is None:
                continue
            assert self.event_tickets[event_name] == 0, 'Missed event %s? %s tickets remained.' % event_name

        assert len(self.errors) == 0, '\n'.join(self.errors)

        return self.engine

    def test_lobby_tag_2_matching_to_matched(self):
        self.event_tickets = {
            # Events expected
            'on_lobby_matched': 1,
            'on_lobby_matching': 1,

            # Events don't care
            'on_debug_read_next_frame': None,
            'on_frame_read': None,
        }

        engine = self._test_engine('test_data/movies/lobby/lobby_tag_2_matching_to_matched.mp4')

        assert engine.context['lobby']['type'] == 'tag'
        assert engine.context['lobby']['state'] == 'matched'
        assert engine.context['lobby']['team_members'] == 2

    def test_lobby_public_matching_to_matched(self):
        self.event_tickets = {
            # Events expected
            'on_lobby_matched': 1,
            'on_lobby_matching': 1,

            # Events don't care
            'on_debug_read_next_frame': None,
            'on_frame_read': None,
        }

        engine = self._test_engine('test_data/movies/lobby/lobby_public_matching_to_matched.mp4')

        assert engine.context['lobby']['type'] == 'public'
        assert engine.context['lobby']['state'] == 'matched'

