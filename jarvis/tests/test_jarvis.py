"""JARVIS ke unit tests (bina mic, bina awaaz, bina app khole)."""
from __future__ import annotations

import datetime as dt
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "jarvis"))

import jarvis.config as config  # noqa: E402
from jarvis import tools  # noqa: E402
from jarvis import brain as brainmod  # noqa: E402
from jarvis import rules as brainmod_rules  # noqa: E402

OPENED: list[str] = []


def _fake_open(url, *a, **k):
    OPENED.append(url)
    return True


class Base(unittest.TestCase):
    def setUp(self):
        OPENED.clear()
        self.tmp = Path(tempfile.mkdtemp())
        config.NOTES_FILE = self.tmp / "notes.txt"
        config.REMINDERS_FILE = self.tmp / "reminders.json"
        config.HISTORY_FILE = self.tmp / "history.jsonl"
        config.AUDIO_DIR = self.tmp
        tools.scheduler.stop()          # pichle test ka thread nahi rehna chahiye
        self._patches = [
            mock.patch.object(tools.webbrowser, "open", _fake_open),
            mock.patch.object(tools, "IS_WINDOWS", False),
        ]
        for p in self._patches:
            p.start()

    def tearDown(self):
        tools.scheduler.stop()
        for p in self._patches:
            p.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)


