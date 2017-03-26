#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  IkaLog
#  ======
#  Copyright (C) 2016 Takeshi HASEGAWA
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

from .game.start import V2GameStart as GameStart
from .game.session import V2GameSession as GameSession
from .game.respawn import V2GameRespawn as GameRespawn
from .game.special_gauge.background import V2GameSpecialGaugeBackground as GameSpecialGaugeBackground
from .game.special_gauge.gauge import V2GameSpecialGauge as GameSpecialGauge
from .game.special_gauge.level import V2GameSpecialGaugeLevel as GameSpecialGaugeLevel
from .game.special_gauge.sub_and_special import V2GameSubAndSpecial as GameSubAndSpecial
from .game.superjump import V2GameSuperJump as GameSuperJump
from .game.kill import V2GameKill as GameKill
from .game.dead import V2GameDead as GameDead

from .lobby import V2Lobby as Lobby

from .result.judge import V2ResultJudge as ResultJudge
from .result.scoreboard.simple import ResultScoreboard as ResultScoreboard

from ikalog.scenes.botw.dead import BOTWDead


def initialize_scenes(engine):
    import ikalog.scenes as scenes

    s = [
        scenes.GameTimerIcon(engine),
        GameSession(engine),

        GameStart(engine),
        GameRespawn(engine),

        GameSpecialGauge(engine),
        GameSpecialGaugeBackground(engine),
        GameSpecialGaugeLevel(engine),
        #        GameSubAndSpecial(engine),

        GameSuperJump(engine),
        GameKill(engine),
        GameDead(engine),

        Lobby(engine),

        ResultJudge(engine),
        ResultScoreboard(engine),

        BOTWDead(engine),

        scenes.Blank(engine),
    ]
    return s