# =================================================================== TOOLS
class TestTools(Base):
    def test_time(self):
        r = tools.get_time()
        self.assertTrue(r["ok"])
        self.assertIn("baje", r["speech"])

    def test_math_words_and_symbols(self):
        self.assertEqual(tools.do_math("250 * 4 + 15")["text"].split("=")[1].strip(), "1015")
        self.assertIn("1015", tools.do_math("250 guna 4 plus 15 kitna hota hai")["speech"])
        self.assertFalse(tools.do_math("hello world")["ok"])
        self.assertIn("9", tools.do_math("sqrt(81)")["speech"])

    def test_math_is_safe(self):
        # __import__ / os.system jaisi cheez chalni nahi chahiye
        self.assertFalse(tools.do_math("__import__('os').system('echo hacked')")["ok"])

    def test_reminder_parse(self):
        now = dt.datetime.now()
        cases = {
            "10 minute baad": 10,
            "2 hour baad": 120,
            "1 day baad": 24 * 60,
        }
        for txt, minutes in cases.items():
            when = tools._parse_time_hint(txt, now)
            self.assertIsNotNone(when, txt)
            diff = (when - now).total_seconds() / 60
            self.assertAlmostEqual(diff, minutes, delta=0.6)

    def test_reminder_clock_time_tomorrow(self):
        now = dt.datetime(2026, 9, 4, 20, 0)
        when = tools._parse_time_hint("shaam 6 baje", now)
        self.assertEqual(when, dt.datetime(2026, 9, 5, 18, 0))

    def test_set_and_list_reminder(self):
        r = tools.set_reminder("2 minute baad", "paani piyo")
        self.assertTrue(r["ok"], r)
        lst = tools.list_reminders()
        self.assertTrue(lst["ok"])
        self.assertIn("paani piyo", lst["text"])
        self.assertTrue(tools.delete_reminder("all")["ok"])
        self.assertEqual(tools.list_reminders()["speech"], "Abhi koi reminder set nahi hai.")

    def test_fire_calls_callback(self):
        """Reminder khatam hone par ON_REMINDER callback chale (JARVIS bolega)."""
        fired = []
        old = tools.ON_REMINDER
        tools.ON_REMINDER = lambda t: fired.append(t)
        try:
            tools._fire({"id": "x", "message": "paani piyo"})
            self.assertEqual(len(fired), 1)
            self.assertIn("paani piyo", fired[0])
        finally:
            tools.ON_REMINDER = old

    def test_scheduled_reminder_actually_fires(self):
        """Scheduler due reminder ko fire karta hai aur file se hata deta hai."""
        fired = []
        old = tools.ON_REMINDER
        tools.ON_REMINDER = lambda t: fired.append(t)
        try:
            r = tools.set_reminder("0 minute", "dawa lena")
            self.assertTrue(r["ok"], r)
            due = tools.scheduler.tick()
            self.assertEqual(len(due), 1)
            self.assertIn("dawa lena", fired[0])
            self.assertEqual(tools._load_reminders(), [], "due reminder file se hatna chahiye tha")
        finally:
            tools.ON_REMINDER = old

    def test_future_reminder_not_fired_early(self):
        fired = []
        old = tools.ON_REMINDER
        tools.ON_REMINDER = lambda t: fired.append(t)
        try:
            tools.set_reminder("5 minute", "baad ka kaam")
            self.assertEqual(tools.scheduler.tick(), [])
            self.assertFalse(fired)
            self.assertEqual(len(tools._load_reminders()), 1)
        finally:
            tools.ON_REMINDER = old

    def test_scheduler_thread_is_daemon(self):
        """Non-daemon thread se process atak jaata tha - ye pakka karo ki daemon hai."""
        tools.scheduler.start()
        try:
            th = tools.scheduler._thread
            self.assertTrue(th.daemon)
            self.assertTrue(th.is_alive())
        finally:
            tools.scheduler.stop()
        self.assertIsNone(tools.scheduler._thread)

    def test_notes(self):
        self.assertTrue(tools.add_note("doodh lana hai")["ok"])
        self.assertFalse(tools.add_note("   ")["ok"])
        r = tools.read_notes()
        self.assertIn("doodh lana hai", r["text"])

    def test_open_app_known(self):
        with mock.patch.object(tools.subprocess, "Popen") as popen:
            r = tools.open_app("notepad")
        self.assertTrue(r["ok"])
        popen.assert_called_once()

    def test_open_app_known_with_run(self):
        with mock.patch.object(tools.subprocess, "run") as run:
            r = tools.open_app("notepad")
        self.assertTrue(r["ok"])
        run.assert_called_once()

    def test_open_app_website(self):
        r = tools.open_app("google.com")
        self.assertTrue(r["ok"])
        self.assertIn("google.com", OPENED[-1])

    def test_play_media_builds_url(self):
        with mock.patch.object(tools, "_yt_first_video", return_value=None):
            tools.play_media("arijit singh", "song")
        self.assertIn("youtube.com", OPENED[-1])
        self.assertIn("arijit", OPENED[-1])
        tools.play_media("tum hi ho", "spotify")
        self.assertIn("spotify.com", OPENED[-1])

    def test_volume_not_windows(self):
        self.assertFalse(tools.volume("up")["ok"])

    def test_system_control_not_windows(self):
        self.assertFalse(tools.system_control("shutdown")["ok"])

    def test_whatsapp_needs_number(self):
        self.assertFalse(tools.send_whatsapp("", "hi")["ok"])
        r = tools.send_whatsapp("9876543210", "main aa raha hoon")
        self.assertTrue(r["ok"])
        self.assertIn("wa.me/919876543210", OPENED[-1])

    def test_search_file(self):
        (self.tmp / "resume_final.pdf").write_text("x")
        r = tools.search_file("resume", str(self.tmp))
        self.assertTrue(r["ok"])
        self.assertIn("resume_final.pdf", r["text"])
        self.assertFalse(tools.search_file("zzz_nahi_milega", str(self.tmp))["ok"])

    def test_run_tool_unknown_and_bad_args(self):
        self.assertFalse(tools.run_tool("no_such_tool")["ok"])
        self.assertFalse(tools.run_tool("do_math", {"galat_arg": 1})["ok"])

    def test_joke_and_compliment(self):
        self.assertTrue(tools.joke()["ok"])
        self.assertTrue(tools.compliment()["ok"])

    def test_tool_schemas_match_registry(self):
        """Schema mein jo naam hain, wo tools mein hone chahiye (warna LLM crash karega)."""
        names = {s["function"]["name"] for s in tools.TOOL_SCHEMAS}
        missing = names - set(tools.TOOLS)
        self.assertEqual(missing, set(), f"schema mein hai par tool nahi: {missing}")
        for s in tools.TOOL_SCHEMAS:
            fn = s["function"]
            self.assertIn("description", fn)
            self.assertIn("properties", fn["parameters"])


# =================================================================== NETWORK (best effort)
class TestNetworkTools(Base):
    def test_weather(self):
        r = tools.get_weather("Jabalpur")
        if not r["ok"]:
            self.skipTest("network unavailable: " + str(r.get("text")))
        self.assertIn("degree", r["speech"])

    def test_wikipedia(self):
        r = tools.wikipedia_summary("India", 2)
        if not r["ok"]:
            self.skipTest("network unavailable: " + str(r.get("text")))
        self.assertGreater(len(r["text"]), 30)

    def test_web_search(self):
        r = tools.web_search("python programming")
        if not r["ok"]:
            self.skipTest("network unavailable: " + str(r.get("text")))
        self.assertTrue(r["speech"])


# =================================================================== RULE ENGINE
class TestRuleEngine(Base):
    def test_time_question(self):
        r = brainmod.rule_engine("kitne baje hain")
        self.assertIsNotNone(r)
        self.assertIn("baje", r["speech"])

    def test_math_question(self):
        r = brainmod.rule_engine("250 guna 4 kitna hota hai")
        self.assertIsNotNone(r)
        self.assertIn("1000", r["speech"])

    def test_reminder_question(self):
        r = brainmod.rule_engine("10 minute baad paani peene ka reminder laga")
        self.assertIsNotNone(r)
        self.assertTrue(r["ok"], r)

    def test_reminder_without_time_fails_gracefully(self):
        r = brainmod.rule_engine("reminder laga do")
        self.assertIsNotNone(r)
        self.assertFalse(r["ok"])

    def test_weather(self):
        r = brainmod.rule_engine("jabalpur ka mausam kaisa hai")
        self.assertIsNotNone(r)

    def test_open_app(self):
        with mock.patch.object(tools.subprocess, "Popen"):
            r = brainmod.rule_engine("notepad kholo")
        self.assertIsNotNone(r)
        self.assertTrue(r["ok"])

    def test_note(self):
        r = brainmod.rule_engine("note karo doodh lana hai")
        self.assertIsNotNone(r)
        self.assertIn("doodh", tools.read_notes()["text"])

    def test_greeting_and_bye(self):
        self.assertIsNotNone(brainmod.rule_engine("namaste jarvis"))
        bye = brainmod.rule_engine("bye jarvis")
        self.assertTrue(bye.get("stop"))

    def test_unknown_returns_none(self):
        self.assertIsNone(brainmod.rule_engine("quantum entanglement ke baare mein philosophical view"))

    def test_joke(self):
        self.assertIsNotNone(brainmod.rule_engine("ek joke sunao"))


# =================================================================== BRAIN
class TestBrain(Base):
    def setUp(self):
        super().setUp()
        # Ollama ko band dikhao -> rule engine / fallback path test hoga
        self._p = mock.patch.object(brainmod, "ollama_alive", lambda host=None: False)
        self._p.start()

    def tearDown(self):
        self._p.stop()
        super().tearDown()

    def test_rule_path(self):
        b = brainmod.Brain()
        r = b.think("kitne baje hain")
        self.assertEqual(r["source"], "rule")
        self.assertTrue(r["ok"])

    def test_fallback_path(self):
        b = brainmod.Brain()
        r = b.think("quantum philosophy pe gehra vichar do")
        self.assertEqual(r["source"], "fallback")
        self.assertFalse(r["ok"])

    def test_history_is_kept(self):
        b = brainmod.Brain()
        b.think("kitne baje hain")
        b.think("ek joke sunao")
        roles = [m["role"] for m in b.messages]
        self.assertGreaterEqual(roles.count("user"), 2)
        self.assertEqual(roles[0], "system")

    def test_history_file_written(self):
        b = brainmod.Brain()
        b.think("kitne baje hain")
        self.assertTrue(config.HISTORY_FILE.exists())
        line = config.HISTORY_FILE.read_text(encoding="utf-8").strip().splitlines()[-1]
        self.assertIn("jarvis", json.loads(line))

    def test_empty_input(self):
        self.assertFalse(brainmod.Brain().think("   ")["ok"])

    def test_llm_tool_call_path(self):
        """Ollama ka tool_call wala flow (mock se) - _call_ollama mock hai, par ASLI tool chalta hai."""
        b = brainmod.Brain()
        ask = "mood thoda off hai, kuch halka sa likh kar sunao please"
        # pehle confirm karo ki ye rule engine mein nahi phasta (warna test jhootha pass hoga)
        self.assertIsNone(brainmod.rule_engine(ask))
        seq = [
            {"message": {"tool_calls": [{"function": {"name": "compliment", "arguments": {}}}]}},
            {"message": {"content": "Aap kamaal karte ho, mood theek ho jayega!"}},
        ]
        with mock.patch.object(brainmod, "ollama_alive", lambda host=None: True), \
             mock.patch.object(brainmod, "_call_ollama", side_effect=seq):
            r = b.think(ask)
        self.assertEqual(r["source"], "llm")
        self.assertIn("kamaal", r["speech"])
        self.assertIn("compliment", r["tools"])
        # tool ke messages conversation mein judne chahiye
        self.assertIn("tool", [m["role"] for m in b.messages])

    def test_llm_handles_tool_crash(self):
        b = brainmod.Brain()
        seq = [
            {"message": {"tool_calls": [{"function": {"name": "no_such_tool", "arguments": {}}}]}},
            {"message": {"content": "Maaf karna, wo kaam nahi ho paya."}},
        ]
        with mock.patch.object(brainmod, "ollama_alive", lambda host=None: True), \
             mock.patch.object(brainmod, "_call_ollama", side_effect=seq):
            r = b.think("please kuch karo jo possible nahi")
        self.assertEqual(r["source"], "llm")
        self.assertIn("Maaf", r["speech"])

    def test_llm_down_falls_back(self):
        b = brainmod.Brain()
        with mock.patch.object(brainmod, "_call_ollama", side_effect=AssertionError("call nahi hona chahiye tha")):
            r = b.think("kuch aisa pooch raha hoon jo rule engine nahi jaanta")
        self.assertIn(r["source"], ("fallback", "rule"))

    def test_stream_path(self):
        b = brainmod.Brain()
        got = []
        r = b.think_stream("kitne baje hain", got.append)
        self.assertEqual("".join(got), r["speech"])
        self.assertEqual(r["source"], "rule")


# =================================================================== SPEAKER
class TestSpeaker(Base):
    def test_clean_and_trim(self):
        import speak
        self.assertEqual(speak._clean("hello   world"), "hello world")
        self.assertNotIn("http", speak._clean("dekho https://example.com/page"))
        self.assertLessEqual(len(speak._trim("a" * 5000, 100)), 101)

    def test_muted_says_nothing(self):
        import speak
        s = speak.Speaker(muted=True)
        self.assertEqual(s.say("kuch bhi"), "")

    def test_engine_fallback_chain(self):
        """Pehla engine fail ho to dusra chale."""
        import speak
        calls = []
        s = speak.Speaker(engines=["edge", "gTTS"])
        with mock.patch.object(speak, "_ENGINES", {
                "edge": lambda t: (calls.append("edge"), False)[1],
                "gTTS": lambda t: (calls.append("gTTS"), True)[1]}):
            s.say("test", block=True)
        self.assertEqual(calls, ["edge", "gTTS"])
        self.assertEqual(s.active, "gTTS")

    def test_available_lists_only_installed(self):
        import speak
        for name in speak.Speaker().available():
            self.assertIn(name, ("edge", "gTTS", "piper", "say"))


# =================================================================== WEB APP
class TestWebApp(Base):
    @classmethod
    def setUpClass(cls):
        try:
            from fastapi.testclient import TestClient
        except Exception as e:      # pragma: no cover
            raise unittest.SkipTest(f"fastapi/testclient nahi hai: {e}")
        import webapp
        cls.TestClient = TestClient
        cls.webapp = webapp
        cls.client = TestClient(webapp.app)

    def setUp(self):
        super().setUp()
        with mock.patch.object(brainmod, "ollama_alive", lambda host=None: False):
            pass

    def test_index_html(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("J.A.R.V.I.S", r.text)
        self.assertIn("/api/chat/stream", r.text)

    def test_status(self):
        r = self.client.get("/api/status")
        self.assertEqual(r.status_code, 200)
        d = r.json()
        self.assertEqual(d["name"], config.ASSISTANT_NAME)
        self.assertIn("set_reminder", d["tools"])
        self.assertGreater(len(d["tools"]), 15)

    def test_chat_endpoint(self):
        with mock.patch.object(brainmod, "ollama_alive", lambda host=None: False):
            r = self.client.post("/api/chat", json={"text": "kitne baje hain"})
        self.assertEqual(r.status_code, 200)
        d = r.json()
        self.assertIn("speech", d)
        self.assertIn("baje", d["speech"])

    def test_chat_stream(self):
        with mock.patch.object(brainmod, "ollama_alive", lambda host=None: False):
            r = self.client.get("/api/chat/stream?q=" + "ek joke sunao".replace(" ", "%20"))
        self.assertEqual(r.status_code, 200)
        body = r.text
        self.assertIn("event: done", body)

    def test_reminders_endpoint(self):
        r = self.client.get("/api/reminders")
        self.assertEqual(r.status_code, 200)

    def test_reset_endpoint(self):
        self.assertTrue(self.client.post("/api/reset").json()["ok"])

    def test_speak_endpoint_without_edge_tts(self):
        """edge-tts na ho to 500 + JSON error aana chahiye (crash nahi)."""
        import webapp
        with mock.patch.dict(sys.modules, {"edge_tts": None}):
            r = self.client.post("/api/speak", json={"text": "hello", "play_local": False})
        self.assertEqual(r.status_code, 500)
        self.assertIn("error", r.json())


if __name__ == "__main__":
    unittest.main(verbosity=2)


# =================================================================== REGRESSION
# Ye sab wo asli Hinglish phrases hain jinme pehle bugs the.
# Inhe todna = purana bug wapas aa gaya.
class TestHinglishPhrases(Base):
    def _r(self, text):
        r = brainmod.rule_engine(text)
        self.assertIsNotNone(r, f"rule engine ne '{text}' nahi pakda (LLM pe chala jayega)")
        return r

    # ---- reminders: message sahi nikle (pehle time-words message kha jaate the)
    def test_reminder_messages(self):
        cases = {
            "10 minute baad paani peene ka reminder laga": "paani peene",
            "2 hour baad dawai khane ka reminder": "dawai khane",
            "shaam 6 baje meeting ka reminder": "meeting",
            "kal subah 9 baje gym ka reminder laga": "gym",
            "yaad dilana papa ko call karna 10 minute baad": "papa ko call karna",
        }
        for phrase, expected in cases.items():
            r = self._r(phrase)
            self.assertTrue(r["ok"], phrase)
            self.assertIn(expected, r["speech"], f"{phrase} -> {r['speech']}")

    def test_reminder_needs_a_time(self):
        r = self._r("reminder laga do")
        self.assertFalse(r["ok"])
        self.assertIn("Kab yaad dilaun", r["speech"])

    # ---- file search vs app open (pehle dono ulte ho jaate the)
    def test_file_search_phrases(self):
        (self.tmp / "my_resume_2026.pdf").write_text("x")
        for phrase in ("resume file dhoondho", "file dhoondho resume", "dhoondho resume file",
                       "mera resume file dhoondho"):
            with mock.patch.object(tools.config, "SEARCH_FOLDERS", [str(self.tmp)]):
                r = self._r(phrase)
            self.assertTrue(r["ok"], f"{phrase} -> {r}")
            self.assertIn("my_resume_2026.pdf", r["text"], phrase)

    def test_open_app_still_works(self):
        for phrase in ("notepad kholo", "open notepad", "calculator chalao"):
            with mock.patch.object(tools.subprocess, "Popen"):
                r = self._r(phrase)
            self.assertTrue(r["ok"], f"{phrase} -> {r}")

    def test_open_website(self):
        r = self._r("google.com kholo")
        self.assertTrue(r["ok"])
        self.assertIn("google.com", OPENED[-1])

    # ---- weather: sheher sahi nikle (pehle "mausam" ko sheher maan leta tha)
    def test_weather_city_extraction(self):
        self.assertEqual(brainmod_rules._extract_city("jabalpur ka mausam"), "jabalpur")
        self.assertEqual(brainmod_rules._extract_city("weather in bhopal"), "bhopal")
        self.assertEqual(brainmod_rules._extract_city("mumbai ka weather"), "mumbai")
        self.assertEqual(brainmod_rules._extract_city("mausam kaisa hai"), config.DEFAULT_CITY)
        self.assertEqual(brainmod_rules._extract_city("aaj kitni garmi hai"), config.DEFAULT_CITY)

    def test_weather_uses_default_city(self):
        with mock.patch.object(tools, "get_weather", return_value={"ok": True, "speech": "x", "text": ""}) as gw:
            self._r("mausam kaisa hai")
        gw.assert_called_once_with(config.DEFAULT_CITY)

    # ---- wikipedia: "X kaun hai" search ban jaata tha
    def test_wikipedia_who_is(self):
        with mock.patch.object(tools, "wikipedia_summary",
                               return_value={"ok": True, "speech": "cricketer", "text": "t"}) as ws:
            self._r("virat kohli kaun hai")
            self._r("taj mahal ke baare mein bata")
            self._r("wikipedia india")
        self.assertEqual([c.args[0] for c in ws.call_args_list],
                         ["virat kohli", "taj mahal", "india"])

    # ---- search: "python search karo" -> query "python" hona chahiye
    def test_search_query(self):
        with mock.patch.object(tools, "web_search",
                               return_value={"ok": True, "speech": "s", "text": ""}) as wsr:
            self._r("python search karo")
            self._r("search python")
            self._r("google karo machine learning")
        self.assertEqual([c.args[0] for c in wsr.call_args_list],
                         ["python", "python", "machine learning"])

    # ---- media
    def test_media_phrases(self):
        with mock.patch.object(tools, "play_media",
                               return_value={"ok": True, "speech": "s", "text": ""}) as pm:
            self._r("arijit singh ka gaana chalao")
            self._r("play tum hi ho")
        self.assertEqual(pm.call_args_list[0].args, ("arijit singh", "song"))
        self.assertEqual(pm.call_args_list[1].args[0], "tum hi ho")

    def test_joke_not_played_on_youtube(self):
        with mock.patch.object(tools, "play_media") as pm:
            r = self._r("ek joke sunao")
        pm.assert_not_called()
        self.assertTrue(r["ok"])

    # ---- whatsapp / notes / math / time
    def test_whatsapp_phrase(self):
        r = self._r("whatsapp bhej 9876543210 main aa raha hoon")
        self.assertTrue(r["ok"])
        self.assertIn("wa.me/919876543210", OPENED[-1])
        self.assertIn("main%20aa%20raha%20hoon", OPENED[-1])

    def test_note_phrase(self):
        r = self._r("note karo doodh lana hai")
        self.assertTrue(r["ok"])
        self.assertIn("doodh lana hai", tools.read_notes()["text"])

    def test_math_phrases(self):
        self.assertIn("1015", self._r("250 guna 4 plus 15 kitna hota hai")["speech"])
        self.assertIn("15", self._r("100 ka 15 percent")["speech"])
        self.assertIn("144", self._r("12 times 12")["speech"])

    def test_time_phrases(self):
        for p in ("kitne baje hain", "aaj ki date kya hai", "what time is it"):
            self.assertIn("baje", self._r(p)["speech"])

    def test_bye_stops(self):
        self.assertTrue(self._r("bye jarvis").get("stop"))

    def test_media_phrases_round2(self):
        """Bol-chaal wale andaaz bhi instant rule-engine se music chalayein."""
        with mock.patch.object(tools, "play_media",
                               return_value={"ok": True, "speech": "s", "text": ""}) as pm:
            self._r("youtube se gana bajao")
            self._r("yt pe tum hi ho chalao")
            self._r("arijit singh ka gaana lagao")
            self._r("gana sunao")
        self.assertEqual([c.args for c in pm.call_args_list],
                         [("", "song"), ("tum hi ho", "youtube"),
                          ("arijit singh", "song"), ("", "song")])

    def test_play_media_empty_opens_home(self):
        tools.play_media("", "song")
        self.assertEqual(OPENED[-1], "https://www.youtube.com")
        tools.play_media("", "spotify")
        self.assertEqual(OPENED[-1], "https://open.spotify.com")


    # ---------------------------------------------------------- DEVANAGARI
    # Google STT aksar Devanagari Hindi deta hai ("कितने बजे हैं") -
    # pehle ye sab slow Ollama pe jaata tha, ab instant rule-engine.
    def test_devanagari_phrases(self):
        with mock.patch.object(tools.subprocess, "Popen"):
            self.assertTrue(self._r("नोटपैड खोलो")["ok"])
        self.assertIn("15", self._r("१०० का १५ प्रतिशत")["speech"])
        self.assertIn("baje", self._r("कितने बजे हैं")["speech"])
        self.assertTrue(self._r("सिस्टम इन्फो बताओ मेरे पी सी का")["ok"])
        self.assertIn("100", self._r("२५ गुणा ४")["speech"])
        self.assertIn("1000", self._r("२५० गुणा ४")["speech"])

    def test_devanagari_media(self):
        with mock.patch.object(tools, "play_media",
                               return_value={"ok": True, "speech": "s", "text": ""}) as pm:
            self._r("यूट्यूब से गाना बजाओ")
            self._r("अरिजित सिंह का गाना चलाओ")
            self._r("गाना सुनाओ")
        self.assertEqual([c.args for c in pm.call_args_list],
                         [("", "song"), ("अरिजित सिंह", "song"), ("", "song")])

    def test_devanagari_reminder_time(self):
        r = self._r("शाम ६ बजे मीटिंग का रिमाइंडर")
        self.assertTrue(r["ok"])
        self.assertIn("6 baje", r["speech"])
        r2 = self._r("१० मिनट बाद पानी पीने का रिमाइंडर लगाओ")
        self.assertTrue(r2["ok"])
        self.assertIn("पानी पीने", r2["speech"])

    def test_youtube_autoplay_first_video(self):
        """Gaana sirf page nahi khule - pehla video BAJE (watch?v=...)."""
        with mock.patch.object(tools, "_yt_first_video", return_value="abc12345678"):
            r = tools.play_media("tum hi ho")
        self.assertIn("watch?v=abc12345678", r["text"])
        self.assertIn("suniye", r["speech"])

    def test_youtube_fallback_search_page(self):
        with mock.patch.object(tools, "_yt_first_video", return_value=None):
            r = tools.play_media("tum hi ho")
        self.assertIn("results?search_query=", r["text"])


# =================================================================== LISTENER
class TestListener(Base):
    def test_backend_detected(self):
        from listen import Listener
        self.assertIn(Listener().backend_name(), ("sounddevice", "pyaudio", "none"))

    def test_record_raises_cleanly_without_backend(self):
        """Mic backend na ho to ERROR SPAM nahi - ek saaf NoMicError."""
        from listen import Listener, NoMicError
        l = Listener()
        if l.backend_name() != "none":
            self.skipTest("is machine pe backend available hai")
        with self.assertRaises(NoMicError):
            l.record()

    def test_listen_once_empty_on_silence(self):
        from listen import Listener, NoMicError
        l = Listener()
        if l.backend_name() == "none":
            self.skipTest("backend nahi hai")
        self.assertEqual(l.listen_once(timeout=1, phrase_limit=1), "")

    def test_list_mics_returns_list(self):
        from listen import Listener
        self.assertIsInstance(Listener.list_microphones(), list)

    def test_wake_word_raises_nomic_without_backend(self):
        from listen import Listener, NoMicError
        l = Listener()
        if l.backend_name() != "none":
            self.skipTest("backend available")
        with self.assertRaises(NoMicError):
            l.listen_for_wake_word()


    def test_cloud_groq_tool_call_path(self):
        """Groq cloud brain ka tool-calling flow (mock) - asli tool chalta hai."""
        b = brainmod.Brain()
        ask = "cloud dimaag se wo poochho jo rules kabhi nahi jaante"
        self.assertIsNone(brainmod.rule_engine(ask))
        seq = [
            {"tool_calls": [{"function": {"name": "compliment", "arguments": "{}"}}]},
            {"content": "Aap kamaal karte ho!"},
        ]
        with mock.patch.object(brainmod, "groq_key", lambda: "test-key"), \
             mock.patch.object(brainmod, "_call_cloud_msg", side_effect=seq):
            r = b.think(ask)
        self.assertEqual(r["source"], "llm")
        self.assertIn("kamaal", r["speech"])
        self.assertIn("compliment", r["tools"])

    def test_groq_error_falls_back_to_rule_or_ollama_off(self):
        """Groq fail ho to crash nahi - fallback."""
        b = brainmod.Brain()
        with mock.patch.object(brainmod, "groq_key", lambda: "bad-key"), \
             mock.patch.object(brainmod, "_call_cloud_msg", side_effect=RuntimeError("401")), \
             mock.patch.object(brainmod, "ollama_alive", lambda host=None: False):
            r = b.think("aisa sawaal jo koi engine nahi jaanta bilkul")
        self.assertIn(r["source"], ("fallback", "rule"))
